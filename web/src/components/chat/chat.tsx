"use client";

import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { useMemo, useRef, useState } from "react";

const STARTERS = [
  "What is the retention period for council minutes?",
  "How long should we keep employee personnel files?",
  "What are the disposition requirements for audit records?",
  "What is the retention schedule for legal case files?",
];

type Source = { sourceId: string; title: string };

function messageText(message: {
  parts: { type: string; text?: string }[];
}): string {
  return message.parts
    .filter((p) => p.type === "text" && p.text)
    .map((p) => p.text as string)
    .join("");
}

function sourcesFrom(message: { metadata?: unknown }): Source[] {
  const meta = message.metadata as { sources?: Source[] } | undefined;
  if (!meta?.sources?.length) return [];
  const seen = new Set<string>();
  return meta.sources.filter((s) => {
    if (seen.has(s.sourceId)) return false;
    seen.add(s.sourceId);
    return true;
  });
}

function errorCopy(message: string): { text: string; signIn?: boolean } {
  const lower = message.toLowerCase();
  if (lower.includes("unauthorized") || message.includes("401")) {
    return {
      text: "Your session expired or you are not signed in.",
      signIn: true,
    };
  }
  if (lower.includes("temporarily unavailable") || message.includes("503")) {
    return { text: "The AI service is briefly unavailable. Try again in a moment." };
  }
  return { text: message };
}

export function Chat() {
  const { data: session, status } = useSession();
  const authRequired = process.env.NODE_ENV === "production";
  const sessionReady = status !== "loading";
  const needsAuth = authRequired && sessionReady && !session?.user;

  const [input, setInput] = useState("");
  const transport = useMemo(
    () => new DefaultChatTransport({ api: "/api/chat" }),
    [],
  );
  const { messages, sendMessage, status: chatStatus, error, stop } = useChat({
    transport,
  });
  const bottomRef = useRef<HTMLDivElement>(null);
  const busy = chatStatus === "submitted" || chatStatus === "streaming";

  function submit(text: string) {
    const t = text.trim();
    if (!t || busy || needsAuth) return;
    sendMessage({ text: t });
    setInput("");
    requestAnimationFrame(() =>
      bottomRef.current?.scrollIntoView({ behavior: "smooth" }),
    );
  }

  if (authRequired && !sessionReady) {
    return (
      <p className="mx-auto max-w-2xl px-4 py-12 text-sm text-zinc-500">
        Checking your session…
      </p>
    );
  }

  if (needsAuth) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12 text-center">
        <p className="mb-4 text-sm text-zinc-600">
          Sign in to ask questions about Utah General Retention Schedules.
          Answers cite ingested GRS series ids.
        </p>
        <Link
          href="/sign-in"
          className="inline-block rounded-lg bg-teal-700 px-4 py-2 text-sm text-white hover:bg-teal-800"
        >
          Sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-4 py-6">
        {messages.length === 0 && (
          <div className="mx-auto max-w-2xl">
            <p className="mb-4 text-sm text-zinc-600">
              Ask about Utah General Retention Schedules. Answers are grounded
              in ingested GRS PDFs and cite the series id.
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              {STARTERS.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => submit(s)}
                  className="rounded-lg border border-teal-200 bg-white px-3 py-2 text-left text-sm text-teal-900 hover:bg-teal-50"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) => {
          const text = messageText(m);
          const sources =
            m.role === "assistant"
              ? sourcesFrom(m).filter(
                  (s) => !text || text.includes(s.sourceId),
                )
              : [];
          return (
            <div
              key={m.id}
              className={`mx-auto max-w-2xl rounded-xl px-4 py-3 text-sm leading-relaxed ${
                m.role === "user"
                  ? "bg-teal-700 text-white"
                  : "border border-zinc-200 bg-white text-zinc-900"
              }`}
            >
              <div className="mb-1 text-xs font-semibold uppercase tracking-wide opacity-70">
                {m.role === "user" ? "You" : "DataGovAI"}
              </div>
              <div className="whitespace-pre-wrap">{text}</div>
              {sources.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {sources.map((s) => (
                    <span
                      key={s.sourceId}
                      className="rounded-full bg-teal-50 px-2 py-0.5 text-xs text-teal-800"
                    >
                      {s.sourceId}
                      {s.title ? ` · ${s.title}` : ""}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
        {error && (
          <p className="mx-auto max-w-2xl text-sm text-red-600">
            {(() => {
              const copy = errorCopy(error.message);
              return (
                <>
                  {copy.text}
                  {copy.signIn ? (
                    <>
                      {" "}
                      <Link href="/sign-in" className="underline">
                        Sign in
                      </Link>
                    </>
                  ) : null}
                </>
              );
            })()}
          </p>
        )}
        <div ref={bottomRef} />
      </div>

      <form
        className="border-t border-zinc-200 bg-white px-4 py-3"
        onSubmit={(e) => {
          e.preventDefault();
          submit(input);
        }}
      >
        <div className="mx-auto flex max-w-2xl gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a GRS question…"
            className="flex-1 rounded-lg border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-teal-600"
          />
          {busy ? (
            <button
              type="button"
              onClick={() => stop()}
              className="rounded-lg bg-zinc-700 px-4 py-2 text-sm text-white"
            >
              Stop
            </button>
          ) : (
            <button
              type="submit"
              className="rounded-lg bg-teal-700 px-4 py-2 text-sm text-white hover:bg-teal-800"
            >
              Ask
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
