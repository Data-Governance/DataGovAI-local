import bcrypt from "bcryptjs";
import { eq } from "drizzle-orm";
import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";

import { db } from "@/lib/db/client";
import { users } from "@/lib/db/schema";

const DEV_EMAIL = "admin@datagovai.local";

export const { handlers, auth, signIn, signOut } = NextAuth({
  session: { strategy: "jwt" },
  pages: { signIn: "/sign-in" },
  trustHost: true,
  secret: process.env.AUTH_SECRET,
  providers: [
    Credentials({
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        const emailRaw = credentials?.email as string | undefined;
        const password = credentials?.password as string | undefined;
        const email = emailRaw?.trim().toLowerCase();
        if (!email || !password) return null;

        const isDevShortcut =
          process.env.NODE_ENV !== "production" &&
          process.env.ENABLE_DEV_LOGIN !== "false" &&
          (email === "admin" || email === DEV_EMAIL) &&
          password === "admin";

        if (isDevShortcut) {
          const [existing] = await db
            .select()
            .from(users)
            .where(eq(users.email, DEV_EMAIL))
            .limit(1);
          if (existing) {
            return {
              id: existing.id,
              email: existing.email,
              name: existing.name ?? "Admin",
              role: existing.role,
            };
          }
          const hash = await bcrypt.hash("admin", 10);
          const [created] = await db
            .insert(users)
            .values({
              email: DEV_EMAIL,
              passwordHash: hash,
              name: "DataGovAI Admin",
              role: "admin",
              emailVerified: new Date(),
            })
            .returning();
          return {
            id: created!.id,
            email: created!.email,
            name: created!.name ?? "Admin",
            role: created!.role,
          };
        }

        const [user] = await db
          .select()
          .from(users)
          .where(eq(users.email, email))
          .limit(1);
        if (!user?.passwordHash) return null;
        const ok = await bcrypt.compare(password, user.passwordHash);
        if (!ok) return null;
        return {
          id: user.id,
          email: user.email,
          name: user.name ?? undefined,
          role: user.role,
        };
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.sub = user.id;
        token.email = user.email;
        token.role = (user as { role?: string }).role ?? "user";
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user && token.sub) {
        session.user.id = token.sub;
        if (token.email) session.user.email = String(token.email);
        session.user.role =
          typeof token.role === "string" ? token.role : "user";
      }
      return session;
    },
  },
});
