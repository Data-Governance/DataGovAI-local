# DataGovAI web

Implementation of the GRS chatbot.

- How it works: **[root README](../README.md)**
- **Login and test:** [root README — Login and test](../README.md#login-and-test)
- Plan: [`docs/development/plan.md`](../docs/development/plan.md)

```bash
cd web
cp .env.example .env.local
npm install
npm run db:push
npm run ingest -- --limit 20
npm run seed:admin
npm run dev
```
