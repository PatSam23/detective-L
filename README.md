# 🕵️ Detective-L

**A production-grade, multi-agent AI research intelligence platform.**

> *"I built a production-grade AI system with a multi-agent research pipeline backed by an LLM Gateway that handles caching, failover, rate limiting, and observability."*

Detective-L autonomously researches any business or technical topic by orchestrating specialized AI agents in parallel, synthesizes findings into structured intelligence reports, fact-checks its own output, and delivers everything through a real-time streaming dashboard.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🤖 **Multi-Agent Pipeline** | 7 specialized agents (Planner → Web Research → Synthesis → Critic → Revisor → Formatter) orchestrated via LangGraph |
| 🌐 **LLM Gateway** | Unified proxy for OpenAI, Anthropic, and Gemini — swap providers without touching agent code |
| ⚡ **Redis Cache** | SHA-256 prompt-hash caching with 24h TTL — 50–90% reduction in redundant LLM API calls |
| 🗄️ **PostgreSQL Analytics** | Full request/response logging: tokens, latency, model, cache hit/miss, timestamp |
| 🚦 **Rate Limiting** | Redis-backed Token Bucket algorithm — per API key / IP enforcement with HTTP 429 |
| 🔁 **Circuit Breaker + Failover** | Exponential backoff retries, provider failover chain (gemini → openai → anthropic) |
| 📊 **Observability** | Structured JSON logging, Prometheus metrics, Grafana dashboards |
| 🐳 **Docker Compose** | One-command infrastructure: backend + Redis + PostgreSQL + Prometheus + Grafana |
| 🌍 **Multi-Environment** | `.env.dev` / `.env.uat` / `.env.prod` with strict `dev → uat → main` branching strategy |
| 🖥️ **Real-Time Dashboard** | Next.js frontend with SSE streaming — live agent status updates as research runs |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Next.js Frontend                          │
│         (SSE Streaming • Real-Time Agent Status • Reports)       │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP + SSE
┌───────────────────────────▼─────────────────────────────────────┐
│                     FastAPI Backend                              │
│   POST /research/stream  •  GET /health  •  GET /analytics/usage │
│   GET /cache/stats       •  POST /gateway/chat                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                   LangGraph Agent Pipeline                        │
│                                                                   │
│  [Planner] → [Web Researcher ×N] → [Synthesis] → [Critic]        │
│           ↑_______[Revisor]_____________↓  (max 2 loops)         │
│                        → [Formatter] → Final Report              │
└───────────┬───────────────────────────────────────┬─────────────┘
            │                                       │
┌───────────▼───────────┐               ┌───────────▼─────────────┐
│     LLM Gateway        │               │      Tavily Web Search   │
│  POST /gateway/chat    │               │  (parallel per subtopic) │
│  ┌─────────────────┐  │               └─────────────────────────┘
│  │ Redis Cache      │  │
│  │ Rate Limiter     │  │
│  │ Circuit Breaker  │  │
│  │ Failover Chain   │  │
│  └─────────────────┘  │
│  Gemini/OpenAI/Claude  │
└───────────────────────┘
            │
┌───────────▼───────────────────────────────────────────────────┐
│                    Infrastructure                               │
│   Redis (cache + rate limits + circuit breakers)               │
│   PostgreSQL (analytics + usage tracking)                       │
│   Prometheus (metrics scraping)  •  Grafana (dashboards)        │
└────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend
| Layer | Technology |
|---|---|
| Orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) — multi-agent state machine with cycles |
| LLM Framework | [LangChain](https://python.langchain.com/) — prompts, chains, message types |
| Observability | [LangSmith](https://smith.langchain.com/) — traces, evals, dashboards |
| API Server | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) |
| Web Search | [Tavily API](https://tavily.com/) — real-time web research |
| Caching | [Redis 7](https://redis.io/) — prompt-hash cache + Token Bucket rate limiter |
| Database | [PostgreSQL 15](https://www.postgresql.org/) + SQLAlchemy 2.0 (async) |
| Metrics | [Prometheus](https://prometheus.io/) + [Grafana](https://grafana.com/) |
| HTTP Client | [httpx](https://www.python-httpx.org/) — async gateway calls |

### Frontend
| Layer | Technology |
|---|---|
| Framework | [Next.js 14](https://nextjs.org/) (App Router) |
| Styling | [Tailwind CSS](https://tailwindcss.com/) |
| Streaming | Server-Sent Events (SSE) via `EventSource` |
| State | Custom `useResearch` hook with AbortController |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker + Docker Compose
- [Gemini API Key](https://aistudio.google.com/) (free tier works)
- [Tavily API Key](https://tavily.com/) (free tier: 1000 searches/month)

### 1. Clone & Configure

```bash
git clone https://github.com/PatSam23/detective-L.git
cd detective-L

# Copy environment template and fill in your API keys
cp .env.example .env.dev
# Edit .env.dev with your GEMINI_API_KEY and TAVILY_API_KEY
```

### 2. Start Infrastructure (Docker)

```bash
# Starts Redis, PostgreSQL, Prometheus, Grafana
docker-compose up -d redis postgres prometheus grafana

# Verify services are running
docker-compose ps
```

### 3. Start Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy backend env
cp ../.env.example .env
# Edit .env with your API keys (use localhost instead of service names)

# Start FastAPI server
uvicorn main:app --reload --port 8000
```

### 4. Start Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create frontend env
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start Next.js dev server
npm run dev
```

### 5. Open Dashboard

Navigate to **http://localhost:3000** and submit a research query.

---

## 🐳 Full Docker Deploy (All Services)

```bash
# Copy and configure environment
cp .env.example .env.dev
# Edit .env.dev — set GEMINI_API_KEY and TAVILY_API_KEY

# Build and launch all services
docker-compose up -d --build

# View logs
docker-compose logs -f backend

# Access services:
# Frontend:   http://localhost:3000
# Backend:    http://localhost:8000
# Grafana:    http://localhost:3001  (admin / admin)
# Prometheus: http://localhost:9090
```

---

## 📡 API Reference

### Research Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/research` | Synchronous research (waits for full report) |
| `POST` | `/research/stream` | SSE streaming — real-time agent updates |
| `GET` | `/health` | Service health check |

**Request body:**
```json
{
  "query": "What is the impact of quantum computing on cryptography?"
}
```

### Gateway Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/gateway/chat` | Unified LLM chat endpoint (all providers) |
| `GET` | `/cache/stats` | Redis cache statistics |
| `GET` | `/analytics/usage` | PostgreSQL usage analytics |
| `GET` | `/metrics` | Prometheus metrics endpoint |

**Gateway request:**
```json
{
  "provider": "gemini",
  "model": "gemini-2.5-flash",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 4096
}
```

---

## ⚙️ Configuration

Copy `.env.example` to your target environment file and fill in values:

```bash
# LLM Configuration
GEMINI_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
LLM_FAILOVER_CHAIN=gemini,openai,anthropic

# Redis Cache
REDIS_HOST=localhost        # Use 'redis' in Docker
REDIS_PORT=6379
CACHE_TTL=86400             # 24 hours
CACHE_ENABLED=true

# PostgreSQL Analytics
POSTGRES_USER=detective
POSTGRES_PASSWORD=your_password
POSTGRES_DB=detective_analytics
DATABASE_URL=postgresql+asyncpg://detective:password@localhost:5432/detective_analytics

# Observability
LOG_FORMAT=json             # or 'text' for human-readable console
```

---

## 🤖 Agent Pipeline

```
Query Input
    │
    ▼
┌─────────┐
│ Planner │  → Decomposes query into N subtopics (LLM)
└────┬────┘
     │ Send() — parallel fan-out
     ▼
┌──────────────────┐
│  Web Researcher  │  ×N  → Tavily search per subtopic (parallel)
│  Web Researcher  │
│  Web Researcher  │
└────────┬─────────┘
         │ Annotated[List, operator.add] — fan-in
         ▼
┌───────────┐
│ Synthesis │  → Merges all findings into structured draft (LLM)
└─────┬─────┘
      │
      ▼
┌────────┐
│ Critic │  → Fact-checks claims, scores confidence 0–100% (LLM)
└────┬───┘
     │  needs_revision? AND revision_count < 2?
     ├──YES──▶ ┌─────────┐
     │          │ Revisor │  → Improves draft based on feedback (LLM)
     │          └────┬────┘
     │               └──────────────────────────▶ (back to Critic)
     │
     └──NO──▶ ┌───────────┐
               │ Formatter │  → Structures final report with metadata (LLM)
               └─────┬─────┘
                     │
                     ▼
               Final Report JSON
```

---

## 📊 Observability

### Prometheus Metrics

Available at `http://localhost:8000/metrics`:

| Metric | Description |
|---|---|
| `gateway_cache_hits_total` | Total cache hits |
| `gateway_cache_misses_total` | Total cache misses |
| `gateway_cache_errors_total` | Cache error count |
| `http_request_duration_seconds` | Request latency histogram (auto) |
| `http_requests_total` | Total HTTP requests by status (auto) |

### Grafana Dashboards

Access at `http://localhost:3001` (admin / admin):
- Add Prometheus data source: `http://prometheus:9090`
- Import dashboards for cache hit rate, request latency, error rates

### Structured Logs

Logs are written to `backend/logs/detective-L_YYYYMMDD.log` in JSON format:

```json
{
  "timestamp": "2026-06-11T00:00:00.000Z",
  "level": "INFO",
  "logger": "app.gateway.router",
  "module": "router",
  "line": 42,
  "message": "📦 Cache HIT for key abc123...",
  "cache_hit": true,
  "provider": "gemini"
}
```

---

## 🚦 Rate Limiting

The `/gateway/chat` endpoint enforces a **Token Bucket** rate limiter per client:

- **Default:** 60 requests/minute, burst of 10
- **Client ID resolution:** `X-API-Key` header → `Authorization` header → client IP
- **Response on limit breach:** `HTTP 429 Too Many Requests`
- **Graceful degradation:** If Redis is offline, requests are allowed through

---

## 🔁 Resilience

### Failover Chain

Configure `LLM_FAILOVER_CHAIN=gemini,openai,anthropic`. On provider failure:
1. Retries current provider with exponential backoff (1s, 2s, 4s...)
2. Falls over to next provider in chain
3. Circuit breaker trips after repeated failures — skips unhealthy providers

### Circuit Breaker States

```
CLOSED (normal) → OPEN (tripped after failures) → HALF-OPEN (testing recovery)
```

State is stored in Redis, shared across all backend processes.

---

## 🌿 Git Branching Strategy

```
feature/week-N  →  dev  →  uat  →  main
```

| Branch | Purpose |
|---|---|
| `main` | Production — stable releases only, tagged (v1.0, v2.0...) |
| `uat` | Staging — QA and integration testing |
| `dev` | Active development — all features merged here first |
| `feature/*` | Individual feature branches, short-lived |

**Rules:**
- ❌ Never commit directly to `main`
- ✅ Always open PRs for review
- ✅ Test in `uat` before merging to `main`
- ✅ Tag all production releases (`git tag v1.0`)

---

## 🧪 Testing

```bash
cd backend
source .venv/bin/activate

# Mock pipeline test (no API keys needed)
python test_graph_mock.py

# Full end-to-end test (requires API keys)
python test_graph.py

# Cache unit tests (graceful without Redis)
python test_cache.py

# Rate limiter tests
python test_rate_limiter.py

# Resilience / circuit breaker tests
python test_resilience.py
```

---

## 📁 Project Structure

```
detective-L/
├── backend/
│   ├── app/
│   │   ├── agents/          # 7 specialized agents
│   │   │   ├── planner.py
│   │   │   ├── web_researcher.py
│   │   │   ├── synthesis.py
│   │   │   ├── critic.py
│   │   │   ├── revisor.py
│   │   │   └── formatter.py
│   │   ├── core/
│   │   │   ├── state.py         # AgentState TypedDict
│   │   │   ├── graph.py         # LangGraph orchestration
│   │   │   ├── llm_client.py    # Gateway-backed LLM client
│   │   │   ├── models.py        # Pydantic models
│   │   │   └── logging_config.py # Structured JSON logging
│   │   ├── gateway/
│   │   │   ├── router.py        # POST /gateway/chat endpoint
│   │   │   ├── providers.py     # OpenAI / Anthropic / Gemini
│   │   │   ├── schemas.py       # Request/response models
│   │   │   ├── cache.py         # Redis caching layer
│   │   │   ├── rate_limiter.py  # Token Bucket rate limiter
│   │   │   └── resilience.py    # Circuit breaker + retries
│   │   ├── db/
│   │   │   ├── models.py        # SQLAlchemy ORM models
│   │   │   └── database.py      # Async engine + session
│   │   └── schemas.py           # Public API schemas
│   ├── main.py                  # FastAPI app entrypoint
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── ResearchForm.tsx
│   │   ├── AgentStatus.tsx
│   │   └── ReportDisplay.tsx
│   ├── hooks/
│   │   ├── useResearch.ts
│   │   └── useTheme.ts
│   └── types/index.ts
├── docker-compose.yml           # Full infrastructure stack
├── prometheus.yml               # Prometheus scrape config
├── .env.example                 # Environment template
├── .env.dev / .env.uat / .env.prod
└── BRANCHING_STRATEGY.md
```

---

## 📚 What I Learned Building This

- **API Gateway Pattern** — single abstraction point for provider-agnostic LLM calls
- **Redis** — caching with SHA-256 prompt hashing, TTL management, atomic Lua scripts for rate limiting
- **PostgreSQL** — async SQLAlchemy schema design, indexing, analytics queries
- **Distributed Systems** — Token Bucket algorithm, Circuit Breaker (CLOSED/OPEN/HALF-OPEN), exponential backoff failover
- **Observability** — structured JSON logging, Prometheus metrics, Grafana visualization
- **LangGraph** — complex state machines with parallel fan-out (`Send()`), fan-in (annotated reducers), and conditional cycles
- **Docker** — multi-service containerization, health checks, volume persistence
- **Production Git Flow** — feature → dev → uat → main with semantic versioning

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
