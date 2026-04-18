# Security Model

Hermes executes LLM-generated code at runtime and communicates with a live broker gateway (OpenAlgo). This document explains the multi-layer security model designed to prevent malicious or hallucinated code from causing damage.

## The Threat Model

Because the AI agent calls `exec()` on code that a language model wrote, there are two categories of risk:

1. **Accidental harm** — The LLM hallucinates dangerous code (e.g., `os.remove()`) while trying to do something legitimate.
2. **Adversarial prompts** — A user crafts an input that causes the LLM to generate code that exfiltrates the `OPENALGO_API_KEY` or deletes files.

---

## Layer 1: Execution Sandbox (`_sandbox_execute`)

**File:** `agent/runner.py`

When the agent runs LLM-generated code, it uses Python's `exec()` with a **restricted global namespace** called `safe_globals`:

```python
safe_globals = {
    "pd": pd,
    "np": np,
    "__builtins__": {
        "print": print, "range": range, "len": len,
        "min": min, "max": max, "sum": sum, "abs": abs,
        "round": round, "int": int, "float": float,
        "str": str, "bool": bool, "list": list,
        "dict": dict, "set": set, "tuple": tuple,
        "enumerate": enumerate, "zip": zip
    }
}
```

**What this blocks:**
- `import` statements of any kind (no `__import__` in builtins)
- File system access (`open()` not available)
- `eval()`, `exec()`, `compile()`
- `os`, `subprocess`, `sys` modules
- `globals()`, `getattr()`, `setattr()`

**What this allows (intentionally):**
- `pandas` (`pd`) — required for signal generation
- `numpy` (`np`) — required for numerical calculations
- Core Python builtins needed for standard loops and math

> [!WARNING]
> Python sandbox escapes via object introspection (e.g., `().__class__.__mro__[1].__subclasses__()`) are theoretically possible. **Layer 1 is not a full sandbox.** For production deployments running untrusted code, add Docker container-level isolation for the `_sandbox_execute` call.

---

## Layer 2: Export Gate (`_sanitize_code`)

**File:** `agent/runner.py`

Even if code passes the execution sandbox, it is **scanned a second time** before being written to an export file. Export files (in `hermes_strategies/`) run with **full Python permissions** (they include `import os` in the boilerplate).

The export gate uses regex pattern matching to block **14 dangerous patterns**:

| Pattern | Blocked Because |
|---|---|
| `import os` | OS file system and process access |
| `import subprocess` | Shell command execution |
| `import sys` | Python runtime manipulation |
| `import shutil` | File/directory deletion |
| `from os` | Partial `os` import bypass |
| `from subprocess` | Partial `subprocess` import bypass |
| `__import__(` | Dynamic import bypass |
| `eval(` | Code injection |
| `exec(` | Nested code execution |
| `open(` | Direct file system access |
| `compile(` | Bytecode compilation |
| `globals(` | Global namespace access |
| `getattr(` | Attribute introspection |
| `setattr(` | Attribute mutation |

If any violation is found, the export is **blocked entirely**, a message is printed, and the violation is logged to the wiki for future reference.

---

## Layer 3: Path Sanitization (`_safe_session_id`)

**File:** `agent/runner.py`

Export directories are created using the session ID, which is derived from user input (the symbol name). To prevent **directory traversal attacks** (e.g., a symbol like `../../etc`), all session IDs are sanitized:

```python
re.sub(r'[^a-zA-Z0-9_\-]', '_', session_id)[:200]
```

This strips everything except alphanumeric characters, underscores, and hyphens, and truncates to 200 characters.

---

## Layer 4: Network-Isolated API Communication

**File:** `data_pipeline/openalgo_connector.py`

Hermes communicates with OpenAlgo exclusively via its documented REST API over the internal `hermes_net` Docker network. There is no shared file system access, no DuckDB file mount, and no direct database connection.

This means:
- Hermes cannot corrupt OpenAlgo's internal state.
- The `OPENALGO_API_KEY` is the only credential Hermes holds — it cannot log in to the broker directly.
- Even if the LLM generated code that tried to call `requests.post("http://openalgo:5000/api/v1/placeorder")`, it would be blocked by Layer 1 (no `requests` in `safe_globals`) and Layer 2 (`import requests` is an import statement).
- Exported strategy files that DO have network access use only the `openalgo` SDK with the pre-configured API key from environment variables — they cannot access or exfiltrate the broker session token.

---

## Layer 5: Non-Root Docker Containers

**File:** `Dockerfile` (Hermes), `openalgo/Dockerfile` (OpenAlgo)

Both the Streamlit application and OpenAlgo run as **non-root users** inside Docker. If a sandbox escape occurs within either container, the attacker cannot write to system directories or escalate privileges.

---

## Summary

| Layer | Mechanism | Protects Against |
|---|---|---|
| 1 | Restricted `exec()` builtins | Accidental/malicious imports at runtime |
| 2 | Regex static analysis export gate | Dangerous code reaching production files |
| 3 | Session ID path sanitization | Directory traversal |
| 4 | REST API only, no shared filesystem | DB corruption, credential theft |
| 5 | Non-root Docker user (both containers) | Container privilege escalation |

## Known Limitations & Recommendations

> [!CAUTION]
> - Layer 1 does not protect against advanced Python introspection-based sandbox escapes.
> - If you run this platform as a public web service, wrap `_sandbox_execute()` in a subprocess call that runs inside a throwaway Docker container with a resource limit (CPU, memory, network disabled).
> - Rotate your `OPENALGO_API_KEY` and `OPENROUTER_API_KEY` regularly.
> - Never commit your `.env` files — both `hermes_research_platform/.env` and `openalgo/.env` are already in their respective `.gitignore` files.
> - The `openalgo/.env` contains your broker API keys. Treat it with the same care as a password.
