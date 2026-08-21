import { convertToModelMessages, streamText, type UIMessage } from "ai";

import { auth } from "@/auth";
import { PRIMARY_MODEL, TEMPERATURE } from "@/lib/ai/model";
import { buildSystemPrompt } from "@/lib/ai/system-prompt";
import { db } from "@/lib/db/client";
import { conversations, messages as messagesTable } from "@/lib/db/schema";
import { logger } from "@/lib/logger";
import { formatRetrievedChunks, retrieveContext } from "@/lib/rag/retrieve";

export const maxDuration = 60;

type ChatBody = {
  messages: UIMessage[];
};

function lastUserText(messages: UIMessage[]): string {
  for (let i = messages.length - 1; i >= 0; i--) {
    const m = messages[i];
    if (m.role !== "user") continue;
    return m.parts
      .filter((p): p is { type: "text"; text: string } => p.type === "text")
      .map((p) => p.text)
      .join(" ");
  }
  return "";
}

export async function POST(req: Request) {
  const session = await auth();
  if (process.env.NODE_ENV === "production" && !session?.user?.id) {
    return new Response("Unauthorized", { status: 401 });
  }

  const body = (await req.json()) as ChatBody;
  const { messages } = body;
  if (!Array.isArray(messages)) {
    return new Response("Invalid body", { status: 400 });
  }

  const query = lastUserText(messages);
  const retrieved = query ? await retrieveContext(query, 5) : [];
  const system = buildSystemPrompt(formatRetrievedChunks(retrieved));

  let result;
  try {
    result = streamText({
      model: PRIMARY_MODEL,
      system,
      messages: await convertToModelMessages(messages),
      temperature: TEMPERATURE,
    });
  } catch (err) {
    logger.error({ err }, "stream.init_failed");
    return new Response("AI service temporarily unavailable.", { status: 503 });
  }

  const sources = retrieved.map((r) => ({
    sourceId: r.sourceId,
    title: r.title,
  }));

  return result.toUIMessageStreamResponse({
    originalMessages: messages,
    messageMetadata: ({ part }) => {
      if (part.type === "start") {
        return { sources };
      }
    },
    onFinish: async ({ messages: finalMessages }) => {
      const userId = session?.user?.id;
      if (!userId || !query) return;
      const assistant = [...finalMessages]
        .reverse()
        .find((m) => m.role === "assistant");
      const text =
        assistant?.parts
          .filter((p): p is { type: "text"; text: string } => p.type === "text")
          .map((p) => p.text)
          .join("") ?? "";
      try {
        const [convo] = await db
          .insert(conversations)
          .values({ userId, title: query.slice(0, 80) })
          .returning();
        if (!convo) return;
        await db.insert(messagesTable).values([
          { conversationId: convo.id, role: "user", content: query },
          { conversationId: convo.id, role: "assistant", content: text },
        ]);
      } catch (err) {
        logger.warn({ err }, "persist.messages_failed");
      }
    },
  });
}
