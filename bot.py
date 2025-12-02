import os
import re
import yt_dlp
import discord
import asyncio
import random
import datetime
import logging
from samp_query import Client
from discord.ext import commands
from discord import app_commands
from urllib.parse import quote
import json
import requests
import sys
import time
from datetime import timedelta
import aiohttp
import socket
import struct

# --- Configuration ---
VERIFICATION_FIVEM = False # If set True FiveM Verification will Enable
FIVEM_VERIFICATION_DISCORD_REQUIRED = False  # Set to True if Discord ID must match in-game
FIVEM_ROLE_ID = None # Set Role ID for FiveM Verified.
FIVEM_SERVER = None  # Set your FiveM server "IP:PORT"
VERIFICATION_ROBLOX = False  # If set True Roblox Verification will Enable
ROBLOX_ROLE_ID = None # Set Role ID for Roblox Verified.
VERIFICATION_SAMP = False # If set True SA:MP Verification will Enable (Currently under maintenance)
SAMP_ROLE_ID = None # Set Role ID for SA:MP Verified.
SAMP_SERVER_IP = None # Set SA:MP IP using ""
SAMP_SERVER_PORT = None # Set SA:MP PORT using ""
VERIFICATION_VALO = False # If set True Valorant Verification will Enable (Currently under maintenance)
RIOT_API_KEY = None
VALORANT_ROLE_ID = None # Set Role ID for Valorant Verified.
REGIONS = ["americas", "europe", "asia"]  # For Valorant API
CHANGE_NICKNAME = False # If you set it True it will change Nickname after Verification.
BOT_OWNER = None  # Bot Owner ID
EXTRA_ROLES_LOCK_UNLOCK = None  # Set this if you want to more role to lock/unlock
GAME_PREFIX = "owo"  # Can be changed to "XD" or any other prefix
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY') or 'your_api_key_here' # Get API Key from here: https://home.openweathermap.org/api_keys
COINFLIP_GIF = "https://cdn.dribbble.com/userupload/20764551/file/original-ec7c7b25323fea450739f13b38db735f.gif" # Replace If you have any other Gif
PREFIX = "!" # You can change Prefix from here.
intents = discord.Intents.all()
warnings_db = {}
PERMA_VC = {}

if not os.path.exists('db'):
    os.makedirs('db')

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def format_duration(seconds):
    if isinstance(seconds, str):
        return seconds
    try:
        seconds = int(seconds)
        return str(timedelta(seconds=seconds))
    except:
        return "N/A"

def beautiful_print(message, box_char="═", padding=1):
    terminal_width = os.get_terminal_size().columns
    box_line = box_char * terminal_width
    padding_lines = "\n" * padding
    message_lines = message.split('\n')
    
    centered_message = []
    for line in message_lines:
        if line.strip():
            centered_line = line.center(terminal_width)
            centered_message.append(centered_line)
        else:
            centered_message.append('')
    
    print(f"{padding_lines}{box_line}\n" + "\n".join(centered_message) + f"\n{box_line}{padding_lines}")
    
def format_uptime(seconds):
    """Convert seconds to human-readable format (days, hours, minutes)"""
    if seconds is None or isinstance(seconds, str) and not seconds.isdigit():
        return "N/A"
    
    try:
        seconds = int(seconds)
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or not parts:
            parts.append(f"{minutes}m")
            
        return " ".join(parts)
    except:
        return "N/A"

async def query_samp(ip: str, port: int):
    """Query SA-MP server using samp-query library"""
    try:
        client = Client(ip=ip, port=port)
        info = await client.info()
        players = await client.players()
        return [player.name for player in players.players]
    except Exception as e:
        print(f"Error querying SA-MP server: {str(e)}")
        return None

async def get_valorant_account(username: str, tag: str):
    if not RIOT_API_KEY:
        return None
        
    async with aiohttp.ClientSession() as session:
        for region in REGIONS:
            url = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{username}/{tag}"
            headers = {"X-Riot-Token": RIOT_API_KEY}
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
    return None

async def get_fivem_players(server_address=None):
    """Get FiveM players with enhanced information"""
    server = server_address or FIVEM_SERVER
    if not server:
        return []
        
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{server}/players.json", 
                                 headers={"Accept": "application/json"}) as resp:
                players = await resp.json(content_type=None) if resp.status == 200 else []
                    
            async with session.get(f"http://{server}/info.json",
                                 headers={"Accept": "application/json"}) as resp:
                info = await resp.json(content_type=None) if resp.status == 200 else {}
                    
            async with session.get(f"http://{server}/dynamic.json",
                                 headers={"Accept": "application/json"}) as resp:
                dynamic = await resp.json(content_type=None) if resp.status == 200 else {}
                    
            for player in players:
                player['server_info'] = info
                player['server_dynamic'] = dynamic
                
            return players
    except Exception as e:
        print(f"Error getting FiveM players: {e}")
        return []

async def get_fivem_player_by_identifier(identifier, server_address=None):
    """Get a FiveM player by identifier (name or ID)"""
    players = await get_fivem_players(server_address)
    if not players:
        return None
    
    for player in players:
        if str(player.get('id')) == str(identifier):
            return player
    
    for player in players:
        if player.get('name', '').lower() == str(identifier).lower():
            return player
    
    return None

async def get_fivem_server_info(server_address=None):
    """Get detailed FiveM server information"""
    server = server_address or FIVEM_SERVER
    if not server:
        return None
        
    try:
        async with aiohttp.ClientSession() as session:
            info_url = f"http://{server}/info.json"
            dynamic_url = f"http://{server}/dynamic.json"
            players_url = f"http://{server}/players.json"
            
            headers = {"Accept": "application/json"}
            
            info, dynamic, players = await asyncio.gather(
                session.get(info_url, headers=headers),
                session.get(dynamic_url, headers=headers),
                session.get(players_url, headers=headers)
            )
            
            info_data = await info.json(content_type=None) if info.status == 200 else {}
            dynamic_data = await dynamic.json(content_type=None) if dynamic.status == 200 else {}
            players_data = await players.json(content_type=None) if players.status == 200 else []
            
            uptime = info_data.get('vars', {}).get('Uptime')
            
            if uptime is not None:
                uptime = format_uptime(uptime)
            else:
                uptime = "N/A"
            
            return {
                'info': info_data,
                'dynamic': dynamic_data,
                'players': players_data,
                'status': 'online' if info.status == 200 else 'offline',
                'uptime': uptime
            }
    except Exception as e:
        print(f"Error getting FiveM server info: {e}")
        return None

async def get_roblox_profile(username: str):
    """Get Roblox profile information"""
    try:
        url = "https://users.roblox.com/v1/usernames/users"
        async with aiohttp.ClientSession() as session:
            resp = await session.post(url, json={"usernames": [username]})
            resp_data = await resp.json()
        
            if "data" not in resp_data or not resp_data["data"]:
                return None
                
            user_id = resp_data["data"][0]["id"]
            
            profile_url = f"https://users.roblox.com/v1/users/{user_id}"
            async with session.get(profile_url) as profile_resp:
                profile_data = await profile_resp.json()
            
            avatar_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png"
            async with session.get(avatar_url) as avatar_resp:
                avatar_data = await avatar_resp.json()
            avatar = avatar_data["data"][0]["imageUrl"]
            
            friends_url = f"https://friends.roblox.com/v1/users/{user_id}/friends/count"
            async with session.get(friends_url) as friends_resp:
                friends_data = await friends_resp.json()
            friends_count = friends_data.get("count", 0)
            
            created = profile_data.get("created")
            if created:
                created = datetime.datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%B %d, %Y")
            
            return {
                "id": user_id,
                "username": profile_data.get("name"),
                "displayName": profile_data.get("displayName"),
                "description": profile_data.get("description", ""),
                "created": created,
                "avatar": avatar,
                "friends": friends_count
            }
    except Exception as e:
        print(f"Error getting Roblox profile: {e}")
        return None

async def send_to_owner(guild: discord.Guild, embed: discord.Embed):
    try:
        await guild.owner.send(embed=embed)
    except Exception as e:
        print(f"Could not DM owner: {e}")

def get_warnings_data():
    try:
        with open('db/warnings.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_warnings_data(data):
    with open('db/warnings.json', 'w') as f:
        json.dump(data, f, indent=4)

def get_owo_data():
    try:
        with open('db/owo_data.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_owo_data(data):
    with open('db/owo_data.json', 'w') as f:
        json.dump(data, f, indent=4)

def get_fivem_verification_data():
    try:
        with open('db/fivem.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_fivem_verification_data(data):
    with open('db/fivem.json', 'w') as f:
        json.dump(data, f, indent=4)

discord.utils.setup_logging(level=logging.INFO, root=False)
logger = logging.getLogger('discord')
logger.setLevel(logging.WARNING)

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fivem_status_tasks = {}
    
    async def on_connect(self):
        clear_console()
        beautiful_print("🔌 Connecting to Discord Bot...", "─")
    
    async def on_ready(self):
        clear_console()
        login_msg = f"""
🤖 Connected to {self.user.name}
🆔 ID: {self.user.id}
⚡ Prefix: "{PREFIX}"
🔒 Verification Systems:
  • Valorant: {'✅ Enabled' if VERIFICATION_VALO and RIOT_API_KEY and VALORANT_ROLE_ID else '❌ Disabled'}
  • FiveM: {'✅ Enabled' if VERIFICATION_FIVEM and FIVEM_SERVER and FIVEM_ROLE_ID else '❌ Disabled'}
  • SA-MP: {'✅ Enabled' if VERIFICATION_SAMP and SAMP_SERVER_IP and SAMP_SERVER_PORT and SAMP_ROLE_ID else '❌ Disabled'}
  • Roblox: {'✅ Enabled' if VERIFICATION_ROBLOX and ROBLOX_ROLE_ID else '❌ Disabled'}
        """
        beautiful_print(login_msg, "═")
        await self.change_presence(activity=discord.Game(name=f"Music | {PREFIX}help"))
        
        # Sync slash commands with better error handling
        try:
            synced = await self.tree.sync()
            beautiful_print(f"✅ Synced {len(synced)} slash commands", "─")
        except Exception as e:
            beautiful_print(f"❌ Failed to sync slash commands: {e}", "!")
            # Try to sync with individual command error handling
            await self.sync_commands_with_retry()
    
    async def sync_commands_with_retry(self):
        """Sync commands individually to identify problematic ones"""
        beautiful_print("🔄 Attempting to sync commands individually...", "─")
        successful = 0
        failed = 0
        
        for command in self.tree.get_commands():
            try:
                await self.tree.sync_command(command)
                beautiful_print(f"✅ Synced: /{command.name}", "─")
                successful += 1
            except Exception as e:
                beautiful_print(f"❌ Failed to sync /{command.name}: {e}", "!")
                failed += 1
        
        beautiful_print(f"📊 Sync Results: {successful} successful, {failed} failed", "─")

bot = MyBot(command_prefix=PREFIX, intents=intents, help_command=None)

queues = {}
current_players = {}
song_queues = {}
idle_timers = {}

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extract_flat': True,
    'verbose': False
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -loglevel error',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = format_duration(data.get('duration'))
        self.thumbnail = data.get('thumbnail')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]
            
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

async def check_empty_vc(guild_id):
    if guild_id not in current_players:
        return True
    
    voice_client = current_players[guild_id]['voice_client']
    if not voice_client or not voice_client.is_connected():
        return True
    
    if len(voice_client.channel.members) == 1:
        await voice_client.disconnect()
        if guild_id in current_players:
            if 'control_message' in current_players[guild_id]:
                try:
                    await current_players[guild_id]['control_message'].delete()
                except:
                    pass
            del current_players[guild_id]
        if guild_id in song_queues:
            song_queues[guild_id].clear()
        return True
    return False

async def start_idle_timer(guild_id):
    if guild_id in idle_timers:
        idle_timers[guild_id].cancel()
    
    async def idle_task():
        try:
            start_time = time.time()
            while time.time() - start_time < 30:
                if guild_id in current_players and current_players[guild_id]['voice_client'].is_playing():
                    return
                await asyncio.sleep(1)
            
            if guild_id in current_players:
                voice_client = current_players[guild_id]['voice_client']
                if voice_client and not voice_client.is_playing():
                    await check_empty_vc(guild_id)
        except Exception as e:
            print(f"Error in idle timer: {e}")
    
    idle_timers[guild_id] = asyncio.create_task(idle_task())

# --- Slash Commands ---

@bot.tree.command(name="sc", description="Get bot information and GitHub link")
async def sc(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Discord MultiBot",
        description="A multipurpose Discord bot with music, verification, and moderation tools",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="GitHub Repository",
        value="[Visit GitHub](https://github.com/y-nabeelxd/Discord-MultiBot-py)",
        inline=False
    )
    view = discord.ui.View()
    view.add_item(discord.ui.Button(
        label="Visit GitHub",
        style=discord.ButtonStyle.link,
        url="https://github.com/y-nabeelxd/Discord-MultiBot-py"
    ))
    await interaction.response.send_message(embed=embed, view=view)

def is_owner_or_server_owner():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.id == BOT_OWNER or interaction.user == interaction.guild.owner
    return app_commands.check(predicate)

@bot.tree.command(name="kick", description="Kick a user from the server")
@app_commands.describe(user="The user to kick", reason="Reason for kicking")
@is_owner_or_server_owner()
async def slash_kick(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if user == interaction.user:
        await interaction.response.send_message("You cannot kick yourself!", ephemeral=True)
        return
    if user == interaction.guild.owner:
        await interaction.response.send_message("You cannot kick the server owner!", ephemeral=True)
        return
    if user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
        await interaction.response.send_message("You cannot kick someone with a higher or equal role!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="👢 Member Kicked",
        description=f"{user.mention} has been kicked by {interaction.user.mention}",
        color=discord.Color.orange()
    )
    embed.add_field(name="Reason", value=reason, inline=False)
    
    try:
        dm_embed = discord.Embed(
            title=f"👢 You've been kicked from {interaction.guild.name}",
            color=discord.Color.orange()
        )
        dm_embed.add_field(name="Reason", value=reason, inline=False)
        await user.send(embed=dm_embed)
    except:
        pass
    
    await user.kick(reason=reason)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ban", description="Ban a user from the server")
@app_commands.describe(user="The user to ban", reason="Reason for banning")
@is_owner_or_server_owner()
async def slash_ban(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if user == interaction.user:
        await interaction.response.send_message("You cannot ban yourself!", ephemeral=True)
        return
    if user == interaction.guild.owner:
        await interaction.response.send_message("You cannot ban the server owner!", ephemeral=True)
        return
    if user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
        await interaction.response.send_message("You cannot ban someone with a higher or equal role!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="🔨 Member Banned",
        description=f"{user.mention} has been banned by {interaction.user.mention}",
        color=discord.Color.red()
    )
    embed.add_field(name="Reason", value=reason, inline=False)
    
    try:
        dm_embed = discord.Embed(
            title=f"🔨 You've been banned from {interaction.guild.name}",
            color=discord.Color.red()
        )
        dm_embed.add_field(name="Reason", value=reason, inline=False)
        await user.send(embed=dm_embed)
    except:
        pass
    
    await user.ban(reason=reason)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="clear", description="Clear messages from the channel")
@app_commands.describe(amount="Number of messages to clear")
@is_owner_or_server_owner()
async def slash_clear(interaction: discord.Interaction, amount: int):
    if amount <= 0 or amount > 100:
        await interaction.response.send_message("Please provide a number between 1 and 100.", ephemeral=True)
        return
    
    await interaction.response.defer()
    deleted = await interaction.channel.purge(limit=amount + 1)  # +1 to include the command message
    
    embed = discord.Embed(
        title="🗑️ Messages Cleared",
        description=f"Deleted {len(deleted) - 1} messages.",
        color=discord.Color.green()
    )
    await interaction.followup.send(embed=embed, delete_after=5)

@bot.tree.command(name="invite", description="Get the bot invite link")
async def slash_invite(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Bot Invite",
        description="Invite this bot to your server!",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="Invite Link",
        value=f"[Click here to invite](https://discord.com/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot%20applications.commands)",
        inline=False
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="move_all", description="Move all members to a voice channel")
@app_commands.describe(channel="The voice channel to move everyone to")
@is_owner_or_server_owner()
async def slash_move_all(interaction: discord.Interaction, channel: discord.VoiceChannel = None):
    if not channel and not interaction.user.voice:
        await interaction.response.send_message("You are not in a voice channel! Please specify a channel or join one.", ephemeral=True)
        return
    
    target_channel = channel or interaction.user.voice.channel
    
    # Send confirmation message
    await interaction.response.send_message(f"Are you sure that you want to move all users to {target_channel.mention}? Type **(y)** to confirm")
    
    def check(m):
        return m.author == interaction.user and m.content.lower() == 'y' and m.channel == interaction.channel
    
    try:
        msg = await bot.wait_for('message', timeout=30.0, check=check)
        # Delete the confirmation message
        try:
            await msg.delete()
        except:
            pass
        
        # Edit original message to show progress
        await interaction.edit_original_response(content="Moving all members...")
        
        moved_count = 0
        for member in interaction.guild.members:
            if member.voice and member.voice.channel and member.voice.channel != target_channel:
                try:
                    await member.move_to(target_channel)
                    moved_count += 1
                except:
                    pass
        
        await interaction.edit_original_response(content=f"** All members are being moved!** (Moved {moved_count} members)")
        
    except asyncio.TimeoutError:
        await interaction.edit_original_response(content="Move operation cancelled.")

@bot.tree.command(name="move_user", description="Move a user to a voice channel")
@app_commands.describe(user="The user to move", channel="The voice channel to move to")
@is_owner_or_server_owner()
async def slash_move_user(interaction: discord.Interaction, user: discord.Member, channel: discord.VoiceChannel = None):
    if not channel and not interaction.user.voice:
        await interaction.response.send_message("You are not in a voice channel! Please specify a channel or join one.", ephemeral=True)
        return
    
    target_channel = channel or interaction.user.voice.channel
    
    if not user.voice:
        await interaction.response.send_message(f"{user.mention} is not in a voice channel!", ephemeral=True)
        return
    
    try:
        await user.move_to(target_channel)
        await interaction.response.send_message(f"Moved {user.mention} to {target_channel.mention}")
    except Exception as e:
        await interaction.response.send_message(f"Failed to move user: {e}", ephemeral=True)

@bot.tree.command(name="moveme", description="Move yourself to a voice channel")
@app_commands.describe(channel="The voice channel to move to")
@is_owner_or_server_owner()
async def slash_moveme(interaction: discord.Interaction, channel: discord.VoiceChannel):
    if not interaction.user.voice:
        await interaction.response.send_message("You are not in a voice channel!", ephemeral=True)
        return
    
    try:
        await interaction.user.move_to(channel)
        await interaction.response.send_message(f"Moved you to {channel.mention}")
    except Exception as e:
        await interaction.response.send_message(f"Failed to move: {e}", ephemeral=True)

@bot.tree.command(name="move_role", description="Move all members with a role to a voice channel")
@app_commands.describe(role="The role to move", channel="The voice channel to move to")
@is_owner_or_server_owner()
async def slash_move_role(interaction: discord.Interaction, role: discord.Role, channel: discord.VoiceChannel = None):
    if not channel and not interaction.user.voice:
        await interaction.response.send_message("You are not in a voice channel! Please specify a channel or join one.", ephemeral=True)
        return
    
    target_channel = channel or interaction.user.voice.channel
    
    # Send confirmation message
    await interaction.response.send_message(f"Are you sure that you want to move all {role.mention} given users? Type **(y)** to confirm")
    
    def check(m):
        return m.author == interaction.user and m.content.lower() == 'y' and m.channel == interaction.channel
    
    try:
        msg = await bot.wait_for('message', timeout=30.0, check=check)
        # Delete the confirmation message
        try:
            await msg.delete()
        except:
            pass
        
        # Edit original message to show progress
        await interaction.edit_original_response(content="Moving the all role members...")
        
        moved_count = 0
        for member in interaction.guild.members:
            if role in member.roles and member.voice and member.voice.channel != target_channel:
                try:
                    await member.move_to(target_channel)
                    moved_count += 1
                except:
                    pass
        
        await interaction.edit_original_response(content=f"** All {role.mention} members are being moved!** (Moved {moved_count} members)")
        
    except asyncio.TimeoutError:
        await interaction.edit_original_response(content="Move operation cancelled.")

@bot.tree.command(name="role_give", description="Give a role to a user")
@app_commands.describe(user="The user to give the role to", role="The role to give")
@is_owner_or_server_owner()
async def slash_role_give(interaction: discord.Interaction, user: discord.Member, role: discord.Role):
    if role in user.roles:
        await interaction.response.send_message(f"{user.mention} already has the {role.mention} role!", ephemeral=True)
        return
    
    try:
        await user.add_roles(role)
        embed = discord.Embed(
            title="➕ Role Added",
            description=f"{role.mention} has been added to {user.mention}",
            color=role.color
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"Failed to add role: {e}", ephemeral=True)

@bot.tree.command(name="role_remove", description="Remove a role from a user")
@app_commands.describe(user="The user to remove the role from", role="The role to remove")
@is_owner_or_server_owner()
async def slash_role_remove(interaction: discord.Interaction, user: discord.Member, role: discord.Role):
    if role not in user.roles:
        await interaction.response.send_message(f"{user.mention} doesn't have the {role.mention} role!", ephemeral=True)
        return
    
    try:
        await user.remove_roles(role)
        embed = discord.Embed(
            title="➖ Role Removed",
            description=f"{role.mention} has been removed from {user.mention}",
            color=role.color
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"Failed to remove role: {e}", ephemeral=True)

@bot.tree.command(name="setnick", description="Set a user's nickname")
@app_commands.describe(new_name="The new nickname", user="The user to set nickname for")
@is_owner_or_server_owner()
async def slash_setnick(interaction: discord.Interaction, new_name: str, user: discord.Member = None):
    target_user = user or interaction.user
    
    try:
        old_nick = target_user.display_name
        await target_user.edit(nick=new_name)
        embed = discord.Embed(
            title="📝 Nickname Changed",
            description=f"{target_user.mention}'s nickname has been updated",
            color=discord.Color.blue()
        )
        embed.add_field(name="Before", value=old_nick, inline=True)
        embed.add_field(name="After", value=new_name, inline=True)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"Failed to change nickname: {e}", ephemeral=True)

@bot.tree.command(name="unban", description="Unban a user")
@app_commands.describe(user="The username or ID of the user to unban")
@is_owner_or_server_owner()
async def slash_unban(interaction: discord.Interaction, user: str):
    try:
        banned_users = [ban async for ban in interaction.guild.bans()]
        
        for ban_entry in banned_users:
            if user.lower() in ban_entry.user.name.lower() or user == str(ban_entry.user.id):
                await interaction.guild.unban(ban_entry.user)
                embed = discord.Embed(
                    title="✅ User Unbanned",
                    description=f"{ban_entry.user.mention} has been unbanned by {interaction.user.mention}",
                    color=discord.Color.green()
                )
                await interaction.response.send_message(embed=embed)
                return
        
        await interaction.response.send_message("User not found in ban list!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Failed to unban user: {e}", ephemeral=True)

# --- Music System ---

class SongSelect(discord.ui.Select):
    def __init__(self, results, ctx):
        self.results = results
        self.ctx = ctx
        
        options = [
            discord.SelectOption(
                label=f"{idx+1}. {video['title'][:90]}",
                description=f"{video.get('duration', 'N/A')}",
                value=str(idx)
            ) for idx, video in enumerate(results[:10])
        ]
        
        super().__init__(
            placeholder="Select a song to play...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("You didn't request this song selection!", ephemeral=True)
        
        selected = int(self.values[0])
        video_url = self.results[selected]['url']
        song_title = self.results[selected]['title']
        
        await interaction.response.defer()
        await interaction.message.delete()
        
        voice_client = self.ctx.voice_client
        
        if self.ctx.guild.id not in song_queues:
            song_queues[self.ctx.guild.id] = []
        
        if voice_client.is_playing() or voice_client.is_paused():
            song_queues[self.ctx.guild.id].append({'url': video_url, 'title': song_title})
            await self.ctx.send(f"Added to queue: **{song_title}**")
        else:
            await play_song(self.ctx, video_url, song_title)

class SongSelectView(discord.ui.View):
    def __init__(self, results, ctx, timeout=60):
        super().__init__(timeout=timeout)
        self.add_item(SongSelect(results, ctx))
    
    async def on_timeout(self):
        try:
            await self.message.delete()
        except:
            pass

class ControlButtons(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx
    
    @discord.ui.button(label="Pause", style=discord.ButtonStyle.primary, emoji="⏸️")
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("⏸ Playback paused", ephemeral=True)
        else:
            await interaction.response.send_message("Nothing is playing!", ephemeral=True)
    
    @discord.ui.button(label="Resume", style=discord.ButtonStyle.primary, emoji="▶️")
    async def resume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message("▶ Playback resumed", ephemeral=True)
        else:
            await interaction.response.send_message("Playback is not paused!", ephemeral=True)
    
    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary, emoji="⏭️")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
            voice_client.stop()
            await interaction.response.send_message("⏭️ Song skipped", ephemeral=True)
            await play_next(self.ctx)
        else:
            await interaction.response.send_message("Nothing is playing!", ephemeral=True)
    
    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="🛑")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client:
            if interaction.guild.id in song_queues:
                song_queues[interaction.guild.id].clear()
            if interaction.guild.id in current_players:
                if 'control_message' in current_players[interaction.guild.id]:
                    try:
                        await current_players[interaction.guild.id]['control_message'].delete()
                    except:
                        pass
                del current_players[interaction.guild.id]
            await voice_client.disconnect()
            await interaction.response.send_message("⏹ Playback stopped and queue cleared", ephemeral=True)
        else:
            await interaction.response.send_message("I'm not in a voice channel!", ephemeral=True)

async def play_next(ctx):
    if ctx.guild.id in song_queues and song_queues[ctx.guild.id]:
        next_song = song_queues[ctx.guild.id].pop(0)
        await play_song(ctx, next_song['url'], next_song['title'])
    else:
        await start_idle_timer(ctx.guild.id)

async def play_song(ctx, url, title):
    voice_client = ctx.voice_client
    
    if ctx.guild.id in idle_timers:
        idle_timers[ctx.guild.id].cancel()
    
    try:
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        
        current_players[ctx.guild.id] = {
            'voice_client': voice_client,
            'player': player,
            'ctx': ctx,
            'last_activity': time.time()
        }
        
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"[{player.title}]({url})",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=player.thumbnail)
        
        if player.duration:
            embed.add_field(name="Duration", value=player.duration, inline=True)
            
        view = ControlButtons(ctx)
        control_message = await ctx.send(embed=embed, view=view)
        
        current_players[ctx.guild.id]['control_message'] = control_message
        
        def after_playing(error):
            if error:
                print(f'Player error: {error}')
            asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
            
        voice_client.play(player, after=after_playing)
        
    except Exception as e:
        await ctx.send(f"Error playing song: {e}")
        await play_next(ctx)

def search_youtube(query):
    search_url = f"https://www.youtube.com/results?search_query={quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(search_url, headers=headers)
        if response.status_code != 200:
            print("Failed to fetch YouTube results")
            return []
        
        html = response.text
        initial_data = {}
        try:
            start = html.index('var ytInitialData = ') + len('var ytInitialData = ')
            end = html.index('};</script>', start) + 1
            json_str = html[start:end]
            initial_data = json.loads(json_str)
        except (ValueError, json.JSONDecodeError) as e:
            print("Failed to parse YouTube data:", e)
            return []
        
        videos = []
        contents = initial_data.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {}).get('sectionListRenderer', {}).get('contents', [{}])[0].get('itemSectionRenderer', {}).get('contents', [])
        
        for content in contents:
            if 'videoRenderer' in content:
                video = content['videoRenderer']
                video_id = video.get('videoId')
                title = video.get('title', {}).get('runs', [{}])[0].get('text')
                duration_text = video.get('lengthText', {}).get('simpleText', '')
                
                if video_id and title:
                    videos.append({
                        'title': title,
                        'url': f'https://www.youtube.com/watch?v={video_id}',
                        'duration': duration_text,
                        'thumbnail': f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg'
                    })
                if len(videos) >= 10:
                    break
        return videos
    except Exception as e:
        print(f"Error searching YouTube: {e}")
        return []

@bot.command(aliases=['p'])
async def play(ctx, *, query: str):
    """Play a song or add to queue. Usage: !play <song name/url>"""
    voice_client = ctx.voice_client
    
    if not ctx.author.voice:
        await ctx.send("You need to be in a voice channel to play music!")
        return
    
    if voice_client and voice_client.is_connected():
        if voice_client.channel != ctx.author.voice.channel:
            await voice_client.move_to(ctx.author.voice.channel)
    else:
        voice_client = await ctx.author.voice.channel.connect()
    
    if ctx.guild.id in idle_timers:
        idle_timers[ctx.guild.id].cancel()
    
    results = search_youtube(query)
    if not results:
        await ctx.send("No results found!")
        return
    
    embed = discord.Embed(title="🔍 Search Results", description=f"Results for: {query}", color=0x00ff00)
    for idx, video in enumerate(results[:10], 1):
        embed.add_field(
            name=f"{idx}. {video['title']}",
            value=f"Duration: {video.get('duration', 'N/A')}",
            inline=False
        )
    
    view = SongSelectView(results, ctx)
    view.message = await ctx.send(embed=embed, view=view)

@bot.command()
async def skip(ctx):
    """Skip the current song. Usage: !skip"""
    voice_client = ctx.voice_client
    if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
        voice_client.stop()
        await ctx.send("⏭️ Song skipped")
        await play_next(ctx)
    else:
        await ctx.send("Nothing is playing to skip!")

@bot.command()
async def queue(ctx):
    """Show the current queue. Usage: !queue"""
    if ctx.guild.id in song_queues and song_queues[ctx.guild.id]:
        queue_list = [f"{idx+1}. {song['title']}" for idx, song in enumerate(song_queues[ctx.guild.id])]
        embed = discord.Embed(
            title="🎶 Current Queue",
            description="\n".join(queue_list),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send("The queue is empty.")

@bot.command()
async def clearqueue(ctx):
    """Clear the current queue. Usage: !clearqueue"""
    if ctx.guild.id in song_queues:
        song_queues[ctx.guild.id].clear()
        await ctx.send("Queue cleared!")
    else:
        await ctx.send("The queue is already empty.")

@bot.command()
async def pause(ctx):
    """Pause the current song. Usage: !pause"""
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("⏸ Playback paused")
    else:
        await ctx.send("Nothing is playing!")

@bot.command()
async def resume(ctx):
    """Resume the current song. Usage: !resume"""
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("▶ Playback resumed")
    else:
        await ctx.send("Playback is not paused!")

@bot.command()
async def stop(ctx):
    """Stop playback and clear queue. Usage: !stop"""
    voice_client = ctx.voice_client
    if voice_client:
        if ctx.guild.id in song_queues:
            song_queues[ctx.guild.id].clear()
        if ctx.guild.id in current_players:
            if 'control_message' in current_players[ctx.guild.id]:
                try:
                    await current_players[ctx.guild.id]['control_message'].delete()
                except:
                    pass
            del current_players[ctx.guild.id]
        await voice_client.disconnect()
        await ctx.send("⏹ Playback stopped and queue cleared")
    else:
        await ctx.send("I'm not in a voice channel!")

@bot.command()
async def leave(ctx):
    """Make the bot leave the voice channel. Usage: !leave"""
    voice_client = ctx.voice_client
    if voice_client:
        if ctx.guild.id in PERMA_VC:
            del PERMA_VC[ctx.guild.id]
            
        if ctx.guild.id in song_queues:
            song_queues[ctx.guild.id].clear()
        if ctx.guild.id in current_players:
            if 'control_message' in current_players[ctx.guild.id]:
                try:
                    await current_players[ctx.guild.id]['control_message'].delete()
                except:
                    pass
            del current_players[ctx.guild.id]
        await voice_client.disconnect()
        await ctx.send("⏹ Playback stopped and queue cleared")
    else:
        await ctx.send("I'm not in a voice channel!")

# --- Verification Commands ---

class FiveMVerificationView(discord.ui.View):
    """View for FiveM verification confirmation"""
    def __init__(self, ctx, player_data, server_address=None):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.player_data = player_data
        self.server_address = server_address or FIVEM_SERVER
        self.message = None
        self.verified = False
    
    async def on_timeout(self):
        if not self.verified and self.message:
            try:
                await self.message.delete()
            except:
                pass
    
    @discord.ui.button(label="Verify", style=discord.ButtonStyle.success, emoji="✅")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("You're not the one verifying!", ephemeral=True)
        
        role = None
        if FIVEM_ROLE_ID:
            role = self.ctx.guild.get_role(FIVEM_ROLE_ID)
        else:
            for r in self.ctx.guild.roles:
                if r.name.lower() not in ["@everyone", "bot"] and r < self.ctx.guild.me.top_role:
                    role = r
                    break
        
        if not role:
            return await interaction.response.send_message("❌ No valid role found to assign!", ephemeral=True)
        
        try:
            await self.ctx.author.add_roles(role)
            
            if CHANGE_NICKNAME:
                try:
                    await self.ctx.author.edit(nick=self.player_data['name'])
                except discord.Forbidden:
                    pass
            
            fivem_data = get_fivem_verification_data()
            user_id = str(self.ctx.author.id)
            
            if user_id not in fivem_data:
                fivem_data[user_id] = {}
            
            fivem_data[user_id] = {
                'player_id': self.player_data.get('id'),
                'player_name': self.player_data.get('name'),
                'verified_at': datetime.datetime.now().isoformat(),
                'identifiers': self.player_data.get('identifiers', [])
            }
            
            save_fivem_verification_data(fivem_data)
            
            embed = discord.Embed(
                title="✅ FiveM Verification Complete",
                description=f"Connected to `{self.player_data['name']}`",
                color=discord.Color.green()
            )
            embed.add_field(name="Player ID", value=self.player_data.get('id', 'N/A'), inline=True)
            embed.add_field(name="Server", value=self.server_address, inline=True)
            
            identifiers = self.player_data.get('identifiers', [])
            if identifiers:
                embed.add_field(name="Identifiers", value="\n".join(identifiers), inline=False)
            
            self.verified = True
            
            try:
                await interaction.message.delete()
            except:
                pass
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            public_msg = await self.ctx.send(
                f"Connected to {self.player_data.get('id', 'N/A')} | {self.player_data['name']} > {self.ctx.author.mention}"
            )
            
            await asyncio.sleep(600)
            try:
                await public_msg.edit(content=f"Connected to {self.player_data['name']} > {self.ctx.author.mention}")
            except:
                pass
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Verification failed: {e}", ephemeral=True)
    
    @discord.ui.button(label="🔄 Retry", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def retry_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("You're not the one verifying!", ephemeral=True)
        
        await interaction.response.defer()
        
        player = await get_fivem_player_by_identifier(
            self.player_data.get('id') or self.player_data.get('name'),
            self.server_address
        )
        
        if not player:
            embed = discord.Embed(
                title="❌ Verification Failed",
                description="Could not find your player on the server. Please ensure:\n"
                           "1. You are connected to the game\n"
                           "2. You used the correct player name/ID\n"
                           "3. The server is online",
                color=discord.Color.red()
            )
            await interaction.message.edit(embed=embed, view=None)
            return
        
        self.player_data = player
        
        identifiers = player.get('identifiers', [])
        discord_id = None
        for ident in identifiers:
            if ident.startswith('discord:'):
                discord_id = ident.split(':')[1]
                break
        
        if FIVEM_VERIFICATION_DISCORD_REQUIRED and (not discord_id or str(self.ctx.author.id) != discord_id):
            embed = discord.Embed(
                title="❌ Discord Verification Required",
                description="We couldn't verify your Discord ID in-game.\n\n" \
                           "Please ensure:\n" \
                           "1. You have linked your Discord account in-game\n" \
                           "2. You are currently online on the server\n" \
                           "3. You used the correct player name/ID",
                color=discord.Color.red()
            )
            await interaction.message.edit(embed=embed, view=self)
            await interaction.followup.send("❌ Couldn't verify your Discord ID. Please check the instructions.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🔍 FiveM Verification",
            color=discord.Color.blue()
        )
        
        if discord_id and str(self.ctx.author.id) == discord_id:
            embed.description = f"We found your account: **{player['name']}**"
            embed.add_field(name="Player ID", value=player.get('id', 'N/A'), inline=True)
            embed.add_field(name="FiveM ID", value=discord_id or "Not linked", inline=True)
            
            platforms = []
            for ident in identifiers:
                if ident.startswith('steam:'):
                    platforms.append("Steam")
                elif ident.startswith('license:'):
                    platforms.append("Rockstar")
                elif ident.startswith('xbl:'):
                    platforms.append("Xbox Live")
                elif ident.startswith('live:'):
                    platforms.append("Microsoft")
                elif ident.startswith('ip:'):
                    platforms.append(f"IP: {ident[3:]}")
            
            if platforms:
                embed.add_field(name="Platforms", value=", ".join(platforms), inline=False)
            
            await interaction.message.edit(embed=embed, view=self)
            await interaction.followup.send("✅ Found your account! Please verify now.", ephemeral=True)
        else:
            if FIVEM_VERIFICATION_DISCORD_REQUIRED:
                embed.description = "We couldn't verify your Discord ID in-game.\n\n" \
                                   "Please ensure:\n" \
                                   "1. You have linked your Discord account in-game\n" \
                                   "2. You are currently online on the server\n" \
                                   "3. You used the correct player name/ID"
            else:
                embed.description = f"We found your account: **{player['name']}**\n\n" \
                                   "Click Verify to complete the process"
                embed.add_field(name="Player ID", value=player.get('id', 'N/A'), inline=True)
                embed.add_field(name="FiveM ID", value=discord_id or "Not linked", inline=True)
            
            await interaction.message.edit(embed=embed, view=self)
            await interaction.followup.send("Please verify now.", ephemeral=True)

@bot.command()
async def verifyfivem(ctx, *, identifier: str):
    """Verify your FiveM account. Usage: !verifyfivem <player name or ID>"""
    if not VERIFICATION_FIVEM:
        return await ctx.send("❌ FiveM verification is currently disabled.", delete_after=10)
    
    if not FIVEM_SERVER:
        return await ctx.send("❌ FiveM server is not configured.", delete_after=10)
    
    try:
        await ctx.message.delete()
    except:
        pass
    
    fivem_data = get_fivem_verification_data()
    user_id = str(ctx.author.id)
    
    if FIVEM_ROLE_ID and discord.utils.get(ctx.author.roles, id=FIVEM_ROLE_ID):
        if user_id in fivem_data:
            player = await get_fivem_player_by_identifier(identifier)
            if player and str(player.get('id')) == str(fivem_data[user_id].get('player_id')):
                return await ctx.send(f"You're already verified as {fivem_data[user_id].get('player_name')}!", delete_after=10)
            else:
                await ctx.author.remove_roles(discord.utils.get(ctx.guild.roles, id=FIVEM_ROLE_ID))
                if user_id in fivem_data:
                    del fivem_data[user_id]
                    save_fivem_verification_data(fivem_data)
        else:
            await ctx.author.remove_roles(discord.utils.get(ctx.guild.roles, id=FIVEM_ROLE_ID))
    
    if user_id in fivem_data:
        player = await get_fivem_player_by_identifier(identifier)
        if player and str(player.get('id')) == str(fivem_data[user_id].get('player_id')):
            if FIVEM_ROLE_ID:
                role = ctx.guild.get_role(FIVEM_ROLE_ID)
                await ctx.author.add_roles(role)
                if CHANGE_NICKNAME:
                    try:
                        await ctx.author.edit(nick=fivem_data[user_id].get('player_name'))
                    except discord.Forbidden:
                        pass
                return await ctx.send(f"✅ You're already verified as {fivem_data[user_id].get('player_name')}! Role restored.", delete_after=10)
        else:
            del fivem_data[user_id]
            save_fivem_verification_data(fivem_data)
    
    msg = await ctx.send("🔍 Searching for your FiveM player...")
    
    player = await get_fivem_player_by_identifier(identifier)
    
    if not player:
        embed = discord.Embed(
            title="❌ Player Not Found",
            description="Could not find this player on the server. Please ensure:\n"
                       "1. You are connected to the game\n"
                       "2. You used the correct player name/ID\n"
                       "3. The server is online",
            color=discord.Color.red()
        )
        return await msg.edit(embed=embed)
    
    identifiers = player.get('identifiers', [])
    discord_id = None
    for ident in identifiers:
        if ident.startswith('discord:'):
            discord_id = ident.split(':')[1]
            break
    
    embed = discord.Embed(
        title="🔍 FiveM Verification",
        color=discord.Color.blue()
    )
    
    if discord_id and str(ctx.author.id) == discord_id:
        embed.description = f"We found your account: **{player['name']}**"
        embed.add_field(name="Player ID", value=player.get('id', 'N/A'), inline=True)
        embed.add_field(name="FiveM ID", value=discord_id, inline=True)
        
        platforms = []
        for ident in identifiers:
            if ident.startswith('steam:'):
                platforms.append("Steam")
            elif ident.startswith('license:'):
                platforms.append("Rockstar")
            elif ident.startswith('xbl:'):
                platforms.append("Xbox Live")
            elif ident.startswith('live:'):
                platforms.append("Microsoft")
            elif ident.startswith('ip:'):
                platforms.append(f"IP: {ident[3:]}")
        
        if platforms:
            embed.add_field(name="Platforms", value=", ".join(platforms), inline=False)
    else:
        if FIVEM_VERIFICATION_DISCORD_REQUIRED:
            embed.description = "We couldn't verify your Discord ID in-game.\n\n" \
                               "Please ensure:\n" \
                               "1. You have linked your Discord account in-game\n" \
                               "2. You are currently online on the server\n" \
                               "3. You used the correct player name/ID"
        else:
            embed.description = f"We found your account: **{player['name']}**\n\n" \
                               "Click Verify to complete the process"
            embed.add_field(name="Player ID", value=player.get('id', 'N/A'), inline=True)
            embed.add_field(name="FiveM ID", value=discord_id or "Not linked", inline=True)
    
    view = FiveMVerificationView(ctx, player)
    view.message = await msg.edit(embed=embed, view=view)

@bot.command()
async def fivemserverlive(ctx, channel: discord.TextChannel = None):
    """Post live FiveM server status in a channel. Usage: !fivemserverlive [#channel]"""
    if not VERIFICATION_FIVEM or not FIVEM_SERVER:
        return await ctx.send("❌ FiveM verification is not enabled or server not configured.", delete_after=10)
    
    target_channel = channel or ctx.channel
    
    if target_channel.id in bot.fivem_status_tasks:
        return await ctx.send("❌ There's already a live status in that channel!", delete_after=10)
    
    embed = discord.Embed(title="🔄 Fetching server status...", color=discord.Color.blue())
    status_msg = await target_channel.send(embed=embed)
    
    async def update_status():
        while True:
            try:
                server_info = await get_fivem_server_info()
                if not server_info:
                    embed = discord.Embed(
                        title="Server Status",
                        description="🔴 Server offline or unreachable",
                        color=discord.Color.red()
                    )
                else:
                    embed = discord.Embed(
                        title="Server Status",
                        color=discord.Color.green() if server_info['status'] == 'online' else discord.Color.red()
                    )
                    embed.add_field(name="Server Name", value=server_info['dynamic'].get('hostname', 'N/A'), inline=False)
                    embed.add_field(
                        name="Server Status", 
                        value="🟢 Online" if server_info['status'] == 'online' else "🔴 Offline", 
                        inline=True
                    )
                    embed.add_field(
                        name="Uptime", 
                        value=format_uptime(server_info.get('uptime')), 
                        inline=True
                    )
                    embed.add_field(
                        name="F8 Command", 
                        value=f"connect {FIVEM_SERVER}", 
                        inline=False
                    )
                    
                    players = server_info.get('players', [])
                    embed.add_field(
                        name=f"Citizens ({len(players)}/{server_info['dynamic'].get('sv_maxclients', 'N/A')})", 
                        value="\n".join([f"[{p.get('id', '?')}] | {p.get('name', 'Unknown')}" for p in players]) if players else "No players online",
                        inline=False
                    )
                
                await status_msg.edit(embed=embed)
                await asyncio.sleep(60)
            
            except Exception as e:
                print(f"Error updating server status: {e}")
                await asyncio.sleep(60)
    
    task = bot.loop.create_task(update_status())
    bot.fivem_status_tasks[target_channel.id] = {
        'task': task,
        'message': status_msg
    }
    
    await ctx.message.add_reaction("✅")
    
    async def stop_updates():
        if target_channel.id in bot.fivem_status_tasks:
            task = bot.fivem_status_tasks[target_channel.id]['task']
            task.cancel()
            del bot.fivem_status_tasks[target_channel.id]
            await status_msg.edit(content="Live updates stopped.", embed=None)
    
    bot.fivem_status_tasks[target_channel.id]['stop'] = stop_updates

@bot.command()
async def sampstatus(ctx):
    """Check SA-MP server status"""
    try:
        players = await query_samp(SAMP_SERVER_IP, SAMP_SERVER_PORT)
        if players is None:
            return await ctx.send("🔴 Server offline or unreachable")
            
        client = Client(ip=SAMP_SERVER_IP, port=SAMP_SERVER_PORT)
        info = await client.info()
        
        embed = discord.Embed(
            title=f"SA-MP Server: {info.name}",
            color=discord.Color.green()
        )
        embed.add_field(name="Players", value=f"{len(players)}/{info.max_players}", inline=True)
        embed.add_field(name="Gamemode", value=info.game_mode, inline=True)
        embed.add_field(name="Address", value=f"{SAMP_SERVER_IP}:{SAMP_SERVER_PORT}", inline=False)
        
        if players:
            player_list = "\n".join(players[:10])
            more = f"\n...and {len(players)-10} more" if len(players) > 10 else ""
            embed.add_field(name="Online Players", value=f"{player_list}{more}", inline=False)
            
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"🔴 Error checking server status: {str(e)}")

class RobloxConfirmationView(discord.ui.View):
    def __init__(self, ctx, profile):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.profile = profile
        self.confirmed = None
    
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

@bot.command()
async def verifyroblox(ctx, *, username: str):
    """Verify your Roblox account. Usage: !verifyroblox <username>"""
    if not VERIFICATION_ROBLOX:
        return await ctx.send("❌ Roblox verification is currently disabled.", delete_after=10)
    
    try:
        await ctx.message.delete()
    except:
        pass
    
    msg = await ctx.send("🔍 Fetching Roblox profile...")
    profile = await get_roblox_profile(username)
    
    if not profile:
        await msg.edit(content="❌ Couldn't find that Roblox username. Please check the spelling and try again.")
        return
    
    embed = discord.Embed(
        title="🔎 Is this your Roblox account?",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=profile['avatar'])
    embed.add_field(name="Username", value=profile['username'], inline=True)
    embed.add_field(name="Display Name", value=profile['displayName'], inline=True)
    embed.add_field(name="Account Created", value=profile['created'], inline=True)
    embed.add_field(name="Friends", value=f"{profile['friends']:,}", inline=True)
    embed.add_field(name="Description", value=profile['description'][:500] + ("..." if len(profile['description']) > 500 else "") or "No description", inline=False)
    embed.set_footer(text="Please confirm this is your account to continue verification")
    
    view = RobloxConfirmationView(ctx, profile)
    await msg.edit(content=None, embed=embed, view=view)
    
    await view.wait()
    
    if view.confirmed is None:
        await msg.edit(content="⏳ Verification timed out. Please try again.", view=None)
        return
    elif not view.confirmed:
        return
    
    code = f"Verify-{random.randint(10000, 99999)}"
    
    try:
        embed = discord.Embed(
            title="🔑 Roblox Verification",
            description=f"To verify your Roblox account **{profile['username']}**, please:\n\n"
                       f"1. Copy this verification code:\n"
                       f"```\n{code}\n```\n"
                       f"2. Paste it into your Roblox profile description\n"
                       f"3. The bot will automatically check for the code\n\n"
                       f"You have **2 minutes** to complete this.",
            color=discord.Color.gold()
        )
        embed.set_footer(text="The bot will automatically detect when you've added the code")
        
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="Copy Verification Code",
            style=discord.ButtonStyle.primary,
            custom_id="copy_code",
            emoji="📋"
        ))
        
        dm_msg = await ctx.author.send(embed=embed, view=view)
    except discord.Forbidden:
        await ctx.send(f"{ctx.author.mention} I couldn't send you a DM. Please enable DMs and try again.", delete_after=15)
        return
    
    await ctx.send(f"{ctx.author.mention} Check your DMs for verification instructions!", delete_after=15)
    
    original_desc = profile['description']
    
    start_time = time.time()
    verified = False
    
    while time.time() - start_time < 120:
        await asyncio.sleep(5)
        
        current_profile = await get_roblox_profile(username)
        if not current_profile:
            await ctx.author.send("❌ Couldn't fetch your Roblox profile anymore. Verification failed.")
            return
        
        if current_profile['description'] != original_desc:
            if code in current_profile['description']:
                verified = True
                break
            else:
                await ctx.author.send("❌ I found a description change but it doesn't contain the correct verification code. Please try again.")
                return
    
    if not verified:
        await ctx.author.send("⏳ Verification timed out. You didn't add the code in time.")
        return
    
    role = None
    if ROBLOX_ROLE_ID:
        role = ctx.guild.get_role(ROBLOX_ROLE_ID)
    else:
        for r in ctx.guild.roles:
            if r.name.lower() not in ["@everyone", "bot"] and r < ctx.guild.me.top_role:
                role = r
                break
    
    if not role:
        await ctx.author.send("❌ Verification failed: No valid role found to assign. Please contact server staff.")
        return
    
    try:
        await ctx.author.add_roles(role)
        
        if CHANGE_NICKNAME:
            try:
                await ctx.author.edit(nick=profile['username'])
            except discord.Forbidden:
                pass
        
        embed = discord.Embed(
            title="✅ Verification Successful",
            description=f"You've been verified as Roblox user **{profile['username']}**",
            color=discord.Color.green()
        )
        embed.add_field(name="Username", value=profile['username'], inline=True)
        embed.add_field(name="Display Name", value=profile['displayName'], inline=True)
        embed.set_thumbnail(url=profile['avatar'])
        
        await ctx.author.send(embed=embed)
        
        embed = discord.Embed(
            title="✅ Roblox Verification Complete",
            description=f"{ctx.author.mention} has been verified as Roblox user **{profile['username']}**",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=profile['avatar'])
        await ctx.send(embed=embed)
        
        owner_embed = discord.Embed(
            title="Roblox Verification",
            description=f"{ctx.author} verified as {profile['username']}",
            color=discord.Color.blue()
        )
        owner_embed.add_field(name="Roblox Username", value=profile['username'], inline=True)
        owner_embed.add_field(name="Display Name", value=profile['displayName'], inline=True)
        owner_embed.add_field(name="User ID", value=profile['id'], inline=False)
        owner_embed.set_thumbnail(url=profile['avatar'])
        await send_to_owner(ctx.guild, owner_embed)
        
    except Exception as e:
        await ctx.author.send(f"❌ Verification failed: {str(e)}")
        await ctx.send(f"❌ Failed to complete verification for {ctx.author.mention}. Please contact staff.", delete_after=15)

@bot.command()
async def verifyvalo(ctx, *, riotid: str):
    """Verify a Valorant account. Usage: !verifyvalo Username#Tag"""
    if not VERIFICATION_VALO:
        return
        
    if not RIOT_API_KEY:
        return await ctx.reply("❌ Valorant verification is currently disabled.")
    
    if "#" not in riotid:
        return await ctx.reply("❌ Invalid Riot ID. Use `Username#Tag` format.")
    
    username, tag = riotid.split("#", 1)
    msg = await ctx.reply("🔍 Verifying your Valorant account...")
    account = await get_valorant_account(username, tag)
    if not account:
        return await msg.edit(content="❌ Account not found in any region!")
    
    role = None
    if VALORANT_ROLE_ID:
        role = ctx.guild.get_role(VALORANT_ROLE_ID)
    else:
        for r in ctx.guild.roles:
            if r.name.lower() not in ["@everyone", "bot"] and r < ctx.guild.me.top_role:
                role = r
                break
    
    if not role:
        return await msg.edit(content="❌ No valid role found to assign!")
    
    await ctx.author.add_roles(role)
    
    if CHANGE_NICKNAME:
        try:
            await ctx.author.edit(nick=f"{account['gameName']}#{account['tagLine']}")
        except discord.Forbidden:
            pass
    
    embed = discord.Embed(title="Valorant Verification Successful ✅", color=0x00ff88)
    embed.add_field(name="Username", value=f"{account['gameName']}#{account['tagLine']}", inline=True)
    embed.add_field(name="PUUID", value=account['puuid'], inline=False)
    embed.set_footer(text=f"Verified by {ctx.author}")

    await msg.edit(content=None, embed=embed)
    await send_to_owner(ctx.guild, embed)

@bot.command()
async def verifysamp(ctx, *, playername: str):
    """Verify a SA-MP account. Usage: !verifysamp PlayerName"""
    if not VERIFICATION_SAMP:
        return await ctx.reply("❌ SA-MP verification is currently disabled.")
    
    if not SAMP_SERVER_IP or not SAMP_SERVER_PORT:
        return await ctx.reply("❌ SA-MP verification is not properly configured.")
    
    msg = await ctx.reply(f"🔍 Checking SA-MP server at {SAMP_SERVER_IP}:{SAMP_SERVER_PORT}...")
    
    try:
        players = await query_samp(SAMP_SERVER_IP, SAMP_SERVER_PORT)
        
        if players is None:
            return await msg.edit(content="❌ Could not connect to the SA-MP server. Please ensure:\n"
                                      "1. The server is online\n"
                                      "2. The IP and port are correct\n"
                                      "3. The server allows connections from this bot")
        
        player = next((p for p in players if p.lower() == playername.lower()), None)
        
        if not player:
            player_list = "\n".join(players[:10])
            more = f"\n...and {len(players)-10} more" if len(players) > 10 else ""
            return await msg.edit(content=f"❌ Could not find '{playername}' on the server.\n\nCurrent players:\n{player_list}{more}")
        
        role = None
        if SAMP_ROLE_ID:
            role = ctx.guild.get_role(SAMP_ROLE_ID)
        else:
            for r in ctx.guild.roles:
                if r.name.lower() not in ["@everyone", "bot"] and r < ctx.guild.me.top_role:
                    role = r
                    break
        
        if not role:
            return await msg.edit(content="❌ No valid role found to assign!")
        
        await ctx.author.add_roles(role)
        
        if CHANGE_NICKNAME:
            try:
                await ctx.author.edit(nick=player)
            except discord.Forbidden:
                pass
        
        embed = discord.Embed(
            title="✅ SA-MP Verification Successful",
            description=f"{ctx.author.mention} has been verified as `{player}`",
            color=discord.Color.green()
        )
        embed.add_field(name="Server", value=f"{SAMP_SERVER_IP}:{SAMP_SERVER_PORT}", inline=False)
        embed.set_footer(text=f"Verified at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        await msg.edit(content=None, embed=embed)
        
        owner_embed = discord.Embed(
            title="SA-MP Verification Log",
            description=f"{ctx.author} verified as {player}",
            color=discord.Color.blue()
        )
        await send_to_owner(ctx.guild, owner_embed)
        
    except Exception as e:
        await msg.edit(content=f"❌ An error occurred: {str(e)}")

# --- Moderation Commands ---

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    """Ban a member from the server. Usage: !ban @user [reason]"""
    try:
        await member.ban(reason=reason)
        embed = discord.Embed(
            title="🔨 Member Banned",
            description=f"{member.mention} has been banned by {ctx.author.mention}",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=reason)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Failed to ban member: {e}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    """Kick a member from the server. Usage: !kick @user [reason]"""
    try:
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="👢 Member Kicked",
            description=f"{member.mention} has been kicked by {ctx.author.mention}",
            color=discord.Color.orange()
        )
        embed.add_field(name="Reason", value=reason)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Failed to kick member: {e}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def timeout(ctx, member: discord.Member, duration: str, *, reason="No reason provided"):
    """Timeout a member (format: 1h, 30m, 2d). Usage: !timeout @user 30m [reason]"""
    try:
        time_units = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400
        }
        duration_lower = duration.lower()
        if duration_lower[-1] not in time_units:
            raise ValueError("Invalid time unit. Use s, m, h, or d")
        
        time_value = int(duration_lower[:-1])
        time_unit = duration_lower[-1]
        seconds = time_value * time_units[time_unit]
        
        timeout_duration = datetime.timedelta(seconds=seconds)
        await member.timeout(timeout_duration, reason=reason)
        
        embed = discord.Embed(
            title="⏳ Member Timed Out",
            description=f"{member.mention} has been timed out by {ctx.author.mention}",
            color=discord.Color.gold()
        )
        embed.add_field(name="Duration", value=duration)
        embed.add_field(name="Reason", value=reason)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Failed to timeout member: {e}\nUsage: `{PREFIX}timeout @user 30m [reason]`")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, duration: str):
    """Set slowmode for the channel (format: 1h, 30m, 2d). Usage: !slowmode 30s"""
    try:
        time_units = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400
        }
        duration_lower = duration.lower()
        if duration_lower[-1] not in time_units:
            raise ValueError("Invalid time unit. Use s, m, h, or d")
        
        time_value = int(duration_lower[:-1])
        time_unit = duration_lower[-1]
        seconds = time_value * time_units[time_unit]
        
        if seconds > 21600:
            await ctx.send("Slowmode cannot be longer than 6 hours!")
            return
        
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"⏳ Slowmode set to {duration} in this channel.")
    except Exception as e:
        await ctx.send(f"❌ Failed to set slowmode: {e}\nUsage: `{PREFIX}slowmode 30s`")

@bot.command(aliases=['nick'])
@commands.has_permissions(manage_nicknames=True)
async def setnick(ctx, member: discord.Member, *, nickname: str):
    """Set a member's nickname. Usage: !setnick @user NewNickname"""
    try:
        old_nick = member.display_name
        await member.edit(nick=nickname)
        embed = discord.Embed(
            title="📝 Nickname Changed",
            description=f"{member.mention}'s nickname has been updated",
            color=discord.Color.blue()
        )
        embed.add_field(name="Before", value=old_nick, inline=True)
        embed.add_field(name="After", value=nickname, inline=True)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Failed to change nickname: {e}")

@bot.command()
async def getroles(ctx, member: discord.Member = None):
    """Get a member's roles. Usage: !getroles [@user]"""
    target = member or ctx.author
    roles = [role.mention for role in target.roles if role.name != "@everyone"]
    
    if not roles:
        await ctx.send(f"{target.display_name} has no roles.")
        return
    
    embed = discord.Embed(
        title=f"🎭 Roles for {target.display_name}",
        description=" ".join(roles),
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def addrole(ctx, member: discord.Member, *, role: discord.Role):
    """Add a role to a member. Usage: !addrole @user @Role"""
    try:
        if role in member.roles:
            await ctx.send(f"{member.display_name} already has the {role.name} role!")
            return
            
        await member.add_roles(role)
        embed = discord.Embed(
            title="➕ Role Added",
            description=f"{role.mention} has been added to {member.mention}",
            color=role.color
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Failed to add role: {e}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def removerole(ctx, member: discord.Member, *, role: discord.Role):
    """Remove a role from a member. Usage: !removerole @user @Role"""
    try:
        if role not in member.roles:
            await ctx.send(f"{member.display_name} doesn't have the {role.name} role!")
            return
            
        await member.remove_roles(role)
        embed = discord.Embed(
            title="➖ Role Removed",
            description=f"{role.mention} has been removed from {member.mention}",
            color=role.color
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Failed to remove role: {e}")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx, channel: discord.TextChannel = None, role: discord.Role = None):
    """
    Lock a channel for everyone or a specific role.
    Usage: 
    !lock - Locks current channel for everyone
    !lock #channel - Locks mentioned channel for everyone
    !lock #channel @role - Locks channel for specific role
    """
    target_channel = channel or ctx.channel
    target_role = role or ctx.guild.default_role
    
    additional_roles = []
    if EXTRA_ROLES_LOCK_UNLOCK:
        additional_role = ctx.guild.get_role(EXTRA_ROLES_LOCK_UNLOCK)
        if additional_role:
            additional_roles.append(additional_role)
    
    try:
        overwrite = target_channel.overwrites_for(target_role)
        
        overwrite.send_messages = False
        
        await target_channel.set_permissions(target_role, overwrite=overwrite)
        
        for role in additional_roles:
            if role != target_role:
                role_overwrite = target_channel.overwrites_for(role)
                role_overwrite.send_messages = False
                await target_channel.set_permissions(role, overwrite=role_overwrite)
        
        if target_role == ctx.guild.default_role:
            await ctx.send(f"🔒 {target_channel.mention} has been locked for everyone!")
        else:
            await ctx.send(f"🔒 {target_channel.mention} has been locked for {target_role.mention}!")
            
    except discord.Forbidden:
        await ctx.send("I don't have permission to lock this channel!")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx, channel: discord.TextChannel = None, role: discord.Role = None):
    """
    Unlock a channel for everyone or a specific role.
    Usage: 
    !unlock - Unlocks current channel for everyone
    !unlock #channel - Unlocks mentioned channel for everyone
    !unlock #channel @role - Unlocks channel for specific role
    """
    target_channel = channel or ctx.channel
    target_role = role or ctx.guild.default_role
    
    additional_roles = []
    if EXTRA_ROLES_LOCK_UNLOCK:
        additional_role = ctx.guild.get_role(EXTRA_ROLES_LOCK_UNLOCK)
        if additional_role:
            additional_roles.append(additional_role)
    
    try:
        overwrite = target_channel.overwrites_for(target_role)
        
        overwrite.send_messages = None
        
        await target_channel.set_permissions(target_role, overwrite=overwrite)
        
        for role in additional_roles:
            if role != target_role:
                role_overwrite = target_channel.overwrites_for(role)
                role_overwrite.send_messages = None
                await target_channel.set_permissions(role, overwrite=role_overwrite)
        
        if target_role == ctx.guild.default_role:
            await ctx.send(f"🔓 {target_channel.mention} has been unlocked for everyone!")
        else:
            await ctx.send(f"🔓 {target_channel.mention} has been unlocked for {target_role.mention}!")
            
    except discord.Forbidden:
        await ctx.send("I don't have permission to unlock this channel!")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    """Warn a member and keep track of warnings. Usage: !warn @user [reason]"""
    warnings_data = get_warnings_data()
    guild_id = str(ctx.guild.id)
    user_id = str(member.id)
    
    if guild_id not in warnings_data:
        warnings_data[guild_id] = {}
    
    if user_id not in warnings_data[guild_id]:
        warnings_data[guild_id][user_id] = []
    
    warning = {
        "moderator": ctx.author.id,
        "reason": reason,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    warnings_data[guild_id][user_id].append(warning)
    save_warnings_data(warnings_data)
    
    embed = discord.Embed(
        title="⚠️ Member Warned",
        description=f"{member.mention} has been warned by {ctx.author.mention}",
        color=discord.Color.orange()
    )
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Total Warnings", value=len(warnings_data[guild_id][user_id]), inline=False)
    embed.set_footer(text=f"User ID: {member.id}")
    
    await ctx.send(embed=embed)
    
    try:
        dm_embed = discord.Embed(
            title=f"⚠️ You've been warned in {ctx.guild.name}",
            color=discord.Color.orange()
        )
        dm_embed.add_field(name="Reason", value=reason, inline=False)
        dm_embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
        dm_embed.add_field(name="Total Warnings", value=len(warnings_data[guild_id][user_id]), inline=False)
        await member.send(embed=dm_embed)
    except discord.Forbidden:
        pass

@bot.command()
async def warnings(ctx, member: discord.Member = None):
    """Check a member's warnings. Usage: !warnings [@user]"""
    target = member or ctx.author
    warnings_data = get_warnings_data()
    guild_id = str(ctx.guild.id)
    user_id = str(target.id)
    
    if guild_id not in warnings_data or user_id not in warnings_data[guild_id] or not warnings_data[guild_id][user_id]:
        return await ctx.send(f"{target.display_name} has no warnings.")
    
    warnings_list = warnings_data[guild_id][user_id]
    
    embed = discord.Embed(
        title=f"⚠️ Warnings for {target.display_name}",
        description=f"Total warnings: {len(warnings_list)}",
        color=discord.Color.orange()
    )
    
    for i, warning in enumerate(warnings_list, 1):
        moderator = ctx.guild.get_member(warning["moderator"]) or f"User ID: {warning['moderator']}"
        timestamp = datetime.datetime.fromisoformat(warning["timestamp"]).strftime("%Y-%m-%d %H:%M")
        embed.add_field(
            name=f"Warning #{i}",
            value=f"**Reason:** {warning['reason']}\n**By:** {moderator}\n**On:** {timestamp}",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clearwarns(ctx, member: discord.Member):
    """Clear all warnings for a member. Usage: !clearwarns @user"""
    warnings_data = get_warnings_data()
    guild_id = str(ctx.guild.id)
    user_id = str(member.id)
    
    if guild_id not in warnings_data or user_id not in warnings_data[guild_id]:
        return await ctx.send(f"{member.display_name} has no warnings to clear.")
    
    warnings_data[guild_id].pop(user_id)
    save_warnings_data(warnings_data)
    
    embed = discord.Embed(
        title="✅ Warnings Cleared",
        description=f"All warnings for {member.mention} have been cleared.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command(aliases=['clear'])
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int = 10):
    """Purge messages from the channel (default: 10). Usage: !purge [amount]"""
    if amount <= 0 or amount > 100:
        return await ctx.send("Please provide a number between 1 and 100.")
    
    deleted = await ctx.channel.purge(limit=amount + 1)
    
    embed = discord.Embed(
        title="🗑️ Messages Purged",
        description=f"Deleted {len(deleted) - 1} messages.",
        color=discord.Color.green()
    )
    msg = await ctx.send(embed=embed, delete_after=5)

@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def resetnick(ctx, member: discord.Member):
    """Reset a member's nickname. Usage: !resetnick @user"""
    try:
        old_nick = member.display_name
        await member.edit(nick=None)
        embed = discord.Embed(
            title="✅ Nickname Reset",
            description=f"{member.mention}'s nickname has been reset.",
            color=discord.Color.green()
        )
        embed.add_field(name="Previous Nickname", value=old_nick, inline=True)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Failed to reset nickname: {e}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def mute(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    """Mute a member in text channels. Usage: !mute @user [reason]"""
    try:
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted")
            
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role,
                    send_messages=False,
                    speak=False,
                    add_reactions=False
                )
        
        await member.add_roles(muted_role, reason=reason)
        
        embed = discord.Embed(
            title="🔇 Member Muted",
            description=f"{member.mention} has been muted by {ctx.author.mention}",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.send(embed=embed)
        
        try:
            dm_embed = discord.Embed(
                title=f"🔇 You've been muted in {ctx.guild.name}",
                color=discord.Color.red()
            )
            dm_embed.add_field(name="Reason", value=reason, inline=False)
            dm_embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass
            
    except Exception as e:
        await ctx.send(f"❌ Failed to mute member: {e}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def unmute(ctx, member: discord.Member):
    """Unmute a member. Usage: !unmute @user"""
    try:
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        
        if not muted_role or muted_role not in member.roles:
            return await ctx.send(f"{member.display_name} is not muted.")
        
        await member.remove_roles(muted_role)
        
        embed = discord.Embed(
            title="🔊 Member Unmuted",
            description=f"{member.mention} has been unmuted by {ctx.author.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        
        try:
            dm_embed = discord.Embed(
                title=f"🔊 You've been unmuted in {ctx.guild.name}",
                color=discord.Color.green()
            )
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass
            
    except Exception as e:
        await ctx.send(f"❌ Failed to unmute member: {e}")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def nuke(ctx, channel: discord.TextChannel = None):
    """Clone and delete a channel to remove all messages. Usage: !nuke [channel]"""
    target_channel = channel or ctx.channel
    
    confirmation = await ctx.send(f"⚠️ Are you sure you want to nuke {target_channel.mention}? This will delete ALL messages! React with ✅ to confirm.")
    await confirmation.add_reaction("✅")
    
    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) == "✅" and reaction.message.id == confirmation.id
    
    try:
        await bot.wait_for('reaction_add', timeout=30.0, check=check)
    except asyncio.TimeoutError:
        await confirmation.edit(content="🚫 Channel nuke cancelled.")
        return
    
    try:
        new_channel = await target_channel.clone(reason=f"Channel nuked by {ctx.author}")
        await target_channel.delete(reason=f"Channel nuked by {ctx.author}")
        
        embed = discord.Embed(
            title="💥 Channel Nuked",
            description=f"This channel has been nuked by {ctx.author.mention}",
            color=discord.Color.red()
        )
        embed.set_image(url="https://media.giphy.com/media/oe33xf3B50fsc/giphy.gif")
        await new_channel.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Failed to nuke channel: {e}")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def clone(ctx, channel: discord.TextChannel = None):
    """Clone a text channel. Usage: !clone [channel]"""
    target_channel = channel or ctx.channel
    
    try:
        new_channel = await target_channel.clone()
        await ctx.send(f"✅ Successfully cloned {target_channel.mention} to {new_channel.mention}")
    except Exception as e:
        await ctx.send(f"❌ Failed to clone channel: {e}")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def slowoff(ctx, channel: discord.TextChannel = None):
    """Remove slowmode from a channel. Usage: !slowoff [channel]"""
    target_channel = channel or ctx.channel
    
    try:
        await target_channel.edit(slowmode_delay=0)
        await ctx.send(f"✅ Slowmode removed from {target_channel.mention}")
    except Exception as e:
        await ctx.send(f"❌ Failed to remove slowmode: {e}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def createrole(ctx, name: str, color: str = None, *, reason: str = None):
    """Create a new role. Usage: !createrole <name> [hex color] [reason]"""
    try:
        role_color = discord.Color.default()
        if color:
            if color.startswith('#'):
                color = color[1:]
            try:
                role_color = discord.Color(int(color, 16))
            except ValueError:
                await ctx.send("❌ Invalid color format. Use hex (e.g., #FF0000 or FF0000)")
                return
        
        new_role = await ctx.guild.create_role(
            name=name,
            color=role_color,
            reason=reason
        )
        
        embed = discord.Embed(
            title="✅ Role Created",
            description=f"New role {new_role.mention} has been created",
            color=role_color
        )
        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Failed to create role: {e}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def deleterole(ctx, *, role: discord.Role):
    """Delete a role. Usage: !deleterole @role"""
    try:
        await role.delete()
        await ctx.send(f"✅ Role `{role.name}` has been deleted")
    except Exception as e:
        await ctx.send(f"❌ Failed to delete role: {e}")

# --- Utility Commands ---

@bot.command()
async def translate(ctx, target_lang: str, *, text: str):
    """Translate text to another language. Usage: !translate <target_lang> <text>"""
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            'client': 'gtx',
            'sl': 'auto',
            'tl': target_lang,
            'dt': 't',
            'q': text
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    translated_text = data[0][0][0]
                    source_lang = data[2]
                    
                    embed = discord.Embed(
                        title="🌍 Translation",
                        color=discord.Color.blue()
                    )
                    embed.add_field(name=f"Original ({source_lang})", value=text, inline=False)
                    embed.add_field(name=f"Translated ({target_lang})", value=translated_text, inline=False)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ Failed to translate text. Please try again later.")
    except Exception as e:
        await ctx.send(f"❌ Translation error: {e}")

@bot.command()
async def weather(ctx, *, location: str):
    """Get weather for a location. Usage: !weather <city>"""
    try:
        if WEATHER_API_KEY == 'your_api_key_here':
            return await ctx.send("Weather API is not configured.")
            
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': location,
            'appid': WEATHER_API_KEY,
            'units': 'metric'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    city = data['name']
                    country = data['sys']['country']
                    temp = data['main']['temp']
                    feels_like = data['main']['feels_like']
                    humidity = data['main']['humidity']
                    wind = data['wind']['speed']
                    description = data['weather'][0]['description'].title()
                    icon = data['weather'][0]['icon']
                    
                    embed = discord.Embed(
                        title=f"⛅ Weather in {city}, {country}",
                        description=f"**{description}**",
                        color=discord.Color.blue()
                    )
                    embed.set_thumbnail(url=f"http://openweathermap.org/img/wn/{icon}@2x.png")
                    embed.add_field(name="🌡️ Temperature", value=f"{temp}°C (Feels like {feels_like}°C)", inline=True)
                    embed.add_field(name="💧 Humidity", value=f"{humidity}%", inline=True)
                    embed.add_field(name="🌬️ Wind Speed", value=f"{wind} m/s", inline=True)
                    
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ Could not find weather for that location. Please check the spelling.")
    except Exception as e:
        await ctx.send(f"❌ Weather lookup error: {e}")

@bot.command(aliases=['calc'])
async def calculator(ctx, *, expression: str):
    """Evaluate a math expression. Usage: !calc <expression>"""
    try:
        expr = expression.replace(' ', '')
        if not re.match(r'^[\d+\-*/().^% ]+$', expr):
            return await ctx.send("❌ Invalid characters in expression. Only numbers and +-*/^% operators allowed.")
        
        expr = expr.replace('^', '**')
        result = eval(expr, {'__builtins__': None}, {})
        
        embed = discord.Embed(
            title="🧮 Calculator",
            color=discord.Color.blue()
        )
        embed.add_field(name="Expression", value=expression, inline=False)
        embed.add_field(name="Result", value=str(result), inline=False)
        await ctx.send(embed=embed)
    except ZeroDivisionError:
        await ctx.send("❌ Cannot divide by zero!")
    except Exception as e:
        await ctx.send(f"❌ Calculation error: {e}")

@bot.command()
async def poll(ctx, question: str, *options: str):
    """Create a poll. Usage: !poll "Question" "Option1" "Option2" ..."""
    if len(options) < 2:
        return await ctx.send("Please provide at least 2 options for the poll.")
    if len(options) > 10:
        return await ctx.send("You can only have up to 10 options.")
    
    emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    
    description = []
    for i, option in enumerate(options):
        description.append(f"{emojis[i]} {option}")
    
    embed = discord.Embed(
        title=f"📊 Poll: {question}",
        description="\n".join(description),
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Poll created by {ctx.author.display_name}")
    
    message = await ctx.send(embed=embed)
    
    for i in range(len(options)):
        await message.add_reaction(emojis[i])

@bot.command()
@commands.has_permissions(manage_channels=True)
async def vc247(ctx):
    """Make the bot stay in voice channel 24/7. Usage: !24-7vc"""
    if not ctx.author.voice:
        return await ctx.send("You need to be in a voice channel to use this command!")
    
    voice_client = ctx.voice_client
    
    if voice_client and voice_client.is_connected():
        if voice_client.channel != ctx.author.voice.channel:
            await voice_client.move_to(ctx.author.voice.channel)
    else:
        voice_client = await ctx.author.voice.channel.connect()
    
    PERMA_VC[ctx.guild.id] = True
    
    async def maintain_connection():
        while PERMA_VC.get(ctx.guild.id, False):
            if not voice_client.is_connected():
                try:
                    await ctx.author.voice.channel.connect()
                except:
                    pass
            
            await asyncio.sleep(10)  # Check every 10 seconds
    
    bot.loop.create_task(maintain_connection())
    
    await ctx.send("🔊 Bot will now stay in this voice channel 24/7. Use `!leave` to stop.")

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    """Get a user's avatar. Usage: !avatar [@user]"""
    target = member or ctx.author
    embed = discord.Embed(
        title=f"{target.display_name}'s Avatar",
        color=discord.Color.blue()
    )
    embed.set_image(url=target.avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def serverinfo(ctx):
    """Get server information. Usage: !serverinfo"""
    guild = ctx.guild
    embed = discord.Embed(
        title=f"Server Info: {guild.name}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=guild.icon.url)
    
    embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
    embed.add_field(name="Created", value=guild.created_at.strftime("%B %d, %Y"), inline=True)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="Channels", value=f"Text: {len(guild.text_channels)}\nVoice: {len(guild.voice_channels)}", inline=True)
    embed.add_field(name="Boosts", value=guild.premium_subscription_count, inline=True)
    
    await ctx.send(embed=embed)

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    """Get user information. Usage: !userinfo [@user]"""
    target = member or ctx.author
    embed = discord.Embed(
        title=f"User Info: {target.display_name}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=target.avatar.url)
    
    embed.add_field(name="ID", value=target.id, inline=True)
    embed.add_field(name="Nickname", value=target.nick or "None", inline=True)
    embed.add_field(name="Created", value=target.created_at.strftime("%B %d, %Y"), inline=True)
    embed.add_field(name="Joined", value=target.joined_at.strftime("%B %d, %Y"), inline=True)
    
    roles = [role.mention for role in target.roles if role.name != "@everyone"]
    embed.add_field(
        name=f"Roles ({len(roles)})", 
        value=" ".join(roles) if roles else "None", 
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command()
async def remind(ctx, time: str, *, reminder: str):
    """Set a reminder. Usage: !remind 1h30m Do homework"""
    try:
        seconds = 0
        time_lower = time.lower()
        
        if 'd' in time_lower:
            days = int(time_lower.split('d')[0])
            seconds += days * 86400
            time_lower = time_lower.split('d')[1]
        if 'h' in time_lower:
            hours = int(time_lower.split('h')[0])
            seconds += hours * 3600
            time_lower = time_lower.split('h')[1]
        if 'm' in time_lower:
            minutes = int(time_lower.split('m')[0])
            seconds += minutes * 60
            time_lower = time_lower.split('m')[1]
        if 's' in time_lower:
            secs = int(time_lower.split('s')[0])
            seconds += secs
        
        if seconds <= 0:
            return await ctx.send("Please provide a valid time greater than 0 seconds.")
        
        await ctx.send(f"⏰ I'll remind you in {time} about: {reminder}")
        
        await asyncio.sleep(seconds)
        
        embed = discord.Embed(
            title="⏰ Reminder",
            description=reminder,
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"You set this reminder {time} ago")
        
        await ctx.author.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Failed to set reminder: {e}\nUsage: `{PREFIX}remind 1h30m Do homework`")

# --- Fun & Game Commands ---

@bot.command(aliases=['rockpaperscissors'])
async def rps(ctx, choice: str):
    """Play Rock Paper Scissors. Usage: !rps rock|paper|scissors"""
    choices = ["rock", "paper", "scissors"]
    emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
    bot_choice = random.choice(choices)
    user_choice = choice.lower()
    
    if user_choice not in choices:
        await ctx.send("Please choose rock, paper, or scissors!")
        return
    
    if user_choice == bot_choice:
        result = "It's a tie! 🤝"
    elif (user_choice == "rock" and bot_choice == "scissors") or \
         (user_choice == "paper" and bot_choice == "rock") or \
         (user_choice == "scissors" and bot_choice == "paper"):
        result = "You win! 🎉"
    else:
        result = "I win! 😎"
    
    embed = discord.Embed(
        title="🪨 📄 ✂️ Rock Paper Scissors",
        color=discord.Color.blurple()
    )
    embed.add_field(name="Your Choice", value=f"{emojis[user_choice]} {user_choice.capitalize()}", inline=True)
    embed.add_field(name="My Choice", value=f"{emojis[bot_choice]} {bot_choice.capitalize()}", inline=True)
    embed.add_field(name="Result", value=result, inline=False)
    await ctx.send(embed=embed)

@bot.command(aliases=['dice'])
async def roll(ctx, dice: str = "1d6"):
    """Roll dice in NdN format (e.g., 2d20). Usage: !roll 2d20"""
    try:
        rolls, limit = map(int, dice.split('d'))
        if rolls > 20 or limit > 100:
            await ctx.send("Maximum 20 dice with 100 sides each!")
            return
            
        results = [random.randint(1, limit) for _ in range(rolls)]
        total = sum(results)
        
        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"Rolling {dice}",
            color=discord.Color.random()
        )
        embed.add_field(name="Results", value=", ".join(map(str, results)), inline=True)
        embed.add_field(name="Total", value=total, inline=True)
        
        if rolls == 1 and limit == 20:
            if results[0] == 20:
                embed.set_footer(text="Nat 20! Critical success! 🎯")
            elif results[0] == 1:
                embed.set_footer(text="Critical fail! 💀")
        
        await ctx.send(embed=embed)
    except Exception:
        await ctx.send(f'Format must be NdN! Example: `{PREFIX}roll 2d20`')

@bot.command(aliases=['flip'])
async def flipcoin(ctx):
    """Flip a coin (no betting). Usage: !flipcoin"""
    result = random.choice(["Heads", "Tails"])
    embed = discord.Embed(
        title="🪙 Coin Flip",
        description=f"The coin landed on... **{result}**!",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)

@bot.command()
async def guess(ctx, number: int):
    """Guess a number between 1 and 10. Usage: !guess 5"""
    if number < 1 or number > 10:
        await ctx.send("Please guess a number between 1 and 10!")
        return
        
    secret = random.randint(1, 10)
    if number == secret:
        message = f"🎉 Congratulations! You guessed it! The number was {secret}."
        color = discord.Color.green()
    else:
        message = f"❌ Sorry, the number was {secret}. Try again!"
        color = discord.Color.red()
    
    embed = discord.Embed(
        title="🔢 Number Guessing Game",
        description=message,
        color=color
    )
    await ctx.send(embed=embed)

@bot.command()
async def slap(ctx, member: discord.Member):
    """Slap someone! Usage: !slap @user"""
    gif_url = "https://c.tenor.com/XiYuU9h44-AAAAAC/tenor.gif"
    reactions = ["(╯°□°）╯︵ ┻━┻", "⊙﹏⊙", "(ﾉ｀Д´)ﾉ", "ಠ_ಠ", "(•̀o•́)ง"]
    
    embed = discord.Embed(
        color=discord.Color.red()
    )
    embed.set_author(name=f"{ctx.author.display_name} slapped {member.display_name} {random.choice(reactions)}")
    embed.set_image(url=gif_url)
    await ctx.send(embed=embed)

@bot.command()
async def kiss(ctx, member: discord.Member):
    """Kiss someone! Usage: !kiss @user"""
    gif_url = "https://www.icegif.com/wp-content/uploads/2022/08/icegif-1235.gif"
    reactions = ["(づ￣ ³￣)づ", "(*˘︶˘*).｡.:*♡", "(っ˘ω˘ς )", "♡(˃͈ દ ˂͈ ༶ )", "(´∀｀)♡"]
    
    embed = discord.Embed(
        color=discord.Color.pink()
    )
    embed.set_author(name=f"{ctx.author.display_name} kissed {member.display_name} {random.choice(reactions)}")
    embed.set_image(url=gif_url)
    await ctx.send(embed=embed)

@bot.command()
async def hug(ctx, member: discord.Member):
    """Hug someone! Usage: !hug @user"""
    gif_url = "https://usagif.com/wp-content/uploads/gif/anime-hug-59.gif"
    reactions = ["(⊃｡•́‿•̀｡)⊃", "(っ´▽｀)っ", "⊂((・▽・))⊃", "(つ≧▽≦)つ", "╰(*´︶`*)╯"]
    
    embed = discord.Embed(
        color=discord.Color.gold()
    )
    embed.set_author(name=f"{ctx.author.display_name} hugged {member.display_name} {random.choice(reactions)}")
    embed.set_image(url=gif_url)
    await ctx.send(embed=embed)

# --- Owo Economy Games ---

@bot.command(name=f'{GAME_PREFIX}coinflip', aliases=[f'{GAME_PREFIX}cf'])
async def owo_coinflip(ctx, amount: int, choice: str = None):
    """
    Flip a coin with your coins (optionally choose heads/tails).
    Usage: 
    owo coinflip <amount> [heads/tails]
    Examples:
    owo coinflip 100          - Random choice
    owo coinflip 100 heads    - Bet on heads
    owo coinflip 100 tails    - Bet on tails
    """
    if amount <= 0:
        return await ctx.send("Amount must be positive!")
    
    data = get_owo_data()
    user_id = str(ctx.author.id)
    
    if user_id not in data or data[user_id]['balance'] < amount:
        return await ctx.send("You don't have enough coins!")
    
    if choice is not None:
        choice = choice.lower()
        if choice not in ['heads', 'tails']:
            return await ctx.send("Please choose either 'heads' or 'tails' or leave it blank for random choice!")
        was_random = False
    else:
        choice = random.choice(['heads', 'tails'])
        was_random = True
    
    embed = discord.Embed(
        title="🪙 Coin Flip",
        color=discord.Color.gold()
    )
    if was_random:
        embed.description = f"**{ctx.author.display_name}** flips a coin for {amount} coins (random choice)..."
    else:
        embed.description = f"**{ctx.author.display_name}** flips a coin for {amount} coins (betting on {choice})..."
    
    embed.set_image(url=COINFLIP_GIF)
    msg = await ctx.send(embed=embed)
    
    await asyncio.sleep(3)
    
    result = random.choice(['heads', 'tails'])
    
    if was_random:
        
        won = True
        winnings = amount * 1.5  # 1.5x payout for random
    else:
        won = choice == result
        winnings = amount * 2 if won else 0
    
    if won:
        net_gain = winnings - amount
        data[user_id]['balance'] += net_gain
        if was_random:
            outcome = f"**Random choice won!** The coin landed on {result} (1.5x payout)!"
        else:
            outcome = f"**You won!** The coin landed on {result}!"
    else:
        data[user_id]['balance'] -= amount
        outcome = f"**You lost!** The coin landed on {result}."
    
    save_owo_data(data)
    
    embed = discord.Embed(
        title="🪙 Coin Flip Result",
        description=outcome,
        color=discord.Color.gold() if won else discord.Color.red()
    )
    
    if not was_random:
        embed.add_field(name="Your Choice", value=choice.capitalize(), inline=True)
    else:
        embed.add_field(name="Random Choice", value=choice.capitalize(), inline=True)
    
    embed.add_field(name="Actual Result", value=result.capitalize(), inline=True)
    
    if won:
        embed.add_field(name="Winnings", value=f"+{net_gain} coins", inline=False)
    
    embed.add_field(name="New Balance", value=f"{data[user_id]['balance']} coins", inline=False)
    
    await msg.edit(embed=embed)

@bot.command(name=f'{GAME_PREFIX}slots', aliases=[f'{GAME_PREFIX}s'])
async def owo_slots(ctx, amount: int):
    """Play slots with your coins. Usage: owo slots <amount> or owo s <amount>"""
    if amount <= 0:
        return await ctx.send("Amount must be positive!")
    
    data = get_owo_data()
    user_id = str(ctx.author.id)
    
    if user_id not in data or data[user_id]['balance'] < amount:
        return await ctx.send("You don't have enough coins!")
    
    emojis = ["🍎", "🍒", "🍋", "🍉", "🍇", "7️⃣"]
    weights = [0.25, 0.25, 0.2, 0.15, 0.1, 0.05]  # 7 is rarest
    
    losing_streak = data[user_id].get('slots_losing_streak', 0)
    adjusted_weights = [w * (1 + losing_streak * 0.1) for w in weights]
    
    embed = discord.Embed(
        title="🎰 Slots Spinning...",
        description="[ 🎰 | 🎰 | 🎰 ]",
        color=discord.Color.gold()
    )
    msg = await ctx.send(embed=embed)
    
    for _ in range(3):
        temp_slots = [random.choices(emojis, weights=adjusted_weights)[0] for _ in range(3)]
        embed.description = f"[ {' | '.join(temp_slots)} ]"
        await msg.edit(embed=embed)
        await asyncio.sleep(0.5)
    
    slots = [random.choices(emojis, weights=adjusted_weights)[0] for _ in range(3)]
    slot_display = " | ".join(slots)
    
    if slots[0] == slots[1] == slots[2]:
        if slots[0] == "7️⃣":
            multiplier = 10  # Jackpot!
        else:
            multiplier = 5
        won = True
        winnings = amount * multiplier
        data[user_id]['slots_losing_streak'] = 0
    elif slots[0] == slots[1] or slots[1] == slots[2] or slots[0] == slots[2]:
        multiplier = 2
        won = True
        winnings = amount * multiplier
        data[user_id]['slots_losing_streak'] = max(0, data[user_id].get('slots_losing_streak', 0) - 1)
    else:
        won = False
        winnings = 0
        data[user_id]['slots_losing_streak'] = data[user_id].get('slots_losing_streak', 0) + 1
    
    if won:
        net_gain = winnings - amount
        data[user_id]['balance'] += net_gain
        outcome = f"**You won {winnings} coins!** (x{multiplier})"
    else:
        data[user_id]['balance'] -= amount
        outcome = "**You lost!**"
        if data[user_id]['slots_losing_streak'] >= 5:
            consolation = min(amount, 100)
            data[user_id]['balance'] += consolation
            outcome += f"\nHere's {consolation} coins as a consolation prize!"
    
    save_owo_data(data)
    
    embed = discord.Embed(
        title="🎰 Slots Result",
        description=f"[ {slot_display} ]\n{outcome}",
        color=discord.Color.gold() if won else discord.Color.red()
    )
    embed.add_field(name="Bet Amount", value=f"{amount} coins", inline=True)
    if won:
        embed.add_field(name="Winnings", value=f"{winnings} coins", inline=True)
    embed.add_field(name="New Balance", value=f"{data[user_id]['balance']} coins", inline=False)
    
    await msg.edit(embed=embed)

@bot.command(name=f'{GAME_PREFIX}daily')
async def owo_daily(ctx):
    """Claim your daily coins (300-5000). Usage: owo daily"""
    data = get_owo_data()
    user_id = str(ctx.author.id)
    
    if user_id not in data:
        data[user_id] = {
            'balance': 0,
            'last_daily': None
        }
    
    now = datetime.datetime.now()
    if data[user_id]['last_daily']:
        last_daily = datetime.datetime.fromisoformat(data[user_id]['last_daily'])
        cooldown = datetime.timedelta(hours=24)
        
        if now - last_daily < cooldown:
            remaining = cooldown - (now - last_daily)
            return await ctx.send(f"⏳ You can claim your next daily in {remaining.seconds // 3600}h {(remaining.seconds % 3600) // 60}m!")
    
    amount = random.randint(300, 5000)
    data[user_id]['balance'] += amount
    data[user_id]['last_daily'] = now.isoformat()
    
    save_owo_data(data)
    
    embed = discord.Embed(
        title="🎁 Daily Reward Claimed!",
        description=f"You received **{amount} coins**!\nYour new balance is **{data[user_id]['balance']} coins**.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command(name=f'{GAME_PREFIX}balance', aliases=[f'{GAME_PREFIX}bal'])
async def owo_balance(ctx, member: discord.Member = None):
    """Check your coin balance. Usage: owo balance [@user] or owo bal [@user]"""
    target = member or ctx.author
    data = get_owo_data()
    user_id = str(target.id)
    
    if user_id not in data:
        balance = 0
    else:
        balance = data[user_id]['balance']
    
    embed = discord.Embed(
        title=f"💰 {target.display_name}'s Balance",
        description=f"**{balance} coins**",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)

@bot.command(name=f'{GAME_PREFIX}addcoin')
@commands.is_owner()
async def owo_addcoin(ctx, member: discord.Member, amount: int):
    """Add coins to a user's balance (Bot owner only). Usage: owo addcoin @user <amount>"""
    if ctx.author.id != BOT_OWNER:
        return await ctx.send("Only the bot owner can use this command!")
    
    if amount <= 0:
        return await ctx.send("Amount must be positive!")
    
    data = get_owo_data()
    user_id = str(member.id)
    
    if user_id not in data:
        data[user_id] = {
            'balance': 0,
            'last_daily': None
        }
    
    data[user_id]['balance'] += amount
    save_owo_data(data)
    
    embed = discord.Embed(
        title="➕ Coins Added",
        description=f"Added **{amount} coins** to {member.mention}'s balance.\nNew balance: **{data[user_id]['balance']} coins**",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command(name=f'{GAME_PREFIX}setgameprefix')
@commands.is_owner()
async def owo_setgameprefix(ctx, new_prefix: str):
    """Change the game command prefix (Bot owner only). Usage: owo setgameprefix <new_prefix>"""
    if ctx.author.id != BOT_OWNER:
        return await ctx.send("Only the bot owner can use this command!")
    
    global GAME_PREFIX
    old_prefix = GAME_PREFIX
    GAME_PREFIX = new_prefix.lower()
    
    game_commands = [
        owo_coinflip, owo_slots, owo_daily, 
        owo_balance, owo_addcoin, owo_setgameprefix
    ]
    
    for cmd in game_commands:
        bot.remove_command(cmd.name)
        
        cmd_name = cmd.__name__.replace('owo_', '').replace(f'{old_prefix}_', '')
        new_name = f"{GAME_PREFIX}{cmd_name}"
        
        new_cmd = commands.Command(
            name=new_name,
            callback=cmd.callback,
            help=cmd.help,
            aliases=getattr(cmd, 'aliases', []),
            checks=cmd.checks
        )
        
        if hasattr(cmd, 'aliases'):
            new_cmd.aliases = [
                alias.replace(old_prefix, GAME_PREFIX) 
                for alias in cmd.aliases
                if alias.startswith(old_prefix)
            ]
        
        bot.add_command(new_cmd)
    
    await ctx.send(f"✅ Game command prefix changed from `{old_prefix}` to `{GAME_PREFIX}`")

# --- Help Command ---

class HelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(command_attrs={
            'help': 'Shows help about the bot, a command, or a category'
        })

    async def send_bot_help(self, mapping):
        ctx = self.context
        embed = discord.Embed(
            title=f"{bot.user.name} Help",
            description=f"Use `{PREFIX}help <command>` for more info on a command.",
            color=discord.Color.blue()
        )
        
        # Music commands
        music_commands = [
            'play', 'skip', 'queue', 'clearqueue', 
            'pause', 'resume', 'stop', 'leave'
        ]
        music_desc = "\n".join(f"`{PREFIX}{cmd}`" for cmd in music_commands)
        embed.add_field(name="🎵 Music Commands", value=music_desc, inline=False)
        
        # Verification commands
        verification_commands = []
        if VERIFICATION_VALO and RIOT_API_KEY:
            verification_commands.append('verifyvalo')
        if VERIFICATION_FIVEM and FIVEM_SERVER:
            verification_commands.extend(['verifyfivem', 'fivemserverlive'])
        if VERIFICATION_SAMP and SAMP_SERVER_IP and SAMP_SERVER_PORT:
            verification_commands.append('verifysamp')
        if VERIFICATION_ROBLOX:
            verification_commands.append('verifyroblox')
            
        if verification_commands:
            verif_desc = "\n".join(f"`{PREFIX}{cmd}`" for cmd in verification_commands)
            embed.add_field(name="🔒 Verification Commands", value=verif_desc, inline=False)
        
        # Moderation commands
        mod_commands = [
    'ban', 'kick', 'timeout', 'slowmode', 'slowoff',
    'setnick', 'resetnick', 'addrole', 'removerole', 'createrole', 'deleterole',
    'getroles', 'lock', 'unlock', 'warn', 'warnings', 'clearwarns',
    'mute', 'unmute', 'purge', 'nuke', 'clone'
]
        mod_desc = "\n".join(f"`{PREFIX}{cmd}`" for cmd in mod_commands)
        embed.add_field(name="🛡️ Moderation Commands", value=mod_desc, inline=False)
        
        # Game commands
        game_commands = ['rps', 'roll', 'flipcoin', 'guess']
        game_desc = "\n".join(f"`{PREFIX}{cmd}`" for cmd in game_commands)
        embed.add_field(name="🎮 Game Commands", value=game_desc, inline=False)
        
        # Owo game commands
        owo_commands = ['coinflip', 'slots', 'daily', 'balance']
        owo_desc = "\n".join(f"{PREFIX}`{GAME_PREFIX}{cmd}`" for cmd in owo_commands)
        embed.add_field(name=f"🎲 {GAME_PREFIX.capitalize()} Game Commands", value=owo_desc, inline=False)
        
        # Fun commands
        fun_commands = ['slap', 'kiss', 'hug']
        fun_desc = "\n".join(f"`{PREFIX}{cmd}`" for cmd in fun_commands)
        embed.add_field(name="😂 Fun Commands", value=fun_desc, inline=False)
        
        # Utility commands
        utility_commands = [
    'poll', 'avatar', 'serverinfo', 'userinfo', 'remind',
    'translate', 'weather', 'calculator', 'calc' , 'vc247'
]

        utility_desc = "\n".join(f"`{PREFIX}{cmd}`" for cmd in utility_commands)
        embed.add_field(name="🔧 Utility Commands", value=utility_desc, inline=False)
        
        await ctx.send(embed=embed)

    async def send_command_help(self, command):
        ctx = self.context
        embed = discord.Embed(
            title=f"Command: {PREFIX}{command.name}",
            description=command.help or "No description available",
            color=discord.Color.green()
        )
        
        if command.help and "Usage:" in command.help:
            usage = command.help.split("Usage:")[1].strip()
            embed.add_field(name="Usage", value=f"`{usage}`", inline=False)
        
        if command.aliases:
            embed.add_field(name="Aliases", value=", ".join(f"`{alias}`" for alias in command.aliases), inline=False)
        
        if command.name in ['slap', 'kiss', 'hug', 'poll', 'avatar', 'userinfo']:
            example = f"Example: `{PREFIX}{command.name} @user`"
            embed.add_field(name="Example", value=example, inline=False)
        
        await ctx.send(embed=embed)

    async def send_error_message(self, error):
        ctx = self.context
        embed = discord.Embed(
            title="Error",
            description=error,
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

bot.help_command = HelpCommand()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"❌ You don't have permission to use this command!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: `{error.param.name}`\nUsage: `{PREFIX}{ctx.command.name} {ctx.command.signature}`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Invalid argument: {error}\nUsage: `{PREFIX}{ctx.command.name} {ctx.command.signature}`")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ This command is on cooldown. Try again in {error.retry_after:.1f} seconds.")
    else:
        print(f"Ignoring exception in command {ctx.command}:", error)
        await ctx.send(f"⚠ An unexpected error occurred while executing that command.")

@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user:
        return
    
    for guild_id, player_data in current_players.items():
        voice_client = player_data['voice_client']
        if voice_client and voice_client.is_connected():
            if guild_id in PERMA_VC:
                continue
                
            if len(voice_client.channel.members) == 1:
                beautiful_print(f"🔇 Voice channel empty. Disconnecting...", "─")
                await voice_client.disconnect()
                if guild_id in current_players:
                    if 'control_message' in current_players[guild_id]:
                        try:
                            await current_players[guild_id]['control_message'].delete()
                        except:
                            pass
                    del current_players[guild_id]
                if guild_id in song_queues:
                    song_queues[guild_id].clear()

TOKEN = os.getenv('DISCORD_TOKEN') or 'YOUR_BOT_TOKEN_HERE'

if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        beautiful_print(f"❌ Failed to start bot: {e}", "!")
        sys.exit(1)
