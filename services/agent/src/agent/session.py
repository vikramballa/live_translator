"""A translator session inside one LiveKit room (two people).

For every human participant the agent:
  * listens to their microphone: VAD → adaptive endpointing → utterances;
  * translates each utterance into the *other* person's language;
  * publishes one audio track per listener named ``tr:<identity>``, so each
    browser subscribes only to the translation meant for it;
  * sends captions, Key-Facts and status as JSON on the data channel.

Ordering: each utterance gets an ``UtteranceAudio`` stream that is queued for
the listener at the moment the speaker *stops* talking, so audio always
plays in speaking order even though translation runs concurrently; within an
utterance the first sentence plays while later ones are still synthesised.

Privacy: no audio or text is written to disk or logs; logs carry timings only.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import math
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

import numpy as np
from livekit import api, rtc

from pipeline_core.endpointing import (
    Endpointer,
    SpeechCancelled,
    SpeechEnd,
    SpeechStart,
    config_for,
)

from . import translator
from .audio import VAD_FRAME, SileroVAD, float_to_int16, int16_to_float, resample, silero_model_path
from .engines import preload
from .settings import enabled_pairs, routes, settings
from .tts_client import TTSClient, TTSError

log = logging.getLogger(__name__)

TOPIC_EVENTS = "lt.events"  # agent → browsers
TOPIC_CONTROL = "lt.control"  # browsers → agent
OUT_RATE = 48_000
OUT_FRAME = OUT_RATE // 50  # 20 ms
EMPTY_ROOM_GRACE_S = 60.0
INTERIM_EVERY_S = 1.0
# Limits on what one participant can make the shared server do. A person
# speaking normally has 1-2 translations pending; bursts of noise must not
# queue unbounded work that slows every other call.
MAX_PENDING_TRANSLATIONS = 4
CONTROL_COOLDOWN_S = 1.5  # between "repeat" / "didn't understand" taps
MAX_QUEUED_PLAYOUT = 6

# Said to a speaker when the listener taps "Didn't understand".
DIDNT_UNDERSTAND = {
    "en": "They didn't understand. Please say it again, slowly and simply.",
    "te": "వారికి అర్థం కాలేదు. దయచేసి మళ్ళీ నెమ్మదిగా, సులభంగా చెప్పండి.",
    "hi": "उन्हें समझ नहीं आया। कृपया फिर से धीरे और आसान शब्दों में कहें।",
    "zh": "对方没有听懂。请慢一点、简单一点再说一遍。",
}
# ASR engines fast enough to run interim (live) captions on CPU.
_INTERIM_ENGINES = {"parakeet", "indic_conformer"}


@dataclass
class UtteranceAudio:
    """Audio for one translated utterance, filled sentence by sentence."""

    chunks: asyncio.Queue[np.ndarray | None] = field(default_factory=asyncio.Queue)
    played: list[np.ndarray] = field(default_factory=list)


@dataclass
class Person:
    identity: str
    lang: str
    source: rtc.AudioSource
    track: rtc.LocalAudioTrack
    playout: asyncio.Queue[UtteranceAudio] = field(default_factory=asyncio.Queue)
    last_played: list[np.ndarray] = field(default_factory=list)
    tasks: list[asyncio.Task] = field(default_factory=list)
    seq: int = 0
    speech_rate: float = 1.0
    pending: int = 0  # translations of this person's speech still running
    last_control: float = float("-inf")


class RoomSession:
    def __init__(self, room_name: str, pool: ThreadPoolExecutor, tts: TTSClient) -> None:
        self.room_name = room_name
        self.room = rtc.Room()
        self.pool = pool
        self.tts = tts
        self.people: dict[str, Person] = {}
        # Every language that joined; the room outlives its last caller by
        # EMPTY_ROOM_GRACE_S, so the agent's idle-model check always sees them.
        self.seen_langs: set[str] = set()
        self.closed = asyncio.Event()
        self._empty_since: float | None = time.monotonic()
        self._bg: set[asyncio.Task] = set()

    # --- Setup ---
    def _token(self) -> str:
        s = settings()
        return (
            api.AccessToken(s.livekit_api_key, s.livekit_api_secret)
            .with_identity(s.agent_identity)
            .with_name("Translator")
            .with_kind("agent")
            .with_grants(api.VideoGrants(room_join=True, room=self.room_name, can_publish=True,
                                         can_subscribe=True, can_publish_data=True, agent=True))
            .to_jwt()
        )

    async def run(self) -> None:
        room = self.room
        room.on("participant_connected", lambda p: self._spawn(self._on_join(p)))
        room.on("participant_disconnected", lambda p: self._spawn(self._on_leave(p)))
        room.on("track_published", self._on_published)
        room.on("track_subscribed", self._on_track)
        room.on("data_received", self._on_data)
        room.on("disconnected", lambda *_: self.closed.set())

        await room.connect(settings().livekit_url, self._token(),
                           rtc.RoomOptions(auto_subscribe=False))
        log.info("joined room %s", self.room_name)
        for p in list(room.remote_participants.values()):
            await self._on_join(p)
        try:
            while not self.closed.is_set():
                await asyncio.sleep(2)
                if self._empty_since and time.monotonic() - self._empty_since > EMPTY_ROOM_GRACE_S:
                    log.info("room %s empty; leaving", self.room_name)
                    break
        finally:
            await self.close()

    async def close(self) -> None:
        for person in self.people.values():
            for t in person.tasks:
                t.cancel()
        for t in list(self._bg):
            t.cancel()
        with contextlib.suppress(Exception):
            await self.room.disconnect()
        self.closed.set()

    def _spawn(self, coro) -> asyncio.Task:
        task = asyncio.ensure_future(coro)
        self._bg.add(task)
        task.add_done_callback(self._bg.discard)
        task.add_done_callback(_log_task_error)
        return task

    # --- Participants ---
    async def _on_join(self, p: rtc.RemoteParticipant) -> None:
        if p.kind == rtc.ParticipantKind.PARTICIPANT_KIND_AGENT or p.identity in self.people:
            return
        try:
            meta = json.loads(p.metadata or "{}")
            lang = meta["lang"]
        except (ValueError, KeyError):
            log.warning("participant without language metadata; ignoring")
            return
        if lang not in routes()["asr"]:
            log.warning("unsupported language %s", lang)
            return
        source = rtc.AudioSource(OUT_RATE, 1, queue_size_ms=1000)
        track = rtc.LocalAudioTrack.create_audio_track(f"tr:{p.identity}", source)
        await self.room.local_participant.publish_track(
            track, rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
        )
        person = Person(identity=p.identity, lang=lang, source=source, track=track)
        self.people[p.identity] = person
        self.seen_langs.add(lang)
        person.tasks.append(asyncio.create_task(self._playout_loop(person)))
        self._empty_since = None
        log.info("participant joined (%s); %d in room", lang, len(self.people))

        # Subscribe to their microphone.
        for pub in p.track_publications.values():
            if pub.kind == rtc.TrackKind.KIND_AUDIO:
                pub.set_subscribed(True)
        await self._announce_state()

    async def _on_leave(self, p: rtc.RemoteParticipant) -> None:
        person = self.people.pop(p.identity, None)
        if not person:
            return
        for t in person.tasks:
            t.cancel()
        with contextlib.suppress(Exception):
            await self.room.local_participant.unpublish_track(person.track.sid)
        if not self.people:
            self._empty_since = time.monotonic()
        await self._announce_state()

    def partner_of(self, identity: str) -> Person | None:
        return next((q for i, q in self.people.items() if i != identity), None)

    async def _announce_state(self) -> None:
        if len(self.people) < 2:
            await self._send({"type": "state", "state": "waiting"})
            return
        a, b = list(self.people.values())[:2]
        if a.lang == b.lang:
            await self._send({"type": "state", "state": "same_language"})
            return
        if frozenset((a.lang, b.lang)) not in enabled_pairs():
            await self._send({"type": "state", "state": "unsupported", "langs": [a.lang, b.lang]})
            return
        await self._send({"type": "state", "state": "loading"})
        langs = sorted({a.lang, b.lang})
        await asyncio.get_running_loop().run_in_executor(self.pool, preload, langs)
        await self._send({"type": "state", "state": "ready"})

    # --- Incoming audio ---
    def _on_published(self, pub: rtc.RemoteTrackPublication, p: rtc.RemoteParticipant) -> None:
        if pub.kind == rtc.TrackKind.KIND_AUDIO and p.identity in self.people:
            pub.set_subscribed(True)

    def _on_track(self, track: rtc.Track, _pub: rtc.RemoteTrackPublication,
                  p: rtc.RemoteParticipant) -> None:
        person = self.people.get(p.identity)
        if track.kind != rtc.TrackKind.KIND_AUDIO or person is None:
            return
        person.tasks.append(asyncio.create_task(self._listen(person, track)))

    async def _listen(self, speaker: Person, track: rtc.Track) -> None:
        loop = asyncio.get_running_loop()
        vad = SileroVAD(silero_model_path(), threads=1)
        ep = Endpointer(config_for(speaker.lang))
        stream = rtc.AudioStream(track, sample_rate=16_000, num_channels=1)
        pending = np.zeros(0, dtype=np.float32)
        frames: list[np.ndarray] = []  # VAD frames since `base`
        base = 0
        utt_start: int | None = None
        last_interim = 0.0
        interim_task: asyncio.Future | None = None
        interim_ok = routes()["asr"][speaker.lang]["engine"] in _INTERIM_ENGINES
        # Frames to keep while idle: pre-roll plus the frames needed to confirm speech start.
        keep_idle = (ep.config.pre_roll_ms + ep.config.min_start_ms) // ep.config.frame_ms + 4

        async for event in stream:
            pcm = np.frombuffer(event.frame.data, dtype=np.int16)
            pending = np.concatenate([pending, int16_to_float(pcm)])
            while pending.size >= VAD_FRAME:
                chunk, pending = pending[:VAD_FRAME], pending[VAD_FRAME:]
                frames.append(chunk)
                prob = vad(chunk)
                for ev in ep.push(prob):
                    if isinstance(ev, SpeechStart):
                        utt_start = ev.frame
                        await self._send({"type": "speaking", "identity": speaker.identity,
                                          "active": True})
                    elif isinstance(ev, SpeechCancelled):
                        utt_start = None
                        await self._send({"type": "speaking", "identity": speaker.identity,
                                          "active": False})
                    elif isinstance(ev, SpeechEnd):
                        audio = np.concatenate(
                            frames[max(0, ev.start_frame - base): ev.end_frame - base])
                        utt_start = None if not ep.in_speech else ev.end_frame
                        if not ep.in_speech:
                            await self._send({"type": "speaking", "identity": speaker.identity,
                                              "active": False})
                        self._on_utterance(speaker, audio, time.perf_counter())
                # Drop audio we no longer need (keep pre-roll while idle).
                keep_from = utt_start if utt_start is not None else ep.frame_index - keep_idle
                if keep_from - base > 0:
                    drop = min(keep_from - base, len(frames))
                    frames = frames[drop:]
                    base += drop

            # Live (interim) captions while the person is still speaking.
            now = time.monotonic()
            if (interim_ok and utt_start is not None and now - last_interim > INTERIM_EVERY_S
                    and (interim_task is None or interim_task.done())):
                last_interim = now
                audio = np.concatenate(frames[max(0, utt_start - base):])
                if audio.size > 16_000 * 0.6:
                    interim_task = loop.run_in_executor(
                        self.pool, translator.recognise, audio, speaker.lang)
                    interim_task.add_done_callback(
                        lambda f, s=speaker: self._spawn(self._send_partial(s, f)))

        for ev in ep.flush():
            if isinstance(ev, SpeechEnd):
                audio = np.concatenate(frames[max(0, ev.start_frame - base): ev.end_frame - base])
                self._on_utterance(speaker, audio, time.perf_counter())

    async def _send_partial(self, speaker: Person, fut: asyncio.Future) -> None:
        if fut.cancelled() or fut.exception() is not None:
            return
        text = fut.result()
        if text:
            await self._send({"type": "partial", "identity": speaker.identity, "seq": speaker.seq,
                              "lang": speaker.lang, "text": text})

    # --- Utterances ---
    def _on_utterance(self, speaker: Person, audio: np.ndarray, t_end: float) -> None:
        listener = self.partner_of(speaker.identity)
        seq = speaker.seq
        speaker.seq += 1
        if listener is None or listener.lang == speaker.lang:
            return  # alone, or both speak the same language: nothing to translate
        if frozenset((speaker.lang, listener.lang)) not in enabled_pairs():
            return
        if speaker.pending >= MAX_PENDING_TRANSLATIONS:
            log.warning("%d translations pending for one speaker; dropping an utterance",
                        speaker.pending)
            self._spawn(self._send({"type": "caption", "identity": speaker.identity, "seq": seq,
                                    "error": True}))
            return
        speaker.pending += 1
        out = UtteranceAudio()
        listener.playout.put_nowait(out)  # queued now → plays in speaking order
        self._spawn(self._translate(speaker, listener, seq, audio, t_end, out))

    async def _translate(self, speaker: Person, listener: Person, seq: int, audio: np.ndarray,
                         t_end: float, out: UtteranceAudio) -> None:
        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(
                self.pool, translator.process_audio, audio, speaker.lang, listener.lang)
            if result is None:
                await self._send({"type": "caption", "identity": speaker.identity, "seq": seq,
                                  "empty": True})
                return
            t_text = time.perf_counter()
            await self._send({"type": "caption", "identity": speaker.identity, "seq": seq,
                              **result.caption_payload()})
            first_audio_ms = None
            for sentence in result.tts_sentences:
                pcm, sr = await self.tts.synth(sentence, listener.lang, listener.speech_rate)
                pcm48 = float_to_int16(resample(int16_to_float(pcm), sr, OUT_RATE))
                if first_audio_ms is None:
                    first_audio_ms = (time.perf_counter() - t_end) * 1000
                out.chunks.put_nowait(pcm48)
            # Timings only, never text (privacy rule).
            log.info(
                "utt %s>%s audio=%.1fs asr=%.0fms mt=%.0fms text=%.0fms first_audio=%.0fms flags=%s",
                speaker.lang, listener.lang, audio.size / 16000, result.timings.asr_ms,
                result.timings.mt_ms, (t_text - t_end) * 1000, first_audio_ms or -1,
                ",".join(result.issues) or "-",
            )
        except TTSError:
            log.exception("speech synthesis failed")
        except Exception:
            log.exception("translation failed")
            await self._send({"type": "caption", "identity": speaker.identity, "seq": seq,
                              "error": True})
        finally:
            speaker.pending -= 1
            out.chunks.put_nowait(None)

    async def _playout_loop(self, person: Person) -> None:
        while True:
            utt = await person.playout.get()
            played: list[np.ndarray] = []
            while True:
                try:
                    chunk = await asyncio.wait_for(utt.chunks.get(), timeout=20)
                except TimeoutError:
                    break
                if chunk is None:
                    break
                played.append(chunk)
                await self._play(person, chunk)
            if played:
                person.last_played = played

    async def _play(self, person: Person, pcm: np.ndarray) -> None:
        for i in range(0, len(pcm), OUT_FRAME):
            frame = pcm[i: i + OUT_FRAME]
            if frame.size < OUT_FRAME:
                frame = np.pad(frame, (0, OUT_FRAME - frame.size))
            await person.source.capture_frame(
                rtc.AudioFrame(frame.tobytes(), OUT_RATE, 1, OUT_FRAME))

    # --- Buttons from the browser ---
    def _on_data(self, packet: rtc.DataPacket) -> None:
        if packet.topic != TOPIC_CONTROL or packet.participant is None:
            return
        person = self.people.get(packet.participant.identity)
        if person is None:
            return
        try:
            msg = json.loads(packet.data)
        except ValueError:
            return
        if not isinstance(msg, dict):
            return
        kind = msg.get("type")
        if kind in ("repeat", "didnt_understand"):
            # Each tap costs speech synthesis and plays audio to someone: rate-limit.
            now = time.monotonic()
            if now - person.last_control < CONTROL_COOLDOWN_S:
                return
            person.last_control = now
        if kind == "repeat" and person.last_played:
            if person.playout.qsize() >= MAX_QUEUED_PLAYOUT:
                return
            utt = UtteranceAudio()
            for chunk in person.last_played:
                utt.chunks.put_nowait(chunk)
            utt.chunks.put_nowait(None)
            person.playout.put_nowait(utt)
        elif kind == "didnt_understand":
            partner = self.partner_of(person.identity)
            if partner:
                self._spawn(self._tell(partner, DIDNT_UNDERSTAND[partner.lang], "didnt_understand"))
        elif kind == "speech_rate":
            with contextlib.suppress(TypeError, ValueError):
                rate = float(msg.get("value", 1.0))
                if math.isfinite(rate):
                    person.speech_rate = min(1.3, max(0.7, rate))

    async def _tell(self, person: Person, text: str, kind: str) -> None:
        await self._send({"type": "notice", "kind": kind}, to=[person.identity])
        pcm, sr = await self.tts.synth(text, person.lang)
        utt = UtteranceAudio()
        utt.chunks.put_nowait(float_to_int16(resample(int16_to_float(pcm), sr, OUT_RATE)))
        utt.chunks.put_nowait(None)
        person.playout.put_nowait(utt)

    async def _send(self, payload: dict, to: list[str] | None = None) -> None:
        with contextlib.suppress(Exception):
            await self.room.local_participant.publish_data(
                json.dumps(payload, ensure_ascii=False), reliable=True, topic=TOPIC_EVENTS,
                destination_identities=to or [],
            )


def _log_task_error(task: asyncio.Task) -> None:
    if not task.cancelled() and task.exception() is not None:
        log.error("background task failed", exc_info=task.exception())

