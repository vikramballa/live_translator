/** Helpers shared by the dev scripts. */
import { join } from "node:path";

export const ROOT = join(import.meta.dir, "..");

/** Minimal .env reader (Bun only loads .env from the current directory). */
export async function loadEnv(): Promise<Record<string, string>> {
  const file = Bun.file(join(ROOT, ".env"));
  const vars: Record<string, string> = {};
  if (!(await file.exists())) return vars;
  for (const line of (await file.text()).split("\n")) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/);
    if (m?.[1] && !line.trimStart().startsWith("#"))
      vars[m[1]] = m[2]?.replace(/^["']|["']$/g, "") ?? "";
  }
  return vars;
}

/**
 * macOS (an iCloud-synced Desktop, for example) can flag uv's editable .pth
 * files as "hidden". Python 3.12.12+ then skips them and `import agent` fails,
 * so clear the flag on both virtualenvs.
 */
export async function unhidePthFiles(): Promise<void> {
  if (process.platform !== "darwin") return;
  for (const venv of ["services/.venv", "services/tts-worker/.venv"]) {
    const site = join(ROOT, venv, "lib", "python3.12", "site-packages");
    const files = [...new Bun.Glob("*.pth").scanSync(site)].map((f) => join(site, f));
    if (files.length) await Bun.spawn(["chflags", "nohidden", ...files]).exited;
  }
}
