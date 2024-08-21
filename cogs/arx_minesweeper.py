import discord
from discord.ext import commands
import random
import asyncio
import utils.my_emojis as my_emojis

class MinesweeperButton(discord.ui.Button):
    def __init__(self, x, y):
        super().__init__(label='⬜', style=discord.ButtonStyle.secondary, row=x)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view: MinesweeperView = self.view
        if view.is_mine(self.x, self.y):
            self.label = '💥'
            self.style = discord.ButtonStyle.danger
            view.disable_all_buttons()
            await interaction.response.edit_message(content=f"{my_emojis.PREFIX} Boom! You hit a mine!", view=view)
        else:
            self.label = str(view.adjacent_mines(self.x, self.y))
            self.style = discord.ButtonStyle.primary
            self.disabled = True
            await interaction.response.edit_message(view=view)
            if view.check_win():
                await interaction.followup.send(f"{my_emojis.PREFIX} Congratulations! You cleared the minefield!")

class MinesweeperView(discord.ui.View):
    def __init__(self, size=5, mines=5):
        super().__init__(timeout=None)
        self.size = size
        self.mines = mines
        self.grid = [[0 for _ in range(size)] for _ in range(size)]
        self.populate_mines()
        self.populate_numbers()
        self.create_buttons()

    def create_buttons(self):
        for x in range(self.size):
            for y in range(self.size):
                button = MinesweeperButton(x, y)
                self.add_item(button)

    def populate_mines(self):
        mine_locations = random.sample(range(self.size * self.size), self.mines)
        for loc in mine_locations:
            x, y = divmod(loc, self.size)
            self.grid[x][y] = -1

    def populate_numbers(self):
        for x in range(self.size):
            for y in range(self.size):
                if self.grid[x][y] == -1:
                    continue
                self.grid[x][y] = self.adjacent_mines(x, y)

    def is_mine(self, x, y):
        return self.grid[x][y] == -1

    def adjacent_mines(self, x, y):
        mines = 0
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if 0 <= x + dx < self.size and 0 <= y + dy < self.size:
                    if self.grid[x + dx][y + dy] == -1:
                        mines += 1
        return mines

    def check_win(self):
        for button in self.children:
            if not button.disabled and not self.is_mine(button.x, button.y):
                return False
        return True

    def disable_all_buttons(self):
        for button in self.children:
            button.disabled = True

class Minesweeper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def sweeper(self, ctx):
        """Play a game of Minesweeper."""
        await ctx.send(f"{my_emojis.PREFIX} Let's play Minesweeper!", view=MinesweeperView())
