import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    token: str
    guild_id: int
    database_path: str
    default_report_channel_id: int | None

def _optional_int(value):
    return int(value) if value and value.strip() else None

token = os.getenv("DISCORD_TOKEN")
guild_id = os.getenv("GUILD_ID")

if not token:
    raise RuntimeError("DISCORD_TOKEN is missing from .env")
if not guild_id:
    raise RuntimeError("GUILD_ID is missing from .env")

settings = Settings(
    token=token,
    guild_id=int(guild_id),
    database_path=os.getenv("DATABASE_PATH", "./data/health.db"),
    default_report_channel_id=_optional_int(os.getenv("DEFAULT_REPORT_CHANNEL_ID")),
)
