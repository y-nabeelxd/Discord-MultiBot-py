"""
plugins/economy/economy_cog.py
Owo economy game commands (coinflip, slots, daily, balance).
"""
import asyncio
import random
import datetime
import discord
from discord.ext import commands
from config import GAME_PREFIX, BOT_OWNER, COINFLIP_GIF
from utils import get_owo_data, save_owo_data


def _ensure_user(data: dict, user_id: str) -> None:
    if user_id not in data:
        data[user_id] = {"balance": 0, "last_daily": None}


class EconomyCog(commands.Cog, name="Economy"):
    """🪙 Owo economy game commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name=f"{GAME_PREFIX}coinflip", aliases=[f"{GAME_PREFIX}cf"])
    async def coinflip(self, ctx: commands.Context, amount: int, choice: str = None):
        """Flip a coin with coins. Usage: owo coinflip <amount> [heads/tails]"""
        if amount <= 0:
            return await ctx.send("❌ Amount must be positive!")

        data = get_owo_data()
        uid = str(ctx.author.id)
        _ensure_user(data, uid)

        if data[uid]["balance"] < amount:
            return await ctx.send("❌ You don't have enough coins!")

        was_random = False
        if choice is not None:
            choice = choice.lower()
            if choice not in ["heads", "tails"]:
                return await ctx.send("❌ Choose `heads` or `tails`.")
        else:
            choice = random.choice(["heads", "tails"])
            was_random = True

        embed = discord.Embed(title="🪙 Coin Flip", color=discord.Color.gold())
        embed.description = (
            f"**{ctx.author.display_name}** flips for **{amount}** coins "
            f"({'random' if was_random else f'betting {choice}'})…"
        )
        embed.set_image(url=COINFLIP_GIF)
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(3)

        result = random.choice(["heads", "tails"])

        if was_random:
            won = True
            net_gain = int(amount * 0.5)  # random always wins 0.5x
        else:
            won = choice == result
            net_gain = amount if won else -amount

        data[uid]["balance"] += net_gain
        save_owo_data(data)

        outcome = (
            f"**{'Random win' if was_random else 'You won'}!** Landed on **{result}**!"
            if won
            else f"**You lost!** Landed on **{result}**."
        )

        result_embed = discord.Embed(
            title="🪙 Coin Flip Result",
            description=outcome,
            color=discord.Color.gold() if won else discord.Color.red(),
        )
        if was_random:
            result_embed.add_field(name="Random Choice", value=choice.capitalize(), inline=True)
        else:
            result_embed.add_field(name="Your Choice", value=choice.capitalize(), inline=True)
        result_embed.add_field(name="Actual Result", value=result.capitalize(), inline=True)
        result_embed.add_field(name=f"{'Winnings' if won else 'Loss'}", value=f"{'+' if won else ''}{net_gain} coins", inline=False)
        result_embed.add_field(name="New Balance", value=f"{data[uid]['balance']} coins", inline=False)
        await msg.edit(embed=result_embed)

    @commands.command(name=f"{GAME_PREFIX}slots", aliases=[f"{GAME_PREFIX}s"])
    async def slots(self, ctx: commands.Context, amount: int):
        """Play slots. Usage: owo slots <amount>"""
        if amount <= 0:
            return await ctx.send("❌ Amount must be positive!")

        data = get_owo_data()
        uid = str(ctx.author.id)
        _ensure_user(data, uid)

        if data[uid]["balance"] < amount:
            return await ctx.send("❌ You don't have enough coins!")

        emojis = ["🍎", "🍒", "🍋", "🍉", "🍇", "7️⃣"]
        weights = [0.25, 0.25, 0.20, 0.15, 0.10, 0.05]
        streak = data[uid].get("slots_losing_streak", 0)
        adj = [w * (1 + streak * 0.1) for w in weights]

        spin_embed = discord.Embed(title="🎰 Slots Spinning…", description="[ 🎰 | 🎰 | 🎰 ]", color=discord.Color.gold())
        msg = await ctx.send(embed=spin_embed)

        for _ in range(3):
            temp = [random.choices(emojis, weights=adj)[0] for _ in range(3)]
            spin_embed.description = f"[ {' | '.join(temp)} ]"
            await msg.edit(embed=spin_embed)
            await asyncio.sleep(0.5)

        final = [random.choices(emojis, weights=adj)[0] for _ in range(3)]

        if final[0] == final[1] == final[2]:
            multiplier = 10 if final[0] == "7️⃣" else 5
            won = True
            data[uid]["slots_losing_streak"] = 0
        elif final[0] == final[1] or final[1] == final[2] or final[0] == final[2]:
            multiplier = 2
            won = True
            data[uid]["slots_losing_streak"] = max(0, streak - 1)
        else:
            multiplier = 0
            won = False
            data[uid]["slots_losing_streak"] = streak + 1

        if won:
            winnings = amount * multiplier
            net = winnings - amount
            data[uid]["balance"] += net
            outcome = f"**You won {winnings} coins!** (×{multiplier})"
        else:
            data[uid]["balance"] -= amount
            outcome = "**You lost!**"
            if data[uid]["slots_losing_streak"] >= 5:
                consolation = min(amount, 100)
                data[uid]["balance"] += consolation
                outcome += f"\nConsolation: +{consolation} coins 🎁"

        save_owo_data(data)

        res_embed = discord.Embed(
            title="🎰 Slots Result",
            description=f"[ {' | '.join(final)} ]\n{outcome}",
            color=discord.Color.gold() if won else discord.Color.red(),
        )
        res_embed.add_field(name="Bet", value=f"{amount} coins", inline=True)
        if won:
            res_embed.add_field(name="Winnings", value=f"{winnings} coins", inline=True)
        res_embed.add_field(name="New Balance", value=f"{data[uid]['balance']} coins", inline=False)
        await msg.edit(embed=res_embed)

    @commands.command(name=f"{GAME_PREFIX}daily")
    async def daily(self, ctx: commands.Context):
        """Claim daily coins (300–5000). Usage: owo daily"""
        data = get_owo_data()
        uid = str(ctx.author.id)
        _ensure_user(data, uid)

        now = datetime.datetime.now()
        if data[uid]["last_daily"]:
            last = datetime.datetime.fromisoformat(data[uid]["last_daily"])
            diff = datetime.timedelta(hours=24)
            if now - last < diff:
                remaining = diff - (now - last)
                h = remaining.seconds // 3600
                m = (remaining.seconds % 3600) // 60
                return await ctx.send(f"⏳ Next daily in **{h}h {m}m**!")

        amount = random.randint(300, 5000)
        data[uid]["balance"] += amount
        data[uid]["last_daily"] = now.isoformat()
        save_owo_data(data)

        embed = discord.Embed(
            title="🎁 Daily Reward!",
            description=f"You got **{amount} coins**!\nBalance: **{data[uid]['balance']} coins**",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @commands.command(name=f"{GAME_PREFIX}balance", aliases=[f"{GAME_PREFIX}bal"])
    async def balance(self, ctx: commands.Context, member: discord.Member = None):
        """Check coin balance. Usage: owo balance [@user]"""
        target = member or ctx.author
        data = get_owo_data()
        uid = str(target.id)
        bal = data.get(uid, {}).get("balance", 0)
        embed = discord.Embed(
            title=f"💰 {target.display_name}'s Balance",
            description=f"**{bal} coins**",
            color=discord.Color.gold(),
        )
        await ctx.send(embed=embed)

    @commands.command(name=f"{GAME_PREFIX}addcoin")
    async def addcoin(self, ctx: commands.Context, member: discord.Member, amount: int):
        """Add coins to a user (Bot owner only). Usage: owo addcoin @user <amount>"""
        if BOT_OWNER and ctx.author.id != BOT_OWNER:
            return await ctx.send("❌ Only the bot owner can use this command!")
        if amount <= 0:
            return await ctx.send("❌ Amount must be positive!")

        data = get_owo_data()
        uid = str(member.id)
        _ensure_user(data, uid)
        data[uid]["balance"] += amount
        save_owo_data(data)

        embed = discord.Embed(
            title="➕ Coins Added",
            description=f"Added **{amount} coins** to {member.mention}. New balance: **{data[uid]['balance']} coins**",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyCog(bot))
