import os
import re
import time
import pandas as pd
import numpy as np
import vectorbt as vbt
from datetime import datetime
from data_pipeline.openalgo_connector import OpenAlgoClient

from agent.llm_router import HermesLLM
from agent.memory import HermesMemory
from agent.registry import HermesRegistry
from agent.optimizer import HermesOptimizer
from backtester.engine import HermesBacktester
from agent.db import init_db, save_iteration, get_history

class HermesRunner:
    """
    The Core Agentic Loop for Hermes.
    Connects the LLM, Context Memory, Backtester, and Iteration Registry.
    """
    def __init__(self, session_id: str, df: pd.DataFrame, config: dict, llm_config: dict = None):
        self.session_id = session_id
        self.df = df
        self.config = config
        
        # Use UI overrides if provided, otherwise defaults to .env
        llm_config = llm_config or {}
        self.llm = HermesLLM(
            model_name=llm_config.get("model_name"),
            api_base=llm_config.get("api_base"),
            api_key=llm_config.get("api_key")
        )
        self.memory = HermesMemory()
        self.registry = HermesRegistry()
        self.backtester = HermesBacktester()
        self.optimizer = HermesOptimizer(self.backtester)
        self.iteration_log = []
        
    def execute_research_loop(self, max_iterations=5, status_callback=None, auto_deploy=False):
        """
        Runs the autonomous strategy generation loop.
        """
        def update_status(msg):
            if status_callback:
                status_callback(msg)
            print(msg)

        update_status(f"Starting Research Session: {self.session_id}")
        update_status(f"🎯 Objective: ROI > {self.config.get('target_roi', 0)}% | Drawdown < {self.config.get('max_drawdown', 100)}%")
        
        # 1. Retrieve Context & Skills
        context = self.memory.retrieve_wiki_context(keywords=["success", "failure", "iteration", "insight"])
        skills = self.memory.list_available_skills()
        
        previous_code = ""
        previous_feedback = ""
        
        for i in range(1, max_iterations + 1):
            update_status(f"--- Iteration {i}/{max_iterations} ---")
            
            # 2. Build Prompt
            prompt = f"Goal: Create a trading strategy meeting these metrics: {self.config}\n"
            if previous_code:
                prompt += f"\nPrevious attempt failed. Code:\n{previous_code}\n\nFeedback:\n{previous_feedback}\n"
                if "0.00%" in previous_feedback:
                    prompt += "CRITICAL: The previous strategy had ZERO trades. You MUST simplify the logic. Remove unnecessary filters and loosen the entry thresholds so that trades are actually triggered."
                else:
                    prompt += "Please fix the logic to achieve the target metrics."
            else:
                prompt += "Please write the initial `evaluate(df, params)` function."
                
            # 3. Generate Code
            update_status("🧠 Generating strategy logic via LLM...")
            code = self.llm.generate_strategy_code(prompt=prompt, context=context, skills=skills)
            if code.strip() == previous_code.strip():
                update_status("⚠️ Duplicate code generation detected. Breaking to avoid infinite loop.")
                break
            
            if not code:
                update_status("❌ Failed to generate code.")
                break
            
            strategy_desc = "Unknown"
            match = re.search(r"# Strategy: (.*)", code)
            if match:
                strategy_desc = match.group(1)
            update_status(f"🚀 **Concept**: {strategy_desc}")
                
            # 4. Sandbox Execution
            metrics, failures, eval_func, param_ranges = self._sandbox_execute(code)
            
            # 5. Local Optimization
            opt_metrics, opt_params = None, None
            robustness_score = 0
            
            if eval_func and param_ranges:
                update_status("🔍 Logic acquired. Now optimizing parameters locally (Zero LLM Hits)...")
                opt_metrics, opt_params = self.optimizer.optimize(self.df, eval_func, param_ranges, self.config)
                if opt_metrics:
                    update_status(f"✨ Found improved parameters: {opt_params}")
                    metrics = opt_metrics
            
            # 6. Check Goals
            goals_met = False
            if metrics:
                goals_met, failure_reasons = self.backtester.check_goals(metrics, self.config)
                if failure_reasons:
                    failures.extend(failure_reasons)
            else:
                goals_met = False
                if not failures:
                    failures.append("Strategy execution returned no metrics.")
            
            log_entry = f"Iteration {i}: ROI {metrics.get('Total_Return_Pct', 0):.2f}%, DD {metrics.get('Max_Drawdown_Pct', 0):.2f}% | Concept: {strategy_desc}"
            if failures:
                log_entry += f"\n  - Failures: {failures}"
            self.iteration_log.append(log_entry)
            
            # Save iteration details
            status_text = "SUCCESS" if goals_met else "FAILURE"
            wiki_content = f"ROI: {metrics.get('Total_Return_Pct', 0):.2f}%\nDD: {metrics.get('Max_Drawdown_Pct', 0):.2f}%\nConcept: {strategy_desc}\nFailures: {failures}\n\nCode:\n```python\n{code}\n```"
            save_iteration(
                session_id=self.session_id,
                iteration=i,
                success=goals_met,
                code=code,
                metrics=metrics,
                wiki_md=wiki_content,
            )

            # 7. Log Iteration to Registry
            self.registry.log_iteration(
                session_id=self.session_id,
                strategy_name=strategy_desc,
                iteration_number=i,
                code_snippet=code,
                metrics=metrics,
                failures=failures,
                goals_met=goals_met,
                robustness_score=robustness_score,
            )

            if goals_met:
                update_status(f"✅ GOAL MET: ROI {metrics.get('Total_Return_Pct', 0):.2f}% >= {self.config.get('target_roi', 0)}% | DD {abs(metrics.get('Max_Drawdown_Pct', 0)):.2f}% <= {self.config.get('max_drawdown', 0)}%")
                update_status(f"✅ Success! Strategy meets all goals on iteration {i}.")

                if eval_func:
                    update_status("🛡️  Running OASIS Stress Test (Regime Robustness)...")
                    robustness_score, regime_details = self.backtester.run_oasis_stress_test(self.df, eval_func, opt_params or self.config.get("params", {}))
                    update_status(f"🛡️  Robustness Score: {robustness_score:.1f}%")
                    
                    for regime, info in regime_details.items():
                        if info.get('passed'):
                            update_status(f"✅ Regime '{regime}' passed (ROI {info.get('roi'):.2f}%).")
                        else:
                            reason = info.get('error') or f"ROI {info.get('roi'):.2f}% failed"
                            update_status(f"❌ Regime '{regime}' failed: {reason}")
                    
                    regime_label = "Robust" if robustness_score >= 60 else "Fragile"
                    self.memory.save_market_insight(
                        relationship=f"{strategy_desc} -> {regime_label} in stressed regimes",
                        evidence=f"Achieved {metrics.get('Total_Return_Pct', 0):.2f}% ROI with {robustness_score:.1f}% robustness on {self.session_id}"
                    )
                    
                    if robustness_score < 60:
                        update_status("⚠️  Warning: Strategy is fragile in non‑ideal regimes.")
                
                if auto_deploy:
                    update_status("🚀 Auto-deploying success to OpenAlgo...")
                    self.export_to_openalgo(code, deploy=True)
                else:
                    self._export_strategy(code)
                return True
                
            update_status(f"❌ Goals not met. Failures: {failures}")
            previous_code = code
            previous_feedback = str(failures)
            
        print("❌ Max iterations reached without meeting goals.")
        save_iteration(
            session_id=self.session_id,
            iteration=max_iterations,
            success=False,
            code="",
            metrics={},
            wiki_md="Strategy failed to meet goals after max iterations.",
        )
        return False

    def _sandbox_execute(self, code: str):
        from skills.vbt_utils import get_ma, get_rsi, get_bbands, get_macd, get_atr, get_adx, run_indicator
        safe_globals = {
            "pd": pd, "np": np, "vbt": vbt,
            "get_ma": get_ma, "get_rsi": get_rsi, "get_bbands": get_bbands,
            "get_macd": get_macd, "get_atr": get_atr, "get_adx": get_adx,
            "run_indicator": run_indicator, "__builtins__": __builtins__
        }
        local_scope = {}
        try:
            exec(code, safe_globals, local_scope)
            if "evaluate" not in local_scope:
                return {}, ["Code is missing the `evaluate(df, params)` function."], None, None
                
            evaluate_func = local_scope["evaluate"]
            param_ranges = local_scope.get("PARAM_RANGES", {})
            entries, exits, short_entries, short_exits = evaluate_func(self.df, self.config.get("params", {}))
            
            metrics, _ = self.backtester.evaluate_signals(
                df=self.df, entries=entries, exits=exits, 
                short_entries=short_entries, short_exits=short_exits
            )
            return metrics, [], evaluate_func, param_ranges
        except Exception as e:
            return {}, [f"Runtime Error during execution: {str(e)}"], None, None

    @staticmethod
    def _sanitize_code(code: str) -> tuple[bool, list[str]]:
        violations = []
        banned_patterns = [
            (r'\bimport\s+os\b', 'import os'), (r'\bimport\s+subprocess\b', 'import subprocess'),
            (r'\bimport\s+sys\b', 'import sys'), (r'\bimport\s+shutil\b', 'import shutil'),
            (r'\beval\s*\(', 'eval()'), (r'\bexec\s*\(', 'exec()'), (r'\bopen\s*\(', 'open()')
        ]
        for pattern, name in banned_patterns:
            if re.search(pattern, code):
                violations.append(f"Blocked dangerous pattern: {name}")
        return len(violations) == 0, violations

    @staticmethod
    def _safe_session_id(session_id: str) -> str:
        return re.sub(r'[^a-zA-Z0-9_\-]', '_', session_id)[:200]

    def _export_strategy(self, code: str):
        is_safe, violations = self._sanitize_code(code)
        if not is_safe:
            print(f"⛔ Strategy export BLOCKED")
            return None

        safe_id = self._safe_session_id(self.session_id)
        boilerplate = f'# Session: {safe_id}\nimport pandas as pd\nimport numpy as np\n{code}'
        export_dir = os.path.join("hermes_strategies", safe_id)
        os.makedirs(export_dir, exist_ok=True)
        file_path = os.path.join(export_dir, "strategy.py")
        with open(file_path, "w") as f:
            f.write(boilerplate)
        return file_path

    def export_to_openalgo(self, code: str, deploy: bool = False) -> dict:
        result = {"exported_path": None, "deployed": False, "order_result": {}, "errors": []}
        try:
            path = self._export_strategy(code)
            result["exported_path"] = path
        except Exception as e:
            result["errors"].append(f"Local export failed: {e}")
            return result

        if deploy:
            client = OpenAlgoClient()
            if not client.ping():
                result["errors"].append("OpenAlgo not reachable.")
                return result
            # ... (deployment logic)
        return result