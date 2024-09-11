import discord
from discord.ext import commands
import aiohttp
import utils.configs as uc
import utils.checks

class Memes(commands.Cog):
    def __init__(self, bot, embed_color):
        self.bot = bot
        self.embed_color = embed_color

    async def fetch_meme(self, sub):
        BASE_URL = f"https://meme-api.com/gimme/{sub}"

        if sub == "random":
            BASE_URL = "https://meme-api.com/gimme"

        async with aiohttp.ClientSession() as session:
            async with session.get(BASE_URL) as response:
                if response.status == 200:
                    return await response.json()
                return None
    

    @commands.group(invoke_without_command=True)
    async def meme(self, ctx):
        pass

    @meme.command()
    @utils.checks.blacklist_check()
    async def random(self, ctx):
        """Sends a random meme"""
        pass

    @meme.command()
    @utils.checks.blacklist_check()
    async def funny(self, ctx):
        """Sends a funny meme"""
        pass

    @meme.command()
    @commands.is_nsfw()
    @utils.checks.blacklist_check()
    async def nsfw(self, ctx):
        """Sends an NSFW meme"""
        pass


    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} is ready.")
async def setup(bot):
    await bot.add_cog(Memes(bot, uc.EMBED_COLOR))