import { config } from "dotenv";
import { Pool } from "pg";
import { drizzle } from "drizzle-orm/node-postgres";

import * as schema from "./schema";

if (!process.env.DATABASE_URL) {
  config({ path: ".env.local" });
  config();
}

const url = process.env.DATABASE_URL;

if (!url && process.env.NODE_ENV !== "test") {
  console.warn(
    "[DataGovAI] DATABASE_URL is not set — copy web/.env.example to web/.env.local.",
  );
}

const pool = new Pool({
  connectionString:
    url || "postgresql://placeholder:placeholder@localhost:5432/placeholder",
});

export const db = drizzle(pool, { schema });
