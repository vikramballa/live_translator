import { SQL } from "bun";
import { env } from "./env.ts";

export const sql = new SQL(env.DATABASE_URL);
