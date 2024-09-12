import discord
from discord.ext import commands

import utils.configs as uc

class FastClick(commands.Cog):
    def __init__(self, bot, embed_color):
        self.bot = bot
        self.embed_color = embed_color

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} is ready.")
async def setup(bot):
    await bot.add_cog(FastClick(bot, uc.EMBED_COLOR))