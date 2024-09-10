import discord
from discord.ext import commands

import utils.configs as uc

class Memes(commands.Cog):
    def __init__(self, bot, embed_color):
        self.bot = bot
        self.embed_color = embed_color

    @commands.group(invoke_without_command=True)
    async def meme(self, ctx):
        pass


    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} is ready.")
async def setup(bot):
    await bot.add_cog(Memes(bot, uc.EMBED_COLOR))