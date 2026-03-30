"""
Simple configuration for Cloud Music Video Creator
Direct API keys, simple settings
"""

import os
from pathlib import Path


class Settings:
    """Simple settings class"""
    
    def __init__(self):
        # Server
        self.host = "localhost"
        self.port = 8080
        self.mcp_server_port = 3001
        
        # Storage
        self.temp_storage_path = "/tmp/music-video-creator"
        
        # API Keys - read from environment
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY') 
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # LLM Models
        self.gemini_pro_model = "gemini-2.0-flash-exp"
        self.gemini_flash_model = "gemini-1.5-flash"
        self.claude_creative_model = "claude-3-5-sonnet-20241022"
        self.claude_processing_model = "claude-3-5-haiku-20241022"
        self.openai_creative_model = "gpt-4o"
        self.openai_processing_model = "gpt-4o-mini"
        
        # Which LLM to use (change these to switch providers)
        self.user_llm_provider = "gemini"      # "gemini", "claude", "openai"
        self.processing_llm_provider = "gemini" # "gemini", "claude", "openai"
    
    def setup_directories(self):
        """Create temp directories"""
        base = Path(self.temp_storage_path)
        for subdir in ["temp", "generated-videos", "source", "processing"]:
            (base / subdir).mkdir(parents=True, exist_ok=True)
    
    def get_user_llm_config(self):
        """Get user-facing LLM config"""
        if self.user_llm_provider == "gemini":
            return {"api_key": self.gemini_api_key, "model": self.gemini_pro_model}
        elif self.user_llm_provider == "claude":
            return {"api_key": self.anthropic_api_key, "model": self.claude_creative_model}
        elif self.user_llm_provider == "openai":
            return {"api_key": self.openai_api_key, "model": self.openai_creative_model}
    
    def get_processing_llm_config(self):
        """Get processing LLM config"""
        if self.processing_llm_provider == "gemini":
            return {"api_key": self.gemini_api_key, "model": self.gemini_flash_model}
        elif self.processing_llm_provider == "claude":
            return {"api_key": self.anthropic_api_key, "model": self.claude_processing_model}
        elif self.processing_llm_provider == "openai":
            return {"api_key": self.openai_api_key, "model": self.openai_processing_model}


# Global settings
settings = Settings()