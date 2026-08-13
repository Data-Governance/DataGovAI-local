# DataGovAI web

Implementation of the GRS chatbot. How the system works, architecture, and operations: **[root README](../README.md)**. Plan: [`docs/development/plan.md`](../docs/development/plan.md).

```bash
cd web
cp .env.example .env.local
npm install
npm run db:push
npm run ingest -- --limit 20
npm run seed:admin
npm run dev
```
