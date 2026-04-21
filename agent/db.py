import json
from pathlib import Path
import duckdb

# Path to the SQLite/DuckDB file (located at project root)
DB_PATH = Path(__file__).parent.parent / "hermes.db"


def _conn():
    """Create a fresh DuckDB connection to the DB file."""
    return duckdb.connect(str(DB_PATH))


def init_db():
    """Create tables if they do not exist. Call at application start‑up."""
    conn = _conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS strategies (
            session_id   VARCHAR,
            iteration    INTEGER,
            success      BOOLEAN,
            code         VARCHAR,
            metrics      JSON,
            wiki_md      VARCHAR,
            created_at   TIMESTAMP DEFAULT now()
        );
        """
    )
    conn.close()


def save_iteration(session_id: str, iteration: int, success: bool, code: str, metrics: dict, wiki_md: str) -> None:
    """Insert a completed iteration into the DB.

    Args:
        session_id: Unique identifier for the research session.
        iteration:  Iteration number (1‑based).
        success:    Whether the iteration met the user goals.
        code:       The generated strategy source code.
        metrics:    Dictionary of back‑test metrics (will be stored as JSON).
        wiki_md:    Full markdown that would have been written to hermes_wiki/.
    """
    conn = _conn()
    conn.execute(
        """
        INSERT INTO strategies (session_id, iteration, success, code, metrics, wiki_md)
        VALUES (?,?,?,?,?,?);
        """,
        (session_id, iteration, success, code, json.dumps(metrics), wiki_md),
    )
    conn.close()


def get_history(session_id: str):
    """Retrieve all stored iterations for a given session.

    Returns a list of tuples: ``(iteration, success, metrics_dict)``
    """
    conn = _conn()
    rows = conn.execute(
        """
        SELECT iteration, success, metrics
        FROM strategies
        WHERE session_id = ?
        ORDER BY iteration;
        """,
        (session_id,),
    ).fetchall()
    conn.close()
    result = []
    for iteration, success, metrics_json in rows:
        try:
            metrics = json.loads(metrics_json) if isinstance(metrics_json, str) else metrics_json
        except Exception:
            metrics = {}
        result.append((iteration, success, metrics))
    return result
