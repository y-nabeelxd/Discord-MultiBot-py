"""
bot.py — Entry point for Discord MultiBot.
Loads all plugins from the /plugins directory and starts the bot.
"""
import sys
import os
import logging
import asyncio
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

import config
from utils import beautiful_print, clear_console

# ── Logging ───────────────────────────────────────────────────────────────────
discord.utils.setup_logging(level=logging.INFO, root=False)
logger = logging.getLogger("discord")
logger.setLevel(logging.WARNING)

# ── Bot setup ─────────────────────────────────────────────────────────────────
intents = discord.Intents.all()

# List of all plugin extension paths to load
EXTENSIONS = [
    "plugins.music.music_cog",
    "plugins.moderation.moderation_cog",
    "plugins.verification.verification_cog",
    "plugins.fun.fun_cog",
    "plugins.economy.economy_cog",
    "plugins.utility.utility_cog",
    "plugins.slash.slash_cog",
    "plugins.leveling.leveling_cog",
    "plugins.ticket.ticket_cog",
    "plugins.giveaway.giveaway_cog",
]


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=config.PREFIX,
            intents=intents,
            help_command=None,  # Custom help command loaded from HelpCog below
        )
        self.fivem_status_tasks: dict = {}
        self.presence_index = 0
        self.tree.on_error = self.on_tree_error

    @tasks.loop(seconds=15)
    async def status_task(self):
        total_members = sum(g.member_count for g in self.guilds if getattr(g, "member_count", 0))
        statuses = [
            discord.Game(name=f"Music | {config.PREFIX}help"),
            discord.Activity(type=discord.ActivityType.watching, name=f"{len(self.guilds)} servers"),
            discord.Activity(type=discord.ActivityType.listening, name=f"{total_members} users"),
            discord.Game(name=f"{config.GAME_PREFIX} daily"),
            discord.Activity(type=discord.ActivityType.playing, name="Slash Commands (/)")
        ]
        await self.change_presence(activity=statuses[self.presence_index % len(statuses)])
        self.presence_index += 1

    @status_task.before_loop
    async def before_status_task(self):
        await self.wait_until_ready()

    async def setup_hook(self):
        """Load all plugin cogs before the bot connects."""
        loaded, failed = [], []
        for ext in EXTENSIONS:
            try:
                await self.load_extension(ext)
                loaded.append(ext.split(".")[-1])
            except Exception as e:
                failed.append(f"{ext}: {e}")
                print(f"[Cog Error] Failed to load {ext}: {e}")

        print(f"[Cogs] Loaded: {', '.join(loaded)}")
        if failed:
            print(f"[Cogs] Failed: {'; '.join(failed)}")
            
        self.status_task.start()

    async def on_connect(self):
        clear_console()
        beautiful_print("🔌 Connecting to Discord…", "─")

    async def on_ready(self):
        clear_console()
        msg = f"""
🤖 Connected: {self.user.name}
🆔 ID: {self.user.id}
⚡ Prefix: "{config.PREFIX}"
🎮 Game Prefix: "{config.GAME_PREFIX}"
🔒 Verification:
  • FiveM:   {'✅ Enabled' if config.VERIFICATION_FIVEM and config.FIVEM_SERVER else '❌ Disabled'}
  • Roblox:  {'✅ Enabled' if config.VERIFICATION_ROBLOX else '❌ Disabled'}
  • SA-MP:   {'✅ Enabled' if config.VERIFICATION_SAMP else '❌ Disabled'}
  • Valorant:{'✅ Enabled' if config.VERIFICATION_VALO and config.RIOT_API_KEY else '❌ Disabled'}
"""
        beautiful_print(msg, "═")

        try:
            synced = await self.tree.sync()
            beautiful_print(f"✅ Synced {len(synced)} slash commands", "─")
        except Exception as e:
            beautiful_print(f"❌ Slash sync failed: {e}", "!")

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                f"❌ Missing argument: `{error.param.name}`\n"
                f"Usage: `{config.PREFIX}{ctx.command.name} {ctx.command.signature}`"
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                f"❌ Invalid argument: {error}\n"
                f"Usage: `{config.PREFIX}{ctx.command.name} {ctx.command.signature}`"
            )
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ Cooldown — try again in {error.retry_after:.1f}s.")
        elif isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, discord.Forbidden):
                try:
                    await ctx.send("❌ I don't have the required permissions to do that.")
                except discord.Forbidden:
                    pass  # Can't even send the error message
            elif isinstance(error.original, discord.HTTPException):
                await ctx.send("⚠️ Discord API error occurred. Please try again.")
            else:
                print(f"[Error] Command {ctx.command}: {error.original}")
                await ctx.send("⚠️ An unexpected error occurred while running the command.")
        else:
            print(f"[Error] Command {ctx.command}: {error}")
            await ctx.send("⚠️ An unexpected error occurred.")

    async def on_tree_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Global error handler for slash commands and interactions."""
        if isinstance(error, app_commands.CommandOnCooldown):
            msg = f"⏳ Cooldown — try again in {error.retry_after:.1f}s."
        elif isinstance(error, app_commands.MissingPermissions):
            msg = "❌ You don't have permission to use this command!"
        elif isinstance(error, app_commands.BotMissingPermissions):
            msg = "❌ I lack the permissions needed to execute this command."
        else:
            print(f"[Slash Error] {interaction.command.name if interaction.command else 'Unknown'}: {error}")
            msg = "⚠️ An unexpected error occurred."
            
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                await interaction.followup.send(msg, ephemeral=True)
        except discord.HTTPException:
            pass


# ── Custom Help Command ───────────────────────────────────────────────────────

class HelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(command_attrs={"help": "Shows help about the bot"})

    async def send_bot_help(self, mapping):
        ctx = self.context
        embed = discord.Embed(
            title=f"{ctx.bot.user.name} — Help",
            description=f"Use `{config.PREFIX}help <command>` for details.",
            color=discord.Color.blue(),
        )

        music = ["play", "skip", "queue", "clearqueue", "pause", "resume", "stop", "leave"]
        embed.add_field(name="🎵 Music", value="\n".join(f"`{config.PREFIX}{c}`" for c in music), inline=False)

        verif = []
        if config.VERIFICATION_FIVEM and config.FIVEM_SERVER:
            verif += ["verifyfivem", "fivemserverlive"]
        if config.VERIFICATION_ROBLOX:
            verif.append("verifyroblox")
        if config.VERIFICATION_SAMP:
            verif += ["verifysamp", "sampstatus"]
        if config.VERIFICATION_VALO and config.RIOT_API_KEY:
            verif.append("verifyvalo")
        if verif:
            embed.add_field(name="🔒 Verification", value="\n".join(f"`{config.PREFIX}{c}`" for c in verif), inline=False)

        mod = [
            "ban", "kick", "timeout", "slowmode", "slowoff", "setnick", "resetnick",
            "addrole", "removerole", "createrole", "deleterole", "getroles",
            "lock", "unlock", "warn", "warnings", "clearwarns", "mute", "unmute",
            "purge", "nuke", "clone",
        ]
        embed.add_field(name="🛡️ Moderation", value="\n".join(f"`{config.PREFIX}{c}`" for c in mod), inline=False)

        games = ["rps", "roll", "flipcoin", "guess", "8ball", "tictactoe", "trivia"]
        embed.add_field(name="🎮 Games", value="\n".join(f"`{config.PREFIX}{c}`" for c in games), inline=False)

        gp = config.GAME_PREFIX
        economy = [f"{gp}coinflip", f"{gp}slots", f"{gp}daily", f"{gp}balance"]
        embed.add_field(name=f"🪙 Economy ({gp})", value="\n".join(f"`{c}`" for c in economy), inline=False)

        lvl = ["rank", "leaderboard"]
        embed.add_field(name="🏆 Leveling", value="\n".join(f"`{config.PREFIX}{c}`" for c in lvl), inline=False)

        fun = ["slap", "kiss", "hug"]
        embed.add_field(name="😂 Fun", value="\n".join(f"`{config.PREFIX}{c}`" for c in fun), inline=False)

        util = ["poll", "avatar", "serverinfo", "userinfo", "remind", "translate", "weather", "calc", "vc247", "afk", "snipe"]
        embed.add_field(name="🔧 Utility", value="\n".join(f"`{config.PREFIX}{c}`" for c in util), inline=False)

        ticket = ["ticket setup", "ticket close"]
        embed.add_field(name="🎫 Tickets", value="\n".join(f"`{config.PREFIX}{c}`" for c in ticket), inline=False)

        gw = ["gstart", "gend", "greroll"]
        embed.add_field(name="🎉 Giveaways", value="\n".join(f"`{config.PREFIX}{c}`" for c in gw), inline=False)

        slash_cmds = ["sc", "invite", "kick", "ban", "clear", "unban", "setnick", "role_give", "role_remove", "move_all", "move_user", "moveme", "move_role"]
        embed.add_field(name="⚡ Slash Commands", value="\n".join(f"`/{c}`" for c in slash_cmds), inline=False)

        await ctx.send(embed=embed)

    async def send_command_help(self, command):
        ctx = self.context
        embed = discord.Embed(
            title=f"Command: {config.PREFIX}{command.name}",
            description=command.help or "No description available.",
            color=discord.Color.green(),
        )
        if command.aliases:
            embed.add_field(name="Aliases", value=", ".join(f"`{a}`" for a in command.aliases), inline=False)
        await ctx.send(embed=embed)

    async def send_error_message(self, error):
        await self.context.send(
            embed=discord.Embed(title="Help Error", description=error, color=discord.Color.red())
        )


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not config.DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN is not set. Add it to your .env file.")
        sys.exit(1)

    bot = MyBot()
    bot.help_command = HelpCommand()

    try:
        bot.run(config.DISCORD_TOKEN)
    except discord.LoginFailure:
        beautiful_print("❌ Invalid bot token! Check your DISCORD_TOKEN in .env", "!")
        sys.exit(1)
    except Exception as e:
        beautiful_print(f"❌ Failed to start bot: {e}", "!")
        sys.exit(1)
