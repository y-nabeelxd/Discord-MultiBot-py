"""
config.py — Centralised configuration loaded from .env
All bot settings live here. Import from this module everywhere.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Bot Core ─────────────────────────────────────────────────────────────────
DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
PREFIX: str = os.getenv("PREFIX", "!")
GAME_PREFIX: str = os.getenv("GAME_PREFIX", "owo")
BOT_OWNER: int | None = int(os.getenv("BOT_OWNER_ID")) if os.getenv("BOT_OWNER_ID") else None

# ── Misc ──────────────────────────────────────────────────────────────────────
WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")
YT_API_KEY: str = os.getenv("YT_API_KEY", "")
COINFLIP_GIF: str = os.getenv(
    "COINFLIP_GIF",
    "https://cdn.dribbble.com/userupload/20764551/file/original-ec7c7b25323fea450739f13b38db735f.gif",
)
CHANGE_NICKNAME: bool = os.getenv("CHANGE_NICKNAME", "false").lower() == "true"
EXTRA_ROLES_LOCK_UNLOCK: int | None = (
    int(os.getenv("EXTRA_ROLES_LOCK_UNLOCK")) if os.getenv("EXTRA_ROLES_LOCK_UNLOCK") else None
)

# ── FiveM Verification ────────────────────────────────────────────────────────
VERIFICATION_FIVEM: bool = os.getenv("VERIFICATION_FIVEM", "false").lower() == "true"
FIVEM_SERVER: str | None = os.getenv("FIVEM_SERVER")
FIVEM_ROLE_ID: int | None = int(os.getenv("FIVEM_ROLE_ID")) if os.getenv("FIVEM_ROLE_ID") else None
FIVEM_VERIFICATION_DISCORD_REQUIRED: bool = (
    os.getenv("FIVEM_VERIFICATION_DISCORD_REQUIRED", "false").lower() == "true"
)

# ── Roblox Verification ───────────────────────────────────────────────────────
VERIFICATION_ROBLOX: bool = os.getenv("VERIFICATION_ROBLOX", "false").lower() == "true"
ROBLOX_ROLE_ID: int | None = int(os.getenv("ROBLOX_ROLE_ID")) if os.getenv("ROBLOX_ROLE_ID") else None

# ── SA:MP Verification ────────────────────────────────────────────────────────
VERIFICATION_SAMP: bool = os.getenv("VERIFICATION_SAMP", "false").lower() == "true"
SAMP_SERVER_IP: str | None = os.getenv("SAMP_SERVER_IP")
SAMP_SERVER_PORT: int | None = int(os.getenv("SAMP_SERVER_PORT")) if os.getenv("SAMP_SERVER_PORT") else None
SAMP_ROLE_ID: int | None = int(os.getenv("SAMP_ROLE_ID")) if os.getenv("SAMP_ROLE_ID") else None

SAMP_VERIF_TYPE: str = os.getenv("SAMP_VERIF_TYPE", "basic").lower()

# MySQL config
SAMP_DB_HOST: str = os.getenv("SAMP_DB_HOST", "localhost")
SAMP_DB_USER: str = os.getenv("SAMP_DB_USER", "root")
SAMP_DB_PASSWORD: str = os.getenv("SAMP_DB_PASSWORD", "")
SAMP_DB_NAME: str = os.getenv("SAMP_DB_NAME", "samp_server")
SAMP_DB_TABLE: str = os.getenv("SAMP_DB_TABLE", "players")
SAMP_DB_COL_USERNAME: str = os.getenv("SAMP_DB_COL_USERNAME", "name")
SAMP_DB_COL_VERIFY_CODE: str = os.getenv("SAMP_DB_COL_VERIFY_CODE", "verify_code")
SAMP_DB_COL_DISCORD_ID: str = os.getenv("SAMP_DB_COL_DISCORD_ID", "discord_id")

# RCON config
SAMP_RCON_PASSWORD: str = os.getenv("SAMP_RCON_PASSWORD", "")
SAMP_RCON_CMD_FORMAT: str = os.getenv("SAMP_RCON_CMD_FORMAT", "pm {player} Your verification code is {code}")

# ── Valorant Verification ─────────────────────────────────────────────────────
VERIFICATION_VALO: bool = os.getenv("VERIFICATION_VALO", "false").lower() == "true"
RIOT_API_KEY: str | None = os.getenv("RIOT_API_KEY")
VALORANT_ROLE_ID: int | None = int(os.getenv("VALORANT_ROLE_ID")) if os.getenv("VALORANT_ROLE_ID") else None
REGIONS: list[str] = ["americas", "europe", "asia"]
