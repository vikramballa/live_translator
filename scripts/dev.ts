/**
 * Start everything natively (no Docker):
 *   livekit-server (Homebrew binary) · translator agent (Python/uv) · API (Bun) · web (Vite)
 *
 *   bun run dev            development, with hot reload
 *   bun run dev --prod     build the web app and serve it from the API (like the server)
 */
import { join } from "node:path";
import { type Subprocess, spawn } from "bun";
import { loadEnv, ROOT, unhidePthFiles } from "./lib.ts";

const prod = process.argv.includes("--prod");
const env: Record<string, string | undefined> = {
  ...process.env,
  ...(await loadEnv()),
  FORCE_COLOR: "1",
};

type Proc = {
  name: string;
  color: string;
  cmd: string[];
  cwd: string;
  env?: Record<string, string>;
};

const venvBin = join(ROOT, "services", ".venv", "bin");
const procs: Proc[] = [
  {
    name: "livekit",
    color: "\x1b[35m",
    // Listens on all interfaces (WebRTC clients cannot use a loopback-only server)
    // with the random key/secret from .env. LIVEKIT_NODE_IP pins the advertised IP.
    cmd: [
      "livekit-server",
      "--config",
      join(ROOT, "infra", "livekit", "livekit.dev.yaml"),
      ...(env.LIVEKIT_NODE_IP ? ["--node-ip", env.LIVEKIT_NODE_IP] : []),
    ],
    cwd: ROOT,
    // Via the environment, not --keys: command lines are visible to every local user (ps).
    env: { LIVEKIT_KEYS: `${env.LIVEKIT_API_KEY}: ${env.LIVEKIT_API_SECRET}` },
  },
  {
    name: "agent",
    color: "\x1b[36m",
    cmd: [join(venvBin, "translator-agent")],
    cwd: join(ROOT, "services", "agent"),
    env: {
      PYTHONSAFEPATH: "1",
      PYTHONUNBUFFERED: "1",
      // Explicit, so imports never depend on uv's editable .pth files (see unhidePthFiles).
      PYTHONPATH: [
        join(ROOT, "services", "agent", "src"),
        join(ROOT, "services", "pipeline-core", "src"),
      ].join(":"),
    },
  },
  {
    name: "api",
    color: "\x1b[33m",
    cmd: prod ? ["bun", "src/index.ts"] : ["bun", "--watch", "src/index.ts"],
    cwd: join(ROOT, "apps", "api"),
    env: prod ? { WEB_DIST: join(ROOT, "apps", "web", "dist"), NODE_ENV: "development" } : {},
  },
];
if (!prod) {
  procs.push({
    name: "web",
    color: "\x1b[32m",
    cmd: ["bunx", "--bun", "vite"],
    cwd: join(ROOT, "apps", "web"),
  });
}

async function portFree(port: number): Promise<boolean> {
  try {
    const s = Bun.listen({ hostname: "127.0.0.1", port, socket: { data() {} } });
    s.stop(true);
    return true;
  } catch {
    return false;
  }
}

const ports: Record<string, number> = {
  livekit: 7880,
  agent: Number(env.AGENT_PORT ?? 8765),
  api: Number(env.PORT ?? 3000),
};
if (!prod) ports.web = 5173;
const busy = [];
for (const [name, port] of Object.entries(ports))
  if (!(await portFree(port))) busy.push(`${name} (:${port})`);
if (busy.length) {
  console.error(`Ports already in use: ${busy.join(", ")}. Stop the other process first.`);
  process.exit(1);
}

await unhidePthFiles();

if (prod) {
  console.log("building web app…");
  const b = spawn(["bunx", "--bun", "vite", "build"], {
    cwd: join(ROOT, "apps", "web"),
    env,
    stdout: "inherit",
    stderr: "inherit",
  });
  if ((await b.exited) !== 0) process.exit(1);
}

const children: Subprocess[] = [];
const reset = "\x1b[0m";

async function pipe(stream: ReadableStream<Uint8Array>, prefix: string) {
  const decoder = new TextDecoder();
  let buf = "";
  for await (const chunk of stream) {
    buf += decoder.decode(chunk, { stream: true });
    const lines = buf.split("\n");
    buf = lines.pop() ?? "";
    for (const line of lines) if (line.trim()) console.log(`${prefix} ${line}`);
  }
}

for (const p of procs) {
  const child = spawn(p.cmd, {
    cwd: p.cwd,
    env: { ...env, ...p.env },
    stdout: "pipe",
    stderr: "pipe",
  });
  children.push(child);
  const prefix = `${p.color}${p.name.padEnd(7)}${reset}│`;
  void pipe(child.stdout, prefix);
  void pipe(child.stderr, prefix);
  void child.exited.then((code) => {
    console.log(`${prefix} exited with code ${code}`);
    if (!stopping) shutdown(code ?? 1);
  });
}

console.log(
  `\n  Open ${prod ? `http://127.0.0.1:${ports.api}` : "http://localhost:5173"}  (Ctrl-C to stop)\n`,
);

let stopping = false;
function shutdown(code = 0) {
  if (stopping) return;
  stopping = true;
  for (const c of children) c.kill("SIGTERM");
  setTimeout(() => {
    for (const c of children) c.kill("SIGKILL");
    process.exit(code);
  }, 5000).unref();
  Promise.all(children.map((c) => c.exited)).then(() => process.exit(code));
}
process.on("SIGINT", () => shutdown(0));
process.on("SIGTERM", () => shutdown(0));
