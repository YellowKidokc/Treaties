# Docker Deployment Guide

## Quick Start

### Option 1: App + Postgres (Ollama runs separately)
Best for: Most setups. Ollama stays on your main machine or a separate box.

```bash
# 1. Make sure Ollama is running locally (or on another machine)
ollama serve

# 2. Start the stack
docker-compose up --build

# 3. Pull the model (first time only)
ollama pull llama3.1:8b-instruct-q4_K_M

# 4. Seed axioms (optional)
docker exec treaties-app python scripts/seed_axioms.py
```

App: http://localhost:8000  
Postgres: localhost:5432

---

### Option 2: Everything in Docker (App + Postgres + Ollama)
Best for: Dedicated server with 16GB+ RAM.

```bash
# 1. Start everything
docker-compose -f docker-compose.full.yml up --build

# 2. Pull the model into the Ollama container
docker exec treaties-ollama ollama pull llama3.1:8b-instruct-q4_K_M

# 3. Seed axioms
docker exec treaties-app python scripts/seed_axioms.py
```

---

### Option 3: Mini PC / Low Power Setup
Best for: Low-RAM machines. Ollama is too heavy — use an external LLM API instead.

**You have two choices:**

**A) Keep Ollama on a more powerful machine**  
Set `OLLAMA_BASE_URL=http://192.168.1.X:11434` in your `.env` pointing to your main PC.

```bash
docker-compose up --build
```

**B) Replace Ollama with an API (Groq, OpenAI, etc.)**  
This requires a small code change in `app/services/ollama_client.py` to call the API instead. Ask Kimmy or me to wire that up — it's about 20 lines of code.

---

## RAM Requirements

| Setup | Minimum RAM | Recommended |
|-------|-------------|-------------|
| App + Postgres only | 2GB | 4GB |
| App + Postgres + Ollama 8B | 8GB | 16GB |
| App + Postgres + Ollama 70B | 48GB | 64GB+ |

---

## Snapshots

Generated HTML snapshots are written to:
- **In container:** `/app/snapshots/`
- **On host:** `./snapshots/` (mounted volume)

Copy these files to your website:
```bash
cp snapshots/*.html /path/to/faiththruphysics.com/proof-explorer/
```

---

## Updating the App

```bash
# Pull latest code, rebuild, keep Postgres data
docker-compose down
docker-compose up --build

# Or force full rebuild
docker-compose down -v
docker-compose up --build
```

---

## Troubleshooting

**"Cannot connect to Ollama"**
- Check `OLLAMA_BASE_URL` in `.env`
- If Ollama is on the Docker host (Windows/Mac), use `http://host.docker.internal:11434`
- Make sure Ollama is actually running: `curl http://localhost:11434/api/tags`

**"Database does not exist"**
- Postgres takes a few seconds to start. The app waits for the healthcheck, but if you manually connect too fast, wait.
- Or run: `docker-compose up -d postgres`, wait 5s, then `docker-compose up app`

**"Out of memory" when running Ollama in Docker**
- Your machine doesn't have enough RAM. Use Option 1 or 3 instead.
- Or use a smaller model: `OLLAMA_MODEL=llama3.2:3b`
