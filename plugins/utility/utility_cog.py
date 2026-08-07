"""
plugins/utility/utility_cog.py
Utility commands: weather, translate, poll, remind, avatar, server/user info, vc247, calculator.
"""
import asyncio
import re
import datetime
import discord
import aiohttp
import psutil
import time
from discord.ext import commands
from config import PREFIX, WEATHER_API_KEY
from plugins.music.player import PERMA_VC
from utils import get_afk_data, save_afk_data


class UtilityCog(commands.Cog, name="Utility"):
    """ðŸ”§ Utility and miscellaneous commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()
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
                    await message.channel.send(f"ðŸ’¤ **{mention.display_name}** is currently AFK: {reason}")
                except discord.Forbidden:
                    pass

    @commands.command()
    async def snipe(self, ctx: commands.Context):
        """Get the last deleted message in this channel. Usage: !snipe"""
        snipe_data = self.snipes.get(ctx.channel.id)
        if not snipe_data:
            return await ctx.send("âŒ There's nothing to snipe!")

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
        await ctx.send(f"âœ… {ctx.author.mention} I set your AFK: {reason}")

    @commands.command(aliases=["calc"])
    async def calculator(self, ctx: commands.Context, *, expression: str):
        """Evaluate a math expression. Usage: !calc <expression>"""
        try:
            expr = expression.replace(" ", "").replace("^", "**")
            if not re.match(r"^[\d+\-*/().%\s]+$", expr):
                return await ctx.send("âŒ Invalid characters â€” only numbers and `+ - * / ^ %` allowed.")
            result = eval(expr, {"__builtins__": None}, {})
            embed = discord.Embed(title="ðŸ§® Calculator", color=discord.Color.blue())
            embed.add_field(name="Expression", value=expression, inline=False)
            embed.add_field(name="Result", value=str(result), inline=False)
            await ctx.send(embed=embed)
        except ZeroDivisionError:
            await ctx.send("âŒ Cannot divide by zero!")
        except Exception as e:
            await ctx.send(f"âŒ Calculation error: {e}")

    @commands.command()
    async def translate(self, ctx: commands.Context, target_lang: str, *, text: str):
        """Translate text. Usage: !translate <lang_code> <text>"""
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {"client": "gtx", "sl": "auto", "tl": target_lang, "dt": "t", "q": text}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        return await ctx.send("âŒ Failed to translate. Try again later.")
                    data = await resp.json()
                    translated = data[0][0][0]
                    src_lang = data[2]
            embed = discord.Embed(title="ðŸŒ Translation", color=discord.Color.blue())
            embed.add_field(name=f"Original ({src_lang})", value=text, inline=False)
            embed.add_field(name=f"Translated ({target_lang})", value=translated, inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"âŒ Translation error: {e}")

    @commands.command()
    async def weather(self, ctx: commands.Context, *, location: str):
        """Get weather for a location. Usage: !weather <city>"""
        if not WEATHER_API_KEY:
            return await ctx.send("âŒ Weather API key is not configured.")
        try:
            params = {"q": location, "appid": WEATHER_API_KEY, "units": "metric"}
            async with aiohttp.ClientSession() as session:
                async with session.get("http://api.openweathermap.org/data/2.5/weather", params=params) as resp:
                    if resp.status != 200:
                        return await ctx.send("âŒ Could not find that location.")
                    data = await resp.json()
            embed = discord.Embed(
                title=f"â›… Weather in {data['name']}, {data['sys']['country']}",
                description=f"**{data['weather'][0]['description'].title()}**",
                color=discord.Color.blue(),
            )
            embed.set_thumbnail(url=f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png")
            embed.add_field(name="ðŸŒ¡ï¸ Temperature", value=f"{data['main']['temp']}Â°C (feels {data['main']['feels_like']}Â°C)", inline=True)
            embed.add_field(name="ðŸ’§ Humidity", value=f"{data['main']['humidity']}%", inline=True)
            embed.add_field(name="ðŸŒ¬ï¸ Wind", value=f"{data['wind']['speed']} m/s", inline=True)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"âŒ Error: {e}")

    @commands.command()
    async def poll(self, ctx: commands.Context, question: str, *options: str):
        """Create a poll. Usage: !poll "Question" "Option1" "Option2" ..."""
        if len(options) < 2:
            return await ctx.send("âŒ Provide at least 2 options.")
        if len(options) > 10:
            return await ctx.send("âŒ Maximum 10 options.")
        emojis = ["1ï¸âƒ£", "2ï¸âƒ£", "3ï¸âƒ£", "4ï¸âƒ£", "5ï¸âƒ£", "6ï¸âƒ£", "7ï¸âƒ£", "8ï¸âƒ£", "9ï¸âƒ£", "ðŸ”Ÿ"]
        desc = "\n".join(f"{emojis[i]} {opt}" for i, opt in enumerate(options))
        embed = discord.Embed(
            title=f"ðŸ“Š Poll: {question}",
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
                return await ctx.send("âŒ Provide a valid time (e.g. 1h30m).")
            await ctx.send(f"â° I'll remind you in **{time_str}**: {reminder}")
            await asyncio.sleep(seconds)
            embed = discord.Embed(
                title="â° Reminder",
                description=reminder,
                color=discord.Color.gold(),
            )
            embed.set_footer(text=f"Set {time_str} ago")
            await ctx.author.send(embed=embed)
        except Exception as e:
            await ctx.send(f"âŒ Failed to set reminder: {e}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def vc247(self, ctx: commands.Context):
        """Make the bot stay in VC 24/7. Usage: !vc247"""
        if not ctx.author.voice:
            return await ctx.send("âŒ Join a voice channel first!")
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
        await ctx.send("ðŸ”Š Bot will stay in VC 24/7. Use `!leave` to stop.")

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
        await ctx.message.delete()
        
    @commands.command(aliases=["binfo", "stats"])
    async def botinfo(self, ctx: commands.Context):
        """Show detailed statistics about the bot."""
        process = psutil.Process()
        memory_usage = process.memory_full_info().uss / 1024**2
        cpu_usage = process.cpu_percent()
        
        uptime_seconds = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"
        
        embed = discord.Embed(
            title="ðŸ¤– Bot Statistics",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.now()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        embed.add_field(name="Ping", value=f"`{round(self.bot.latency * 1000)}ms`", inline=True)
        embed.add_field(name="Uptime", value=f"`{uptime_str}`", inline=True)
        embed.add_field(name="Memory", value=f"`{memory_usage:.2f} MB`", inline=True)
        
        embed.add_field(name="CPU", value=f"`{cpu_usage}%`", inline=True)
        embed.add_field(name="Servers", value=f"`{len(self.bot.guilds)}`", inline=True)
        embed.add_field(name="Users", value=f"`{sum(g.member_count for g in self.bot.guilds)}`", inline=True)
        
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["rinfo"])
    async def roleinfo(self, ctx: commands.Context, *, role: discord.Role):
        """Show detailed information about a role."""
        embed = discord.Embed(
            title=f"Role: {role.name}",
            color=role.color,
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="ID", value=f"`{role.id}`", inline=True)
        embed.add_field(name="Color", value=f"`{role.color}`", inline=True)
        embed.add_field(name="Position", value=f"`{role.position}`", inline=True)
        
        embed.add_field(name="Members", value=f"`{len(role.members)}`", inline=True)
        embed.add_field(name="Mentionable", value=f"`{'Yes' if role.mentionable else 'No'}`", inline=True)
        embed.add_field(name="Hoisted", value=f"`{'Yes' if role.hoist else 'No'}`", inline=True)
        
        created_at = role.created_at.strftime("%b %d, %Y")
        embed.add_field(name="Created At", value=f"`{created_at}`", inline=True)
        
        key_perms = []
        if role.permissions.administrator: key_perms.append("Administrator")
        if role.permissions.manage_guild: key_perms.append("Manage Server")
        if role.permissions.manage_roles: key_perms.append("Manage Roles")
        if role.permissions.manage_channels: key_perms.append("Manage Channels")
        if role.permissions.manage_messages: key_perms.append("Manage Messages")
        if role.permissions.ban_members: key_perms.append("Ban Members")
        if role.permissions.kick_members: key_perms.append("Kick Members")
        
        if key_perms:
            embed.add_field(name="Key Permissions", value=", ".join(f"`{p}`" for p in key_perms), inline=False)
            
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityCog(bot))

