"""
plugins/music/music_cog.py
All music commands as a discord.py Cog.
"""
import asyncio
import time
import discord
from discord.ext import commands
from config import PREFIX
from plugins.music.player import (
    YTDLSource,
    search_youtube,
    current_players,
    song_queues,
    idle_timers,
    PERMA_VC,
)


# ── UI Components ─────────────────────────────────────────────────────────────

class SongSelect(discord.ui.Select):
    def __init__(self, results: list[dict], ctx: commands.Context):
        self.results = results
        self.ctx = ctx
        options = [
            discord.SelectOption(
                label=f"{i+1}. {v['title'][:90]}",
                description=v.get("duration", "N/A"),
                value=str(i),
            )
            for i, v in enumerate(results[:10])
        ]
        super().__init__(
            placeholder="Select a song to play…",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message(
                "You didn't request this selection!", ephemeral=True
            )
        selected = int(self.values[0])
        video = self.results[selected]
        await interaction.response.defer()
        try:
            await interaction.message.delete()
        except Exception:
            pass

        vc = self.ctx.voice_client
        guild_id = self.ctx.guild.id
        song_queues.setdefault(guild_id, [])

        if vc.is_playing() or vc.is_paused():
            song_queues[guild_id].append({"url": video["url"], "title": video["title"]})
            await self.ctx.send(f"➕ Added to queue: **{video['title']}**")
        else:
            await _play_song(self.ctx, video["url"], video["title"])


class SongSelectView(discord.ui.View):
    def __init__(self, results: list[dict], ctx: commands.Context, timeout: int = 60):
        super().__init__(timeout=timeout)
        self.message: discord.Message | None = None
        self.add_item(SongSelect(results, ctx))

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except Exception:
                pass


class ControlButtons(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__(timeout=None)
        self.ctx = ctx

    @discord.ui.button(label="⏸ Pause", style=discord.ButtonStyle.primary)
    async def pause_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸ Paused", ephemeral=True)
        else:
            await interaction.response.send_message("Nothing is playing!", ephemeral=True)

    @discord.ui.button(label="▶ Resume", style=discord.ButtonStyle.primary)
    async def resume_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶ Resumed", ephemeral=True)
        else:
            await interaction.response.send_message("Not paused!", ephemeral=True)

    @discord.ui.button(label="⏭ Skip", style=discord.ButtonStyle.secondary)
    async def skip_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
            await interaction.response.send_message("⏭ Skipped", ephemeral=True)
        else:
            await interaction.response.send_message("Nothing is playing!", ephemeral=True)

    @discord.ui.button(label="🛑 Stop", style=discord.ButtonStyle.danger)
    async def stop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        guild_id = interaction.guild.id
        if vc:
            song_queues.get(guild_id, []).clear()
            ctrl = current_players.pop(guild_id, {}).get("control_message")
            if ctrl:
                try:
                    await ctrl.delete()
                except Exception:
                    pass
            await vc.disconnect()
            await interaction.response.send_message("⏹ Stopped and cleared queue", ephemeral=True)
        else:
            await interaction.response.send_message("I'm not in a voice channel!", ephemeral=True)


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _start_idle_timer(guild_id: int, bot_loop: asyncio.AbstractEventLoop):
    if guild_id in idle_timers:
        idle_timers[guild_id].cancel()

    async def idle_task():
        try:
            start = time.time()
            while time.time() - start < 30:
                p = current_players.get(guild_id)
                if p and p["voice_client"].is_playing():
                    return
                await asyncio.sleep(1)
            p = current_players.get(guild_id)
            if p and not p["voice_client"].is_playing():
                await p["voice_client"].disconnect()
                ctrl = current_players.pop(guild_id, {}).get("control_message")
                if ctrl:
                    try:
                        await ctrl.delete()
                    except Exception:
                        pass
                song_queues.get(guild_id, []).clear()
        except Exception as e:
            print(f"[Music] Idle timer error: {e}")

    idle_timers[guild_id] = asyncio.ensure_future(idle_task())


async def _play_next(ctx: commands.Context):
    guild_id = ctx.guild.id
    queue = song_queues.get(guild_id, [])
    if queue:
        next_song = queue.pop(0)
        await _play_song(ctx, next_song["url"], next_song["title"])
    else:
        await _start_idle_timer(guild_id, ctx.bot.loop)


async def _play_song(ctx: commands.Context, url: str, title: str):
    vc = ctx.voice_client
    guild_id = ctx.guild.id

    # Cancel idle timer
    if guild_id in idle_timers:
        idle_timers[guild_id].cancel()

    loading_msg = await ctx.send(f"⏳ Loading **{title}**…")
    try:
        source = await YTDLSource.from_url(url, loop=ctx.bot.loop, stream=True)
    except Exception as e:
        await loading_msg.edit(content=f"❌ Error loading song: {e}")
        await _play_next(ctx)
        return

    try:
        await loading_msg.delete()
    except Exception:
        pass

    current_players[guild_id] = {
        "voice_client": vc,
        "player": source,
        "ctx": ctx,
        "last_activity": time.time(),
    }

    embed = discord.Embed(
        title="🎵 Now Playing",
        description=f"[{source.title}]({source.url})",
        color=discord.Color.green(),
    )
    if source.thumbnail:
        embed.set_thumbnail(url=source.thumbnail)
    if source.duration:
        embed.add_field(name="Duration", value=source.duration, inline=True)

    view = ControlButtons(ctx)
    ctrl_msg = await ctx.send(embed=embed, view=view)
    current_players[guild_id]["control_message"] = ctrl_msg

    def after_playing(error):
        if error:
            print(f"[Music] Player error: {error}")
        asyncio.run_coroutine_threadsafe(_play_next(ctx), ctx.bot.loop)

    try:
        vc.play(source, after=after_playing)
    except discord.ClientException:
        # Already playing audio
        print(f"[Music] ClientException: Already playing audio in {guild_id}")


# ── Cog ───────────────────────────────────────────────────────────────────────

class MusicCog(commands.Cog, name="Music"):
    """🎵 Music playback commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _ensure_voice(self, ctx: commands.Context) -> discord.VoiceClient | None:
        """Join / move to the author's voice channel. Returns voice client or None."""
        if not ctx.author.voice:
            await ctx.send("❌ You need to be in a voice channel to play music!")
            return None
        vc = ctx.voice_client
        if vc and vc.is_connected():
            if vc.channel != ctx.author.voice.channel:
                await vc.move_to(ctx.author.voice.channel)
        else:
            try:
                vc = await ctx.author.voice.channel.connect(timeout=60.0, reconnect=True)
            except discord.errors.ConnectionClosed:
                await asyncio.sleep(2)
                vc = await ctx.author.voice.channel.connect(timeout=60.0, reconnect=True)
        return vc

    # ── Commands ──────────────────────────────────────────────────────────────

    @commands.hybrid_command(aliases=["p"])
    async def play(self, ctx: commands.Context, *, query: str):
        """Play a song or add to queue. Usage: !play <song name or URL>"""
        await ctx.defer()
        vc = await self._ensure_voice(ctx)
        if not vc:
            return

        guild_id = ctx.guild.id
        if guild_id in idle_timers:
            idle_timers[guild_id].cancel()

        # If it's a direct URL, play it immediately
        if query.startswith("http://") or query.startswith("https://"):
            song_queues.setdefault(guild_id, [])
            if vc.is_playing() or vc.is_paused():
                song_queues[guild_id].append({"url": query, "title": query})
                await ctx.send(f"➕ Added to queue: **{query}**")
            else:
                await _play_song(ctx, query, query)
            return

        # Search YouTube
        searching_msg = await ctx.send(f"🔍 Searching for **{query}**…")
        results = await search_youtube(query)
        try:
            await searching_msg.delete()
        except Exception:
            pass

        if not results:
            await ctx.send("❌ No results found for that query.")
            return

        embed = discord.Embed(
            title="🔍 Search Results",
            description=f"Results for: **{query}**",
            color=0x00FF7F,
        )
        for i, video in enumerate(results[:10], 1):
            embed.add_field(
                name=f"{i}. {video['title'][:80]}",
                value=f"⏱ {video.get('duration', 'N/A')}",
                inline=False,
            )

        view = SongSelectView(results, ctx)
        view.message = await ctx.send(embed=embed, view=view)

    @commands.hybrid_command()
    async def skip(self, ctx: commands.Context):
        """Skip the current song. Usage: !skip"""
        vc = ctx.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
            await ctx.send("⏭ Song skipped")
        else:
            await ctx.send("❌ Nothing is playing to skip!")

    @commands.hybrid_command()
    async def queue(self, ctx: commands.Context):
        """Show the current song queue. Usage: !queue"""
        guild_id = ctx.guild.id
        q = song_queues.get(guild_id, [])
        if q:
            lines = [f"{i+1}. {s['title']}" for i, s in enumerate(q)]
            embed = discord.Embed(
                title="🎶 Song Queue",
                description="\n".join(lines),
                color=discord.Color.blue(),
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("📭 The queue is empty.")

    @commands.hybrid_command()
    async def clearqueue(self, ctx: commands.Context):
        """Clear the song queue. Usage: !clearqueue"""
        song_queues[ctx.guild.id] = []
        await ctx.send("🗑 Queue cleared!")

    @commands.hybrid_command()
    async def pause(self, ctx: commands.Context):
        """Pause playback. Usage: !pause"""
        vc = ctx.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await ctx.send("⏸ Playback paused")
        else:
            await ctx.send("❌ Nothing is playing!")

    @commands.hybrid_command()
    async def resume(self, ctx: commands.Context):
        """Resume playback. Usage: !resume"""
        vc = ctx.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await ctx.send("▶ Playback resumed")
        else:
            await ctx.send("❌ Playback is not paused!")

    @commands.hybrid_command()
    async def stop(self, ctx: commands.Context):
        """Stop playback and clear queue. Usage: !stop"""
        vc = ctx.voice_client
        guild_id = ctx.guild.id
        if vc:
            song_queues[guild_id] = []
            ctrl = current_players.pop(guild_id, {}).get("control_message")
            if ctrl:
                try:
                    await ctrl.delete()
                except Exception:
                    pass
            await vc.disconnect()
            await ctx.send("⏹ Playback stopped and queue cleared")
        else:
            await ctx.send("❌ I'm not in a voice channel!")

    @commands.hybrid_command()
    async def leave(self, ctx: commands.Context):
        """Make the bot leave the voice channel. Usage: !leave"""
        vc = ctx.voice_client
        guild_id = ctx.guild.id
        if vc:
            PERMA_VC.pop(guild_id, None)
            song_queues[guild_id] = []
            ctrl = current_players.pop(guild_id, {}).get("control_message")
            if ctrl:
                try:
                    await ctrl.delete()
                except Exception:
                    pass
            await vc.disconnect()
            await ctx.send("👋 Left the voice channel")
        else:
            await ctx.send("❌ I'm not in a voice channel!")

    # ── Events ────────────────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if member == self.bot.user:
            # Check if bot was forcibly disconnected
            if before.channel and not after.channel:
                guild_id = member.guild.id
                song_queues.get(guild_id, []).clear()
                ctrl = current_players.pop(guild_id, {}).get("control_message")
                if ctrl:
                    try:
                        await ctrl.delete()
                    except Exception:
                        pass
            return
            
        # Snapshot guild IDs to avoid dict-changed-during-iteration error
        for guild_id in list(current_players.keys()):
            data = current_players.get(guild_id)
            if not data:
                continue
            vc = data.get("voice_client")
            if not vc or not vc.is_connected():
                continue
            if guild_id in PERMA_VC:
                continue
            if len(vc.channel.members) == 1:
                await vc.disconnect()
                ctrl = current_players.pop(guild_id, {}).get("control_message")
                if ctrl:
                    try:
                        await ctrl.delete()
                    except Exception:
                        pass
                song_queues.get(guild_id, []).clear()



    @commands.hybrid_command()
    async def lyrics(self, ctx: commands.Context, *, query: str = None):
        """Get lyrics for a song. If no query provided, gets lyrics for current song."""
        await ctx.defer()
        if not query:
            if ctx.guild.id in current_players:
                player = current_players[ctx.guild.id].get("player")
                if player and player.title:
                    query = player.title
            
            if not query:
                return await ctx.send("❌ Please provide a song name or play a song first.")
                
        msg = await ctx.send(f"🔍 Searching lyrics for {query}...")
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://some-random-api.com/lyrics?title={query}") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        lyrics = data.get("lyrics", "")
                        title = data.get("title", query)
                        author = data.get("author", "Unknown")
                        
                        if len(lyrics) > 4000:
                            lyrics = lyrics[:3997] + "..."
                            
                        embed = discord.Embed(title=f"{title} - {author}", description=lyrics, color=discord.Color.blurple())
                        
                        try:
                            thumbnail = data.get("thumbnail", {}).get("genius")
                            if thumbnail:
                                embed.set_thumbnail(url=thumbnail)
                        except Exception:
                            pass
                            
                        await msg.edit(content=None, embed=embed)
                    else:
                        await msg.edit(content=f"❌ Couldn't find lyrics for {query}.")
        except Exception as e:
            await msg.edit(content=f"❌ Error fetching lyrics: {e}")

async def setup(bot: commands.Bot):

    await bot.add_cog(MusicCog(bot))
