<p align="center">
  <img src="./logo.png" alt="DataGovAI Logo" style="width: 100%; max-width: 800px;"/>
</p>

Utah General Retention Schedules (GRS) knowledge assistant. Ask a records question; answers are grounded in ingested GRS PDFs and cite the series id.

Copyright © 2026 Utah Office of Data Privacy (ODP). All Rights Reserved.

Collaboration: Utah Valley University, Smith College of Engineering and Technology.

## Live

**https://datagovai-web.vercel.app** — production chat requires sign-in (seeded admin: `admin@datagovai.local`).

## Quick start

```bash
cd web
cp .env.example .env.local   # fill DATABASE_URL, AUTH_SECRET, gateway auth
npm install
npm run db:push
npm run ingest -- --limit 20
npm run seed:admin
npm run dev
```

Open the URL Next prints (often http://localhost:3000). Local shortcut: `admin` / `admin`. Details: [`web/README.md`](web/README.md). Plan: [`docs/development/plan.md`](docs/development/plan.md).

## How it works

```
data/raw GRS PDFs → web/scripts/ingest.ts → Neon document_chunks (pgvector)
question → /api/chat → hybrid retrieve + rerank → AI Gateway → cited answer
```

Citation chips show only series ids named in the answer.

## Layout

```
DataGovAI-local/
├── web/                 # Next.js app (the product)
│   ├── src/app/         # Chat UI, sign-in, /api/chat
│   ├── src/lib/         # DB, RAG retrieve/embed/rerank, prompts
│   └── scripts/         # ingest, seed-admin, smoke, push-env
├── data/raw/            # GRS PDFs (local; gitignored)
├── docs/development/plan.md
└── README.md
```
