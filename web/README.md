# DataGovAI web

Next.js + Vercel AI SDK + Neon pgvector. Answers Utah GRS questions from ingested PDFs.

**Live:** https://datagovai-web.vercel.app

## Local

```bash
cd web
cp .env.example .env.local
npm install
npm run db:push
npm run ingest -- --limit 20
npm run seed:admin
npm run dev
```

Local shortcut: `admin` / `admin` (disabled when `NODE_ENV=production`). Production uses the seeded admin (`admin@datagovai.local`; set `ADMIN_SEED_PASSWORD` or the default from `scripts/seed-admin.ts`).

Gateway auth locally: `vercel env pull` or `VERCEL_OIDC_TOKEN` / `AI_GATEWAY_API_KEY` in `.env.local`.

## Scripts

| Command | Purpose |
|---------|---------|
| `npm run ingest -- --limit 20` | Chunk + embed preferred GRS PDFs from `../data/raw` |
| `npm run ingest -- --pdf ../data/raw/<file>.pdf` | Ingest one PDF |
| `npm run seed:admin` | Create/update the admin user |
| `npm run smoke` | Retrieval check for starter queries (`--generate` also calls the LLM) |
| `./scripts/push-env.sh` | Sync `.env.local` to Vercel production + development |

## Deploy

```bash
vercel link --yes --project datagovai-web --scope memari-majids-projects
./scripts/push-env.sh
vercel deploy --prod --yes
```
