"""
plugins/slash/slash_cog.py
All slash (/) commands.
"""
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from config import BOT_OWNER


def is_owner_or_server_owner():
    async def predicate(interaction: discord.Interaction) -> bool:
        return (
            (BOT_OWNER and interaction.user.id == BOT_OWNER)
            or interaction.user == interaction.guild.owner
        )
    return app_commands.check(predicate)


class SlashCog(commands.Cog, name="Slash"):
    """⚡ Slash command equivalents."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── Info ──────────────────────────────────────────────────────────────────

    @app_commands.command(name="sc", description="Get bot info and GitHub link")
    async def sc(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Discord MultiBot",
            description="A multipurpose Discord bot with music, verification, and moderation tools",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="GitHub",
            value="[Visit GitHub](https://github.com/y-nabeelxd/Discord-MultiBot-py)",
            inline=False,
        )
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="Visit GitHub",
                style=discord.ButtonStyle.link,
                url="https://github.com/y-nabeelxd/Discord-MultiBot-py",
            )
        )
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="invite", description="Get the bot invite link")
    async def invite(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🤖 Bot Invite", color=discord.Color.blue())
        embed.add_field(
            name="Invite Link",
            value=f"[Click here](https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot%20applications.commands)",
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── Moderation ────────────────────────────────────────────────────────────

    @app_commands.command(name="move_all", description="Move all members to a voice channel")
    @app_commands.describe(channel="Target voice channel (defaults to yours)")
    @is_owner_or_server_owner()
    async def slash_move_all(self, interaction: discord.Interaction, channel: discord.VoiceChannel = None):
        if not channel and not interaction.user.voice:
            return await interaction.response.send_message("You're not in a voice channel!", ephemeral=True)
        target = channel or interaction.user.voice.channel
        await interaction.response.send_message(f"Move everyone to {target.mention}? Type **y** to confirm.")

        def check(m):
            return m.author == interaction.user and m.content.lower() == "y" and m.channel == interaction.channel

        try:
            msg = await self.bot.wait_for("message", timeout=30.0, check=check)
            try:
                await msg.delete()
            except Exception:
                pass
            await interaction.edit_original_response(content="Moving…")
            count = 0
            for member in interaction.guild.members:
                if member.voice and member.voice.channel and member.voice.channel != target:
                    try:
                        await member.move_to(target)
                        count += 1
                    except Exception:
                        pass
            await interaction.edit_original_response(content=f"✅ Moved {count} members to {target.mention}!")
        except asyncio.TimeoutError:
            await interaction.edit_original_response(content="Move cancelled.")

    @app_commands.command(name="move_user", description="Move a user to a voice channel")
    @app_commands.describe(user="User to move", channel="Target channel")
    @is_owner_or_server_owner()
    async def slash_move_user(self, interaction: discord.Interaction, user: discord.Member, channel: discord.VoiceChannel = None):
        if not channel and not interaction.user.voice:
            return await interaction.response.send_message("Specify a channel or join one!", ephemeral=True)
        target = channel or interaction.user.voice.channel
        if not user.voice:
            return await interaction.response.send_message(f"{user.mention} is not in a voice channel!", ephemeral=True)
        try:
            await user.move_to(target)
            await interaction.response.send_message(f"✅ Moved {user.mention} to {target.mention}")
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed: {e}", ephemeral=True)

    @app_commands.command(name="moveme", description="Move yourself to a voice channel")
    @app_commands.describe(channel="Target voice channel")
    @is_owner_or_server_owner()
    async def slash_moveme(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        if not interaction.user.voice:
            return await interaction.response.send_message("You're not in a voice channel!", ephemeral=True)
        try:
            await interaction.user.move_to(channel)
            await interaction.response.send_message(f"✅ Moved you to {channel.mention}")
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed: {e}", ephemeral=True)

    @app_commands.command(name="move_role", description="Move all members with a role to a voice channel")
    @app_commands.describe(role="The role", channel="Target channel")
    @is_owner_or_server_owner()
    async def slash_move_role(self, interaction: discord.Interaction, role: discord.Role, channel: discord.VoiceChannel = None):
        if not channel and not interaction.user.voice:
            return await interaction.response.send_message("Specify a channel or join one!", ephemeral=True)
        target = channel or interaction.user.voice.channel
        await interaction.response.send_message(f"Move all {role.mention} members to {target.mention}? Type **y**.")

        def check(m):
            return m.author == interaction.user and m.content.lower() == "y" and m.channel == interaction.channel

        try:
            msg = await self.bot.wait_for("message", timeout=30.0, check=check)
            try:
                await msg.delete()
            except Exception:
                pass
            count = 0
            for member in interaction.guild.members:
                if role in member.roles and member.voice and member.voice.channel != target:
                    try:
                        await member.move_to(target)
                        count += 1
                    except Exception:
                        pass
            await interaction.edit_original_response(content=f"✅ Moved {count} {role.mention} members!")
        except asyncio.TimeoutError:
            await interaction.edit_original_response(content="Move cancelled.")


async def setup(bot: commands.Bot):
    await bot.add_cog(SlashCog(bot))
