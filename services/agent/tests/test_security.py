"""Abuse cases: what one participant, or a cancelled call, must not be able to do."""

import asyncio
import json
import os
import sys
import time
from types import SimpleNamespace

import pytest

from agent import main, session, tts_client
from agent.session import TOPIC_CONTROL, Person, RoomSession

# A stand-in TTS worker speaking the real protocol; it echoes the text as "audio".
FAKE_WORKER = r"""
import json, sys, time
out = sys.stdout.buffer
out.write(b'{"ready": true, "langs": ["en"]}\n'); out.flush()
for line in sys.stdin:
    req = json.loads(line)
    time.sleep(float(req["text"].split(":")[1]) if ":" in req["text"] else 0)
    data = req["text"].encode().ljust(16, b" ")[:16]
    header = {"id": req["id"], "sample_rate": 1, "bytes": 16, "error": None}
    out.write(json.dumps(header).encode() + b"\n" + data); out.flush()
"""


@pytest.fixture
def fake_worker(tmp_path, monkeypatch):
    (tmp_path / ".venv" / "bin").mkdir(parents=True)
    (tmp_path / "src" / "tts_worker").mkdir(parents=True)
    os.symlink(sys.executable, tmp_path / ".venv" / "bin" / "python")
    (tmp_path / "src" / "tts_worker" / "main.py").write_text(FAKE_WORKER)
    monkeypatch.setattr(tts_client, "WORKER_DIR", tmp_path)


async def test_cancelled_request_never_leaks_into_the_next_one(fake_worker):  # noqa: ARG001
    client = tts_client.TTSClient()
    await client.start()
    try:
        first = asyncio.create_task(client.synth("ROOM_A:0.3", "en"))
        await asyncio.sleep(0.1)
        first.cancel()  # room A closes while its sentence is being synthesised
        pcm, _ = await client.synth("ROOM_B", "en")
        assert pcm.tobytes().rstrip() == b"ROOM_B"
        pcm, _ = await client.synth("ROOM_B_again", "en")  # still in step afterwards
        assert pcm.tobytes().rstrip() == b"ROOM_B_again"
    finally:
        await client.close()


async def test_hung_or_broken_worker_is_restarted(fake_worker, monkeypatch):  # noqa: ARG001
    monkeypatch.setattr(tts_client, "REQUEST_TIMEOUT_S", 0.2)
    client = tts_client.TTSClient()
    await client.start()
    try:
        with pytest.raises(tts_client.TTSError):
            await client.synth("slow:1", "en")
        pcm, _ = await client.synth("after", "en")
        assert pcm.tobytes().rstrip() == b"after"
    finally:
        await client.close()


# --- Control messages ---
class _Session(RoomSession):
    """A RoomSession with one fake listener and a recording TTS/data channel."""

    def __init__(self) -> None:
        self.people = {}
        self._bg = set()
        self.sent: list[dict] = []
        self.told: list[str] = []
        for ident, lang in (("u_a", "te"), ("u_b", "en")):
            self.people[ident] = Person(identity=ident, lang=lang, source=None, track=None)  # type: ignore[arg-type]
        self.people["u_a"].last_played = [b"audio"]  # type: ignore[list-item]

    async def _send(self, payload, to=None):  # noqa: ARG002
        self.sent.append(payload)

    async def _tell(self, person, text, kind):  # noqa: ARG002
        self.told.append(person.identity)


def _packet(sender: str, data) -> SimpleNamespace:
    raw = data if isinstance(data, bytes) else json.dumps(data).encode()
    return SimpleNamespace(topic=TOPIC_CONTROL, participant=SimpleNamespace(identity=sender),
                           data=raw)


async def test_control_messages_of_the_wrong_shape_are_ignored():
    s = _Session()
    for bad in (b"[1, 2]", b"42", b'"repeat"', b"null", b"\xff\xfe", {"type": "speech_rate",
                                                                      "value": "nan"}):
        s._on_data(_packet("u_a", bad))
    assert s.people["u_a"].speech_rate == 1.0
    assert s.people["u_a"].playout.empty()


async def test_repeat_and_didnt_understand_are_rate_limited():
    s = _Session()
    for _ in range(50):
        s._on_data(_packet("u_a", {"type": "repeat"}))
        s._on_data(_packet("u_a", {"type": "didnt_understand"}))
    await asyncio.sleep(0)
    assert s.people["u_a"].playout.qsize() == 1
    assert s.told == []  # the second tap type came within the cooldown
    s.people["u_a"].last_control = time.monotonic() - session.CONTROL_COOLDOWN_S
    s._on_data(_packet("u_a", {"type": "didnt_understand"}))
    await asyncio.sleep(0)
    assert s.told == ["u_b"]


async def test_strangers_cannot_send_control_messages():
    s = _Session()
    s._on_data(_packet("u_stranger", {"type": "repeat"}))
    assert all(p.playout.empty() for p in s.people.values())


async def test_pending_translations_per_speaker_are_capped(monkeypatch):
    s = _Session()
    started = []
    monkeypatch.setattr(s, "_translate", lambda *a: asyncio.sleep(0, started.append(a)))
    monkeypatch.setattr(session, "enabled_pairs", lambda: {frozenset(("te", "en"))})
    speaker = s.people["u_a"]
    for _ in range(session.MAX_PENDING_TRANSLATIONS + 3):
        s._on_utterance(speaker, None, 0.0)  # type: ignore[arg-type]
    await asyncio.sleep(0)
    assert len(started) == session.MAX_PENDING_TRANSLATIONS
    assert sum(1 for m in s.sent if m.get("error")) == 3


# --- Control server ---
async def test_join_endpoint_checks_secret_and_room_id(monkeypatch):
    from aiohttp.test_utils import TestClient, TestServer

    monkeypatch.setattr(main, "settings", lambda: SimpleNamespace(control_secret="s3cret"))
    joined = []
    agent = SimpleNamespace(join=lambda room: joined.append(room) or True, sessions={})
    async with TestClient(TestServer(main.build_app(agent))) as client:  # type: ignore[arg-type]
        room = "A" * 22
        assert (await client.post(f"/rooms/{room}/join")).status == 401
        assert (await client.post(f"/rooms/{room}/join",
                                  headers={"x-agent-secret": "wrong"})).status == 401
        ok = {"x-agent-secret": "s3cret"}
        assert (await client.post("/rooms/..%2f..%2fetc/join", headers=ok)).status in (400, 404)
        assert (await client.post(f"/rooms/{room}x/join", headers=ok)).status == 400
        assert (await client.post(f"/rooms/{room}/join", headers=ok)).status == 200
    assert joined == [room]


def test_agent_refuses_a_network_facing_control_port_without_secret(monkeypatch):
    monkeypatch.setattr(main, "settings", lambda: SimpleNamespace(control_secret="",
                                                                  control_host="0.0.0.0"))
    with pytest.raises(SystemExit, match="AGENT_SHARED_SECRET"):
        asyncio.run(main.amain())
