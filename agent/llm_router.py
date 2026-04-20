import os
import litellm

class HermesLLM:
    """
    Generic LLM Router for Hermes. 
    Powered by LiteLLM to support any provider (OpenRouter, OpenAI, Anthropic, Local, etc.)
    """
    def __init__(self, model_name=None, api_base=None, api_key=None):
        # 1. Prioritize passed arguments, then fall back to .env
        self.model = model_name or os.getenv("MODEL_NAME", "openrouter/anthropic/claude-3.5-sonnet")
        self.api_base = api_base or os.getenv("LLM_API_BASE")
        self.api_key = api_key or os.getenv("LLM_API_KEY") # Optional: LiteLLM usually finds provider-specific keys (e.g. OPENROUTER_API_KEY)

    def generate_strategy_code(self, prompt: str, context: str, skills: str) -> str:
        """
        Queries the LLM to generate Python code for a strategy.
        """
        system_prompt = f"""
        You are Hermes, an expert algorithmic trading AI.
        Your goal is to write a Python trading strategy using the `vectorbt` library and OpenAlgo SDK format.
        
        SAFE SKILLS CHEAT SHEET (USE THESE INSTEAD OF DIRECT VBT):
        - SMA: `get_ma(df['close'], window=20)`
        - RSI: `get_rsi(df['close'], window=14)`
        - Bollinger Bands: `bb = get_bbands(df['close'], window=20, std=2.0)` -> then use `bb.upper`, `bb.lower`, `bb.middle`
        - MACD: `m = get_macd(df['close'], fast=12, slow=26, signal=9)` -> then use `m.macd`, `m.signal`
        - ATR: `get_atr(df['high'], df['low'], df['close'], window=14)`
        - ADX: `get_adx(df['high'], df['low'], df['close'], window=14)`
        - Generic: `run_indicator('RSI', df['close'], window=14)` -> Recommended for others
        
        AVAILABLE SKILLS & CONTEXT:
        {skills}
        {context}

        RULES:
        1. An `evaluate(df, params)` function that returns `entries`, `exits`, `short_entries`, `short_exits`.
        2. MANDATORY: Review the "AVAILABLE SKILLS & CONTEXT" section above. DO NOT repeat any strategy concept that has already been documented as a SUCCESS or FAILURE. Use this context to evolve your logic.
        3. You MUST include a one-line comment at the very top of the function: `# Strategy: [One sentence description]`.
        4. All constants MUST be pulled from the `params` dictionary.
        5. YOU MUST NOT OVER-FILTER. If a strategy has zero trades, it is a failure. Avoid using more than 2-3 simultaneous conditions for entry.
        6. ENSURE VARIETY. If your previous attempt failed, DO NOT repeat the same concept. Try a different approach (e.g. if Trend-Following failed, try Mean-Reversion or Volatility-Breakout).
        7. At the end of the file, provide a dictionary named `PARAM_RANGES`.
        
        Example Format:
        ```python
        def evaluate(df, params):
            rsi_window = params.get('rsi_window', 14)
            rsi = run_indicator('RSI', df['close'], window=rsi_window)
            entries = rsi < params.get('rsi_lower', 30)
            exits = rsi > params.get('rsi_upper', 70)
            return entries, exits, None, None

        PARAM_RANGES = {{
            "rsi_window": range(10, 30, 2),
            "rsi_lower": range(20, 40, 5),
            "rsi_upper": range(60, 80, 5)
        }}
        ```
        
        Do not wrap in markdown blocks, just return the raw python string.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        print(f"Routing request to {self.model}...")
        
        try:
            return self._call_llm(messages, self.model, self.api_base, self.api_key)
        except Exception as e:
            print(f"Primary LLM Error: {e}")
            
            # Check for Local Fallback
            if os.getenv("ENABLE_LOCAL_FALLBACK", "false").lower() == "true":
                fallback_model = os.getenv("LOCAL_MODEL_NAME", "ollama/llama3")
                fallback_base = os.getenv("LOCAL_LLM_URL", "http://localhost:11434/v1")
                print(f"🔄 Attempting Local Fallback to {fallback_model}...")
                try:
                    return self._call_llm(messages, fallback_model, fallback_base, "no-key")
                except Exception as fe:
                    print(f"Fallback Error: {fe}")
            
            return ""

    def _call_llm(self, messages, model, api_base, api_key) -> str:
        """Helper to perform the actual litellm call and cleaning."""
        call_kwargs = {
            "model": model,
            "messages": messages,
            "temperature": 0.2
        }
        if api_base:
            call_kwargs["api_base"] = api_base
        if api_key:
            call_kwargs["api_key"] = api_key
            
        response = litellm.completion(**call_kwargs)
        code = response.choices[0].message.content
        
        # Clean up potential markdown formatting
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
            
        return code.strip()
