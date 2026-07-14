"""
Configuration module — loads environment variables and defines constants.
"""

import os
import logging
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


# Available models that users can switch between
AVAILABLE_MODELS = {
    "gemini-2.5-pro": "Gemini 2.5 Pro — Best reasoning, slower",
    "gemini-2.5-flash": "Gemini 2.5 Flash — Fast and capable",
    "gemini-2.5-flash-lite": "Gemini 2.5 Flash Lite — Fastest, lightweight",
    "claude-sonnet-4": "Claude Sonnet 4 — Balanced performance",
    "claude-opus-4": "Claude Opus 4 — Most capable Claude",
}

# Telegram message limits
TELEGRAM_MAX_MESSAGE_LENGTH = 4096
TELEGRAM_MAX_CAPTION_LENGTH = 1024


@dataclass
class Settings:
    """Bot configuration loaded from environment variables."""

    # Telegram
    telegram_bot_token: str = ""
    allowed_user_ids: list[int] = field(default_factory=list)

    # AGY
    default_model: str = ""

    # Behavior
    log_level: str = "INFO"
    max_context_messages: int = 50
    session_timeout_minutes: int = 60
    enable_streaming: bool = True

    # Database
    db_path: str = "data/agy_bot.db"

    def __post_init__(self):
        """Load and validate settings from environment."""
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.default_model = os.getenv("DEFAULT_MODEL", "")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.max_context_messages = int(os.getenv("MAX_CONTEXT_MESSAGES", "50"))
        self.session_timeout_minutes = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))
        self.enable_streaming = os.getenv("ENABLE_STREAMING", "true").lower() == "true"

        # Parse allowed user IDs
        raw_ids = os.getenv("ALLOWED_USER_IDS", "")
        if raw_ids:
            self.allowed_user_ids = [
                int(uid.strip()) for uid in raw_ids.split(",") if uid.strip()
            ]

        self._validate()

    def _validate(self):
        """Validate required configuration."""
        if not self.telegram_bot_token or self.telegram_bot_token == "your_bot_token_here":
            raise ValueError(
                "❌ TELEGRAM_BOT_TOKEN is not set! "
                "Get one from @BotFather on Telegram and add it to .env"
            )

        if not self.allowed_user_ids:
            logger.warning(
                "⚠️  ALLOWED_USER_IDS is empty — bot will reject ALL messages! "
                "Add your Telegram User ID to .env"
            )

    @property
    def log_level_int(self) -> int:
        """Convert log level string to logging constant."""
        return getattr(logging, self.log_level.upper(), logging.INFO)


def load_settings() -> Settings:
    """Create and return a Settings instance."""
    return Settings()
