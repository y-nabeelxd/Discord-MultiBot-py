"""
plugins/ticket/ticket_cog.py
Support Ticket System using Discord UI.
"""
import discord
from discord.ext import commands

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="ticket_close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.channel.name.startswith("ticket-"):
            return await interaction.response.send_message("This is not a ticket channel!", ephemeral=True)
            
        await interaction.response.defer()
        await interaction.followup.send("Closing ticket in 5 seconds...")
        import asyncio
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except discord.NotFound:
            pass
        except Exception as e:
            await interaction.followup.send(f"Failed to close ticket: {e}")


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cooldowns = {}

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.primary, custom_id="ticket_create", emoji="🎫")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        import time
        now = time.time()
        # 60s cooldown per user to prevent spam
        if user.id in self.cooldowns and now - self.cooldowns[user.id] < 60:
            return await interaction.response.send_message(f"Please wait before creating another ticket. ({int(60 - (now - self.cooldowns[user.id]))}s left)", ephemeral=True)
            
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        
        # Check if user already has a ticket
        existing_ticket = discord.utils.get(guild.channels, name=f"ticket-{user.name.lower()}")
        if existing_ticket:
            return await interaction.followup.send(f"You already have an open ticket: {existing_ticket.mention}")

        self.cooldowns[user.id] = now
        
        # Set permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        category = interaction.channel.category

        try:
            ticket_channel = await guild.create_text_channel(
                name=f"ticket-{user.name}",
                category=category,
                overwrites=overwrites,
                reason=f"Ticket created by {user.name}"
            )
            
            await interaction.followup.send(f"Ticket created! {ticket_channel.mention}")
            
            embed = discord.Embed(
                title="🎫 Support Ticket",
                description=f"Welcome {user.mention}!\nPlease describe your issue and staff will be with you shortly.\n\nClick the button below to close this ticket.",
                color=discord.Color.blue()
            )
            await ticket_channel.send(content=user.mention, embed=embed, view=TicketControlView())
            
        except Exception as e:
            await interaction.followup.send(f"Failed to create ticket: {e}")


class TicketCog(commands.Cog, name="Ticket"):
    """🎫 Support Ticket System."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Re-add the persistent views if bot restarts
        self.bot.add_view(TicketPanelView())
        self.bot.add_view(TicketControlView())

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def ticket(self, ctx: commands.Context, action: str = None):
        """Ticket system management. Usage: !ticket setup | !ticket close"""
        if action == "setup":
            embed = discord.Embed(
                title="🎫 Support Tickets",
                description="Click the **Create Ticket** button below to open a private channel with the staff team.",
                color=discord.Color.blue()
            )
            embed.set_footer(text="Please do not open a ticket without a valid reason.")
            await ctx.send(embed=embed, view=TicketPanelView())
            # Delete the setup command message if possible
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass
                
        elif action == "close":
            if not ctx.channel.name.startswith("ticket-"):
                return await ctx.send("❌ This command can only be used in a ticket channel!")
            await ctx.send("Closing ticket in 5 seconds...")
            import asyncio
            await asyncio.sleep(5)
            try:
                await ctx.channel.delete()
            except Exception as e:
                await ctx.send(f"❌ Failed to close ticket: {e}")
        else:
            await ctx.send(f"Usage: `{ctx.prefix}ticket setup` or `{ctx.prefix}ticket close`")


async def setup(bot: commands.Bot):
    await bot.add_cog(TicketCog(bot))
