"""Headless end-to-end call test.

Two bot participants join a LiveKit room. The *speaker* plays a WAV file into
its microphone; the *listener* records the translated audio track meant for
it and every caption event. Measures SE2FA: end of speech → first translated
audio at the listener.

Needs livekit-server, the agent and (for synthesis of the test sentence) the
TTS worker. Run:

    uv run translator-cli e2e --src en --tgt zh --text "Give me 500 rupees."
"""

from __future__ import annotations

import asyncio
import json
import secrets
import time

import aiohttp
import numpy as np
from livekit import api, rtc

from .audio import float_to_int16, int16_to_float, resample
from .settings import settings
from .tts_client import TTSClient

RATE = 48_000
FRAME = RATE // 100  # 10 ms


def _token(room: str, identity: str, lang: str) -> str:
    s = settings()
    return (
        api.AccessToken(s.livekit_api_key, s.livekit_api_secret)
        .with_identity(identity)
        .with_metadata(json.dumps({"lang": lang}))
        .with_grants(api.VideoGrants(room_join=True, room=room))
        .to_jwt()
    )


async def run(src: str, tgt: str, text: str, timeout: float = 120.0) -> dict:
    s = settings()
    room_name = secrets.token_urlsafe(16)
    tts = TTSClient()
    await tts.start()
    pcm, sr = await tts.synth(text, src)
    await tts.close()
    speech = float_to_int16(resample(int16_to_float(pcm), sr, RATE))

    speaker, listener = rtc.Room(), rtc.Room()
    events: list[dict] = []
    state = {"ready": asyncio.Event(), "first_audio": None, "audio_s": 0.0, "caption": asyncio.Event()}
    speech_end: dict[str, float] = {}

    def on_data(packet: rtc.DataPacket) -> None:
        msg = json.loads(packet.data)
        events.append(msg)
        if msg.get("type") == "state" and msg.get("state") == "ready":
            state["ready"].set()
        if msg.get("type") == "caption" and not msg.get("empty"):
            state["caption"].set()

    async def record(track: rtc.Track) -> None:
        stream = rtc.AudioStream(track, sample_rate=RATE, num_channels=1)
        async for ev in stream:
            a = np.frombuffer(ev.frame.data, dtype=np.int16)
            if np.abs(a).max(initial=0) > 500:
                state["audio_s"] += a.size / RATE
                if state["first_audio"] is None and "t" in speech_end:
                    state["first_audio"] = time.perf_counter()

    recorders: list[asyncio.Task] = []  # keep references so the tasks are not garbage-collected

    def on_track(track: rtc.Track, pub: rtc.RemoteTrackPublication, _p: rtc.RemoteParticipant) -> None:
        if pub.name == "tr:bot_listener":
            recorders.append(asyncio.ensure_future(record(track)))

    listener.on("data_received", on_data)
    listener.on("track_subscribed", on_track)
    try:
        await listener.connect(s.livekit_url, _token(room_name, "bot_listener", tgt))
        await speaker.connect(s.livekit_url, _token(room_name, "bot_speaker", src))
    except rtc.ConnectError as e:
        raise SystemExit(
            f"WebRTC media could not connect ({e}).\n"
            "On macOS this is usually the Application Firewall blocking livekit-server and the\n"
            "uv Python from receiving UDP. See docs/runbooks/local-dev.md → 'macOS firewall'."
        ) from None

    source = rtc.AudioSource(RATE, 1)
    mic = rtc.LocalAudioTrack.create_audio_track("mic", source)
    await speaker.local_participant.publish_track(
        mic, rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE))

    async def silence(seconds: float) -> None:
        for _ in range(int(seconds * 100)):
            await source.capture_frame(rtc.AudioFrame(bytes(FRAME * 2), RATE, 1, FRAME))

    async with aiohttp.ClientSession() as http:
        r = await http.post(f"http://{s.control_host}:{s.control_port}/rooms/{room_name}/join",
                            headers={"x-agent-secret": s.control_secret})
        r.raise_for_status()

    t0 = time.perf_counter()
    ready_task = asyncio.ensure_future(state["ready"].wait())
    while not ready_task.done():
        await silence(0.2)  # keep the mic stream alive while models load
        if time.perf_counter() - t0 > timeout:
            raise TimeoutError("agent never became ready")
    load_s = time.perf_counter() - t0

    await silence(0.5)
    for i in range(0, len(speech), FRAME):
        chunk = speech[i: i + FRAME]
        chunk = np.pad(chunk, (0, FRAME - chunk.size))
        await source.capture_frame(rtc.AudioFrame(chunk.tobytes(), RATE, 1, FRAME))
    await source.wait_for_playout()
    speech_end["t"] = time.perf_counter()

    deadline = time.perf_counter() + 30
    while time.perf_counter() < deadline and not (state["caption"].is_set() and state["audio_s"] > 0.5):
        await silence(0.1)
    await silence(2.0)  # let the rest of the translation play

    for task in recorders:
        task.cancel()
    await speaker.disconnect()
    await listener.disconnect()
    caption = next((e for e in events if e.get("type") == "caption" and not e.get("empty")), None)
    return {
        "agent_ready_s": round(load_s, 2),
        "caption": caption,
        "translated_audio_s": round(state["audio_s"], 2),
        "se2fa_ms": round((state["first_audio"] - speech_end["t"]) * 1000)
        if state["first_audio"] else None,
        "events": [e["type"] + (":" + e.get("state", "") if e["type"] == "state" else "") for e in events],
    }
