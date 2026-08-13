import { config } from "dotenv";
config({ path: ".env.local" });
config();

import bcrypt from "bcryptjs";
import { eq } from "drizzle-orm";

import { db } from "../src/lib/db/client";
import { users } from "../src/lib/db/schema";

async function main() {
  const email = (process.env.ADMIN_SEED_EMAIL ?? "admin@datagovai.local")
    .trim()
    .toLowerCase();
  const password = process.env.ADMIN_SEED_PASSWORD;
  if (!password) {
    console.error("Set ADMIN_SEED_PASSWORD in web/.env.local before seeding.");
    process.exit(1);
  }
  const passwordHash = await bcrypt.hash(password, 12);

  const [existing] = await db
    .select()
    .from(users)
    .where(eq(users.email, email))
    .limit(1);

  if (existing) {
    await db
      .update(users)
      .set({ passwordHash, role: "admin", name: "DataGovAI Admin" })
      .where(eq(users.id, existing.id));
    console.log(`Updated admin: ${email}`);
  } else {
    await db.insert(users).values({
      email,
      passwordHash,
      name: "DataGovAI Admin",
      role: "admin",
      emailVerified: new Date(),
    });
    console.log(`Created admin: ${email}`);
  }
  console.log(`Sign in at /sign-in as ${email}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
