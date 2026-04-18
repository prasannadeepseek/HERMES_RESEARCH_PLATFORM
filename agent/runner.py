import os
import re
import time
import pandas as pd
import numpy as np
from datetime import datetime
from data_pipeline.openalgo_connector import OpenAlgoClient

from agent.llm_router import HermesLLM
from agent.memory import HermesMemory
from agent.registry import HermesRegistry
from backtester.engine import HermesBacktester

class HermesRunner:
    """
    The Core Agentic Loop for Hermes.
    Connects the LLM, Context Memory, Backtester, and Iteration Registry.
    """
    def __init__(self, session_id: str, df: pd.DataFrame, config: dict):
        self.session_id = session_id
        self.df = df
        self.config = config
        
        self.llm = HermesLLM()
        self.memory = HermesMemory()
        self.registry = HermesRegistry()
        self.backtester = HermesBacktester()
        
    def execute_research_loop(self, max_iterations=5):
        """
        Runs the autonomous strategy generation loop.
        """
        print(f"Starting Research Session: {self.session_id}")
        
        # 1. Retrieve Context & Skills
        context = self.memory.retrieve_wiki_context(keywords=["strategy", "lessons", "failures"])
        skills = self.memory.list_available_skills()
        
        previous_code = ""
        previous_feedback = ""
        
        for i in range(1, max_iterations + 1):
            print(f"--- Iteration {i}/{max_iterations} ---")
            
            # 2. Build Prompt
            prompt = f"Goal: Create a trading strategy meeting these metrics: {self.config}\n"
            if previous_code:
                prompt += f"\nPrevious attempt failed. Code:\n{previous_code}\n\nFeedback:\n{previous_feedback}\n"
                prompt += "Please fix the logic to achieve the target metrics."
            else:
                prompt += "Please write the initial `evaluate(df, params)` function."
                
            # 3. Generate Code
            print("Generating code via LLM...")
            code = self.llm.generate_strategy_code(prompt=prompt, context=context, skills=skills)
            
            if not code:
                print("Failed to generate code.")
                break
                
            # 4. Sandbox Execution (Evaluate)
            metrics, failures = self._sandbox_execute(code)
            
            # 5. Check Goals
            goals_met, failure_reasons = self.backtester.check_goals(metrics, self.config)
            if failure_reasons:
                failures.extend(failure_reasons)
                
            # 6. Log Iteration to Registry
            self.registry.log_iteration(
                session_id=self.session_id,
                strategy_name=self.config.get("name", "Unknown Strategy"),
                iteration_number=i,
                code_snippet=code,
                metrics=metrics,
                failures=failures,
                goals_met=goals_met
            )
            
            if goals_met:
                print(f"✅ Success! Strategy meets all goals on iteration {i}.")
                self._export_strategy(code)
                self.memory.save_wiki_entry(f"Success: {self.session_id}", f"Achieved goals with {metrics['Total_Return_Pct']:.2f}% ROI. Code pattern saved.")
                return True
                
            print(f"❌ Goals not met. Failures: {failures}")
            previous_code = code
            previous_feedback = str(failures)
            
        print("❌ Max iterations reached without meeting goals.")
        self.memory.save_wiki_entry(f"Failure Analysis: {self.session_id}", "Strategy failed to meet goals after max iterations.")
        return False

    def _sandbox_execute(self, code: str):
        """
        Safely executes the LLM generated code against the backtester.
        """
        # Note: In production, this MUST run in a sandboxed process/Docker container to prevent arbitrary code execution.
        # Restricting __builtins__ to prevent easy access to 'open', '__import__', 'eval', etc.
        safe_globals = {
            "pd": pd,
            "np": np,
            "__builtins__": {
                "print": print,
                "range": range,
                "len": len,
                "min": min,
                "max": max,
                "sum": sum,
                "abs": abs,
                "round": round,
                "int": int,
                "float": float,
                "str": str,
                "bool": bool,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "enumerate": enumerate,
                "zip": zip
            }
        }
        local_scope = {}
        try:
            # Inject pandas and numpy and safe builtins into the local scope for the strategy to use
            exec(code, safe_globals, local_scope)
            
            if "evaluate" not in local_scope:
                return {}, ["Code is missing the `evaluate(df, params)` function."]
                
            # Run the generated evaluate function
            evaluate_func = local_scope["evaluate"]
            entries, exits, short_entries, short_exits = evaluate_func(self.df, self.config.get("params", {}))
            
            # Run through Backtester
            metrics, _ = self.backtester.evaluate_signals(self.df, entries, exits, short_entries, short_exits)
            return metrics, []
            
        except Exception as e:
            return {}, [f"Runtime Error during execution: {str(e)}"]

    @staticmethod
    def _sanitize_code(code: str) -> tuple[bool, list[str]]:
        """
        Static analysis pass to block dangerous patterns in LLM-generated code
        before it is written to an unrestricted export file.
        Returns (is_safe, list_of_violations).
        """
        violations = []
        banned_patterns = [
            (r'\bimport\s+os\b', 'import os'),
            (r'\bimport\s+subprocess\b', 'import subprocess'),
            (r'\bimport\s+sys\b', 'import sys'),
            (r'\bimport\s+shutil\b', 'import shutil'),
            (r'\bfrom\s+os\b', 'from os'),
            (r'\bfrom\s+subprocess\b', 'from subprocess'),
            (r'\b__import__\s*\(', '__import__()'),
            (r'\beval\s*\(', 'eval()'),
            (r'\bexec\s*\(', 'exec()'),
            (r'\bopen\s*\(', 'open()'),
            (r'\bcompile\s*\(', 'compile()'),
            (r'\bglobals\s*\(', 'globals()'),
            (r'\bgetattr\s*\(', 'getattr()'),
            (r'\bsetattr\s*\(', 'setattr()'),
        ]
        for pattern, name in banned_patterns:
            if re.search(pattern, code):
                violations.append(f"Blocked dangerous pattern: {name}")
        return len(violations) == 0, violations

    @staticmethod
    def _safe_session_id(session_id: str) -> str:
        """Sanitize session_id to prevent path traversal."""
        # Strip everything except alphanumeric, underscores, and hyphens
        return re.sub(r'[^a-zA-Z0-9_\-]', '_', session_id)[:200]

    def _export_strategy(self, code: str):
        """
        Wraps the successful logic into OpenAlgo's SDK format and exports to hermes_strategies/
        """
        # Static analysis gate — refuse to export unsafe code
        is_safe, violations = self._sanitize_code(code)
        if not is_safe:
            print(f"⛔ Strategy export BLOCKED due to dangerous code patterns:")
            for v in violations:
                print(f"   - {v}")
            self.memory.save_wiki_entry(
                f"Blocked Export: {self.session_id}",
                f"Code contained dangerous patterns: {violations}"
            )
            return

        # Standard OpenAlgo Boilerplate
        safe_id = self._safe_session_id(self.session_id)
        boilerplate = f'''#!/usr/bin/env python
"""
Auto-Generated by Hermes AI
Session: {safe_id}
"""
from openalgo import api
import pandas as pd
import numpy as np
import time
import os

api_key = os.getenv('OPENALGO_API_KEY')
host    = os.getenv('HOST_SERVER', 'http://127.0.0.1:5000')

if not api_key:
    print("Error: OPENALGO_API_KEY environment variable not set")
    exit(1)

client = api(api_key=api_key, host=host)

{code}

def main():
    print("Starting AI Strategy...")
    # Add live loop execution logic here utilizing the `evaluate` function.
    
if __name__ == "__main__":
    main()
'''
        export_dir = os.path.join("hermes_strategies", safe_id)
        os.makedirs(export_dir, exist_ok=True)
        
        file_path = os.path.join(export_dir, "strategy.py")
        with open(file_path, "w") as f:
            f.write(boilerplate)
            
        print(f"Strategy exported to {file_path} - Ready for OpenAlgo UI upload!")
        return file_path

    def export_to_openalgo(self, code: str, deploy: bool = False) -> dict:
        """
        Export a validated strategy to the local hermes_strategies/ directory
        and optionally deploy it live to the OpenAlgo broker gateway.

        Args:
            code:   The validated strategy Python code (must contain evaluate()).
            deploy: If True, attempt to push the strategy file to OpenAlgo's
                    /api/v1/strategies endpoint. If False (default), only write
                    locally — useful for review before going live.

        Returns:
            dict with keys:
                exported_path (str): Local file path of the written strategy.
                deployed (bool):     Whether the strategy was pushed to OpenAlgo.
                order_result (dict): Result of the OpenAlgo deploy call, if attempted.
                errors (list):       Any errors encountered.
        """
        result = {"exported_path": None, "deployed": False, "order_result": {}, "errors": []}

        # Step 1: Write to local file
        try:
            path = self._export_strategy(code)
            result["exported_path"] = path
        except Exception as e:
            result["errors"].append(f"Local export failed: {e}")
            return result

        if not deploy:
            print("ℹ️  Strategy written locally. Set deploy=True to push to OpenAlgo.")
            return result

        # Step 2: Push to OpenAlgo REST API
        client = OpenAlgoClient()
        if not client.ping():
            result["errors"].append(
                f"OpenAlgo not reachable at {client.host}. "
                "Is OpenAlgo running? Check: make status"
            )
            return result

        safe_id = self._safe_session_id(self.session_id)
        try:
            with open(result["exported_path"], "r") as f:
                strategy_code = f.read()

            # OpenAlgo strategy deployment endpoint
            order_result = client._post("/api/v1/strategies", {
                "strategy_name": safe_id,
                "strategy_code": strategy_code,
                "strategy_type": "python",
            })
            result["order_result"] = order_result

            if order_result.get("status") == "success":
                result["deployed"] = True
                print(f"✅ Strategy '{safe_id}' deployed to OpenAlgo successfully.")
                self.memory.save_wiki_entry(
                    f"Deployed: {self.session_id}",
                    f"Strategy deployed to OpenAlgo at {client.host}. Result: {order_result}"
                )
            else:
                msg = order_result.get("message", "Unknown error from OpenAlgo")
                result["errors"].append(f"OpenAlgo deploy returned: {msg}")
                print(f"⚠️  OpenAlgo deploy response: {msg}")

        except Exception as e:
            result["errors"].append(f"OpenAlgo deploy error: {e}")
            print(f"⚠️  Error deploying to OpenAlgo: {e}")

        return result
