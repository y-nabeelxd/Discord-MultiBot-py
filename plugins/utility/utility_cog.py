"""
plugins/utility/utility_cog.py
Utility commands: weather, translate, poll, remind, avatar, server/user info, vc247, calculator.
"""
import asyncio
import re
import datetime
import discord
import aiohttp
from discord.ext import commands
from config import PREFIX, WEATHER_API_KEY
from plugins.music.player import PERMA_VC
from utils import get_afk_data, save_afk_data


class UtilityCog(commands.Cog, name="Utility"):
    """🔧 Utility and miscellaneous commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.snipes = {}  # channel_id: {msg, author, time}

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return
        self.snipes[message.channel.id] = {
            "content": message.content,
            "author": message.author,
            "time": datetime.datetime.now()
        }

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Check AFK for author (remove AFK)
        afk_data = get_afk_data()
        user_id = str(message.author.id)
        if user_id in afk_data:
            del afk_data[user_id]
            save_afk_data(afk_data)
            try:
                await message.channel.send(f"Welcome back {message.author.mention}, I removed your AFK.")
            except discord.Forbidden:
                pass

        # Check AFK for mentioned users
        for mention in message.mentions:
            m_id = str(mention.id)
            if m_id in afk_data:
                reason = afk_data[m_id]
                try:
                    await message.channel.send(f"💤 **{mention.display_name}** is currently AFK: {reason}")
                except discord.Forbidden:
                    pass

    @commands.command()
    async def snipe(self, ctx: commands.Context):
        """Get the last deleted message in this channel. Usage: !snipe"""
        snipe_data = self.snipes.get(ctx.channel.id)
        if not snipe_data:
            return await ctx.send("❌ There's nothing to snipe!")

        embed = discord.Embed(
            description=snipe_data["content"] or "*No text (embed/image only)*",
            color=discord.Color.blue(),
            timestamp=snipe_data["time"]
        )
        embed.set_author(
            name=snipe_data["author"].display_name,
            icon_url=snipe_data["author"].display_avatar.url
        )
        embed.set_footer(text="Sniped message")
        await ctx.send(embed=embed)

    @commands.command()
    async def afk(self, ctx: commands.Context, *, reason: str = "AFK"):
        """Set your status to AFK. Usage: !afk [reason]"""
        data = get_afk_data()
        data[str(ctx.author.id)] = reason
        save_afk_data(data)
        await ctx.send(f"✅ {ctx.author.mention} I set your AFK: {reason}")

    @commands.command(aliases=["calc"])
    async def calculator(self, ctx: commands.Context, *, expression: str):
        """Evaluate a math expression. Usage: !calc <expression>"""
        try:
            expr = expression.replace(" ", "").replace("^", "**")
            if not re.match(r"^[\d+\-*/().%\s]+$", expr):
                return await ctx.send("❌ Invalid characters — only numbers and `+ - * / ^ %` allowed.")
            result = eval(expr, {"__builtins__": None}, {})
            embed = discord.Embed(title="🧮 Calculator", color=discord.Color.blue())
            embed.add_field(name="Expression", value=expression, inline=False)
            embed.add_field(name="Result", value=str(result), inline=False)
            await ctx.send(embed=embed)
        except ZeroDivisionError:
            await ctx.send("❌ Cannot divide by zero!")
        except Exception as e:
            await ctx.send(f"❌ Calculation error: {e}")

    @commands.command()
    async def translate(self, ctx: commands.Context, target_lang: str, *, text: str):
        """Translate text. Usage: !translate <lang_code> <text>"""
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {"client": "gtx", "sl": "auto", "tl": target_lang, "dt": "t", "q": text}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        return await ctx.send("❌ Failed to translate. Try again later.")
                    data = await resp.json()
                    translated = data[0][0][0]
                    src_lang = data[2]
            embed = discord.Embed(title="🌍 Translation", color=discord.Color.blue())
            embed.add_field(name=f"Original ({src_lang})", value=text, inline=False)
            embed.add_field(name=f"Translated ({target_lang})", value=translated, inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Translation error: {e}")

    @commands.command()
    async def weather(self, ctx: commands.Context, *, location: str):
        """Get weather for a location. Usage: !weather <city>"""
        if not WEATHER_API_KEY:
            return await ctx.send("❌ Weather API key is not configured.")
        try:
            params = {"q": location, "appid": WEATHER_API_KEY, "units": "metric"}
            async with aiohttp.ClientSession() as session:
                async with session.get("http://api.openweathermap.org/data/2.5/weather", params=params) as resp:
                    if resp.status != 200:
                        return await ctx.send("❌ Could not find that location.")
                    data = await resp.json()
            embed = discord.Embed(
                title=f"⛅ Weather in {data['name']}, {data['sys']['country']}",
                description=f"**{data['weather'][0]['description'].title()}**",
                color=discord.Color.blue(),
            )
            embed.set_thumbnail(url=f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png")
            embed.add_field(name="🌡️ Temperature", value=f"{data['main']['temp']}°C (feels {data['main']['feels_like']}°C)", inline=True)
            embed.add_field(name="💧 Humidity", value=f"{data['main']['humidity']}%", inline=True)
            embed.add_field(name="🌬️ Wind", value=f"{data['wind']['speed']} m/s", inline=True)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    @commands.command()
    async def poll(self, ctx: commands.Context, question: str, *options: str):
        """Create a poll. Usage: !poll "Question" "Option1" "Option2" ..."""
        if len(options) < 2:
            return await ctx.send("❌ Provide at least 2 options.")
        if len(options) > 10:
            return await ctx.send("❌ Maximum 10 options.")
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        desc = "\n".join(f"{emojis[i]} {opt}" for i, opt in enumerate(options))
        embed = discord.Embed(
            title=f"📊 Poll: {question}",
            description=desc,
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"Poll by {ctx.author.display_name}")
        message = await ctx.send(embed=embed)
        for i in range(len(options)):
            await message.add_reaction(emojis[i])

    @commands.command()
    async def remind(self, ctx: commands.Context, time_str: str, *, reminder: str):
        """Set a reminder. Usage: !remind 1h30m <reminder>"""
        try:
            seconds = 0
            t = time_str.lower()
            for unit, secs in [("d", 86400), ("h", 3600), ("m", 60), ("s", 1)]:
                if unit in t:
                    idx = t.index(unit)
                    num_str = "".join(c for c in t[:idx] if c.isdigit())
                    if num_str:
                        seconds += int(num_str) * secs
                    t = t[idx + 1:]
            if seconds <= 0:
                return await ctx.send("❌ Provide a valid time (e.g. 1h30m).")
            await ctx.send(f"⏰ I'll remind you in **{time_str}**: {reminder}")
            await asyncio.sleep(seconds)
            embed = discord.Embed(
                title="⏰ Reminder",
                description=reminder,
                color=discord.Color.gold(),
            )
            embed.set_footer(text=f"Set {time_str} ago")
            await ctx.author.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed to set reminder: {e}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def vc247(self, ctx: commands.Context):
        """Make the bot stay in VC 24/7. Usage: !vc247"""
        if not ctx.author.voice:
            return await ctx.send("❌ Join a voice channel first!")
        vc = ctx.voice_client
        if vc and vc.is_connected():
            if vc.channel != ctx.author.voice.channel:
                await vc.move_to(ctx.author.voice.channel)
        else:
            vc = await ctx.author.voice.channel.connect()
        PERMA_VC[ctx.guild.id] = True

        async def maintain():
            while PERMA_VC.get(ctx.guild.id):
                if not vc.is_connected():
                    try:
                        await ctx.author.voice.channel.connect()
                    except Exception:
                        pass
                await asyncio.sleep(10)

        self.bot.loop.create_task(maintain())
        await ctx.send("🔊 Bot will stay in VC 24/7. Use `!leave` to stop.")

    @commands.command()
    async def avatar(self, ctx: commands.Context, member: discord.Member = None):
        """Get a user's avatar. Usage: !avatar [@user]"""
        target = member or ctx.author
        embed = discord.Embed(title=f"{target.display_name}'s Avatar", color=discord.Color.blue())
        embed.set_image(url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command()
    async def serverinfo(self, ctx: commands.Context):
        """Get server information. Usage: !serverinfo"""
        g = ctx.guild
        embed = discord.Embed(title=f"Server: {g.name}", color=discord.Color.blue())
        if g.icon:
            embed.set_thumbnail(url=g.icon.url)
        embed.add_field(name="Owner", value=g.owner.mention if g.owner else "Unknown", inline=True)
        embed.add_field(name="Created", value=g.created_at.strftime("%B %d, %Y"), inline=True)
        embed.add_field(name="Members", value=g.member_count, inline=True)
        embed.add_field(name="Roles", value=len(g.roles), inline=True)
        embed.add_field(name="Channels", value=f"Text: {len(g.text_channels)}  Voice: {len(g.voice_channels)}", inline=True)
        embed.add_field(name="Boosts", value=g.premium_subscription_count, inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        """Get user information. Usage: !userinfo [@user]"""
        target = member or ctx.author
        embed = discord.Embed(title=f"User: {target.display_name}", color=discord.Color.blue())
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="ID", value=target.id, inline=True)
        embed.add_field(name="Nickname", value=target.nick or "None", inline=True)
        embed.add_field(name="Account Created", value=target.created_at.strftime("%B %d, %Y"), inline=True)
        embed.add_field(name="Joined Server", value=target.joined_at.strftime("%B %d, %Y") if target.joined_at else "Unknown", inline=True)
        roles = [r.mention for r in target.roles if r.name != "@everyone"]
        embed.add_field(
            name=f"Roles ({len(roles)})",
            value=" ".join(roles) if roles else "None",
            inline=False,
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityCog(bot))
