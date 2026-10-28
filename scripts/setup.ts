/**
 * One-time local setup (no Docker):
 *   bun run setup              tools check, .env, database, Python envs, models
 *   bun run setup --no-models  skip the model download
 */
import { existsSync } from "node:fs";
import { join } from "node:path";
import { $ } from "bun";
import { loadEnv, ROOT, unhidePthFiles } from "./lib.ts";

const skipModels = process.argv.includes("--no-models");
const ok = (m: string) => console.log(`  \x1b[32m✓\x1b[0m ${m}`);
const fail = (m: string): never => {
  console.error(`  \x1b[31m✗\x1b[0m ${m}`);
  process.exit(1);
};

console.log("1. Tools");
for (const [tool, hint] of [
  ["uv", "curl -LsSf https://astral.sh/uv/install.sh | sh"],
  ["livekit-server", "brew install livekit"],
  ["pg_isready", "brew install postgresql@17"],
] as const) {
  if (!Bun.which(tool)) fail(`${tool} not found. Install: ${hint}`);
  ok(tool);
}

console.log("2. .env");
const envPath = join(ROOT, ".env");
if (!existsSync(envPath)) {
  const secret = Buffer.from(crypto.getRandomValues(new Uint8Array(24))).toString("hex");
  const template = await Bun.file(join(ROOT, ".env.example")).text();
  const rand = (n: number) =>
    Buffer.from(crypto.getRandomValues(new Uint8Array(n))).toString("base64url");
  await Bun.write(
    envPath,
    template
      .replace("YOUR_USER", process.env.USER ?? "postgres")
      .replace("AGENT_SHARED_SECRET=change-me", `AGENT_SHARED_SECRET=${secret}`)
      .replace("change-me-key", `lt_dev_${rand(4)}`)
      .replace("change-me-secret", rand(36)),
  );
  await $`chmod 600 ${envPath}`;
  ok("created .env (edit DATABASE_URL if your Postgres differs)");
} else ok(".env exists");
const env = await loadEnv();

console.log("3. PostgreSQL (local)");
const db = new URL(env.DATABASE_URL ?? "");
const ready = await $`pg_isready -h ${db.hostname} -p ${db.port || "5432"}`.nothrow().quiet();
if (ready.exitCode !== 0)
  fail(
    `Postgres not reachable at ${db.hostname}:${db.port}. Start it: brew services start postgresql@17`,
  );
await $`bun --env-file=${envPath} src/migrate.ts`.cwd(join(ROOT, "apps", "api"));
ok("database migrated");

console.log("4. Python environments (uv)");
await $`uv sync --all-packages`.cwd(join(ROOT, "services")).quiet();
await $`uv sync`.cwd(join(ROOT, "services", "tts-worker")).quiet();
await unhidePthFiles();
ok("agent, pipeline-core and tts-worker installed");

if (!skipModels) {
  console.log("5. Models (several GB on first run)");
  const r = await $`${join(ROOT, "services", ".venv", "bin", "translator-cli")} download`
    .cwd(join(ROOT, "services", "agent"))
    .env({ ...process.env, ...env, PYTHONSAFEPATH: "1" })
    .nothrow();
  if (r.exitCode !== 0) {
    console.log("\n  Some models are not downloaded yet (see above). Everything else is ready.");
  } else ok("models ready");
}

console.log("\nDone. Start everything with:  bun run dev\n");
