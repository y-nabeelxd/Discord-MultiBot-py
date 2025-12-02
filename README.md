# Discord MultiBot (Python)

**Author:** [y-nabeelxd](https://github.com/y-nabeelxd)

A **feature-rich Discord bot** made with **Python** and **discord.py**.

This bot comes with **music playback**, **Roblox verification**, **FiveM verification**, **moderation tools**, and **fun commands**.
> ⚠️ *Valorant and SA:MP verifications are under maintenance (fix coming soon).*

---

## ✨ Features
- **🎵 Music Player** — Play songs from YouTube (no cookies, API keys, or tokens needed)
- **🛡️ Moderation Tools** — Ban, kick, timeout, slowmode, set nicknames, and manage roles
- **🔒 Verification Systems** — Roblox and FiveM verification with role assignment
- **🎮 Fun & Mini Games** — Rock-Paper-Scissors, Dice rolls, Coin flips, Guessing game
- **📊 Owo Economy Games** — Slots, Coinflip, Daily rewards with coin system
- **📆 Polls & Utilities** — Create polls, reminders, server info, and user info
- **📌 FiveM Server Status** — Live server status updates with `!fivemserverlive`
- **🔧 Slash Commands** — Modern `/command` interface for moderation and management alongside traditional prefix commands
- **🚀 Future Plans** — More useful and better commands will be added soon!

---

## 📂 Project Structure
```
Discord-MultiBot-py/
├── bot.py
├── LICENCE
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup & Installation
1. **Clone the repository:**
```
git clone https://github.com/y-nabeelxd/Discord-MultiBot-py
cd Discord-MultiBot-py
```
2. **Install dependencies:**
```
pip install -r requirements.txt
```
3. **Edit bot configuration:**
- **Bot Token:** 
Open `bot.py` and replace:
```
TOKEN = os.getenv('DISCORD_TOKEN') or 'BOT_TOKEN'
```
with your bot token inside 'BOT_TOKEN' or set DISCORD_TOKEN as an environment variable.
- **Prefix:**
Change the command prefix:
```
PREFIX = "!"
```
(This is around line **41** in `bot.py`)

4. **Run the bot:**
```
python bot.py
```

---

## 🔧 Slash Commands (New Feature ✨)

The bot now supports modern **slash commands** alongside traditional prefix commands for better user experience!

### 📝 Moderation Slash Commands:
- `/kick @user [reason]` - Kick users with reason logging
- `/ban @user [reason]` - Ban users with reason logging
- `/clear <amount>` - Bulk delete messages
- `/unban <username/id>` - Remove users from ban list
- `/setnick <new_name> [@user]` - Set user nicknames
- `/role_give @user @role` - Give role to user
- `/role_remove @user @role` - Remove role from user

### 🔊 Voice Channel Management:
- `/move_all [channel]` - Move all members to a voice channel
- `/move_user @user [channel]` - Move specific user to voice channel
- `/moveme <channel>` - Move yourself to a voice channel
- `/move_role @role [channel]` - Move all members with a role to voice channel

### ℹ️ Utility Slash Commands:
- `/invite` - Get bot invite link for your server

> ⚠️ **Note:** Most slash commands require **bot owner** or **server owner** permissions for security.

---

## 🎵 Music Commands
- `!play <song>` — Play a song or add to queue 
- `!skip` — Skip current song 
- `!pause` — Pause playback 
- `!resume` — Resume playback 
- `!queue` — Show current queue 
- `!stop` — Stop playback and clear queue 
- `!leave` — Make the bot leave the voice channel 

---

## 🛡️ Moderation Commands
- `!ban @user [reason]` — Ban a member 
- `!kick @user [reason]` — Kick a member 
- `!timeout @user 30m [reason]` — Timeout a member 
- `!slowmode 30s` — Set channel slowmode 
- `!addrole @user @Role` — Add a role 
- `!removerole @user @Role` — Remove a role 
- `!setnick @user NewName` — Change nickname 
- `!lock [#channel] [@role]` — Lock a channel 
- `!unlock [#channel] [@role]` — Unlock a channel
- `!nuke [channel]` - Clone and delete a channel to remove all messages
- `!clone [channel]` - Clone a text channel
- `!slowoff [channel]` - Remove slowmode from a channel
- `!createrole <name> [hex color] [reason]` - Create a new role
- `!deleterole @role` - Delete a role
- `!resetnick @user` - Reset a member's nickname
- `!mute @user [reason]` - Mute a member in text channels
- `!unmute @user` - Unmute a member
- `!clearwarns @user` - Clear all warnings for a member

---

## 🔒 Verification
- **Roblox**: `!verifyroblox <username>` (Working ✅) 
- **FiveM**: `!verifyfivem <username>` (Working ✅) 
- **FiveM Server Status**: `!fivemserverlive [#channel]`
- **SA:MP Status**: `!sampstatus` - Check SA:MP server status (But Under the maintenance ❌)
- **SA:MP**: `!verifysamp <username>` (Under Maintenance ❌) 
- **Valorant**: `!verifyvalo <Username#Tag>` (Under Maintenance ❌) 

---

## 🎮 Owo Economy Games
- `owo coinflip <amount> [heads/tails]` - Flip a coin with your coins
- `owo slots <amount>` - Play slots with your coins
- `owo daily` - Claim your daily coins (300-5000)
- `owo balance [@user]` - Check coin balance

---

## 🎮 Fun & Game Commands
- `!rps rock|paper|scissors` - Play Rock Paper Scissors
- `!roll 2d20` - Roll dice in NdN format (alias: `!dice`)
- `!flipcoin` - Flip a coin (alias: `!flip`)
- `!guess 5` - Guess a number between 1 and 100
- `!slap @user` - Slap someone!
- `!kiss @user` - Kiss someone!
- `!hug @user` - Hug someone!

---

## 📆 Utility Commands
- `!translate <target_lang> <text>` - Translate text to another language
- `!weather <city>` - Get weather for a location
- `!calculator <expression>` - Evaluate a math expression (alias: `!calc`)
- `!remind <time> <message>` - Set a reminder
- `!vc247` - Make the bot stay in voice channel 24/7
- `!serverinfo` - Get server information
- `!userinfo [@user]` - Get user information
- `!avatar [@user]` - Get a user's avatar
- `!poll "Question" "Option1" "Option2"` - Create a poll

---

## ⚠️ Current Status
- **Roblox Verification**: **Working Perfectly** ✅ 
- **FiveM Verification**: **Working (Improved)** ✅ 
- **SA:MP, Valorant**: **Currently unavailable (fix in progress)** ❌ 

---

## 🚀 Future Updates
- Advanced moderation tools 
- New verification systems 
- More fun commands & games 
- Economy system improvements

---

## 👤 Author
**[y-nabeelxd](https://github.com/y-nabeelxd)**

_If you like this project, star ⭐ the repository!_

