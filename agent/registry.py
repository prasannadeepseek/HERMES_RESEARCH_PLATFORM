import sqlite3
import json
import os
from datetime import datetime

class HermesRegistry:
    """
    SQLite-based Iteration Registry to track LLM strategy generation attempts.
    Ensures that semi-successful strategies are saved even if the final goal isn't met.
    """
    def __init__(self, db_path="registry.sqlite"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create Iterations Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_iterations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                strategy_name TEXT,
                iteration_number INTEGER,
                timestamp TEXT,
                code_snippet TEXT,
                metrics_json TEXT,
                failures_json TEXT,
                goals_met BOOLEAN,
                robustness_score REAL DEFAULT 0
            )
        ''')
        
        # Create Skills Table (For the Dynamic Skill Generation feature)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generated_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT UNIQUE,
                description TEXT,
                file_path TEXT,
                timestamp TEXT
            )
        ''')
        
        # Migration: Add robustness_score if it doesn't exist
        try:
            cursor.execute("ALTER TABLE strategy_iterations ADD COLUMN robustness_score REAL DEFAULT 0")
        except sqlite3.OperationalError:
            # Column already exists
            pass
            
        conn.commit()
        conn.close()

    def log_iteration(self, session_id: str, strategy_name: str, iteration_number: int, 
                      code_snippet: str, metrics: dict, failures: list, goals_met: bool, robustness_score: float = 0):
        """
        Logs a single backtest run iteration to the database.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO strategy_iterations 
            (session_id, strategy_name, iteration_number, timestamp, code_snippet, metrics_json, failures_json, goals_met, robustness_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            strategy_name,
            iteration_number,
            datetime.now().isoformat(),
            code_snippet,
            json.dumps(metrics),
            json.dumps(failures),
            goals_met,
            robustness_score
        ))
        
        conn.commit()
        conn.close()
        
    def get_best_iteration(self, session_id: str):
        """
        Retrieves the iteration with the highest ROI for a given session.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Using JSON_EXTRACT requires sqlite compiled with json1 extension. 
        # For simplicity without assuming sqlite features, we fetch all and sort in python.
        cursor.execute("SELECT id, iteration_number, metrics_json, code_snippet, goals_met, robustness_score FROM strategy_iterations WHERE session_id = ?", (session_id,))
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return None
            
        best_row = None
        best_roi = -float('inf')
        
        for row in rows:
            metrics = json.loads(row[2])
            roi = metrics.get("Total_Return_Pct", -999)
            if roi > best_roi:
                best_roi = roi
                best_row = {
                    "id": row[0],
                    "iteration": row[1],
                    "metrics": metrics,
                    "code": row[3],
                    "goals_met": bool(row[4]),
                    "robustness_score": row[5]
                }
                
        return best_row

    def get_session_history(self, session_id: str):
        """
        Retrieves all iterations for a given session.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT iteration_number, metrics_json, failures_json, goals_met, strategy_name 
            FROM strategy_iterations 
            WHERE session_id = ? 
            ORDER BY iteration_number ASC
        """, (session_id,))
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                "iteration": row[0],
                "metrics": json.loads(row[1]),
                "failures": json.loads(row[2]),
                "goals_met": bool(row[3]),
                "concept": row[4]
            })
        return history
