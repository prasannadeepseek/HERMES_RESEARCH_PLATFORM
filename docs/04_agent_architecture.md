# AI Agent Architecture

The Hermes AI Agent is the core intelligence of the platform. It autonomously generates, backtests, and iterates on trading strategies using a loop-based agentic architecture.

## Overview

The agent loop lives in `agent/runner.py` (`HermesRunner`). Here is the high-level flow:

```
User Clicks "Start Research" in Streamlit UI
        │
        ▼
HermesRunner.execute_research_loop()
        │
        ├── 1. Retrieve context from HermesMemory (wiki + skills)
        │
        ├── 2. Build prompt for the LLM (goal + past feedback)
        │
        ├── 3. HermesLLM generates Python strategy code
        │
        ├── 4. _sandbox_execute(): exec code with restricted builtins
        │
        ├── 5. HermesBacktester.evaluate_signals() → metrics dict
        │
        ├── 6. check_goals() → goals_met? / failure_reasons?
        │
        ├── 7. HermesRegistry.log_iteration() → saves to SQLite
        │
        ├── If goals_met → _export_strategy() → hermes_strategies/
        │
        └── If not → feed failures back into next iteration prompt
```

## Module Reference

### `agent/runner.py` — `HermesRunner`

The orchestrator that ties all modules together.

| Method | Description |
|---|---|
| `execute_research_loop(max_iterations)` | Main agentic loop. Returns `True` if goals are met within iterations. |
| `_sandbox_execute(code)` | Runs LLM-generated code in a restricted `exec()` environment. Returns `(metrics, failures)`. |
| `_sanitize_code(code)` | Static analysis to block dangerous patterns (`import os`, `eval()`, `exec()`, etc.) before exporting. |
| `_safe_session_id(session_id)` | Strips path-unsafe characters from session IDs to prevent directory traversal. |
| `_export_strategy(code)` | Wraps validated strategy code in OpenAlgo SDK boilerplate and writes to `hermes_strategies/{session_id}/strategy.py`. |
| `export_to_openalgo(code, deploy)` | Exports locally AND optionally pushes the strategy to the live OpenAlgo container via REST API. |

> [!WARNING]
> The `_sandbox_execute()` method uses Python's `exec()` with a restricted `__builtins__` dictionary. While this prevents easy escapes, it is **not a full sandbox**. Do not run Hermes with access to production systems without additional container-level isolation.

---

### `agent/llm_router.py` — `HermesLLM`

Routes strategy generation prompts to the configured LLM provider.

**Supported Providers:**

| Provider | Config | Model Example |
|---|---|---|
| `openrouter` | Set `OPENROUTER_API_KEY` | `anthropic/claude-3-5-sonnet` |
| `local` | Set `LOCAL_API_BASE` (Ollama) | `gemma:4b` |

**Key behaviour:**
- `api_base` is stored per-instance (not globally mutated), so multiple `HermesLLM` instances can coexist safely.
- LLM output is automatically stripped of markdown code fences (` ```python `) before use.
- Temperature is fixed at `0.2` for deterministic code generation.

---

### `agent/memory.py` — `HermesMemory`

Manages long-term context and reusable skills without ballooning the LLM context window.

**Two storage systems:**

| System | Directory | Purpose |
|---|---|---|
| Wiki Vault | `hermes_wiki/` | Markdown files storing lessons, successes, failures |
| Skills Vault | `skills/` | Reusable Python scripts for common operations |

| Method | Description |
|---|---|
| `save_wiki_entry(topic, content)` | Saves or appends a learning to a markdown file. Filename truncated to 200 chars. |
| `retrieve_wiki_context(keywords)` | Naive keyword-based RAG — scans all wiki files, returns matching content (capped at 1500 chars per file). |
| `generate_skill(skill_name, code, description)` | Saves a Python snippet as a reusable skill script. |
| `list_available_skills()` | Returns a formatted string listing all `.py` files in `skills/`. |

> [!TIP]
> The wiki is auto-populated by the agent during runs. After a few research sessions, `hermes_wiki/` will build up a rich knowledge base of what strategies have worked and failed, improving future LLM iterations automatically.

---

### `agent/registry.py` — `HermesRegistry`

SQLite-backed persistence for every iteration of the agent loop.

**Database:** `registry.sqlite` (created automatically in the working directory; ignored by git).

**Tables:**

| Table | Description |
|---|---|
| `strategy_iterations` | Logs every LLM iteration: session ID, code, metrics JSON, failures, goals met flag |
| `generated_skills` | Index of all auto-generated skill scripts |

| Method | Description |
|---|---|
| `log_iteration(...)` | Inserts a new row for each backtesting attempt. |
| `get_best_iteration(session_id)` | Fetches the iteration with the highest ROI for a given session. |

---

### `agent/templates/base_straddle.py`

A boilerplate template for writing new strategies that plug directly into the `HermesBacktester`. All strategies must implement an `evaluate(df, params)` function returning `(entries, exits, short_entries, short_exits)` as boolean Pandas Series.

## Security Model

The agent's security model has two layers:

1. **Execution Sandbox** (`_sandbox_execute`): LLM code runs inside `exec()` with a whitelist of safe builtins only (`range`, `len`, `min`, `max`, `print`, etc.) and access to `pandas` and `numpy`. OS-level operations are blocked.

2. **Export Gate** (`_sanitize_code`): Before writing a winning strategy to disk, a regex-based static analysis pass scans for 14 banned patterns including `import os`, `import subprocess`, `eval()`, `open()`, and `__import__()`. Any violation blocks the export.

## Next Steps
See [05_backtesting_guide.md](./05_backtesting_guide.md) to learn how the backtesting engines work.
