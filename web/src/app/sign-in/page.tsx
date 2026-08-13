"use client";

import { signIn } from "next-auth/react";
import { useState } from "react";

const isProd = process.env.NODE_ENV === "production";

export default function SignInPage() {
  const [email, setEmail] = useState(
    isProd ? "admin@datagovai.local" : "admin",
  );
  const [password, setPassword] = useState(isProd ? "" : "admin");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  return (
    <main className="mx-auto flex min-h-dvh max-w-sm flex-col justify-center px-4">
      <h1 className="mb-2 text-xl font-semibold text-teal-900">
        Sign in to DataGovAI
      </h1>
      <p className="mb-6 text-sm text-zinc-600">
        Required in production to ask GRS questions.
      </p>
      <form
        className="space-y-3"
        onSubmit={async (e) => {
          e.preventDefault();
          setError("");
          setBusy(true);
          const res = await signIn("credentials", {
            email,
            password,
            callbackUrl: "/",
            redirect: false,
          });
          setBusy(false);
          if (res?.error) {
            setError("Invalid credentials");
            return;
          }
          window.location.href = "/";
        }}
      >
        <input
          className="w-full rounded-lg border px-3 py-2 text-sm"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          autoComplete="username"
        />
        <input
          className="w-full rounded-lg border px-3 py-2 text-sm"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          autoComplete="current-password"
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-lg bg-teal-700 py-2 text-sm text-white disabled:opacity-60"
        >
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
      {!isProd && (
        <p className="mt-4 text-xs text-zinc-500">
          Local shortcut: admin / admin
        </p>
      )}
      <p className="mt-6 text-center text-xs text-zinc-500">
        <a href="/" className="underline">
          Back to chat
        </a>
      </p>
    </main>
  );
}
