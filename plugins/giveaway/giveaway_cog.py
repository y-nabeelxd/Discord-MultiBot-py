"""
plugins/giveaway/giveaway_cog.py
Giveaway System.
"""
import time
import random
import asyncio
import discord
from discord.ext import commands, tasks
from utils import get_giveaway_data, save_giveaway_data


def parse_time(time_str: str) -> int:
    """Parse time string (1d, 2h, 30m, etc) to seconds."""
    time_dict = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    unit = time_str[-1].lower()
    if unit not in time_dict:
        return -1
    try:
        val = int(time_str[:-1])
        return val * time_dict[unit]
    except ValueError:
        return -1


class GiveawayCog(commands.Cog, name="Giveaway"):
    """🎉 Giveaway System Commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.giveaway_task.start()

    def cog_unload(self):
        self.giveaway_task.cancel()

    @tasks.loop(seconds=15)
    async def giveaway_task(self):
        """Check for ended giveaways."""
        data = get_giveaway_data()
        now = time.time()
        to_remove = []

        for msg_id, info in data.items():
            if now >= info["end_time"]:
                await self.end_giveaway(info["channel_id"], int(msg_id), info["winners"], info["prize"])
                to_remove.append(msg_id)

        if to_remove:
            for msg_id in to_remove:
                del data[msg_id]
            save_giveaway_data(data)

    @giveaway_task.before_loop
    async def before_giveaway_task(self):
        await self.bot.wait_until_ready()

    async def end_giveaway(self, channel_id: int, message_id: int, winner_count: int, prize: str):
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        try:
            msg = await channel.fetch_message(message_id)
        except discord.NotFound:
            return

        # Find reaction
        reaction = None
        for r in msg.reactions:
            if str(r.emoji) == "🎉":
                reaction = r
                break

        if not reaction:
            return

        users = [user async for user in reaction.users() if not user.bot]
        
        if len(users) == 0:
            await channel.send(f"No one entered the giveaway for **{prize}**!")
        else:
            winners = random.sample(users, min(len(users), winner_count))
            winner_mentions = ", ".join(w.mention for w in winners)
            
            embed = discord.Embed(
                title="🎉 Giveaway Ended! 🎉",
                description=f"Prize: **{prize}**\nWinner(s): {winner_mentions}",
                color=discord.Color.green()
            )
            embed.set_footer(text="Congratulations!")
            
            await msg.edit(embed=embed)
            await channel.send(f"Congratulations {winner_mentions}! You won **{prize}**!\n{msg.jump_url}")

    @commands.hybrid_command()
    @commands.has_permissions(manage_messages=True)
    async def gstart(self, ctx: commands.Context, duration: str, winners: str, *, prize: str):
        """Start a giveaway. Usage: !gstart 10m 1w Prize"""
        seconds = parse_time(duration)
        if seconds <= 0:
            return await ctx.send("❌ Invalid duration! Use formats like `10m`, `1h`, `1d`.")
        
        if not winners.endswith("w"):
            return await ctx.send("❌ Invalid winners format! Use `1w`, `2w`, etc.")
        
        try:
            winner_count = int(winners[:-1])
            if winner_count < 1:
                raise ValueError
        except ValueError:
            return await ctx.send("❌ Winner count must be a number followed by 'w' (e.g. `2w`).")

        end_time = time.time() + seconds
        
        embed = discord.Embed(
            title="🎉 GIVEAWAY 🎉",
            description=f"Prize: **{prize}**\nReact with 🎉 to enter!\n\nEnds: <t:{int(end_time)}:R>\nWinners: **{winner_count}**",
            color=discord.Color.purple()
        )
        embed.set_footer(text=f"Hosted by {ctx.author.display_name}")

        msg = await ctx.send(embed=embed)
        await msg.add_reaction("🎉")

        data = get_giveaway_data()
        data[str(msg.id)] = {
            "channel_id": ctx.channel.id,
            "end_time": end_time,
            "winners": winner_count,
            "prize": prize,
            "host_id": ctx.author.id
        }
        save_giveaway_data(data)

    @commands.hybrid_command()
    @commands.has_permissions(manage_messages=True)
    async def gend(self, ctx: commands.Context, message_id: int):
        """End a giveaway early. Usage: !gend <message_id>"""
        data = get_giveaway_data()
        msg_id_str = str(message_id)
        
        if msg_id_str not in data:
            return await ctx.send("❌ Giveaway not found in database. It may have already ended.")

        info = data[msg_id_str]
        await self.end_giveaway(info["channel_id"], message_id, info["winners"], info["prize"])
        
        del data[msg_id_str]
        save_giveaway_data(data)
        
        await ctx.send("✅ Giveaway ended early!")

    @commands.hybrid_command()
    @commands.has_permissions(manage_messages=True)
    async def greroll(self, ctx: commands.Context, message_id: int):
        """Reroll a giveaway winner. Usage: !greroll <message_id>"""
        try:
            msg = await ctx.channel.fetch_message(message_id)
        except discord.NotFound:
            return await ctx.send("❌ Message not found in this channel.")

        reaction = next((r for r in msg.reactions if str(r.emoji) == "🎉"), None)
        if not reaction:
            return await ctx.send("❌ Cannot find the 🎉 reaction on that message.")

        users = [user async for user in reaction.users() if not user.bot]
        if len(users) == 0:
            return await ctx.send("❌ No one entered that giveaway.")

        winner = random.choice(users)
        await ctx.send(f"🎉 The new winner is {winner.mention}! Congratulations!\n{msg.jump_url}")


async def setup(bot: commands.Bot):
    await bot.add_cog(GiveawayCog(bot))
