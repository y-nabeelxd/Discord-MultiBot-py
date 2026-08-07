"""
plugins/fun/fun_cog.py
Fun and game commands.
"""
import random
import aiohttp
import html
import discord
from discord.ext import commands

class TicTacToeButton(discord.ui.Button):
    def __init__(self, x, y):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToe = self.view
        
        if interaction.user != view.current_player:
            return await interaction.response.send_message("It's not your turn!", ephemeral=True)
            
        self.style = discord.ButtonStyle.primary if view.current_player == view.player1 else discord.ButtonStyle.danger
        self.label = "X" if view.current_player == view.player1 else "O"
        self.disabled = True
        
        view.board[self.y][self.x] = view.current_player
        
        winner = view.check_winner()
        if winner:
            for child in view.children:
                child.disabled = True
            await interaction.response.edit_message(content=f"🎉 **{winner.display_name}** won!", view=view)
            return
            
        if view.is_tie():
            await interaction.response.edit_message(content="🤝 It's a tie!", view=view)
            return
            
        view.current_player = view.player2 if view.current_player == view.player1 else view.player1
        await interaction.response.edit_message(content=f"It is now **{view.current_player.display_name}**'s turn.", view=view)


class TicTacToe(discord.ui.View):
    def __init__(self, player1, player2):
        super().__init__()
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.board = [[None, None, None], [None, None, None], [None, None, None]]
        
        for y in range(3):
            for x in range(3):
                self.add_item(TicTacToeButton(x, y))

    def check_winner(self):
        for y in range(3):
            if self.board[y][0] == self.board[y][1] == self.board[y][2] and self.board[y][0] is not None:
                return self.board[y][0]
        for x in range(3):
            if self.board[0][x] == self.board[1][x] == self.board[2][x] and self.board[0][x] is not None:
                return self.board[0][x]
        if self.board[0][0] == self.board[1][1] == self.board[2][2] and self.board[0][0] is not None:
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] and self.board[0][2] is not None:
            return self.board[0][2]
        return None

    def is_tie(self):
        for y in range(3):
            for x in range(3):
                if self.board[y][x] is None:
                    return False
        return True


class TriviaButton(discord.ui.Button):
    def __init__(self, label):
        super().__init__(style=discord.ButtonStyle.secondary, label=label[:80])
        self.answer = label

    async def callback(self, interaction: discord.Interaction):
        view: TriviaView = self.view
        if view.answered:
            return
        
        view.answered = True
        for child in view.children:
            child.disabled = True
            if child.answer == view.correct:
                child.style = discord.ButtonStyle.success
            elif child.answer == self.answer:
                child.style = discord.ButtonStyle.danger
                
        if self.answer == view.correct:
            content = f"✅ **{interaction.user.display_name}** got it right!"
        else:
            content = f"❌ **{interaction.user.display_name}** got it wrong. The correct answer was **{view.correct}**."
            
        await interaction.response.edit_message(content=content, view=view)


class TriviaView(discord.ui.View):
    def __init__(self, correct, answers):
        super().__init__(timeout=30)
        self.correct = correct
        self.answered = False
        for answer in answers:
            self.add_item(TriviaButton(answer))
            
    async def on_timeout(self):
        if not self.answered:
            self.answered = True
            for child in self.children:
                child.disabled = True
            try:
                await self.message.edit(content=f"⏰ Time's up! The correct answer was **{self.correct}**.", view=self)
            except:
                pass


class FunCog(commands.Cog, name="Fun"):
    """🎮 Fun and game commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["rockpaperscissors"])
    async def rps(self, ctx: commands.Context, choice: str):
        """Play Rock Paper Scissors. Usage: !rps rock|paper|scissors"""
        choices = ["rock", "paper", "scissors"]
        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        user_choice = choice.lower()
        if user_choice not in choices:
            return await ctx.send("Please choose rock, paper, or scissors!")

        bot_choice = random.choice(choices)
        if user_choice == bot_choice:
            result = "It's a tie! 🤝"
        elif (
            (user_choice == "rock" and bot_choice == "scissors")
            or (user_choice == "paper" and bot_choice == "rock")
            or (user_choice == "scissors" and bot_choice == "paper")
        ):
            result = "You win! 🎉"
        else:
            result = "I win! 😎"

        embed = discord.Embed(title="🪨 📄 ✂️ Rock Paper Scissors", color=discord.Color.blurple())
        embed.add_field(name="Your Choice", value=f"{emojis[user_choice]} {user_choice.capitalize()}", inline=True)
        embed.add_field(name="My Choice", value=f"{emojis[bot_choice]} {bot_choice.capitalize()}", inline=True)
        embed.add_field(name="Result", value=result, inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=["dice"])
    async def roll(self, ctx: commands.Context, dice: str = "1d6"):
        """Roll dice in NdN format. Usage: !roll 2d20"""
        try:
            n, sides = map(int, dice.lower().split("d"))
        except ValueError:
            return await ctx.send("Format must be NdN, e.g. `!roll 2d20`")
        if n > 20 or sides > 100:
            return await ctx.send("Max 20 dice with 100 sides each!")
        results = [random.randint(1, sides) for _ in range(n)]
        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"Rolling **{dice}**",
            color=discord.Color.random(),
        )
        embed.add_field(name="Results", value=", ".join(map(str, results)), inline=True)
        embed.add_field(name="Total", value=sum(results), inline=True)
        if n == 1 and sides == 20:
            if results[0] == 20:
                embed.set_footer(text="Nat 20! Critical success! 🎯")
            elif results[0] == 1:
                embed.set_footer(text="Critical fail! 💀")
        await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=["flip"])
    async def flipcoin(self, ctx: commands.Context):
        """Flip a coin. Usage: !flipcoin"""
        result = random.choice(["Heads", "Tails"])
        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"The coin landed on… **{result}**!",
            color=discord.Color.gold(),
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def guess(self, ctx: commands.Context, number: int):
        """Guess a number between 1 and 10. Usage: !guess 5"""
        if not 1 <= number <= 10:
            return await ctx.send("Please guess between 1 and 10!")
        secret = random.randint(1, 10)
        if number == secret:
            msg = f"🎉 Correct! The number was **{secret}**."
            color = discord.Color.green()
        else:
            msg = f"❌ Wrong! The number was **{secret}**. Try again!"
            color = discord.Color.red()
        embed = discord.Embed(title="🔢 Number Guessing Game", description=msg, color=color)
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def slap(self, ctx: commands.Context, member: discord.Member):
        """Slap someone! Usage: !slap @user"""
        reactions = ["(╯°□°）╯︵ ┻━┻", "⊙﹏⊙", "(ﾉ`Д´)ﾉ", "ಠ_ಠ", "(•̀o•́)ง"]
        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(name=f"{ctx.author.display_name} slapped {member.display_name} {random.choice(reactions)}")
        embed.set_image(url="https://c.tenor.com/XiYuU9h44-AAAAAC/tenor.gif")
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def kiss(self, ctx: commands.Context, member: discord.Member):
        """Kiss someone! Usage: !kiss @user"""
        reactions = ["(づ￣ ³￣)づ", "(*˘︶˘*).｡.:*♡", "(っ˘ω˘ς )", "♡(˃͈ દ ˂͈ ༶ )", "(´∀｀)♡"]
        embed = discord.Embed(color=discord.Color.pink())
        embed.set_author(name=f"{ctx.author.display_name} kissed {member.display_name} {random.choice(reactions)}")
        embed.set_image(url="https://www.icegif.com/wp-content/uploads/2022/08/icegif-1235.gif")
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def hug(self, ctx: commands.Context, member: discord.Member):
        """Hug someone! Usage: !hug @user"""
        reactions = ["(⊃｡•́‿•̀｡)⊃", "(っ´▽｀)っ", "⊂((・▽・))⊃", "(つ≧▽≦)つ", "╰(*´︶`*)╯"]
        embed = discord.Embed(color=discord.Color.gold())
        embed.set_author(name=f"{ctx.author.display_name} hugged {member.display_name} {random.choice(reactions)}")
        embed.set_image(url="https://usagif.com/wp-content/uploads/gif/anime-hug-59.gif")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="8ball")
    async def eight_ball(self, ctx: commands.Context, *, question: str):
        """Ask the magic 8-ball a question. Usage: !8ball <question>"""
        responses = [
            "It is certain.", "It is decidedly so.", "Without a doubt.",
            "Yes - definitely.", "You may rely on it.", "As I see it, yes.",
            "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
            "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
            "Cannot predict now.", "Concentrate and ask again.",
            "Don't count on it.", "My reply is no.", "My sources say no.",
            "Outlook not so good.", "Very doubtful."
        ]
        embed = discord.Embed(title="🎱 Magic 8-Ball", color=discord.Color.dark_theme())
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=random.choice(responses), inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def tictactoe(self, ctx: commands.Context, member: discord.Member):
        """Play Tic-Tac-Toe with someone. Usage: !tictactoe @user"""
        if member == ctx.author or member.bot:
            return await ctx.send("❌ You can't play with yourself or a bot!")
            
        view = TicTacToe(ctx.author, member)
        await ctx.send(f"Tic-Tac-Toe: **{ctx.author.display_name}** vs **{member.display_name}**\nIt is **{ctx.author.display_name}**'s turn (X)!", view=view)

    @commands.hybrid_command()
    async def trivia(self, ctx: commands.Context):
        """Play a game of trivia. Usage: !trivia"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("https://opentdb.com/api.php?amount=1") as resp:
                    if resp.status != 200:
                        return await ctx.send("❌ Failed to fetch trivia question.")
                    data = await resp.json()
            except Exception:
                return await ctx.send("❌ Failed to fetch trivia question.")

        result = data["results"][0]
        question = html.unescape(result["question"])
        correct = html.unescape(result["correct_answer"])
        incorrect = [html.unescape(ans) for ans in result["incorrect_answers"]]
        
        answers = incorrect + [correct]
        random.shuffle(answers)
        
        embed = discord.Embed(
            title="🧠 Trivia Time!",
            description=f"**Category:** {result['category']}\n**Difficulty:** {result['difficulty'].capitalize()}\n\n{question}",
            color=discord.Color.blue()
        )
        
        view = TriviaView(correct, answers)
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg



    @commands.hybrid_command()
    async def meme(self, ctx: commands.Context):
        """Get a random meme from Reddit."""
        msg = await ctx.send("Fetching a fresh meme...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://meme-api.com/gimme") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        embed = discord.Embed(title=data.get("title", "Meme"), url=data.get("postLink"), color=discord.Color.random())
                        embed.set_image(url=data.get("url"))
                        embed.set_footer(text=f"👍 {data.get('ups', 0)} | r/{data.get('subreddit')}")
                        await msg.edit(content=None, embed=embed)
                    else:
                        await msg.edit(content="❌ Couldn't fetch a meme right now.")
        except Exception:
            await msg.edit(content="❌ An error occurred while fetching the meme.")

    @commands.hybrid_command()
    async def ship(self, ctx: commands.Context, user1: discord.Member, user2: discord.Member = None):
        """Calculate the love compatibility between two users."""
        if not user2:
            user2 = user1
            user1 = ctx.author

        if user1 == user2:
            return await ctx.send("You can't ship someone with themselves! 💔")

        # Create a deterministic seed based on their IDs so the result is always the same for the pair
        random.seed(user1.id + user2.id)
        percentage = random.randint(0, 100)
        random.seed() # reset seed

        bars = int((percentage / 100) * 10)
        progress_bar = "█" * bars + "░" * (10 - bars)

        if percentage >= 90:
            emoji = "💖"
            comment = "True Love!"
        elif percentage >= 70:
            emoji = "💕"
            comment = "Great Match!"
        elif percentage >= 40:
            emoji = "❤️"
            comment = "There's potential."
        elif percentage >= 20:
            emoji = "💔"
            comment = "Might be tough."
        else:
            emoji = "💀"
            comment = "Absolutely not."

        embed = discord.Embed(
            title=f"Love Calculator {emoji}",
            description=f"**{user1.display_name}** x **{user2.display_name}**\n\n**{percentage}%** `[{progress_bar}]`\n*\"{comment}\"*",
            color=discord.Color.pink()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=["ms"])
    async def minesweeper(self, ctx: commands.Context):
        """Play a game of minesweeper."""
        columns = 9
        rows = 9
        bombs = 10

        grid = [[0 for _ in range(columns)] for _ in range(rows)]
        bomb_positions = []

        while len(bomb_positions) < bombs:
            x = random.randint(0, columns - 1)
            y = random.randint(0, rows - 1)
            if (x, y) not in bomb_positions:
                bomb_positions.append((x, y))
                grid[y][x] = 'B'

        for y in range(rows):
            for x in range(columns):
                if grid[y][x] == 'B':
                    continue
                count = 0
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dy == 0 and dx == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < columns and 0 <= ny < rows and grid[ny][nx] == 'B':
                            count += 1
                grid[y][x] = count

        number_emojis = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"]
        board_str = ""
        for y in range(rows):
            for x in range(columns):
                val = grid[y][x]
                if val == 'B':
                    emoji = "💣"
                else:
                    emoji = number_emojis[val]
                board_str += f"||{emoji}||"
            board_str += "\n"

        await ctx.send(f"**Minesweeper** ({bombs} bombs)\n{board_str}")

async def setup(bot: commands.Bot):

    await bot.add_cog(FunCog(bot))
