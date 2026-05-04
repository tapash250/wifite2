from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Tool-specific settings
    tool_interface: str = "wlan0mon"  # Monitor mode interface
    tool_timeout: int = 300
    tool_dict_path: str = "/usr/share/dict/rockyou.txt"  # Default dictionary for WPA cracking

    # WebSocket settings
    ws_heartbeat_interval: int = 30

    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None

    # Database
    database_url: str = "sqlite:///./tool.db"

    # PowerSync
    powersync_enabled: bool = True
    powersync_url: Optional[str] = None  # Set via environment variable in production
    powersync_interval: int = 5  # seconds

    # Security
    allowed_origins: List[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = False


config = Settings()