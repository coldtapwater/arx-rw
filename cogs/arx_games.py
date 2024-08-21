import discord
from discord.ext import commands
import aiohttp
import random
import asyncio
import utils.my_emojis as my_emojis
import aiosqlite
import time
import utils.db_funcs as db_funcs

class HangmanGame:
    def __init__(self, word):
        self.word = word
        self.guessed_letters = []
        self.mistakes = 0
        self.stages = [
            "😶",  # 0 mistakes
            "😕",  # 1 mistake
            "🙁",  # 2 mistakes
            "☹️",  # 3 mistakes
            "😧",  # 4 mistakes
            "😟",  # 5 mistakes
            "😨",  # 6 mistakes
            "😱",  # 7 mistakes (lost)
        ]

    def render_hangman(self):
        return self.stages[self.mistakes]

    def get_display_word(self):
        return ' '.join([letter if letter in self.guessed_letters else '_' for letter in self.word])

    def guess(self, letter):
        if letter in self.word:
            self.guessed_letters.append(letter)
            return True
        else:
            self.guessed_letters.append(letter)
            self.mistakes += 1
            return False

    def is_won(self):
        return all(letter in self.guessed_letters for letter in self.word)

    def is_lost(self):
        return self.mistakes >= len(self.stages) - 1

class Games(commands.Cog):
    def __init__(self, bot, embed_color):
        self.bot = bot
        self.embed_color = embed_color

    @commands.hybrid_command()
    async def flip(self, ctx):
        """Flips a coin."""
        coin = random.randint(0, 1)
        adjectives = ["spitefully", "willingly", "but i ain't happy about it", "with all my heart", "with all my life", "with all my mind", "but i hate you for it"]
        adj = random.choice(adjectives)
        embed = discord.Embed(title=f"{my_emojis.PREFIX} Flipping your coin {adj}", description=f"**{ctx.author.mention}** flipped a coin and got...", color=discord.Color.from_str(self.embed_color))
        if coin == 0:
            embed.add_field(name="Heads", value="\u200b")
        else:
            embed.add_field(name="Tails", value="\u200b")
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def wouldyourather(self, ctx):
        """Would you rather?

        Provides two options that are both fairly undesirable.
        """
        options = [
            "Wear a suit made entirely of duct tape for a day",
            "Have your alarm clock sound like a screaming goat",
            "Eat an entire jar of mayonnaise in one sitting",
            "Wear socks soaked in pickle juice for a day",
            "Sing the national anthem in the middle of a busy shopping mall",
            "Let a clown do your makeup for a formal event",
            "Wear a hat made of live bees",
            "Have your phone ring loudly with an embarrassing ringtone in a silent room full of people",
            "Wear clothes two sizes too small for a week",
            "Drink a smoothie made of blended leftovers from a week",
            "Have to talk in rhymes for an entire day",
            "Have a spider crawl on your face while you sleep",
            "Eat a sandwich filled with random condiments from your fridge",
            "Wear your clothes inside out for a week",
            "Walk around with a visible stain on your pants for a day",
            "Have an ice cube down your shirt for an hour",
            "Eat a salad made of grass",
            "Have a bird nest in your hair for a day",
            "Walk barefoot on a bed of Legos",
            "Sing everything you say for a day",
            "Have to wear a trash bag as clothing for a day",
            "Take a cold shower every day for a month",
            "Wear a pair of underwear on your head for an hour",
            "Eat a bowl of cereal with orange juice instead of milk",
            "Brush your teeth with mustard",
            "Dance like nobody's watching in a crowded place",
            "Wear a paper bag on your head with a funny face drawn on it for a day",
            "Drink a concoction of every soda flavor available at a drink dispenser",
            "Wear gloves filled with jelly for an hour",
            "Use sandpaper as toilet paper"
        ]

        choice1, choice2 = random.sample(options, 2)

        embed = discord.Embed(title=f"{my_emojis.PREFIX} Would you rather?", color=discord.Color.from_str(self.embed_color))
        embed.add_field(name=f"<:choice_1:1255745220105207929> {choice1}", value="\u200b", inline=False)
        embed.add_field(name=f"<:choice_2:1255745258801856576> {choice2}", value="\u200b", inline=False)

        buttons = [
            discord.ui.Button(label="Choice 1", style=discord.ButtonStyle.gray, custom_id=f"wyr:{choice1}"),
            discord.ui.Button(label="Choice 2", style=discord.ButtonStyle.gray, custom_id=f"wyr:{choice2}"),
        ]

        view = discord.ui.View()
        view.add_item(buttons[0])
        view.add_item(buttons[1])

        message = await ctx.send(embed=embed, view=view)

        responses = {choice1: [], choice2: []}

        def check(interaction: discord.Interaction):
            return interaction.message and interaction.message.id == message.id

        while True:
            try:
                interaction = await self.bot.wait_for("interaction", check=check)
            except asyncio.TimeoutError:
                break

            choice = interaction.data["custom_id"].split(":")[1]
            if interaction.user not in responses[choice]:
                responses[choice].append(interaction.user)

                # Update the embed with the new response
                embed.clear_fields()
                embed.add_field(name=f"<:choice_1:1255745220105207929> {choice1}",
                                value="<:discord_reply:1255744704168071189> ".join([f"<@{user.id}>" for user in responses[choice1]]), inline=False)
                embed.add_field(name=f"<:choice_2:1255745258801856576> {choice2}",
                                value="<:discord_reply:1255744704168071189> ".join([f"<@{user.id}>" for user in responses[choice2]]), inline=False)

                await interaction.response.edit_message(embed=embed, view=view)

            for button in buttons:
                if button.custom_id == interaction.data["custom_id"]:
                    button.style = discord.ButtonStyle.grey
                    button.disabled = True

            await interaction.message.edit(embed=embed, view=view)

        # Disable all buttons after timeout
        for button in buttons:
            button.disabled = True

        await message.edit(embed=embed, view=None)


    @commands.hybrid_command()
    async def connect4(self, ctx, opponent: discord.Member):
        """Start a Connect 4 game with another member."""
        if opponent == ctx.author:
            await ctx.send(f"{my_emojis.ERROR} You cannot play against yourself!")
            return

        if opponent.bot:
            await ctx.send(f"{my_emojis.ERROR} You cannot play against a bot!")
            return

        board = [[0 for _ in range(7)] for _ in range(6)]
        turn = ctx.author
        players = {ctx.author: 1, opponent: 2}

        def check_winner(board):
            for c in range(7 - 3):
                for r in range(6):
                    if board[r][c] == board[r][c + 1] == board[r][c + 2] == board[r][c + 3] != 0:
                        return board[r][c]
            for c in range(7):
                for r in range(6 - 3):
                    if board[r][c] == board[r + 1][c] == board[r + 2][c] == board[r + 3][c] != 0:
                        return board[r][c]
            for c in range(7 - 3):
                for r in range(6 - 3):
                    if board[r][c] == board[r + 1][c + 1] == board[r + 2][c + 2] == board[r + 3][c + 3] != 0:
                        return board[r][c]
            for c in range(7 - 3):
                for r in range(3, 6):
                    if board[r][c] == board[r - 1][c + 1] == board[r - 2][c + 2] == board[r - 3][c + 3] != 0:
                        return board[r][c]
            return 0

        def render_board(board):
            symbols = {0: '⚪', 1: '🔴', 2: '🔵'}
            return '\n'.join(''.join(symbols[cell] for cell in row) for row in board)

        def is_full(board):
            return all(cell != 0 for row in board for cell in row)

        async def drop_piece(column, player):
            for row in reversed(board):
                if row[column] == 0:
                    row[column] = players[player]
                    break

        message = await ctx.send(f"{turn.mention}'s turn!!\n{render_board(board)}")

        class DropButton(discord.ui.Button):
            def __init__(self, column):
                super().__init__(style=discord.ButtonStyle.primary, label=str(column + 1))
                self.column = column

            async def callback(self, interaction: discord.Interaction):
                nonlocal turn
                if interaction.user != turn:
                    await interaction.response.send_message(f"{my_emojis.ERROR} It's not your turn!", ephemeral=True)
                    return

                await drop_piece(self.column, turn)
                winner = check_winner(board)
                if winner != 0:
                    await interaction.response.edit_message(content=f"{my_emojis.PREFIX} {turn.mention} wins!\n{render_board(board)}", view=None)
                    user_data = await db_funcs.get_user_data(interaction.user.id)
                    wallet, bank, gems = user_data
                    if winner == 1:
                        await interaction.response.send_message(f"you got some buckaroos! +1000", ephemeral=True)
                        await db_funcs.save_user_data(interaction.user.id, wallet+1000, bank, gems)

                    return

                if is_full(board):
                    await interaction.response.edit_message(content=f"{my_emojis.PREFIX} It's a draw!\n{render_board(board)}", view=None)
                    return

                turn = opponent if turn == ctx.author else ctx.author
                await interaction.response.edit_message(content=f"{my_emojis.PREFIX} {turn.mention}'s turn!\n{render_board(board)}")

        view = discord.ui.View()
        for i in range(7):
            view.add_item(DropButton(i))

        await message.edit(view=view)

    @commands.hybrid_command()
    async def tictactoe(self, ctx, opponent: discord.Member):
        """Start a TicTacToe game with another member."""
        if opponent == ctx.author:
            await ctx.send(f"{my_emojis.ERROR} You cannot play against yourself!")
            return

        if opponent.bot:
            await ctx.send(f"{my_emojis.ERROR} You cannot play against a bot!")
            return
        board_size = 3
        board = [[0 for _ in range(board_size)] for _ in range(board_size)]
        turn = ctx.author
        players = {ctx.author: 1, opponent: 2}
        symbols = {0: '⬜', 1: '❌', 2: '⭕'}

        def check_winner(board):
            # Check rows and columns
            for i in range(board_size):
                if all(cell == board[i][0] and cell != 0 for cell in board[i]):
                    return board[i][0]
                if all(row[i] == board[0][i] and row[i] != 0 for row in board):
                    return board[0][i]
            # Check diagonals
            if all(board[i][i] == board[0][0] and board[i][i] != 0 for i in range(board_size)):
                return board[0][0]
            if all(board[i][board_size - 1 - i] == board[0][board_size - 1] and board[i][board_size - 1 - i] != 0 for i in range(board_size)):
                return board[0][board_size - 1]
            return 0

        def render_board(board):
            return '\n'.join(''.join(symbols[cell] for cell in row) for row in board)

        def is_full(board):
            return all(cell != 0 for row in board for cell in row)

        async def make_move(x, y, player):
            if board[x][y] == 0:
                board[x][y] = players[player]
                return True
            return False

        message = await ctx.send(f"{my_emojis.PREFIX} {turn.mention}'s turn! Use the buttons to play!\n{render_board(board)}")

        class MoveButton(discord.ui.Button):
            def __init__(self, x, y):
                super().__init__(style=discord.ButtonStyle.primary, label="\u200b", row=x)
                self.x = x
                self.y = y

            async def callback(self, interaction: discord.Interaction):
                nonlocal turn
                if interaction.user != turn:
                    await interaction.response.send_message(f"{my_emojis.ERROR} It's not your turn!", ephemeral=True)
                    return

                if await make_move(self.x, self.y, turn):
                    winner = check_winner(board)
                    if winner != 0:
                        await interaction.response.edit_message(content=f"{my_emojis.PREFIX} {turn.mention} wins!\n{render_board(board)}", view=None)
                        user_data = await db_funcs.get_user_data(interaction.user.id)
                        wallet, bank, gems = user_data
                        if winner == 1:
                            await interaction.response.send_message(f"you got some buckaroos! +1000", ephemeral=True)
                            await db_funcs.save_user_data(interaction.user.id, wallet+1000, bank, gems)
                        return

                    if is_full(board):
                        await interaction.response.edit_message(content=f"{my_emojis.PREFIX} It's a draw!\n{render_board(board)}", view=None)
                        return

                    turn = opponent if turn == ctx.author else ctx.author
                    await interaction.response.edit_message(content=f"{my_emojis.PREFIX} {turn.mention}'s turn!\n{render_board(board)}", view=view)
                else:
                    await interaction.response.send_message(f"{my_emojis.ERROR} This spot is already taken!", ephemeral=True)

        view = discord.ui.View()
        for i in range(board_size):
            for j in range(board_size):
                view.add_item(MoveButton(i, j))

        await message.edit(view=view)

    @commands.hybrid_command()
    async def hangman(self, ctx):
        """
        Play a game of hangman with the bot.
        """
        pot_words = ["apple", "banana", "cherry", "date", "elderberry", "fig", "grape", "honeydew", "kiwi", "lemon", "mango", "nectarine", "orange", "pineapple", "quince", "raspberry", "strawberry", "tangerine", "ugli fruit", "watermelon", "xigua", "yam", "zucchini", "avocado", "chickpea", "corn", "cucumber", "garlic", "kale", "lettuce", "onion", "peas", "pepper", "potato", "spinach", "tomato", "volcano", "zombie"]
        word = random.choice(pot_words)
        game = HangmanGame(word)

        embed = discord.Embed(title=f"{my_emojis.PREFIX} Hangman Game", description="Welcome to hangman!", color=discord.Color.from_str(self.embed_color))
        embed.add_field(name="Word", value=f"`{game.get_display_word()}`", inline=False)
        embed.add_field(name="Tries", value=game.render_hangman(), inline=False)
        embed.set_footer(text=f"The word is {len(word)} letters long. Guess a letter by typing it in the chat.")
        message = await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.content.isalpha() and len(m.content) == 1

        while True:
            guess_msg = await self.bot.wait_for('message', check=check)
            guess = guess_msg.content.lower()

            if game.guess(guess):
                if game.is_won():
                    embed = discord.Embed(title=f"{my_emojis.PREFIX} Hangman Game", description="You win!", color=discord.Color.from_str(self.embed_color))
                    embed.add_field(name="Word", value=game.word, inline=False)
                    await message.edit(embed=embed)
                    return
            else:
                if game.is_lost():
                    embed = discord.Embed(title=f"{my_emojis.PREFIX} Hangman Game", description="You lose!", color=discord.Color.from_str(self.embed_color))
                    embed.add_field(name="Word", value=game.word, inline=False)
                    embed.add_field(name="Tries", value=game.render_hangman(), inline=False)
                    await message.edit(embed=embed)
                    return

            embed = discord.Embed(title=f"{my_emojis.PREFIX} Hangman Game", color=discord.Color.from_str(self.embed_color))
            embed.add_field(name="Word", value=f"`{game.get_display_word()}`", inline=False)
            embed.add_field(name="Tries", value=game.render_hangman(), inline=False)
            embed.add_field(name="Guessed Letters", value=', '.join(game.guessed_letters), inline=False)
            await message.edit(embed=embed)


class WordScramble(commands.Cog):
    def __init__(self, bot, embed_color):
        self.bot = bot
        self.embed_color = embed_color
        self.current_word = None
        self.hint = None

    @commands.hybrid_command()
    async def start_scramble(self, ctx):
        word, hint = await self.fetch_word_and_hint()
        if word and hint:
            self.current_word = word
            self.hint = hint
            scrambled_word = ''.join(random.sample(word, len(word)))
            embed = discord.Embed(
                title=f"{my_emojis.PREFIX} Word Scramble",
                description=f"Unscramble the word using `a guess <guess>`: \n\n**{scrambled_word}**\n\nHint: {hint}",
                color=discord.Color.from_str(self.embed_color)
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{my_emojis.ERROR} Couldn't fetch a word. Please try again later.")

    @commands.command()
    async def guess(self, ctx, *, user_guess: str):
        if not self.current_word:
            await ctx.send(f"{my_emojis.ERROR} Start a game first using `/start_scramble`.")
            return

        if user_guess.lower() == self.current_word.lower():
            await ctx.send(f"{my_emojis.PREFIX} Congratulations! You guessed the word correctly: **{self.current_word}**")
            self.current_word = None  # Reset the game
        else:
            await ctx.send(f"{my_emojis.ERROR} Incorrect guess. Try again!")

    async def fetch_word_and_hint(self):
        async with aiohttp.ClientSession() as session:
            word = await self.get_random_word(session)
            if word:
                hint = await self.get_word_definition(session, word)
                return word, hint
        return None, None

    async def get_random_word(self, session):
        async with session.get("https://random-word-api.herokuapp.com/word?number=1") as response:
            if response.status == 200:
                data = await response.json()
                return data[0] if data else None
        return None

    async def get_word_definition(self, session, word):
        async with session.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}") as response:
            if response.status == 200:
                data = await response.json()
                if data and isinstance(data, list) and 'meanings' in data[0]:
                    meanings = data[0]['meanings']
                    if meanings and 'definitions' in meanings[0]:
                        definitions = meanings[0]['definitions']
                        if definitions:
                            return definitions[0].get('definition', 'No definition found.')
        return 'No definition found.'
        

class FastClickGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group()
    async def fastclick(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Use `fastclick start` to start the game or `fastclick leaderboard` to view the leaderboard.")

    @fastclick.command()
    async def start(self, ctx):
        # Create a 5x5 button grid
        view = FastClickView(ctx.author.id, self.bot)
        message = await ctx.send("Click the button that lights up as fast as you can!", view=view)
        view.message = message
        await view.light_up_random_button()

    @fastclick.command()
    async def leaderboard(self, ctx):
        async with aiosqlite.connect('bot.db') as db:
            cursor = await db.execute('SELECT user_id, time FROM click_lb ORDER BY time ASC LIMIT 10')
            rows = await cursor.fetchall()

        embed = discord.Embed(title="Fast Click Leaderboard", color=discord.Color.gold())
        for i, (user_id, time) in enumerate(rows, start=1):
            user = self.bot.get_user(user_id)
            embed.add_field(name=f"{i}. {user.name} | ***{time:.3f}s***", value="\u200b", inline=False)
        
        await ctx.send(embed=embed)

    async def update_leaderboard(self, user_id, time):
        async with aiosqlite.connect('bot.db') as db:
            cursor = await db.execute('SELECT time FROM click_lb WHERE user_id = ?', (user_id,))
            row = await cursor.fetchone()
            
            if row:
                if time < row[0]:
                    await db.execute('UPDATE click_lb SET time = ? WHERE user_id = ?', (time, user_id))
            else:
                await db.execute('INSERT INTO click_lb (user_id, time) VALUES (?, ?)', (user_id, time))
            
            await db.commit()


class FastClickView(discord.ui.View):
    def __init__(self, user_id, bot):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.bot = bot
        self.message = None
        self.start_time = None

        for i in range(4):
            for j in range(4):
                self.add_item(FastClickButton(i, j, self.user_id, self))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)

    async def light_up_random_button(self):
        button = random.choice(self.children)
        await button.light_up()

class FastClickButton(discord.ui.Button):
    def __init__(self, row, col, user_id, view):
        super().__init__(label='\u200b', style=discord.ButtonStyle.secondary, row=row)
        self.user_id = user_id
        self.view_instance = view
        self.is_active = False

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This game is not for you!", ephemeral=True)
            return
        
        if self.is_active:
            end_time = time.time()
            reaction_time = end_time - self.view_instance.start_time
            self.is_active = False

            await self.view_instance.message.edit(content=f"Your time: {reaction_time:.3f} seconds", view=self.view_instance)
            if reaction_time < 0.999:
                user_data = await db_funcs.get_user_data(self.user_id)
                
                wallet, bank, gems = user_data
                bonus = round((1000 / reaction_time) * 10, -1)
                await db_funcs.save_user_data(self.user_id, wallet+bonus, bank, gems)
                await interaction.response.send_message(f"you got some buckaroos! +{bonus}", ephemeral=True)
            else:
                pass

            await self.view_instance.bot.get_cog('FastClickGame').update_leaderboard(self.user_id, reaction_time)
            await self.view_instance.on_timeout()
        else:
            await interaction.response.send_message("Wait for the button to light up!", ephemeral=True)

    async def light_up(self):
        self.is_active = True
        self.style = discord.ButtonStyle.success
        self.label = "Click me!"
        self.view_instance.start_time = time.time()
        await self.view_instance.message.edit(view=self.view_instance)

    