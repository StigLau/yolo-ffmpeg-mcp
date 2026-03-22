#!/usr/bin/env python3
"""
Haiku Configuration Management
Handles API keys, budget controls, and operational settings
"""
import os
import json
import time
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class BudgetConfig:
    daily_limit: float = 5.00
    weekly_limit: float = 30.00
    monthly_limit: float = 100.00
    cost_alert_threshold: float = 0.80  # Alert at 80% of limit
    auto_disable_on_limit: bool = True

@dataclass
class QualityConfig:
    confidence_threshold: float = 0.8
    escalate_to_sonnet: bool = True
    learning_enabled: bool = True
    pattern_storage_path: str = "~/.haiku/patterns"

@dataclass
class ApiConfig:
    model: str = "claude-3-haiku-20240307"
    max_tokens: int = 4096
    temperature: float = 0.1
    timeout: int = 30
    max_retries: int = 3
    rate_limit_calls_per_second: float = 0.8

@dataclass
class HaikuConfig:
    api: ApiConfig
    budget: BudgetConfig  
    quality: QualityConfig
    config_path: str = "~/.haiku/config.json"
    usage_tracking_path: str = "~/.haiku/usage.json"

class ConfigManager:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path or "~/.haiku/config.json").expanduser()
        self.usage_path = Path("~/.haiku/usage.json").expanduser()
        self.config = self.load_config()
    
    def load_config(self) -> HaikuConfig:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    return HaikuConfig(
                        api=ApiConfig(**data.get("api", {})),
                        budget=BudgetConfig(**data.get("budget", {})),
                        quality=QualityConfig(**data.get("quality", {}))
                    )
            except Exception as e:
                logger.warning(f"Failed to load config from {self.config_path}: {e}")
        
        # Create default config
        return HaikuConfig(
            api=ApiConfig(),
            budget=BudgetConfig(),
            quality=QualityConfig()
        )
    
    def save_config(self):
        """Save current configuration to file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = {
            "api": asdict(self.config.api),
            "budget": asdict(self.config.budget),
            "quality": asdict(self.config.quality)
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        logger.info(f"Configuration saved to {self.config_path}")
    
    def get_api_key(self) -> str:
        """Get API key from environment or config file"""
        # Try environment variable first
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            return api_key
        
        # Try config file
        api_key_file = Path("~/.anthropic/api_key").expanduser()
        if api_key_file.exists():
            return api_key_file.read_text().strip()
        
        raise ValueError(
            "No Anthropic API key found. Set ANTHROPIC_API_KEY environment variable "
            "or create ~/.anthropic/api_key file"
        )
    
    def check_budget_available(self, operation_cost: float) -> tuple[bool, str]:
        """Check if operation is within budget limits"""
        usage = self.get_current_usage()
        
        # Check daily limit
        if usage["daily"] + operation_cost > self.config.budget.daily_limit:
            return False, f"Would exceed daily budget limit: ${self.config.budget.daily_limit}"
        
        # Check if approaching limit
        daily_usage_percent = (usage["daily"] + operation_cost) / self.config.budget.daily_limit
        if daily_usage_percent > self.config.budget.cost_alert_threshold:
            return True, f"Warning: {daily_usage_percent:.1%} of daily budget will be used"
        
        return True, "Budget OK"
    
    def record_usage(self, cost: float, operation_type: str):
        """Record API usage for budget tracking"""
        usage = self.get_current_usage()
        
        # Update usage
        usage["daily"] += cost
        usage["weekly"] += cost  
        usage["monthly"] += cost
        usage["operations"].append({
            "timestamp": time.time(),
            "type": operation_type,
            "cost": cost
        })
        
        # Save usage
        self.usage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.usage_path, 'w') as f:
            json.dump(usage, f, indent=2)
    
    def get_current_usage(self) -> Dict:
        """Get current usage statistics"""
        if not self.usage_path.exists():
            return {
                "daily": 0.0,
                "weekly": 0.0, 
                "monthly": 0.0,
                "operations": []
            }
        
        try:
            with open(self.usage_path, 'r') as f:
                usage = json.load(f)
            
            # TODO: Reset counters based on time periods
            # For now, just return raw usage
            return usage
            
        except Exception as e:
            logger.error(f"Failed to load usage data: {e}")
            return {"daily": 0.0, "weekly": 0.0, "monthly": 0.0, "operations": []}

# Global config manager instance
_config_manager = None

def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_api_key() -> str:
    """Convenience function to get API key"""
    return get_config_manager().get_api_key()

def check_budget(cost: float) -> tuple[bool, str]:
    """Convenience function to check budget"""
    return get_config_manager().check_budget_available(cost)

def record_operation(cost: float, operation_type: str):
    """Convenience function to record operation"""
    get_config_manager().record_usage(cost, operation_type)