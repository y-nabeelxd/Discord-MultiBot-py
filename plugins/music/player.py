"""
plugins/music/player.py
YTDLSource, shared player state, and music helpers.

KEY FIX: extract_flat was True in the original code which caused yt-dlp to
return YouTube watch URLs instead of actual audio stream URLs.
We now use ytsearch: for search (no HTML scraping), remove extract_flat,
and stream directly using bestaudio.
"""
import asyncio
import yt_dlp
import discord
from utils import format_duration

# ── yt-dlp options ────────────────────────────────────────────────────────────
# IMPORTANT: Do NOT set extract_flat=True — that prevents stream URL extraction
YTDL_FORMAT_OPTIONS = {
    "format": "bestaudio[ext=webm]/bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",   # use yt-dlp's own search — no scraping needed
    "source_address": "0.0.0.0",
    "verbose": False,
    # Removed extract_flat — it was the root cause of play failures
}

FFMPEG_OPTIONS = {
    "before_options": (
        "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 "
        "-loglevel error"
    ),
    "options": "-vn",
}

ytdl = yt_dlp.YoutubeDL(YTDL_FORMAT_OPTIONS)

# ── Shared state (per-guild) ──────────────────────────────────────────────────
# These dicts are imported by the music cog.
current_players: dict = {}   # guild_id -> {voice_client, player, ctx, ...}
song_queues: dict = {}        # guild_id -> [{'url': ..., 'title': ...}, ...]
idle_timers: dict = {}        # guild_id -> asyncio.Task
PERMA_VC: dict = {}           # guild_id -> True


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)
        self.data = data
        self.title: str = data.get("title", "Unknown")
        self.url: str = data.get("webpage_url", data.get("url", ""))
        self.duration: str = format_duration(data.get("duration"))
        self.thumbnail: str | None = data.get("thumbnail")

    @classmethod
    async def from_url(cls, url: str, *, loop: asyncio.AbstractEventLoop = None, stream: bool = True):
        loop = loop or asyncio.get_event_loop()
        # Run blocking yt-dlp call in executor to avoid blocking the event loop
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )
        if not data:
            raise ValueError("yt-dlp returned no data for that query.")
        # If it's a playlist/search result, take the first entry
        if "entries" in data:
            data = data["entries"][0]
        if not data:
            raise ValueError("No results found.")

        stream_url = data.get("url")
        if not stream_url:
            raise ValueError("Could not extract a stream URL. Try a different song.")

        return cls(discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS), data=data)


async def search_youtube(query: str, max_results: int = 10) -> list[dict]:
    """
    Search YouTube via yt-dlp's ytsearch without downloading.
    Returns list of {title, url, duration, thumbnail}.
    """
    loop = asyncio.get_event_loop()
    search_opts = {
        **YTDL_FORMAT_OPTIONS,
        "extract_flat": True,       # Only for search listing — we re-extract on play
        "quiet": True,
        "no_warnings": True,
        "noplaylist": False,
    }
    ydl = yt_dlp.YoutubeDL(search_opts)
    try:
        data = await loop.run_in_executor(
            None, lambda: ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
        )
    except Exception as e:
        print(f"[Music] Search error: {e}")
        return []

    if not data or "entries" not in data:
        return []

    results = []
    for entry in data["entries"]:
        if not entry:
            continue
        video_id = entry.get("id")
        title = entry.get("title", "Unknown")
        duration_sec = entry.get("duration")
        duration_str = format_duration(duration_sec) if duration_sec else "N/A"
        results.append({
            "title": title,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "duration": duration_str,
            "thumbnail": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
        })
    return results
