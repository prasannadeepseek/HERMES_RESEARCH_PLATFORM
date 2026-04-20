# Hermes Research Platform - System Setup

This document outlines the foundational setup required to get the Hermes Research Platform running locally alongside **OpenAlgo** (MarketCalls), the broker gateway.

## Prerequisites
- **Docker & Docker Compose**: The primary way to run the full stack. Both services run in containers.
- **Git**: For version control and pulling upstream OpenAlgo updates.
- **Python 3.10+** *(only needed for local dev without Docker)*
- **TA-Lib C Library** *(only needed for local dev)*: On macOS: `brew install ta-lib`. On Ubuntu: `sudo apt-get install libta-lib-dev`.

> [!IMPORTANT]
> **OpenAlgo is a completely separate repository.** You do NOT need to install its Python dependencies. Docker handles everything. You only need to fill in your broker credentials in `openalgo/.env`.

---

## 1. Workspace Structure

Your workspace is structured as sibling repositories under a shared root:

```
scratch/                              ← Workspace root
├── docker-compose.yml                ← Root orchestrator (start EVERYTHING here)
├── Makefile                          ← Convenience commands
│
├── openalgo/                         ← OpenAlgo repo (marketcalls/openalgo)
│   └── .env                          ← OpenAlgo broker credentials (fill this in!)
│
└── hermes_research_platform/         ← This repo (Hermes)
    ├── app.py                        ← Streamlit UI entry point
    ├── data_pipeline/
    │   └── openalgo_connector.py     ← REST API client (talks to OpenAlgo over HTTP)
    ├── agent/                        ← AI agent core
    ├── backtester/                   ← Backtesting engines
    ├── hermes_strategies/            ← Exported strategy files
    ├── docker-compose.yml            ← Hermes-only compose (for isolated dev)
    └── .env.example                  ← Copy to .env and fill in
```

> [!NOTE]
> Both services run on a shared Docker network (`hermes_net`). Hermes calls OpenAlgo at `http://openalgo:5000` internally. No file mounts or shared databases.

---

## 2. First-Time Setup

### Step 1: Configure OpenAlgo (Zerodha / Upstox)

```bash
cd scratch/openalgo
# The .env is pre-configured for Zerodha and Upstox. Fill in your broker credentials:
nano .env
```

Set these required values in `openalgo/.env`:

| Variable | Description |
|---|---|
| `BROKER_API_KEY` | Your Zerodha / Upstox API key |
| `BROKER_API_SECRET` | Your Zerodha / Upstox API secret |
| `REDIRECT_URL` | `http://127.0.0.1:5000/zerodha/callback` (or `upstox`) |
| `APP_KEY` | Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `API_KEY_PEPPER` | Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |

### Step 2: Configure Hermes

```bash
cd scratch/hermes_research_platform
cp .env.example .env
nano .env
```

| Variable | Description | Required |
|---|---|---|
| `LLM_PROVIDER` | `openrouter` or `local` | Yes |
| `OPENROUTER_API_KEY` | Your OpenRouter key | Conditional |
| `MODEL_NAME` | Model slug e.g. `anthropic/claude-3-5-sonnet` | Yes |
| `OPENALGO_HOST` | Auto-set to `http://openalgo:5000` in Docker | Yes |
| `OPENALGO_API_KEY` | Get from OpenAlgo UI after first login (see Step 4) | Yes |
| `TRUEDATA_USERNAME` | TrueData username (optional data source) | No |
| `TRUEDATA_PASSWORD` | TrueData password | No |

### Step 3: Start Both Services

```bash
cd scratch/
make start
```

This starts:
- **OpenAlgo** → `http://localhost:5000`
- **Hermes UI** → `http://localhost:8501`

### Step 4: Get Your OpenAlgo API Key

1. Go to `http://localhost:5000`
2. Complete the initial setup wizard (create admin account)
3. Log in with your Zerodha / Upstox broker credentials
4. Navigate to **Settings → API Keys → Generate New Key**
5. Copy the key into `hermes_research_platform/.env` as `OPENALGO_API_KEY`

---

## 3. Daily Workflow

```bash
cd scratch/

make start          # Start both services
make stop           # Stop both services
make status         # Check running containers
make logs           # Tail logs from both
make logs-hermes    # Hermes logs only
make logs-openalgo  # OpenAlgo logs only
```

---

## 4. Updating OpenAlgo (Upstream Changes)

OpenAlgo is maintained independently by MarketCalls. To pull the latest:

```bash
cd scratch/
make update-openalgo    # git pull from marketcalls/openalgo
make rebuild-openalgo   # Rebuild Docker image with new code
make restart-openalgo   # Restart the container
```

> [!IMPORTANT]
> You **never need to check OpenAlgo's Python dependencies** — Docker handles it entirely. `make rebuild-openalgo` will install whatever `requirements.txt` the upstream repo specifies inside the container.

---

## 5. Running Locally (Without Docker)

For Hermes development only (no full Docker stack):

```bash
cd hermes_research_platform
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

> [!NOTE]
> In this mode, set `OPENALGO_HOST=http://127.0.0.1:5000` in your `.env` and run OpenAlgo separately with `make openalgo-only`.

---

## 6. Automated Deployment & Synchronization
        
Hermes is designed for a fully automated research-to-deployment loop. When a research session meets all defined goals (ROI, Drawdown, Robustness), the following happens:

1.  **Local Export**: The strategy code is sanitized and saved to `hermes_strategies/`.
2.  **OpenAlgo Registration**: Hermes calls the OpenAlgo **Strategy Creation API** (`POST /api/v1/strategy/create`) to automatically create an entry in your OpenAlgo dashboard.
3.  **UI Feedback**: You will see a success message in Hermes, and the new strategy will immediately appear in your OpenAlgo "Strategies" list (Standard Strategies) for deployment.

> [!NOTE]
> This automation requires a valid `OPENALGO_API_KEY` to be set in your `.env`.

---

## 7. Project Directory Layout

```
hermes_research_platform/
├── agent/                  # AI agent core (LLM, memory, registry, runner)
│   ├── llm_router.py       # Routes prompts to OpenRouter or local Ollama
│   ├── memory.py           # Obsidian-style wiki + skills vault
│   ├── registry.py         # SQLite-backed iteration tracker
│   └── runner.py           # Core agentic loop + strategy export
├── backtester/             # Backtesting engines
│   ├── engine.py           # vectorbt-based high-speed engine (AI agent)
│   └── swing_backtester.py # Event-driven backtester (manual use)
├── data_pipeline/
│   └── openalgo_connector.py  # OpenAlgo REST API client
├── data/                   # Static datasets (CSVs, instrument tokens)
├── docs/                   # This documentation
├── hermes_strategies/      # AI-generated live strategy files
├── hermes_wiki/            # Agent knowledge vault (auto-created)
├── skills/                 # Agent reusable skill scripts (auto-created)
├── temp_repos/             # Legacy code from previous repos
├── app.py                  # Streamlit UI entry point
├── docker-compose.yml      # Hermes-only compose (for isolated dev)
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Next Steps
Proceed to [02_data_management.md](./02_data_management.md) to understand how Hermes fetches market data from OpenAlgo.
