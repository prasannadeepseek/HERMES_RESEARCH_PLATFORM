# Hermes Research Platform - System Setup

This document outlines the foundational setup required to get the Hermes Research Platform running locally.

## Prerequisites
- **Python 3.10+**: Ensure Python is installed on your system.
- **Docker & Docker Compose**: Used for spinning up the Hermes UI and connecting to external services.
- **Git**: For version control and cloning legacy repositories if needed.
- **TA-Lib C Library**: Required before installing Python TA-Lib. On macOS: `brew install ta-lib`. On Ubuntu: `sudo apt-get install libta-lib-dev`.

> [!IMPORTANT]
> TA-Lib requires its **C library** to be installed on your OS *before* running `pip install -r requirements.txt`. Without this, the `trend_momentum.py` and `mean_reversion.py` strategies will fail to import.

## 1. Virtual Environment Setup
It is highly recommended to use a virtual environment to manage dependencies.

```bash
# Navigate to the project root
cd hermes_research_platform

# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install the required packages
pip install -r requirements.txt
```

## 2. Environment Variables
You need an `.env` file in the root directory to store your API keys and configuration.

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in all required keys:

| Variable | Description | Required |
|---|---|---|
| `LLM_PROVIDER` | `openrouter` or `local` | Yes |
| `OPENROUTER_API_KEY` | Your OpenRouter key (if using cloud LLM) | Conditional |
| `MODEL_NAME` | Model slug e.g. `anthropic/claude-3-5-sonnet` | Yes |
| `OPENALGO_HOST` | OpenAlgo server URL (default `http://127.0.0.1:5000`) | Yes |
| `OPENALGO_API_KEY` | Your OpenAlgo API key | Yes |
| `OPENALGO_DUCKDB_PATH` | Path to Historify DuckDB file | Yes |
| `LOCAL_API_BASE` | Ollama/vLLM base URL (if using local LLM) | Conditional |
| `TRUEDATA_USERNAME` | TrueData username (optional data source) | No |
| `TRUEDATA_PASSWORD` | TrueData password (optional data source) | No |

3. If running **outside Docker**, set `OPENALGO_DUCKDB_PATH` to your local path, e.g.:
   ```
   OPENALGO_DUCKDB_PATH=/Users/yourname/openalgo/data/historify.duckdb
   ```

## 3. Running Locally (Without Docker)
For development, run the Streamlit app directly:
```bash
# With venv active
streamlit run app.py
```

The Streamlit UI will be available at `http://localhost:8501`.

## 4. Running with Docker Compose
The platform is designed to be easily spun up using Docker. The container runs as a **non-root user** (`appuser`) for security.

```bash
# Build and start the services
docker-compose up --build -d

# To view logs
docker-compose logs -f hermes_ui

# Stop the services
docker-compose down
```

> [!NOTE]
> Docker automatically maps the `../openalgo` directory into the container at `/openalgo`. Ensure the OpenAlgo directory exists at the same level as `hermes_research_platform/`.

## 5. Project Directory Layout

```
hermes_research_platform/
├── agent/                  # AI agent core (LLM, memory, registry, runner)
│   ├── llm_router.py       # Routes prompts to OpenRouter or local Ollama
│   ├── memory.py           # Obsidian-style wiki + skills vault
│   ├── registry.py         # SQLite-backed iteration tracker
│   ├── runner.py           # Core agentic loop (generate → backtest → iterate)
│   └── templates/          # OpenAlgo boilerplate templates
├── backtester/             # Backtesting engines
│   ├── engine.py           # vectorbt-based high-speed engine (used by AI agent)
│   └── swing_backtester.py # Simple event-driven backtester (for manual use)
├── data_pipeline/          # Data connectors
│   └── openalgo_connector.py # Reads from OpenAlgo's local DuckDB
├── data/                   # Static datasets (CSVs, instrument tokens)
├── docs/                   # This documentation
├── hermes_strategies/      # Live strategy modules
│   ├── trend_momentum.py
│   ├── mean_reversion.py
│   └── delivery_analysis.py
├── hermes_wiki/            # Agent-generated knowledge vault (auto-created)
├── skills/                 # Agent-generated reusable skill scripts (auto-created)
├── temp_repos/             # Legacy code preserved as git submodules
├── app.py                  # Streamlit UI entry point
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Next Steps
Proceed to [02_data_management.md](./02_data_management.md) to learn how to connect Hermes to OpenAlgo and gather market data.
