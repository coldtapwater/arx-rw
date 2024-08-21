import discord 
from discord.ext import commands
import utils.my_emojis as my_emojis
import aiohttp
import json
import os
import dotenv


dotenv.load_dotenv()

omdb_api_key = os.getenv("OMDB_API_KEY")

class Find(commands.Cog):
    def __init__(self, bot, embed_color):
        self.bot = bot
        self.embed_color = embed_color
        


    @commands.hybrid_group()
    async def find(self, ctx, *, name):
        """Find something on the internet."""
        if ctx.invoked_subcommand is None:
            await ctx.send(f"{my_emojis.ERROR} Invalid subcommand passed. Use `/find help` to see the available subcommands.")

    @find.command()
    async def movie(self, ctx, *, name):
        """Find a movie on the internet."""

        async with aiohttp.ClientSession() as session:  
            async with session.get(f"https://www.omdbapi.com/?t={name}&apikey={omdb_api_key}") as response:
                if response.status == 200:
                    data = await response.json()
                    if data["Response"] == "True":
                        embed = discord.Embed(title=data["Title"], color=self.embed_color)
                        embed.add_field(name="Plot", value=data["Plot"])
                        embed.add_field(name="Year", value=data["Year"])
                        embed.add_field(name="Rating", value=data["imdbRating"])
    
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(f"{my_emojis.ERROR} No results found.")
    