import { createApp } from "./app.ts";
import { env } from "./env.ts";
import { deleteExpiredRooms } from "./rooms.ts";

const app = createApp();

const server = Bun.serve({ port: env.PORT, hostname: env.HOST, fetch: app.fetch });
console.log(`api listening on http://${server.hostname}:${server.port}`);

// Expired rooms (and their seats, via ON DELETE CASCADE) are removed every 10 minutes.
setInterval(
  () =>
    deleteExpiredRooms()
      .then((n) => n && console.log(`removed ${n} expired rooms`))
      .catch((e) => console.error("cleanup failed:", e.message)),
  10 * 60_000,
);
