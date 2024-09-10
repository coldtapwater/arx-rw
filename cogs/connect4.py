import discord
from discord.ext import commands

import utils.configs as uc
import utils.emojis as my_emojis

class Connect4(commands.Cog):
    def __init__(self, bot, embed_color):
        self.bot = bot
        self.embed_color = embed_color

    @commands.command()
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

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} is ready.")
async def setup(bot):
    await bot.add_cog(Connect4(bot, uc.EMBED_COLOR))