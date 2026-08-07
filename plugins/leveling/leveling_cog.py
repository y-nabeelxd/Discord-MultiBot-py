"""
plugins/leveling/leveling_cog.py
Leveling and XP system.
"""
import random
import math
import time
import discord
from discord.ext import commands, tasks
from utils import get_leveling_data, save_leveling_data

def get_level(xp: int) -> int:
    """Calculate level based on XP. Formula: 0.1 * sqrt(xp)"""
    return math.floor(0.1 * math.sqrt(xp))

def get_xp_for_level(level: int) -> int:
    """Calculate XP required for a specific level."""
    return (level / 0.1) ** 2

class LevelingCog(commands.Cog, name="Leveling"):
    """🏆 Leveling and XP system commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cooldowns = {}  # user_id: last_xp_time
        self.data = get_leveling_data()
        self.save_task.start()

    def cog_unload(self):
        self.save_task.cancel()
        save_leveling_data(self.data)

    @tasks.loop(minutes=5)
    async def save_task(self):
        """Save leveling data to disk every 5 minutes."""
        save_leveling_data(self.data)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        user_id = str(message.author.id)
        now = time.time()
        
        # 60 second cooldown on gaining XP
        if user_id in self.cooldowns and now - self.cooldowns[user_id] < 60:
            return

        # Initialize user if not exists
        if user_id not in self.data:
            self.data[user_id] = {"xp": 0, "level": 0}

        xp_gain = random.randint(15, 25)
        old_level = self.data[user_id]["level"]
        
        self.data[user_id]["xp"] += xp_gain
        new_level = get_level(self.data[user_id]["xp"])
        self.data[user_id]["level"] = new_level

        self.cooldowns[user_id] = now

        if new_level > old_level:
            try:
                await message.channel.send(
                    f"🎉 **{message.author.mention}** just leveled up to **Level {new_level}**!"
                )
            except discord.Forbidden:
                pass

    @commands.hybrid_command(aliases=["level"])
    async def rank(self, ctx: commands.Context, member: discord.Member = None):
        """Check your rank and XP. Usage: !rank [@user]"""
        target = member or ctx.author
        user_id = str(target.id)

        if user_id not in self.data or self.data[user_id]["xp"] == 0:
            return await ctx.send(f"❌ {target.display_name} has no XP yet! Send some messages first.")

        user_xp = self.data[user_id]["xp"]
        user_level = self.data[user_id]["level"]
        
        next_level_xp = int(get_xp_for_level(user_level + 1))
        
        # Sort users to find rank
        sorted_users = sorted(self.data.items(), key=lambda x: x[1]["xp"], reverse=True)
        rank = next((i + 1 for i, (uid, _) in enumerate(sorted_users) if uid == user_id), "?")

        embed = discord.Embed(
            title=f"🏆 {target.display_name}'s Rank",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Rank", value=f"#{rank}", inline=True)
        embed.add_field(name="Level", value=f"{user_level}", inline=True)
        embed.add_field(name="XP", value=f"{user_xp} / {next_level_xp}", inline=True)

        # Progress bar
        progress = user_xp / next_level_xp
        filled = int(progress * 10)
        empty = 10 - filled
        bar = "🟩" * filled + "⬛" * empty
        embed.add_field(name="Progress", value=bar, inline=False)

        await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=["lb", "top"])
    async def leaderboard(self, ctx: commands.Context):
        """Show the top 10 members in the server by XP. Usage: !leaderboard"""
        if not self.data:
            return await ctx.send("❌ No one has earned any XP yet!")

        sorted_users = sorted(self.data.items(), key=lambda x: x[1]["xp"], reverse=True)[:10]
        
        embed = discord.Embed(
            title="🏆 Server Leaderboard",
            color=discord.Color.gold()
        )
        
        desc = ""
        for i, (uid, info) in enumerate(sorted_users):
            user = ctx.guild.get_member(int(uid))
            name = user.display_name if user else f"User {uid}"
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}."
            desc += f"{medal} **{name}** — Lvl {info['level']} ({info['xp']} XP)\n"
            
        embed.description = desc
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(LevelingCog(bot))
