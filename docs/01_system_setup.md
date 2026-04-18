# Hermes Research Platform - System Setup

This document outlines the foundational setup required to get the Hermes Research Platform running locally.

## Prerequisites
- **Python 3.10+**: Ensure Python is installed on your system.
- **Docker & Docker Compose**: Used for spinning up the Hermes UI and connecting to external services.
- **Git**: For version control and cloning legacy repositories if needed.

## 1. Virtual Environment Setup
It is highly recommended to use a virtual environment to manage dependencies.

```bash
# Navigate to the project root
cd /Users/prasanna/.gemini/antigravity/scratch/hermes_research_platform

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
2. Open `.env` and fill in your keys (e.g., OpenAI API key for the agents, Anthropic key, etc.).
3. Ensure `OPENALGO_DUCKDB_PATH` is correctly pointing to your local Historify path if running outside of Docker.

## 3. Running with Docker Compose
The platform is designed to be easily spun up using Docker. This ensures the Streamlit UI and any background services have the correct environment.

```bash
# Build and start the services
docker-compose up --build -d

# To view logs
docker-compose logs -f hermes_ui
```

The Streamlit UI will be available at `http://localhost:8501`.

## Next Steps
Proceed to [02_data_management.md](./02_data_management.md) to learn how to connect Hermes to OpenAlgo and gather market data.
