"""Translator agent process.

Runs a tiny HTTP control server bound to localhost. The Bun API calls
``POST /rooms/<name>/join`` when someone joins a call, and the agent joins
that LiveKit room. One process serves every room and shares the models.
"""

from __future__ import annotations

import asyncio
import hmac
import ipaddress
import logging
import re
import signal
import time
from concurrent.futures import ThreadPoolExecutor

from aiohttp import web

from . import engines
from .session import RoomSession
from .settings import languages, settings
from .tts_client import TTSClient

log = logging.getLogger("agent")

# A language's models are unloaded once no call has used it for this long.
# Releasing as soon as a room closes made back-to-back calls reload models.
IDLE_RELEASE_S = 300.0
# Same format as the API's room ids (128-bit random, base64url).
ROOM_ID = re.compile(r"[A-Za-z0-9_-]{22}")


class Agent:
    def __init__(self) -> None:
        s = settings()
        self.pool = ThreadPoolExecutor(max_workers=s.inference_workers, thread_name_prefix="infer")
        self.tts = TTSClient(preload=list(languages()["languages"]) if s.preload else [])
        self.sessions: dict[str, tuple[RoomSession, asyncio.Task]] = {}
        self._last_used: dict[str, float] = {}  # language → monotonic time last seen in a call
        self._release_task: asyncio.Task | None = None

    async def start(self) -> None:
        await self.tts.start()
        if settings().preload:
            log.info("preloading all models…")
            await asyncio.get_running_loop().run_in_executor(
                self.pool, engines.preload, list(languages()["languages"]))
            log.info("models ready")
        else:
            self._release_task = asyncio.create_task(self._release_idle_models())

    async def _release_idle_models(self) -> None:
        loop = asyncio.get_running_loop()
        while True:
            await asyncio.sleep(30)
            now = time.monotonic()
            for session, _ in self.sessions.values():
                self._last_used.update(dict.fromkeys(session.seen_langs, now))
            keep = {lang for lang, t in self._last_used.items() if now - t < IDLE_RELEASE_S}
            await loop.run_in_executor(self.pool, engines.release_unused, keep)

    def join(self, room: str) -> bool:
        if room in self.sessions and not self.sessions[room][1].done():
            return False
        session = RoomSession(room, self.pool, self.tts)
        task = asyncio.create_task(session.run())
        task.add_done_callback(lambda _t, r=room: self.sessions.pop(r, None))
        self.sessions[room] = (session, task)
        return True

    async def stop(self) -> None:
        if self._release_task:
            self._release_task.cancel()
        for session, task in list(self.sessions.values()):
            await session.close()
            task.cancel()
        await self.tts.close()
        self.pool.shutdown(wait=False, cancel_futures=True)


def _authorised(request: web.Request) -> bool:
    secret = settings().control_secret
    if not secret:
        return True  # local development without a secret
    given = request.headers.get("x-agent-secret", "")
    return hmac.compare_digest(given.encode(), secret.encode())


def build_app(agent: Agent) -> web.Application:
    async def join(request: web.Request) -> web.Response:
        if not _authorised(request):
            return web.json_response({"error": "unauthorised"}, status=401)
        room = request.match_info["room"]
        if not ROOM_ID.fullmatch(room):
            return web.json_response({"error": "bad room"}, status=400)
        created = agent.join(room)
        return web.json_response({"ok": True, "created": created})

    async def health(_request: web.Request) -> web.Response:
        return web.json_response({"ok": True, "rooms": len(agent.sessions),
                                  "models": engines.loaded_models()})

    app = web.Application()
    app.router.add_post("/rooms/{room}/join", join)
    app.router.add_get("/health", health)
    return app


def _is_loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


async def amain() -> None:
    s = settings()
    if not s.control_secret and not _is_loopback(s.control_host):
        raise SystemExit(f"AGENT_SHARED_SECRET is required when AGENT_HOST={s.control_host} "
                         "(anyone on the network could make the agent join rooms)")
    agent = Agent()
    await agent.start()
    runner = web.AppRunner(build_app(agent), access_log=None)
    await runner.setup()
    await web.TCPSite(runner, s.control_host, s.control_port).start()
    log.info("agent control on http://%s:%d (LiveKit %s)", s.control_host, s.control_port,
             s.livekit_url)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    await stop.wait()
    log.info("shutting down")
    await agent.stop()
    await runner.cleanup()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("livekit").setLevel(logging.WARNING)
    asyncio.run(amain())


if __name__ == "__main__":
    main()
