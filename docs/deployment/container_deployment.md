# Container-Based Deployment

This project can be run "as-is" inside containers (app + PostgreSQL/pgvector) with a single command. You can use it locally, on a VM, or in GitHub Codespaces—no manual Python or Postgres installs required.

---

## Prerequisites

- **Docker** (v20.10+)
- **Docker Compose** (v2+)
- **Git**
- (Optional) A `.env` file in the project root with your app's environment settings (see `.env.example`).

---

## 1. Clone the Repo

```bash
git clone https://github.com/<your-username>/DataGovAI.git
cd DataGovAI
```

---

## 2. Build & Launch Containers

All services and dependencies are defined in:

- `Dockerfile` (builds the Python/Streamlit app with micromamba)  
- `docker-compose.yml` (stands up PostgreSQL + pgvector and the app)

Run:

```bash
docker-compose up --build -d
```

- **db** service  
  - Image: `ankane/pgvector:postgres14`  
  - Environment: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`  
  - Volume: `db_data` persists your database  
- **app** service  
  - Builds from the `Dockerfile`  
  - Reads your `.env` for `DATABASE_URL`, embedding model settings, etc.  
  - Exposes port **8505**

---

## 3. Access the Application

- Streamlit UI:  http://localhost:8505  
- Postgres (if you want to `psql` in): `localhost:5432`  

```bash
# Example: open a psql shell
docker-compose exec db psql -U datagov_user datagov
```

---

## 4. Tear Down

When you're done, stop and remove containers:

```bash
docker-compose down
```

> The `db_data` volume remains, so restarting with `docker-compose up` will restore your database state.

---

## Running in GitHub Codespaces

1. **Push** all changes (including `Dockerfile` & `docker-compose.yml`) to GitHub.  
2. In GitHub, click **Code → Codespaces → New codespace** on your branch.  
3. Codespaces will detect `.devcontainer/devcontainer.json` (which references your Compose file) and spin up both services.  
4. Once ready, open the **Ports** panel in the bottom bar, find port **8505**, and click **Open in Browser**.  

To inspect containers or run commands inside the app container:

```bash
# Open a bash shell in the app service
docker-compose exec app bash
```

To stop:

```bash
docker-compose down
```

---

You now have a fully containerized DataGovAI stack—no local installs needed! 🎉