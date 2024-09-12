import discord
from discord.ext import commands
import asyncio
import utils.checks

class TicTacToe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @utils.checks.blacklist_check()
    async def tictactoe(self, ctx, opponent: discord.Member):
        """Start a TicTacToe game with another member."""
        if opponent == ctx.author:
            await ctx.send("You cannot play against yourself!")
            return

        if opponent.bot:
            await ctx.send("You cannot play against a bot!")
            return

        board_size = 5
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

        message = await ctx.send(f"{turn.mention}'s turn! Use the buttons to play!\n{render_board(board)}")

        class MoveButton(discord.ui.Button):
            def __init__(self, x, y):
                super().__init__(style=discord.ButtonStyle.primary, label="\u200b", row=x)
                self.x = x
                self.y = y

            async def callback(self, interaction: discord.Interaction):
                nonlocal turn
                if interaction.user != turn:
                    await interaction.response.send_message("It's not your turn!", ephemeral=True)
                    return

                if await make_move(self.x, self.y, turn):
                    winner = check_winner(board)
                    if winner != 0:
                        await interaction.response.edit_message(content=f"{turn.mention} wins!\n{render_board(board)}", view=None)
                        return

                    if is_full(board):
                        await interaction.response.edit_message(content=f"It's a draw!\n{render_board(board)}", view=None)
                        return

                    turn = opponent if turn == ctx.author else ctx.author
                    await interaction.response.edit_message(content=f"{turn.mention}'s turn!\n{render_board(board)}", view=view)
                else:
                    await interaction.response.send_message("This spot is already taken!", ephemeral=True)

        view = discord.ui.View()
        for i in range(board_size):
            for j in range(board_size):
                view.add_item(MoveButton(i, j))

        await message.edit(view=view)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} is ready.")
async def setup(bot):
    await bot.add_cog(TicTacToe(bot))