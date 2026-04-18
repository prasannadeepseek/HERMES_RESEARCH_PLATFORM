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
        if not os.path.exists(self.index_file):
            with open(self.index_file, "w") as f:
                f.write("# Hermes Knowledge Index\n\nThis vault contains learnings about market behavior and API structures.\n")

    def save_wiki_entry(self, topic: str, content: str):
        """
        Saves a learning to the markdown vault.
        """
        # Clean topic string for filename and truncate to safe length
        filename = "".join(x for x in topic if x.isalnum() or x in " _-").replace(" ", "_").lower()
        filename = filename[:200] + ".md"
        filepath = os.path.join(self.wiki_dir, filename)
        
        # Append if exists, else write new
        mode = "a" if os.path.exists(filepath) else "w"
        with open(filepath, mode) as f:
            f.write(f"\n## {topic}\n")
            f.write(content + "\n")
            
        # Update index if new
        if mode == "w":
            with open(self.index_file, "a") as f:
                f.write(f"- [[{filename}]] - {topic}\n")

    def retrieve_wiki_context(self, keywords: list) -> str:
        """
        Naive RAG: Scans markdown files for keywords and returns relevant context.
        In a production system, this would use vector embeddings.
        """
        context = ""
        files = glob.glob(os.path.join(self.wiki_dir, "*.md"))
        
        for file in files:
            with open(file, "r") as f:
                content = f.read()
                if any(kw.lower() in content.lower() for kw in keywords):
                    # For simplicity, returning the whole file if keyword hits.
                    # A better approach would chunk the markdown.
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
