"""
plugins/verification/verification_cog.py
Roblox, FiveM, SA-MP, and Valorant verification commands.
"""
import asyncio
import random
import time
import datetime
import discord
from discord.ext import commands
from samp_query import Client as SampClient

import config
from utils import (
    get_roblox_profile,
    get_fivem_players,
    get_fivem_player_by_identifier,
    get_fivem_server_info,
    get_valorant_account,
    get_fivem_verification_data,
    save_fivem_verification_data,
    format_uptime,
)


# ── FiveM Verification View ───────────────────────────────────────────────────

class FiveMVerificationView(discord.ui.View):
    def __init__(self, ctx: commands.Context, player_data: dict):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.player_data = player_data
        self.server_address = config.FIVEM_SERVER
        self.message: discord.Message | None = None
        self.verified = False

    async def on_timeout(self):
        if not self.verified and self.message:
            try:
                await self.message.delete()
            except Exception:
                pass

    @discord.ui.button(label="✅ Verify", style=discord.ButtonStyle.success)
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("You're not the one verifying!", ephemeral=True)

        role = None
        if config.FIVEM_ROLE_ID:
            role = self.ctx.guild.get_role(config.FIVEM_ROLE_ID)
        if not role:
            for r in self.ctx.guild.roles:
                if r.name.lower() not in ["@everyone", "bot"] and r < self.ctx.guild.me.top_role:
                    role = r
                    break

        if not role:
            return await interaction.response.send_message("❌ No valid role found!", ephemeral=True)

        try:
            await self.ctx.author.add_roles(role)
            if config.CHANGE_NICKNAME:
                try:
                    await self.ctx.author.edit(nick=self.player_data["name"])
                except discord.Forbidden:
                    pass

            data = get_fivem_verification_data()
            uid = str(self.ctx.author.id)
            data[uid] = {
                "player_id": self.player_data.get("id"),
                "player_name": self.player_data.get("name"),
                "verified_at": datetime.datetime.now().isoformat(),
                "identifiers": self.player_data.get("identifiers", []),
            }
            save_fivem_verification_data(data)
            self.verified = True

            embed = discord.Embed(
                title="✅ FiveM Verification Complete",
                description=f"Connected to `{self.player_data['name']}`",
                color=discord.Color.green(),
            )
            embed.add_field(name="Player ID", value=self.player_data.get("id", "N/A"), inline=True)
            embed.add_field(name="Server", value=self.server_address, inline=True)

            try:
                await interaction.message.delete()
            except Exception:
                pass
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await self.ctx.send(
                f"Connected to {self.player_data.get('id', 'N/A')} | {self.player_data['name']} > {self.ctx.author.mention}"
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Verification failed: {e}", ephemeral=True)

    @discord.ui.button(label="🔄 Retry", style=discord.ButtonStyle.secondary)
    async def retry_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("You're not the one verifying!", ephemeral=True)
        await interaction.response.defer()
        player = await get_fivem_player_by_identifier(
            str(self.player_data.get("id") or self.player_data.get("name")),
            config.FIVEM_SERVER,
        )
        if not player:
            embed = discord.Embed(
                title="❌ Verification Failed",
                description="Player not found on server.",
                color=discord.Color.red(),
            )
            await interaction.message.edit(embed=embed, view=None)
            return
        self.player_data = player
        await interaction.followup.send("✅ Found your account! Click Verify.", ephemeral=True)


# ── Roblox Confirmation View ──────────────────────────────────────────────────

class RobloxConfirmationView(discord.ui.View):
    def __init__(self, ctx: commands.Context, profile: dict):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.profile = profile
        self.confirmed: bool | None = None

    @discord.ui.button(label="Yes, this is me", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("You're not the one verifying!", ephemeral=True)
        self.confirmed = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="No, cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("You're not the one verifying!", ephemeral=True)
        self.confirmed = False
        await interaction.response.send_message("Verification cancelled.", ephemeral=True)
        self.stop()


# ── Cog ───────────────────────────────────────────────────────────────────────

class VerificationCog(commands.Cog, name="Verification"):
    """🔒 Account verification commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── FiveM ─────────────────────────────────────────────────────────────────

    @commands.command()
    async def verifyfivem(self, ctx: commands.Context, *, identifier: str):
        """Verify your FiveM account. Usage: !verifyfivem <name or ID>"""
        if not config.VERIFICATION_FIVEM:
            return await ctx.send("❌ FiveM verification is disabled.", delete_after=10)
        if not config.FIVEM_SERVER:
            return await ctx.send("❌ FiveM server is not configured.", delete_after=10)

        try:
            await ctx.message.delete()
        except Exception:
            pass

        msg = await ctx.send("🔍 Searching for your FiveM player…")
        player = await get_fivem_player_by_identifier(identifier, config.FIVEM_SERVER)

        if not player:
            embed = discord.Embed(
                title="❌ Player Not Found",
                description="Ensure you are connected to the server and used the correct name/ID.",
                color=discord.Color.red(),
            )
            return await msg.edit(content=None, embed=embed)

        identifiers = player.get("identifiers", [])
        discord_id = next((i.split(":")[1] for i in identifiers if i.startswith("discord:")), None)

        embed = discord.Embed(title="🔍 FiveM Verification", color=discord.Color.blue())
        if discord_id and str(ctx.author.id) == discord_id:
            embed.description = f"Found your account: **{player['name']}**"
        else:
            if config.FIVEM_VERIFICATION_DISCORD_REQUIRED:
                embed.description = "Could not verify your Discord ID in-game."
            else:
                embed.description = f"Found: **{player['name']}** — click Verify to proceed."
        embed.add_field(name="Player ID", value=player.get("id", "N/A"), inline=True)

        view = FiveMVerificationView(ctx, player)
        view.message = await msg.edit(content=None, embed=embed, view=view)

    @commands.command()
    async def fivemserverlive(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Start live FiveM server status updates. Usage: !fivemserverlive [#channel]"""
        if not config.VERIFICATION_FIVEM or not config.FIVEM_SERVER:
            return await ctx.send("❌ FiveM not enabled or server not configured.", delete_after=10)

        target = channel or ctx.channel
        if target.id in self.bot.fivem_status_tasks:
            return await ctx.send("❌ Live status already running in that channel!", delete_after=10)

        embed = discord.Embed(title="🔄 Fetching server status…", color=discord.Color.blue())
        status_msg = await target.send(embed=embed)

        async def update_status():
            while True:
                try:
                    info = await get_fivem_server_info(config.FIVEM_SERVER)
                    if not info:
                        e = discord.Embed(
                            title="Server Status",
                            description="🔴 Server offline or unreachable",
                            color=discord.Color.red(),
                        )
                    else:
                        color = discord.Color.green() if info["status"] == "online" else discord.Color.red()
                        e = discord.Embed(title="Server Status", color=color)
                        e.add_field(name="Server Name", value=info["dynamic"].get("hostname", "N/A"), inline=False)
                        e.add_field(name="Status", value="🟢 Online" if info["status"] == "online" else "🔴 Offline", inline=True)
                        e.add_field(name="Uptime", value=info.get("uptime", "N/A"), inline=True)
                        e.add_field(name="F8 Connect", value=f"connect {config.FIVEM_SERVER}", inline=False)
                        players = info.get("players", [])
                        max_p = info["dynamic"].get("sv_maxclients", "?")
                        player_list = "\n".join(f"[{p.get('id','?')}] {p.get('name','?')}" for p in players) or "No players"
                        e.add_field(name=f"Citizens ({len(players)}/{max_p})", value=player_list, inline=False)
                    await status_msg.edit(embed=e)
                    await asyncio.sleep(60)
                except Exception as ex:
                    print(f"[FiveM Status] Error: {ex}")
                    await asyncio.sleep(60)

        task = self.bot.loop.create_task(update_status())
        self.bot.fivem_status_tasks[target.id] = {"task": task, "message": status_msg}
        await ctx.message.add_reaction("✅")

    # ── Roblox ────────────────────────────────────────────────────────────────

    @commands.command()
    async def verifyroblox(self, ctx: commands.Context, *, username: str):
        """Verify your Roblox account. Usage: !verifyroblox <username>"""
        if not config.VERIFICATION_ROBLOX:
            return await ctx.send("❌ Roblox verification is disabled.", delete_after=10)

        try:
            await ctx.message.delete()
        except Exception:
            pass

        msg = await ctx.send("🔍 Fetching Roblox profile…")
        profile = await get_roblox_profile(username)

        if not profile:
            return await msg.edit(content="❌ Couldn't find that Roblox username.")

        embed = discord.Embed(title="🔎 Is this your Roblox account?", color=discord.Color.blue())
        embed.set_thumbnail(url=profile["avatar"])
        embed.add_field(name="Username", value=profile["username"], inline=True)
        embed.add_field(name="Display Name", value=profile["displayName"], inline=True)
        embed.add_field(name="Created", value=profile["created"], inline=True)
        embed.add_field(name="Friends", value=f"{profile['friends']:,}", inline=True)
        desc = profile["description"]
        embed.add_field(
            name="Description",
            value=(desc[:500] + "…" if len(desc) > 500 else desc) or "No description",
            inline=False,
        )
        embed.set_footer(text="Confirm this is your account to continue")

        view = RobloxConfirmationView(ctx, profile)
        await msg.edit(content=None, embed=embed, view=view)
        await view.wait()

        if view.confirmed is None:
            return await msg.edit(content="⏳ Timed out. Please try again.", view=None, embed=None)
        if not view.confirmed:
            return

        code = f"Verify-{random.randint(10000, 99999)}"
        try:
            dm_embed = discord.Embed(
                title="🔑 Roblox Verification",
                description=(
                    f"Add this code to your Roblox profile description:\n```\n{code}\n```\n"
                    "The bot will automatically detect it. You have **2 minutes**."
                ),
                color=discord.Color.gold(),
            )
            await ctx.author.send(embed=dm_embed)
        except discord.Forbidden:
            return await ctx.send(f"{ctx.author.mention} Please enable DMs and try again.", delete_after=15)

        await ctx.send(f"{ctx.author.mention} Check your DMs!", delete_after=15)

        original_desc = profile["description"]
        start = time.time()
        verified = False

        while time.time() - start < 120:
            await asyncio.sleep(5)
            current = await get_roblox_profile(username)
            if not current:
                break
            if current["description"] != original_desc and code in current["description"]:
                verified = True
                break

        if not verified:
            return await ctx.author.send("⏳ Verification timed out.")

        role = None
        if config.ROBLOX_ROLE_ID:
            role = ctx.guild.get_role(config.ROBLOX_ROLE_ID)
        if not role:
            for r in ctx.guild.roles:
                if r.name.lower() not in ["@everyone", "bot"] and r < ctx.guild.me.top_role:
                    role = r
                    break

        if not role:
            return await ctx.author.send("❌ No valid role to assign. Contact server staff.")

        try:
            await ctx.author.add_roles(role)
            if config.CHANGE_NICKNAME:
                try:
                    await ctx.author.edit(nick=profile["username"])
                except discord.Forbidden:
                    pass

            success = discord.Embed(
                title="✅ Verification Successful",
                description=f"Verified as **{profile['username']}**",
                color=discord.Color.green(),
            )
            success.set_thumbnail(url=profile["avatar"])
            await ctx.author.send(embed=success)

            pub = discord.Embed(
                title="✅ Roblox Verification Complete",
                description=f"{ctx.author.mention} verified as **{profile['username']}**",
                color=discord.Color.green(),
            )
            pub.set_thumbnail(url=profile["avatar"])
            await ctx.send(embed=pub)
        except Exception as e:
            await ctx.author.send(f"❌ Failed: {e}")

    # ── Valorant ──────────────────────────────────────────────────────────────

    @commands.command()
    async def verifyvalo(self, ctx: commands.Context, *, riotid: str):
        """Verify a Valorant account. Usage: !verifyvalo Username#Tag"""
        if not config.VERIFICATION_VALO:
            return await ctx.send("❌ Valorant verification is disabled.")
        if not config.RIOT_API_KEY:
            return await ctx.send("❌ Riot API key not configured.")
        if "#" not in riotid:
            return await ctx.send("❌ Use `Username#Tag` format.")

        username, tag = riotid.split("#", 1)
        msg = await ctx.send("🔍 Verifying Valorant account…")
        account = await get_valorant_account(username, tag, config.RIOT_API_KEY, config.REGIONS)

        if not account:
            return await msg.edit(content="❌ Account not found in any region!")

        role = None
        if config.VALORANT_ROLE_ID:
            role = ctx.guild.get_role(config.VALORANT_ROLE_ID)
        if not role:
            for r in ctx.guild.roles:
                if r.name.lower() not in ["@everyone", "bot"] and r < ctx.guild.me.top_role:
                    role = r
                    break

        if not role:
            return await msg.edit(content="❌ No valid role found!")

        await ctx.author.add_roles(role)
        if config.CHANGE_NICKNAME:
            try:
                await ctx.author.edit(nick=f"{account['gameName']}#{account['tagLine']}")
            except discord.Forbidden:
                pass

        embed = discord.Embed(title="✅ Valorant Verification Successful", color=0x00FF88)
        embed.add_field(name="Account", value=f"{account['gameName']}#{account['tagLine']}", inline=True)
        embed.set_footer(text=f"Verified by {ctx.author}")
        await msg.edit(content=None, embed=embed)

    # ── SA:MP ─────────────────────────────────────────────────────────────────

    @commands.command()
    async def sampstatus(self, ctx: commands.Context):
        """Check SA-MP server status. Usage: !sampstatus"""
        if not config.SAMP_SERVER_IP or not config.SAMP_SERVER_PORT:
            return await ctx.send("❌ SA-MP server not configured.")
        try:
            client = SampClient(ip=config.SAMP_SERVER_IP, port=config.SAMP_SERVER_PORT)
            info = await client.info()
            players_data = await client.players()
            players = [p.name for p in players_data.players]
            embed = discord.Embed(title=f"SA-MP: {info.name}", color=discord.Color.green())
            embed.add_field(name="Players", value=f"{len(players)}/{info.max_players}", inline=True)
            embed.add_field(name="Gamemode", value=info.game_mode, inline=True)
            embed.add_field(name="Address", value=f"{config.SAMP_SERVER_IP}:{config.SAMP_SERVER_PORT}", inline=False)
            if players:
                pl = "\n".join(players[:10])
                more = f"\n…and {len(players)-10} more" if len(players) > 10 else ""
                embed.add_field(name="Online Players", value=f"{pl}{more}", inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"🔴 Error: {e}")

    @commands.command()
    async def verifysamp(self, ctx: commands.Context, *, playername: str):
        """Verify a SA-MP account. Usage: !verifysamp PlayerName"""
        if not config.VERIFICATION_SAMP:
            return await ctx.send("❌ SA-MP verification is disabled.")
        if not config.SAMP_SERVER_IP or not config.SAMP_SERVER_PORT:
            return await ctx.send("❌ SA-MP server not configured.")

        msg = await ctx.send(f"🔍 Checking SA-MP server…")
        try:
            client = SampClient(ip=config.SAMP_SERVER_IP, port=config.SAMP_SERVER_PORT)
            players_data = await client.players()
            players = [p.name for p in players_data.players]
            player = next((p for p in players if p.lower() == playername.lower()), None)

            if not player:
                pl_list = "\n".join(players[:10])
                return await msg.edit(content=f"❌ Player `{playername}` not found.\nCurrent players:\n{pl_list}")

            role = None
            if config.SAMP_ROLE_ID:
                role = ctx.guild.get_role(config.SAMP_ROLE_ID)
            if not role:
                for r in ctx.guild.roles:
                    if r.name.lower() not in ["@everyone", "bot"] and r < ctx.guild.me.top_role:
                        role = r
                        break

            if not role:
                return await msg.edit(content="❌ No valid role found!")

            await ctx.author.add_roles(role)
            if config.CHANGE_NICKNAME:
                try:
                    await ctx.author.edit(nick=player)
                except discord.Forbidden:
                    pass

            embed = discord.Embed(
                title="✅ SA-MP Verification Successful",
                description=f"{ctx.author.mention} verified as `{player}`",
                color=discord.Color.green(),
            )
            await msg.edit(content=None, embed=embed)
        except Exception as e:
            await msg.edit(content=f"❌ Error: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(VerificationCog(bot))
