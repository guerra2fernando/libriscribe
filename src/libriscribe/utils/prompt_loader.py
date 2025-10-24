"""External prompt template loader for LibriScribe."""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class PromptLoader:
    """Loads and manages external prompt templates."""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.templates_dir = self.prompts_dir / "templates"
        self.configs_dir = self.prompts_dir / "configs"
        self._cache = {}
    
    def load_prompt(self, prompt_name: str) -> Dict[str, Any]:
        """Load prompt template from YAML file."""
        if prompt_name in self._cache:
            return self._cache[prompt_name]
        
        template_path = self.templates_dir / f"{prompt_name}.yml"
        if not template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {template_path}")
        
        with open(template_path, 'r') as f:
            prompt_data = yaml.safe_load(f)
        
        self._cache[prompt_name] = prompt_data
        return prompt_data
    
    def get_template(self, prompt_name: str) -> str:
        """Get the template string for a prompt."""
        prompt_data = self.load_prompt(prompt_name)
        return prompt_data['template']
    
    def get_settings(self, prompt_name: str) -> Dict[str, Any]:
        """Get the settings for a prompt."""
        prompt_data = self.load_prompt(prompt_name)
        return prompt_data.get('settings', {})
    
    def list_prompts(self) -> list:
        """List all available prompt templates."""
        return [f.stem for f in self.templates_dir.glob("*.yml")]
