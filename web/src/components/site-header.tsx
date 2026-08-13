"use client";

import { signOut, useSession } from "next-auth/react";
import Link from "next/link";

export function SiteHeader() {
  const { data, status } = useSession();

  return (
    <header className="border-b border-teal-800 bg-teal-800 px-4 py-3 text-white">
      <div className="mx-auto flex max-w-2xl items-center justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-lg font-semibold">DataGovAI</h1>
          <p className="text-xs text-teal-100">Utah GRS knowledge assistant</p>
        </div>
        {status === "loading" ? (
          <span className="text-xs text-teal-100">…</span>
        ) : data?.user ? (
          <div className="flex items-center gap-3">
            <span className="hidden max-w-[14rem] truncate text-xs text-teal-100 sm:inline">
              {data.user.email}
            </span>
            <button
              type="button"
              onClick={() => signOut({ callbackUrl: "/" })}
              className="rounded-md bg-white/15 px-3 py-1.5 text-xs font-medium hover:bg-white/25"
            >
              Sign out
            </button>
          </div>
        ) : (
          <Link
            href="/sign-in"
            className="rounded-md bg-white px-3 py-1.5 text-xs font-medium text-teal-900 hover:bg-teal-50"
          >
            Sign in
          </Link>
        )}
      </div>
    </header>
  );
}
