/**
 * Creates the database if it does not exist, then applies migrations/*.sql in
 * order, once each. Uses the local PostgreSQL (no Docker).
 */
import { readdir } from "node:fs/promises";
import { join } from "node:path";
import { SQL } from "bun";
import { env } from "./env.ts";

const url = new URL(env.DATABASE_URL);
const dbName = url.pathname.slice(1);
if (!/^[a-z_][a-z0-9_]*$/.test(dbName)) throw new Error(`unsafe database name: ${dbName}`);

const admin = new SQL({ ...urlParts(url), database: "postgres" });
const exists = await admin`SELECT 1 FROM pg_database WHERE datname = ${dbName}`;
if (exists.length === 0) {
  await admin.unsafe(`CREATE DATABASE ${dbName}`);
  console.log(`created database ${dbName}`);
}
await admin.close();

const sql = new SQL(env.DATABASE_URL);
await sql`CREATE TABLE IF NOT EXISTS schema_migrations (
  version text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())`;
const dir = join(import.meta.dir, "..", "migrations");
const files = (await readdir(dir)).filter((f) => f.endsWith(".sql")).sort();
for (const file of files) {
  const done = await sql`SELECT 1 FROM schema_migrations WHERE version = ${file}`;
  if (done.length) continue;
  const body = await Bun.file(join(dir, file)).text();
  await sql.begin(async (tx) => {
    await tx.unsafe(body);
    await tx`INSERT INTO schema_migrations (version) VALUES (${file})`;
  });
  console.log(`applied ${file}`);
}
await sql.close();
console.log("migrations up to date");

function urlParts(u: URL) {
  return {
    hostname: u.hostname,
    port: Number(u.port || 5432),
    username: decodeURIComponent(u.username) || undefined,
    password: decodeURIComponent(u.password) || undefined,
  };
}
