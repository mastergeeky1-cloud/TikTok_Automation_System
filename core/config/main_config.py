#!/usr/bin/env python3
"""
TikTok Automation System - Main Configuration
Geeky Workflow Core v2.0
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class DomainConfig:
    """Domain configuration settings"""
    primary_domain: str = "[your-domain.com]"
    automation_subdomain: str = "automation"
    api_subdomain: str = "api"
    logs_subdomain: str = "logs"
    
    @property
    def automation_url(self) -> str:
        return f"https://{self.automation_subdomain}.{self.primary_domain}"
    
    @property
    def api_url(self) -> str:
        return f"https://{self.api_subdomain}.{self.primary_domain}"
    
    @property
    def logs_url(self) -> str:
        return f"https://{self.logs_subdomain}.{self.primary_domain}"

@dataclass
class APIConfig:
    """API configuration settings"""
    tiktok_base_url: str = "https://open.tiktokapis.com/v2"
    tiktok_app_id: Optional[str] = None
    tiktok_secret: Optional[str] = None
    rate_limit_per_minute: int = 30
    token_refresh_threshold: int = 3600  # 1 hour before expiry
    
@dataclass
class AIConfig:
    """AI services configuration"""
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    stable_diffusion_url: str = "http://localhost:7860"
    whisper_model: str = "base"
    tts_provider: str = "openai"
    
@dataclass
class ContentConfig:
    """Content generation settings"""
    output_dir: str = "./data/media"
    template_dir: str = "./data/templates"
    max_video_duration: int = 60
    video_quality: str = "high"
    auto_generate_captions: bool = True
    content_categories: list = None
    
    def __post_init__(self):
        if self.content_categories is None:
            self.content_categories = ["entertainment", "education", "lifestyle", "tech"]

@dataclass
class DatabaseConfig:
    """Database configuration"""
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "tiktok_automation"
    postgres_user: str = "gm_admin"
    postgres_password: Optional[str] = None
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

@dataclass
class LoggingConfig:
    """Logging configuration"""
    log_level: str = "INFO"
    log_dir: str = "./data/logs"
    max_log_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    enable_console: bool = True
    enable_file: bool = True
    enable_remote: bool = True

class SystemConfig:
    """Main system configuration manager"""
    
    def __init__(self, config_file: str = "./core/config/system_config.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize configuration sections
        self.domain = DomainConfig()
        self.api = APIConfig()
        self.ai = AIConfig()
        self.content = ContentConfig()
        self.database = DatabaseConfig()
        self.logging = LoggingConfig()
        
        # Load configuration from file if exists
        self.load_config()
        
        # Override with environment variables
        self.load_from_env()
    
    def load_from_env(self):
        """Load configuration from environment variables"""
        # Domain settings
        if os.getenv("GM_DOMAIN"):
            self.domain.primary_domain = os.getenv("GM_DOMAIN")
        
        # API settings
        self.api.tiktok_app_id = os.getenv("TIKTOK_CLIENT_KEY")
        self.api.tiktok_secret = os.getenv("TIKTOK_CLIENT_SECRET")
        
        # AI settings
        self.ai.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Database settings
        self.database.postgres_password = os.getenv("POSTGRES_PASSWORD")
        
        # Logging settings
        if os.getenv("LOG_LEVEL"):
            self.logging.log_level = os.getenv("LOG_LEVEL")
    
    def load_config(self):
        """Load configuration from JSON file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Update each configuration section
                if 'domain' in config_data:
                    self.domain = DomainConfig(**config_data['domain'])
                if 'api' in config_data:
                    self.api = APIConfig(**config_data['api'])
                if 'ai' in config_data:
                    self.ai = AIConfig(**config_data['ai'])
                if 'content' in config_data:
                    self.content = ContentConfig(**config_data['content'])
                if 'database' in config_data:
                    self.database = DatabaseConfig(**config_data['database'])
                if 'logging' in config_data:
                    self.logging = LoggingConfig(**config_data['logging'])
                    
            except Exception as e:
                logging.warning(f"Failed to load config file: {e}")
    
    def save_config(self):
        """Save configuration to JSON file"""
        try:
            config_data = {
                'domain': asdict(self.domain),
                'api': asdict(self.api),
                'ai': asdict(self.ai),
                'content': asdict(self.content),
                'database': asdict(self.database),
                'logging': asdict(self.logging)
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            logging.error(f"Failed to save config file: {e}")
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return {
            'domain': asdict(self.domain),
            'api': asdict(self.api),
            'ai': asdict(self.ai),
            'content': asdict(self.content),
            'database': asdict(self.database),
            'logging': asdict(self.logging)
        }
    
    def validate_config(self) -> bool:
        """Validate configuration completeness"""
        required_fields = [
            (self.api.tiktok_app_id, "TIKTOK_CLIENT_KEY"),
            (self.api.tiktok_secret, "TIKTOK_CLIENT_SECRET"),
            (self.ai.openai_api_key, "OPENAI_API_KEY"),
        ]
        
        missing = []
        for value, name in required_fields:
            if not value:
                missing.append(name)
        
        if missing:
            logging.error(f"Missing required configuration: {', '.join(missing)}")
            return False
        
        return True

# Global configuration instance
config = SystemConfig()

if __name__ == "__main__":
    # Test configuration
    print("TikTok Automation System Configuration")
    print("=" * 50)
    print(json.dumps(config.get_all_config(), indent=2))
    print(f"\nConfiguration valid: {config.validate_config()}")
