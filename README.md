<div align="center">

# 🤖 Discord MultiBot

**A modern, plugin-based multipurpose Discord bot — music, verification, moderation & more.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![discord.py](https://img.shields.io/badge/discord.py-2.3-5865F2?logo=discord&logoColor=white)](https://discordpy.readthedocs.io)
[![License](https://img.shields.io/github/license/y-nabeelxd/Discord-MultiBot-py)](LICENSE)
[![Stars](https://img.shields.io/github/stars/y-nabeelxd/Discord-MultiBot-py?style=social)](https://github.com/y-nabeelxd/Discord-MultiBot-py)

**Author:** [y-nabeelxd](https://github.com/y-nabeelxd)

</div>

---

## ✨ Features

| Category | Highlights |
|----------|-----------|
| 🎵 **Music** | YouTube playback, queue, skip, pause, resume — fixed & stable |
| 🛡️ **Moderation** | Ban, kick, timeout, lock, warn, mute, purge, nuke, roles |
| 🔒 **Verification** | Roblox (code-in-bio) · FiveM (player lookup) · SA:MP · Valorant |
| 🏆 **Leveling** | Passive XP system, user ranks, and server leaderboards |
| 🎫 **Tickets** | Support panel with private threads and interactive buttons |
| 🎉 **Giveaways** | Timed giveaways with interactive join buttons and auto-rollers |
| 🎮 **Fun & Games** | RPS, dice, coin flip, 8-ball, Trivia, Tic-Tac-Toe, slap, kiss, hug |
| 🪙 **Economy** | owo slots, coinflip, daily rewards, balance |
| 🔧 **Utility** | Weather, translate, poll, remind, avatar, server/user info, snipe, afk |
| ⚡ **Slash Commands** | Modern `/command` interface for moderation and voice management |
| 🧩 **Plugin System** | Every command category lives in its own plugin file |

---

## 📂 Project Structure

```
Discord-MultiBot-py/
├── bot.py                     # Entry point — loads all plugins
├── config.py                  # All settings read from .env
├── utils.py                   # Shared helpers & API calls
├── .env                       # Your secrets (gitignored)
├── .env.example               # Template — copy and fill in
├── requirements.txt
├── db/                        # Auto-created JSON data files
└── plugins/
    ├── music/
    │   ├── player.py          # yt-dlp engine (fixed)
    │   └── music_cog.py       # Music commands + button controls
    ├── moderation/
    │   └── moderation_cog.py  # All moderation commands
    ├── verification/
    │   └── verification_cog.py
    ├── fun/
    │   └── fun_cog.py
    ├── economy/
    │   └── economy_cog.py
    ├── utility/
    │   └── utility_cog.py
    ├── leveling/
    │   └── leveling_cog.py    # XP and Leveling system
    ├── ticket/
    │   └── ticket_cog.py      # Support Ticket system
    ├── giveaway/
    │   └── giveaway_cog.py    # Timed giveaway system
    └── slash/
        └── slash_cog.py       # All /slash commands
```

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/y-nabeelxd/Discord-MultiBot-py
cd Discord-MultiBot-py
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

> **Note:** FFmpeg must also be installed and on your PATH for music to work.
> - Windows: [ffmpeg.org/download.html](https://ffmpeg.org/download.html)
> - Linux: `sudo apt install ffmpeg`

### 3. Configure your `.env` file
```bash
cp .env.example .env
```
Then open `.env` and fill in your values:

> [!WARNING]
> **Privileged Intents Required**
> You must enable all 3 Privileged Intents (**Presence**, **Server Members**, **Message Content**) in the [Discord Developer Portal](https://discord.com/developers/applications) for this bot to function correctly. If you do not, the bot will not respond to commands.

```env
DISCORD_TOKEN=your_bot_token_here
PREFIX=!
GAME_PREFIX=owo
BOT_OWNER_ID=your_discord_user_id

# Optional
WEATHER_API_KEY=your_openweathermap_key
YT_COOKIES=cookies.txt

# Enable verifications
VERIFICATION_ROBLOX=true
ROBLOX_ROLE_ID=123456789

VERIFICATION_FIVEM=true
FIVEM_SERVER=your_ip:port
FIVEM_ROLE_ID=123456789
```

See [.env.example](.env.example) for all available options.

### 4. Run the bot
```bash
python bot.py
```

---

## ⚡ Hybrid Commands (Slash + Prefix)

> **Almost ALL commands in this bot are Hybrid Commands!**
> This means any command you see below with a prefix (like `!play` or `owo slots`) can also be used as a slash command (like `/play` or `/slots`). The bot perfectly synchronizes both!

### Dedicated Voice Slash Commands (Owner Only)
| Command | Description |
|---------|-------------|
| `/move_all [channel]` | Move all members to a voice channel |
| `/move_user @user [channel]` | Move a specific user |
| `/moveme <channel>` | Move yourself |
| `/move_role @role [channel]` | Move all members with a role |

### Utility
| Command | Description |
|---------|-------------|
| `/sc` | Bot info & GitHub link |
| `/invite` | Get bot invite link |

---

## 🎵 Music Commands

| Command | Description |
|---------|-------------|
| `!play <song or URL>` | Search YouTube and play — shows a select menu |
| `!lyrics [song]` | Get song lyrics |
| `!skip` | Skip the current song |
| `!pause` | Pause playback |
| `!resume` | Resume playback |
| `!queue` | Show the song queue |
| `!clearqueue` | Clear the queue |
| `!stop` | Stop and clear the queue |
| `!leave` | Disconnect from voice |

> Music also includes interactive **Pause / Resume / Skip / Stop** buttons on the Now Playing message.

---

## 🛡️ Moderation Commands

| Command | Description |
|---------|-------------|
| `!ban @user [reason]` | Ban a member |
| `!kick @user [reason]` | Kick a member |
| `!timeout @user 30m [reason]` | Timeout (1s/1m/1h/1d) |
| `!mute @user [reason]` | Mute in text channels |
| `!unmute @user` | Unmute |
| `!warn @user [reason]` | Issue a warning |
| `!warnings [@user]` | View warnings |
| `!clearwarns @user` | Clear all warnings |
| `!purge [amount]` | Delete messages (max 100) |
| `!nuke [#channel]` | Clone & delete a channel |
| `!clone [#channel]` | Clone a channel |
| `!lock [#channel] [@role]` | Lock a channel |
| `!unlock [#channel] [@role]` | Unlock a channel |
| `!slowmode 30s` | Set slowmode |
| `!slowoff [#channel]` | Remove slowmode |
| `!addrole @user @role` | Add a role |
| `!removerole @user @role` | Remove a role |
| `!createrole <name> [color]` | Create a new role |
| `!deleterole @role` | Delete a role |
| `!setnick @user <name>` | Set nickname |
| `!resetnick @user` | Reset nickname |
| `!getroles [@user]` | List a user's roles |

---

## 🏆 Leveling & XP

| Command | Description |
|---------|-------------|
| `!rank [@user]` | View your level, XP, and rank |
| `!leaderboard` | View the top 10 most active members |

Users automatically earn 15-25 XP per minute while chatting.

---

## 🎫 Tickets & 🎉 Giveaways

| Command | Description |
|---------|-------------|
| `!ticket setup` | Create the "Create Ticket" panel |
| `!ticket close` | Close a ticket (or use the button) |
| `!gstart <time> <winners> <prize>` | Start a giveaway (e.g. `!gstart 1h 1w Nitro`) |
| `!gend <msg_id>` | End a giveaway early |
| `!greroll <msg_id>` | Reroll a giveaway winner |

---

## 🔒 Verification

| System | Command | Status |
|--------|---------|--------|
| **Roblox** | `!verifyroblox <username>` | ✅ Working |
| **FiveM** | `!verifyfivem <name or ID>` | ✅ Working |
| **FiveM Live** | `!fivemserverlive [#channel]` | ✅ Working |
| **SA:MP** | `!verifysamp [code/name]` | ✅ Working (MySQL/RCON/Basic) |
| **SA:MP Status** | `!sampstatus` | ✅ Working |
| **Valorant** | `!verifyvalo <Name#Tag>` | ⚠️ Maintenance |

Enable each system in your `.env` file.

---

## 🪙 Economy Commands (owo)

| Command | Description |
|---------|-------------|
| `owo daily` | Claim 300–5000 coins daily |
| `owo balance [@user]` | Check your balance |
| `owo coinflip <amount> [heads/tails]` | Bet on a coin flip |
| `owo slots <amount>` | Spin the slot machine |
| `owo work` | Work to earn coins |
| `owo pay @user <amount>` | Transfer coins to friends |
| `owo rob @user` | Try to steal coins |

---

## 🎮 Fun Commands

| Command | Description |
|---------|-------------|
| `!rps rock\|paper\|scissors` | Rock Paper Scissors |
| `!roll [NdN]` | Roll dice (e.g. `!roll 2d20`) |
| `!flipcoin` | Flip a coin |
| `!guess <1-10>` | Guess the secret number |
| `!8ball <question>` | Ask the magic 8-ball |
| `!tictactoe @user` | Play Tic-Tac-Toe via buttons |
| `!meme` | Get a random meme |
| `!ship @user` | Love compatibility calculator |
| `!minesweeper` | Play minesweeper (spoiler tags) |
| `!slap @user` | Slap someone! |
| `!kiss @user` | Kiss someone! |
| `!hug @user` | Hug someone! |

---

## 🔧 Utility Commands

| Command | Description |
|---------|-------------|
| `!translate <lang> <text>` | Translate text |
| `!weather <city>` | Current weather |
| `!calc <expression>` | Math calculator |
| `!botinfo` | Bot stats and uptime |
| `!roleinfo @role` | Role details and permissions |
| `!poll "Q" "A" "B"` | Create a reaction poll |
| `!remind <time> <msg>` | Set a reminder (e.g. `1h30m`) |
| `!vc247` | Keep bot in VC 24/7 |
| `!avatar [@user]` | Show user avatar |
| `!serverinfo` | Server information |
| `!userinfo [@user]` | User information |
| `!afk [reason]` | Go AFK (notifies anyone who pings you) |
| `!snipe` | Retrieve the last deleted message |

---

## 📦 Requirements

- **Python 3.10+**
- **FFmpeg** (for music)
- See [requirements.txt](requirements.txt) for Python packages

---

## 👤 Author

**[y-nabeelxd](https://github.com/y-nabeelxd)**

_If you like this project, give it a ⭐ star on GitHub!_
