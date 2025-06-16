"""Integration layer for external prompt templates."""
from typing import Dict, Any, Optional
from libriscribe.utils.prompt_loader import PromptLoader

class ExternalPromptMixin:
    """Mixin to add external prompt support to agents."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prompt_loader = PromptLoader()
        self.use_external_prompts = True  # Can be configured
    
    def get_prompt_template(self, prompt_name: str, fallback_prompt: str = "") -> str:
        """Get prompt template from external file or fallback to hardcoded."""
        if not self.use_external_prompts:
            return fallback_prompt
        
        try:
            return self.prompt_loader.get_template(prompt_name)
        except FileNotFoundError:
            print(f"⚠️  External prompt '{prompt_name}' not found, using fallback")
            return fallback_prompt
    
    def get_prompt_settings(self, prompt_name: str) -> Dict[str, Any]:
        """Get prompt settings (max_tokens, temperature, etc.)."""
        if not self.use_external_prompts:
            return {}
        
        try:
            return self.prompt_loader.get_settings(prompt_name)
        except FileNotFoundError:
            return {}
    
    def generate_with_external_prompt(self, prompt_name: str, 
                                    fallback_prompt: str,
                                    prompt_data: Dict[str, Any],
                                    default_max_tokens: int = 2000) -> str:
        """Generate content using external prompt with fallback."""
        template = self.get_prompt_template(prompt_name, fallback_prompt)
        settings = self.get_prompt_settings(prompt_name)
        
        # Format the template
        formatted_prompt = template.format(**prompt_data)
        
        # Use external settings or defaults
        max_tokens = settings.get('max_tokens', default_max_tokens)
        temperature = settings.get('temperature', 0.7)
        
        return self.llm_client.generate_content(
            formatted_prompt, 
            max_tokens=max_tokens, 
            temperature=temperature,
            operation=f"{prompt_name}_generation"
        )
