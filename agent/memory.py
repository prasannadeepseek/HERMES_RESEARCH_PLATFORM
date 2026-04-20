import os
import glob

class HermesMemory:
    """
    Manages long-term context (Obsidian-style Wiki) and dynamic Skill generation.
    This prevents the LLM context window from ballooning while maintaining persistence.
    """
    def __init__(self, base_dir="."):
        self.wiki_dir = os.path.join(base_dir, "hermes_wiki")
        self.skills_dir = os.path.join(base_dir, "skills")
        
        os.makedirs(self.wiki_dir, exist_ok=True)
        os.makedirs(self.skills_dir, exist_ok=True)
        
        # Initialize an index file if it doesn't exist
        self.index_file = os.path.join(self.wiki_dir, "INDEX.md")
        self.insights_file = os.path.join(self.wiki_dir, "MARKET_INSIGHTS.md")
        
        if not os.path.exists(self.index_file):
            with open(self.index_file, "w") as f:
                f.write("# Hermes Knowledge Index\n\nThis vault contains learnings about market behavior and API structures.\n")
        
        if not os.path.exists(self.insights_file):
            with open(self.insights_file, "w") as f:
                f.write("# Market Insights (MiroFish Grounding)\n\nPersistent relationships and behavioral patterns.\n")

    def save_wiki_entry(self, topic: str, content: str, session_id: str = ""):
        """
        Saves a learning to the markdown vault.
        """
        # Clean topic string for filename
        clean_topic = "".join(x for x in topic if x.isalnum() or x in " _-").replace(" ", "_").lower()
        
        # Prefix with session_id if provided
        prefix = f"{session_id}_" if session_id else ""
        filename = f"{prefix}{clean_topic}".replace("__", "_")[:200] + ".md"
        filepath = os.path.join(self.wiki_dir, filename)
        
        # Append if exists, else write new
        mode = "a" if os.path.exists(filepath) else "w"
        with open(filepath, mode) as f:
            f.write(f"\n## {topic} (Session: {session_id})\n")
            f.write(content + "\n")
            
        # Update index if new
        if mode == "w":
            with open(self.index_file, "a") as f:
                f.write(f"- [[{filename}]] - {topic} ({session_id})\n")

    def save_market_insight(self, relationship: str, evidence: str):
        """
        Saves a structured market relationship (MiroFish Grounding).
        Format: "Entity A -> Behavior -> Entity B"
        """
        with open(self.insights_file, "a") as f:
            f.write(f"\n- **Insight**: {relationship}\n")
            f.write(f"  - *Evidence*: {evidence}\n")
            f.write(f"  - *Logged*: {os.path.basename(relationship)}\n")

    def retrieve_wiki_context(self, keywords: list) -> str:
        """
        Naive RAG: Scans markdown files for keywords and returns relevant context.
        In a production system, this would use vector embeddings.
        """
        context = ""
        # 1. Always include Market Insights for grounding
        if os.path.exists(self.insights_file):
            with open(self.insights_file, "r") as f:
                context += "=== MiroFish Market Grounding ===\n"
                context += f.read() + "\n"

        # 2. Search for keyword-specific wiki entries
        files = glob.glob(os.path.join(self.wiki_dir, "*.md"))
        
        for file in files:
            if "MARKET_INSIGHTS" in file or "INDEX" in file:
                continue
            with open(file, "r") as f:
                content = f.read()
                if any(kw.lower() in content.lower() for kw in keywords):
                    context += f"\n--- From {os.path.basename(file)} ---\n"
                    context += content[:1500] + "...\n" # Limit size
                    
        return context if context else "No historical context found for these topics."

    def generate_skill(self, skill_name: str, python_code: str, description: str):
        """
        Saves a redundant action as a reusable Python script.
        """
        filename = f"{skill_name}.py"
        filepath = os.path.join(self.skills_dir, filename)
        
        with open(filepath, "w") as f:
            f.write(f'"""\nSkill: {skill_name}\nDescription: {description}\n"""\n\n')
            f.write(python_code)
            
        self.save_wiki_entry("Skills Index", f"Generated new skill: `{skill_name}` - {description}")
        return filepath

    def list_available_skills(self) -> str:
        """
        Returns a formatted string of available skills for the LLM prompt.
        """
        skills = glob.glob(os.path.join(self.skills_dir, "*.py"))
        if not skills:
            return "No custom skills generated yet."
            
        res = "Available Python Skills (can be imported locally):\n"
        for s in skills:
            res += f"- {os.path.basename(s)}\n"
        return res
