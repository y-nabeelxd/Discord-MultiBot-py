"""
utils.py — Shared helper functions used across all plugins.
"""
import os
import json
import datetime
import asyncio
import aiohttp
from datetime import timedelta


# ── Console helpers ───────────────────────────────────────────────────────────

def clear_console() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def beautiful_print(message: str, box_char: str = "═", padding: int = 1) -> None:
    try:
        terminal_width = os.get_terminal_size().columns
    except OSError:
        terminal_width = 80
    box_line = box_char * terminal_width
    padding_lines = "\n" * padding
    message_lines = message.split("\n")
    centered = [line.center(terminal_width) if line.strip() else "" for line in message_lines]
    output = f"{padding_lines}{box_line}\n" + "\n".join(centered) + f"\n{box_line}{padding_lines}"
    try:
        print(output)
    except UnicodeEncodeError:
        # Windows cp1252 fallback — encode emoji as replacement chars
        import sys
        safe = output.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8", errors="replace")
        print(safe)


# ── Duration formatters ───────────────────────────────────────────────────────

def format_duration(seconds) -> str:
    if isinstance(seconds, str):
        return seconds
    try:
        return str(timedelta(seconds=int(seconds)))
    except Exception:
        return "N/A"


def format_uptime(seconds) -> str:
    """Convert seconds to human-readable format (days, hours, minutes)."""
    if seconds is None:
        return "N/A"
    try:
        seconds = int(seconds)
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or not parts:
            parts.append(f"{minutes}m")
        return " ".join(parts)
    except Exception:
        return "N/A"


# ── DB helpers ────────────────────────────────────────────────────────────────

DB_DIR = "db"

def _ensure_db() -> None:
    os.makedirs(DB_DIR, exist_ok=True)


def _read_json(filename: str) -> dict:
    _ensure_db()
    path = os.path.join(DB_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _write_json(filename: str, data: dict) -> None:
    _ensure_db()
    path = os.path.join(DB_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def get_warnings_data() -> dict:
    return _read_json("warnings.json")


def save_warnings_data(data: dict) -> None:
    _write_json("warnings.json", data)


def get_owo_data() -> dict:
    return _read_json("owo_data.json")


def save_owo_data(data: dict) -> None:
    _write_json("owo_data.json", data)


def get_fivem_verification_data() -> dict:
    return _read_json("fivem.json")


def save_fivem_verification_data(data: dict) -> None:
    _write_json("fivem.json", data)


def get_leveling_data() -> dict:
    return _read_json("leveling.json")


def save_leveling_data(data: dict) -> None:
    _write_json("leveling.json", data)


def get_giveaway_data() -> dict:
    return _read_json("giveaway.json")


def save_giveaway_data(data: dict) -> None:
    _write_json("giveaway.json", data)


def get_afk_data() -> dict:
    return _read_json("afk.json")


def save_afk_data(data: dict) -> None:
    _write_json("afk.json", data)


# ── External API helpers ──────────────────────────────────────────────────────

async def get_roblox_profile(username: str) -> dict | None:
    """Fetch a Roblox user profile by username."""
    try:
        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                "https://users.roblox.com/v1/usernames/users",
                json={"usernames": [username]},
            )
            data = await resp.json()
            if not data.get("data"):
                return None
            user_id = data["data"][0]["id"]

            profile_resp = await session.get(f"https://users.roblox.com/v1/users/{user_id}")
            profile = await profile_resp.json()

            avatar_resp = await session.get(
                f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png"
            )
            avatar_data = await avatar_resp.json()
            avatar = avatar_data["data"][0]["imageUrl"]

            friends_resp = await session.get(
                f"https://friends.roblox.com/v1/users/{user_id}/friends/count"
            )
            friends_data = await friends_resp.json()
            friends_count = friends_data.get("count", 0)

            created = profile.get("created")
            if created:
                created = datetime.datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.%fZ").strftime(
                    "%B %d, %Y"
                )

            return {
                "id": user_id,
                "username": profile.get("name"),
                "displayName": profile.get("displayName"),
                "description": profile.get("description", ""),
                "created": created,
                "avatar": avatar,
                "friends": friends_count,
            }
    except Exception as e:
        print(f"Error getting Roblox profile: {e}")
        return None


async def get_fivem_players(server_address: str) -> list:
    """Fetch players list from a FiveM server."""
    if not server_address:
        return []
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Accept": "application/json"}
            players_resp, info_resp, dynamic_resp = await asyncio.gather(
                session.get(f"http://{server_address}/players.json", headers=headers),
                session.get(f"http://{server_address}/info.json", headers=headers),
                session.get(f"http://{server_address}/dynamic.json", headers=headers),
            )
            players = await players_resp.json(content_type=None) if players_resp.status == 200 else []
            info = await info_resp.json(content_type=None) if info_resp.status == 200 else {}
            dynamic = await dynamic_resp.json(content_type=None) if dynamic_resp.status == 200 else {}
            for p in players:
                p["server_info"] = info
                p["server_dynamic"] = dynamic
            return players
    except Exception as e:
        print(f"Error getting FiveM players: {e}")
        return []


async def get_fivem_player_by_identifier(identifier: str, server_address: str) -> dict | None:
    players = await get_fivem_players(server_address)
    if not players:
        return None
    for p in players:
        if str(p.get("id")) == str(identifier):
            return p
    for p in players:
        if p.get("name", "").lower() == str(identifier).lower():
            return p
    return None


async def get_fivem_server_info(server_address: str) -> dict | None:
    """Get detailed FiveM server info."""
    if not server_address:
        return None
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Accept": "application/json"}
            info_r, dyn_r, play_r = await asyncio.gather(
                session.get(f"http://{server_address}/info.json", headers=headers),
                session.get(f"http://{server_address}/dynamic.json", headers=headers),
                session.get(f"http://{server_address}/players.json", headers=headers),
            )
            info_data = await info_r.json(content_type=None) if info_r.status == 200 else {}
            dynamic_data = await dyn_r.json(content_type=None) if dyn_r.status == 200 else {}
            players_data = await play_r.json(content_type=None) if play_r.status == 200 else []
            uptime = format_uptime(info_data.get("vars", {}).get("Uptime"))
            return {
                "info": info_data,
                "dynamic": dynamic_data,
                "players": players_data,
                "status": "online" if info_r.status == 200 else "offline",
                "uptime": uptime,
            }
    except Exception as e:
        print(f"Error getting FiveM server info: {e}")
        return None


async def get_valorant_account(username: str, tag: str, riot_api_key: str, regions: list) -> dict | None:
    async with aiohttp.ClientSession() as session:
        for region in regions:
            url = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{username}/{tag}"
            headers = {"X-Riot-Token": riot_api_key}
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
    return None
