import os
import litellm

class HermesLLM:
    """
    LLM Router for Hermes. Supports OpenRouter (Antigravity/Claude) and Local (Gemma 4).
    """
    def __init__(self, provider="openrouter", model_name=None):
        self.provider = provider.lower()
        
        if self.provider == "openrouter":
            self.model = model_name or os.getenv("MODEL_NAME", "openrouter/anthropic/claude-3.5-sonnet")
            # liteLLM handles openrouter automatically if OPENROUTER_API_KEY is in env
            
        elif self.provider == "local":
            # For Ollama/vLLM hosting Gemma 4 locally
            base_url = os.getenv("LOCAL_API_BASE", "http://localhost:11434")
            model = model_name or os.getenv("MODEL_NAME", "gemma:4b")
            self.model = f"ollama/{model}"
            litellm.api_base = base_url
            
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def generate_strategy_code(self, prompt: str, context: str, skills: str) -> str:
        """
        Queries the LLM to generate Python code for a strategy.
        """
        system_prompt = f"""
        You are Hermes, an expert algorithmic trading AI.
        Your goal is to write a Python trading strategy using the `vectorbt` library and OpenAlgo SDK format.
        
        AVAILABLE SKILLS (You can import these natively):
        {skills}
        
        HISTORICAL CONTEXT & LEARNINGS:
        {context}
        
        Return ONLY valid Python code. Do not wrap in markdown blocks, just return the raw python string.
        The code must implement an `evaluate()` function that returns `entries` and `exits` pandas Series.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        print(f"Routing request to {self.model} via {self.provider}...")
        
        try:
            response = litellm.completion(
                model=self.model,
                messages=messages,
                temperature=0.2 # Low temp for code logic
            )
            code = response.choices[0].message.content
            
            # Clean up potential markdown formatting from LLM
            if code.startswith("```python"):
                code = code.split("```python")[1]
            if code.endswith("```"):
                code = code.rsplit("```", 1)[0]
                
            return code.strip()
            
        except Exception as e:
            print(f"LLM Generation Error: {e}")
            return ""
