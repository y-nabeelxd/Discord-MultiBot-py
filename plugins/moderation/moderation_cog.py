"""
plugins/moderation/moderation_cog.py
All moderation commands as a discord.py Cog.
"""
import asyncio
import datetime
import discord
from discord.ext import commands
from config import PREFIX, EXTRA_ROLES_LOCK_UNLOCK
from utils import get_warnings_data, save_warnings_data


class ModerationCog(commands.Cog, name="Moderation"):
    """🛡️ Server moderation commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── Ban / Kick ────────────────────────────────────────────────────────────

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Ban a member. Usage: !ban @user [reason]"""
        reason = reason[:512]
        try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                title="🔨 Member Banned",
                description=f"{member.mention} has been banned by {ctx.author.mention}",
                color=discord.Color.red(),
            )
            embed.add_field(name="Reason", value=reason)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed to ban member: {e}")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a member. Usage: !kick @user [reason]"""
        reason = reason[:512]
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="👢 Member Kicked",
                description=f"{member.mention} has been kicked by {ctx.author.mention}",
                color=discord.Color.orange(),
            )
            embed.add_field(name="Reason", value=reason)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed to kick member: {e}")

    # ── Timeout ───────────────────────────────────────────────────────────────

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx: commands.Context, member: discord.Member, duration: str, *, reason: str = "No reason provided"):
        """Timeout a member (1s/1m/1h/1d). Usage: !timeout @user 30m [reason]"""
        reason = reason[:512]
        try:
            time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
            dl = duration.lower()
            if dl[-1] not in time_units:
                raise ValueError("Invalid time unit. Use s, m, h, or d")
            seconds = int(dl[:-1]) * time_units[dl[-1]]
            await member.timeout(datetime.timedelta(seconds=seconds), reason=reason)
            embed = discord.Embed(
                title="⏳ Member Timed Out",
                description=f"{member.mention} timed out by {ctx.author.mention}",
                color=discord.Color.gold(),
            )
            embed.add_field(name="Duration", value=duration)
            embed.add_field(name="Reason", value=reason)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed to timeout member: {e}\nUsage: `{PREFIX}timeout @user 30m [reason]`")

    # ── Slowmode ──────────────────────────────────────────────────────────────

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx: commands.Context, duration: str):
        """Set channel slowmode. Usage: !slowmode 30s"""
        try:
            time_units = {"s": 1, "m": 60, "h": 3600}
            dl = duration.lower()
            if dl[-1] not in time_units:
                raise ValueError("Invalid time unit.")
            seconds = int(dl[:-1]) * time_units[dl[-1]]
            if seconds > 21600:
                return await ctx.send("❌ Slowmode max is 6 hours!")
            await ctx.channel.edit(slowmode_delay=seconds)
            await ctx.send(f"⏳ Slowmode set to **{duration}**.")
        except Exception as e:
            await ctx.send(f"❌ Failed to set slowmode: {e}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def slowoff(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Remove slowmode from a channel. Usage: !slowoff [#channel]"""
        target = channel or ctx.channel
        try:
            await target.edit(slowmode_delay=0)
            await ctx.send(f"✅ Slowmode removed from {target.mention}")
        except Exception as e:
            await ctx.send(f"❌ Failed: {e}")

    # ── Nickname ──────────────────────────────────────────────────────────────

    @commands.command(aliases=["nick"])
    @commands.has_permissions(manage_nicknames=True)
    async def setnick(self, ctx: commands.Context, member: discord.Member, *, nickname: str):
        """Set a member's nickname. Usage: !setnick @user NewNickname"""
        try:
            old = member.display_name
            await member.edit(nick=nickname)
            embed = discord.Embed(
                title="📝 Nickname Changed",
                description=f"{member.mention}'s nickname updated",
                color=discord.Color.blue(),
            )
            embed.add_field(name="Before", value=old, inline=True)
            embed.add_field(name="After", value=nickname, inline=True)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed: {e}")

    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def resetnick(self, ctx: commands.Context, member: discord.Member):
        """Reset a member's nickname. Usage: !resetnick @user"""
        try:
            old = member.display_name
            await member.edit(nick=None)
            embed = discord.Embed(
                title="✅ Nickname Reset",
                description=f"{member.mention}'s nickname has been reset.",
                color=discord.Color.green(),
            )
            embed.add_field(name="Previous", value=old, inline=True)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed: {e}")

    # ── Roles ─────────────────────────────────────────────────────────────────

    @commands.command()
    async def getroles(self, ctx: commands.Context, member: discord.Member = None):
        """Get a member's roles. Usage: !getroles [@user]"""
        target = member or ctx.author
        roles = [r.mention for r in target.roles if r.name != "@everyone"]
        embed = discord.Embed(
            title=f"🎭 Roles for {target.display_name}",
            description=" ".join(roles) if roles else "No roles",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def addrole(self, ctx: commands.Context, member: discord.Member, *, role: discord.Role):
        """Add a role to a member. Usage: !addrole @user @Role"""
        if role in member.roles:
            return await ctx.send(f"{member.display_name} already has {role.name}!")
        try:
            await member.add_roles(role)
            embed = discord.Embed(
                title="➕ Role Added",
                description=f"{role.mention} added to {member.mention}",
                color=role.color,
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed: {e}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def removerole(self, ctx: commands.Context, member: discord.Member, *, role: discord.Role):
        """Remove a role from a member. Usage: !removerole @user @Role"""
        if role not in member.roles:
            return await ctx.send(f"{member.display_name} doesn't have {role.name}!")
        try:
            await member.remove_roles(role)
            embed = discord.Embed(
                title="➖ Role Removed",
                description=f"{role.mention} removed from {member.mention}",
                color=role.color,
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed: {e}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def createrole(self, ctx: commands.Context, name: str, color: str = None, *, reason: str = None):
        """Create a new role. Usage: !createrole <name> [hex color] [reason]"""
        try:
            role_color = discord.Color.default()
            if color:
                color = color.lstrip("#")
                role_color = discord.Color(int(color, 16))
            new_role = await ctx.guild.create_role(name=name, color=role_color, reason=reason)
            embed = discord.Embed(
                title="✅ Role Created",
                description=f"New role {new_role.mention} created",
                color=role_color,
            )
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            await ctx.send(embed=embed)
        except ValueError:
            await ctx.send("❌ Invalid color format. Use hex e.g. #FF0000")
        except Exception as e:
            await ctx.send(f"❌ Failed: {e}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def deleterole(self, ctx: commands.Context, *, role: discord.Role):
        """Delete a role. Usage: !deleterole @role"""
        try:
            name = role.name
            await role.delete()
            await ctx.send(f"✅ Role `{name}` deleted.")
        except Exception as e:
            await ctx.send(f"❌ Failed: {e}")

    # ── Lock / Unlock ─────────────────────────────────────────────────────────

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx: commands.Context, channel: discord.TextChannel = None, role: discord.Role = None):
        """Lock a channel. Usage: !lock [#channel] [@role]"""
        target_channel = channel or ctx.channel
        target_role = role or ctx.guild.default_role
        extra_roles = []
        if EXTRA_ROLES_LOCK_UNLOCK:
            r = ctx.guild.get_role(EXTRA_ROLES_LOCK_UNLOCK)
            if r:
                extra_roles.append(r)
        try:
            ow = target_channel.overwrites_for(target_role)
            ow.send_messages = False
            await target_channel.set_permissions(target_role, overwrite=ow)
            for er in extra_roles:
                if er != target_role:
                    eow = target_channel.overwrites_for(er)
                    eow.send_messages = False
                    await target_channel.set_permissions(er, overwrite=eow)
            label = "everyone" if target_role == ctx.guild.default_role else target_role.mention
            await ctx.send(f"🔒 {target_channel.mention} locked for {label}!")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to lock that channel!")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx: commands.Context, channel: discord.TextChannel = None, role: discord.Role = None):
        """Unlock a channel. Usage: !unlock [#channel] [@role]"""
        target_channel = channel or ctx.channel
        target_role = role or ctx.guild.default_role
        extra_roles = []
        if EXTRA_ROLES_LOCK_UNLOCK:
            r = ctx.guild.get_role(EXTRA_ROLES_LOCK_UNLOCK)
            if r:
                extra_roles.append(r)
        try:
            ow = target_channel.overwrites_for(target_role)
            ow.send_messages = None
            await target_channel.set_permissions(target_role, overwrite=ow)
            for er in extra_roles:
                if er != target_role:
                    eow = target_channel.overwrites_for(er)
                    eow.send_messages = None
                    await target_channel.set_permissions(er, overwrite=eow)
            label = "everyone" if target_role == ctx.guild.default_role else target_role.mention
            await ctx.send(f"🔓 {target_channel.mention} unlocked for {label}!")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to unlock that channel!")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    # ── Warn system ───────────────────────────────────────────────────────────

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Warn a member. Usage: !warn @user [reason]"""
        reason = reason[:512]
        data = get_warnings_data()
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        data.setdefault(guild_id, {}).setdefault(user_id, [])
        warning = {
            "moderator": ctx.author.id,
            "reason": reason,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        data[guild_id][user_id].append(warning)
        save_warnings_data(data)
        embed = discord.Embed(
            title="⚠️ Member Warned",
            description=f"{member.mention} warned by {ctx.author.mention}",
            color=discord.Color.orange(),
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Total Warnings", value=len(data[guild_id][user_id]), inline=False)
        await ctx.send(embed=embed)
        try:
            dm = discord.Embed(title=f"⚠️ You've been warned in {ctx.guild.name}", color=discord.Color.orange())
            dm.add_field(name="Reason", value=reason)
            dm.add_field(name="Moderator", value=ctx.author.mention)
            await member.send(embed=dm)
        except discord.Forbidden:
            pass

    @commands.command()
    async def warnings(self, ctx: commands.Context, member: discord.Member = None):
        """Check a member's warnings. Usage: !warnings [@user]"""
        target = member or ctx.author
        data = get_warnings_data()
        guild_id = str(ctx.guild.id)
        user_id = str(target.id)
        warns = data.get(guild_id, {}).get(user_id, [])
        if not warns:
            return await ctx.send(f"{target.display_name} has no warnings.")
        embed = discord.Embed(
            title=f"⚠️ Warnings for {target.display_name}",
            description=f"Total: {len(warns)}",
            color=discord.Color.orange(),
        )
        for i, w in enumerate(warns, 1):
            mod = ctx.guild.get_member(w["moderator"]) or f"ID:{w['moderator']}"
            ts = datetime.datetime.fromisoformat(w["timestamp"]).strftime("%Y-%m-%d %H:%M")
            embed.add_field(
                name=f"Warning #{i}",
                value=f"**Reason:** {w['reason']}\n**By:** {mod}\n**On:** {ts}",
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clearwarns(self, ctx: commands.Context, member: discord.Member):
        """Clear all warnings for a member. Usage: !clearwarns @user"""
        data = get_warnings_data()
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        if not data.get(guild_id, {}).get(user_id):
            return await ctx.send(f"{member.display_name} has no warnings to clear.")
        data[guild_id].pop(user_id)
        save_warnings_data(data)
        await ctx.send(embed=discord.Embed(
            title="✅ Warnings Cleared",
            description=f"All warnings for {member.mention} cleared.",
            color=discord.Color.green(),
        ))

    # ── Purge / Nuke / Clone ──────────────────────────────────────────────────

    @commands.command(aliases=["clear"])
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, amount: int = 10):
        """Delete messages from the channel (max 100). Usage: !purge [amount]"""
        if not 1 <= amount <= 100:
            return await ctx.send("❌ Provide a number between 1 and 100.")
        deleted = await ctx.channel.purge(limit=amount + 1)
        embed = discord.Embed(
            title="🗑️ Messages Purged",
            description=f"Deleted {len(deleted) - 1} messages.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed, delete_after=5)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def nuke(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Clone and delete a channel to remove all messages. Usage: !nuke [#channel]"""
        target = channel or ctx.channel
        confirm = await ctx.send(
            f"⚠️ Nuke {target.mention}? This deletes ALL messages! React ✅ to confirm."
        )
        await confirm.add_reaction("✅")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == "✅" and reaction.message.id == confirm.id

        try:
            await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
        except asyncio.TimeoutError:
            return await confirm.edit(content="🚫 Nuke cancelled.")

        try:
            new_ch = await target.clone(reason=f"Nuked by {ctx.author}")
            await target.delete(reason=f"Nuked by {ctx.author}")
            embed = discord.Embed(
                title="💥 Channel Nuked",
                description=f"Nuked by {ctx.author.mention}",
                color=discord.Color.red(),
            )
            embed.set_image(url="https://media.giphy.com/media/oe33xf3B50fsc/giphy.gif")
            await new_ch.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed: {e}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def clone(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Clone a channel. Usage: !clone [#channel]"""
        target = channel or ctx.channel
        try:
            new_ch = await target.clone()
            await ctx.send(f"✅ Cloned {target.mention} → {new_ch.mention}")
        except Exception as e:
            await ctx.send(f"❌ Failed: {e}")

    # ── Mute / Unmute ─────────────────────────────────────────────────────────

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Mute a member (creates Muted role if needed). Usage: !mute @user [reason]"""
        try:
            muted = discord.utils.get(ctx.guild.roles, name="Muted")
            if not muted:
                muted = await ctx.guild.create_role(name="Muted")
                for ch in ctx.guild.channels:
                    await ch.set_permissions(muted, send_messages=False, speak=False, add_reactions=False)
            await member.add_roles(muted, reason=reason)
            embed = discord.Embed(
                title="🔇 Member Muted",
                description=f"{member.mention} muted by {ctx.author.mention}",
                color=discord.Color.red(),
            )
            embed.add_field(name="Reason", value=reason)
            await ctx.send(embed=embed)
            try:
                dm = discord.Embed(title=f"🔇 Muted in {ctx.guild.name}", color=discord.Color.red())
                dm.add_field(name="Reason", value=reason)
                await member.send(embed=dm)
            except discord.Forbidden:
                pass
        except Exception as e:
            await ctx.send(f"❌ Failed: {e}")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def unmute(self, ctx: commands.Context, member: discord.Member):
        """Unmute a member. Usage: !unmute @user"""
        try:
            muted = discord.utils.get(ctx.guild.roles, name="Muted")
            if not muted or muted not in member.roles:
                return await ctx.send(f"{member.display_name} is not muted.")
            await member.remove_roles(muted)
            embed = discord.Embed(
                title="🔊 Member Unmuted",
                description=f"{member.mention} unmuted by {ctx.author.mention}",
                color=discord.Color.green(),
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Failed: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
