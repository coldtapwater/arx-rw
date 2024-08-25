import discord
from discord.ext import commands
import aiohttp

import discord
from discord.ext import commands
import aiohttp
import utils.my_emojis as my_emojis

class ArxMemes(commands.Cog):
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
    
    @commands.group()
    async def meme(self, ctx):
        """Get a meme from a subreddit"""
        await ctx.send(f"{my_emojis.ERROR} Invalid subcommand passed. Use `r help meme` to see the available subcommands.")
    
    @meme.command()
    async def random(self, ctx):
        """Get a meme from a random subreddit"""
        meme_data = await self.fetch_meme("random")
        if meme_data:
            embed = discord.Embed(title=f"{my_emojis.PREFIX} Here's a meme for you!", color=discord.Color.from_str(self.embed_color))
            embed.set_image(url=meme_data['url'])
            embed.set_footer(text=f"Source: {meme_data['subreddit']}")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{my_emojis.ERROR} Could not fetch a meme at this time. Please try again later.")

    @meme.command()
    async def funny(self, ctx):
        """Get a meme from the r/funny subreddit"""
        meme_data = await self.fetch_meme("funny")
        if meme_data:
            embed = discord.Embed(title=f"{my_emojis.PREFIX} Here's a meme for you!", color=discord.Color.from_str(self.embed_color))
            embed.set_image(url=meme_data['url'])
            embed.set_footer(text=f"Source: {meme_data['subreddit']}")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{my_emojis.ERROR} Could not fetch a meme at this time. Please try again later.")

    @meme.command()
    async def holup(self, ctx):
        """Get a meme from the r/HolUp subreddit"""
        meme_data = await self.fetch_meme("holup")
        if meme_data:
            embed = discord.Embed(title=f"{my_emojis.PREFIX} Here's a meme for you!", color=discord.Color.from_str(self.embed_color))
            embed.set_image(url=meme_data['url'])
            embed.set_footer(text=f"Source: {meme_data['subreddit']}")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{my_emojis.ERROR} Could not fetch a meme at this time. Please try again later.")

    @meme.command()
    async def dank(self, ctx):
        """Get a meme from the r/dankmemes subreddit"""
        meme_data = await self.fetch_meme("dankmemes")
        if meme_data:
            embed = discord.Embed(title=f"{my_emojis.PREFIX} Here's a meme for you!", color=discord.Color.from_str(self.embed_color))
            embed.set_image(url=meme_data['url'])
            embed.set_footer(text=f"Source: {meme_data['subreddit']}")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{my_emojis.ERROR} Could not fetch a meme at this time. Please try again later.")
