import { config } from "dotenv";
import { neon } from "@neondatabase/serverless";
import { drizzle } from "drizzle-orm/neon-http";

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

export const db = drizzle(
  neon(
    url ||
      "postgresql://placeholder:placeholder@placeholder.neon.tech/placeholder",
  ),
  { schema },
);
