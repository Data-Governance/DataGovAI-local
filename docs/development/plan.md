# DataGovAI GRS RAG

**Status:** Active.

## Goal

A Utah GRS chatbot that answers only from ingested PDFs, with series citations. Stack: Next.js + AI SDK + Neon/pgvector + Voyage via Vercel AI Gateway.

**How the app works, including login and test:** see the root [`README.md`](../../README.md).

## Architecture

```
GRS PDFs (data/raw) → web/scripts/ingest.ts → chunk → embed → Neon document_chunks
User question → /api/chat → hybrid retrieve → GRS system prompt → streamText → cited answer
```

App root: `web/`.

## Stack

- Next.js App Router + TypeScript (`web/src`)
- Vercel AI SDK v6 + AI Gateway (`provider/model` strings)
- Neon Postgres + Drizzle + pgvector (`vector(1024)` + HNSW)
- Voyage `voyage/voyage-3-large` and `voyage/rerank-2.5` via the `ai` package
- Auth.js credentials (production requires a session)
- Chat UI: Sign in / Sign out; chips filtered to cited GRS ids

## Schema

- Auth: `user`, `account`, `session`, `verificationToken`
- `document_chunks`: `sourceId`, `title`, `content`, embedding
- `conversations`, `messages`

Dedicated Neon database `datagovai`.

## Run

```bash
cd web
npm install
npm run db:push
npm run ingest -- --limit 20
npm run seed:admin
npm run dev
```

Preferred ingest set includes council minutes, audits, personnel files (GRS-19374 / GRS-19375), and legal case files (GRS-11284) so the four starter prompts retrieve.

## Deployment

Live: **https://datagovai-web.vercel.app** (Vercel project `datagovai-web`).

```bash
cd web
./scripts/push-env.sh
vercel deploy --prod --yes
```

Production env: `DATABASE_URL`, `AUTH_SECRET`, `AUTH_URL`, `ENABLE_DEV_LOGIN`, `ADMIN_EMAILS`. Do not push `VERCEL_OIDC_TOKEN` / `AI_GATEWAY_API_KEY` — Gateway auth is automatic on Vercel.
