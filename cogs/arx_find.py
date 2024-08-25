import discord 
from discord.ext import commands
import utils.my_emojis as my_emojis
import aiohttp
import json
import os
import dotenv
from serpapi import GoogleSearch
import asyncio
import groq

from groq import Groq


dotenv.load_dotenv()

omdb_api_key = os.getenv("OMDB_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

async def get_groq_response(name):
    client = Groq()
    MODEL = 'llama3-groq-70b-8192-tool-use-preview'
    messages =[
        {"role": "system", "content": f"""You are a search engine. Use the find function to perform search operations and provide the results.

            find: (name: {name}) => string
                returns a brief summary of the of the item: {name}"""},
        {"role": "user", "content": name}
    ]
    
    response = client.chat.completions.create(
        messages=messages,
        model=MODEL
    )
    return response.choices[0].message.content

async def get_groq_responses_if_not_found(name):
    client = Groq()
    MODEL = 'llama3-groq-70b-8192-tool-use-preview'
    messages = [
        {"role": "system", "content": f"""You are a search engine. Use the find function to perform search operations and provide the results.

            find: (name: {name}) => string
                returns a brief summary of the item the user is trying to find: {name}
                pick the top 3 results from your search, and then return a brief summary of the top 3 results
        """},
        {"role": "user", "content": name}
    ]

    response = client.chat.completions.create(
        messages=messages,
        model=MODEL
    )

    return response.choices[0].message.content

class ArxFind(commands.Cog):
    def __init__(self, bot, embed_color):
        self.bot = bot
        self.embed_color = embed_color
        


    @commands.group()
    async def find(self, ctx, *, name):
        """Find something on the internet."""
        # tool set up for groq ai
        await ctx.send(await get_groq_response(name) + "<@" + str(ctx.author.id) + ">")


    @find.command()
    async def movie(self, ctx, *, name):
        """Find a movie on the internet."""

        async with aiohttp.ClientSession() as session:  
            async with session.get(f"https://www.omdbapi.com/?t={name}&apikey={omdb_api_key}") as response:
                if response.status == 200:
                    data = await response.json()
                    if data["Response"] == "True":
                        embed = discord.Embed(title=data["Title"], color=discord.Color.from_str(self.embed_color))
                        embed.add_field(name="Plot", value=data["Plot"])
                        embed.add_field(name="Year", value=data["Year"])
                        embed.add_field(name="Rating", value=data["imdbRating"])
                        embed.set_thumbnail(url=data["Poster"])
    
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(f"{my_emojis.ERROR} No results found. Trying to find something for you.")
                        asyncio.sleep(2)
                        await ctx.send(await get_groq_responses_if_not_found(name) + "<@" + str(ctx.author.id) + ">")

    @find.command()
    async def anime(self, ctx, *, name):
        """Find an anime on the internet."""

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.jikan.moe/v4/anime?q={name}") as response:
                if response.status == 200:
                    data = await response.json()
                    if data["data"]:
                        embed = discord.Embed(title=data["data"][0]["title"], color=discord.Color.from_str(self.embed_color))
                        embed.add_field(name="Episodes", value=data["data"][0]["episodes"])
                        embed.add_field(name="Status", value=data["data"][0]["status"])
                        embed.add_field(name="Rating", value=data["data"][0]["score"])
                        embed.set_thumbnail(url=data["data"][0]["images"]["jpg"]["image_url"])
    
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(f"{my_emojis.ERROR} No results found.")
                        asyncio.sleep(2)
                        await ctx.send(await get_groq_responses_if_not_found(name) + "<@" + str(ctx.author.id) + ">")
    @find.command()
    async def manga(self, ctx, *, name):
        """Find a manga on the internet."""

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.jikan.moe/v4/manga?q={name}") as response:
                if response.status == 200:
                    data = await response.json()
                    if data["data"]:
                        embed = discord.Embed(title=data["data"][0]["title"], color=discord.Color.from_str(self.embed_color))
                        embed.add_field(name="Chapters", value=data["data"][0]["chapters"])
                        embed.add_field(name="Status", value=data["data"][0]["status"])
                        embed.add_field(name="Rating", value=data["data"][0]["score"])
                        embed.set_thumbnail(url=data["data"][0]["images"]["jpg"]["image_url"])
    
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(f"{my_emojis.ERROR} No results found.")
                        asyncio.sleep(2)
                        await ctx.send(await get_groq_responses_if_not_found(name) + "<@" + str(ctx.author.id) + ">")

    @find.command()
    async def book(self, ctx, *, name):
        """Find a book on the internet."""

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://www.googleapis.com/books/v1/volumes?q={name}") as response:
                if response.status == 200:
                    data = await response.json()
                    if data["items"]:
                        embed = discord.Embed(title=data["items"][0]["volumeInfo"]["title"], color=discord.Color.from_str(self.embed_color))
                        embed.add_field(name="Author", value=data["items"][0]["volumeInfo"]["authors"][0])
                        desc = data["items"][0]["volumeInfo"]["description"]
                        if len(desc) > 1024:
                            desc = desc[:1021] + "..."
                            embed.add_field(name="Description", value=desc)
                        embed.add_field(name="Rating", value=data["items"][0]["volumeInfo"]["averageRating"])
                        embed.set_thumbnail(url=data["items"][0]["volumeInfo"]["imageLinks"]["thumbnail"])
    
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(f"{my_emojis.ERROR} No results found.")
                        asyncio.sleep(2)
                        await ctx.send(await get_groq_responses_if_not_found(name) + "<@" + str(ctx.author.id) + ">")

                
    @find.command()
    async def help(self, ctx):
        """Find a help command."""

        embed = discord.Embed(title="Help - Find", color=discord.Color.from_str(self.embed_color))
        embed.add_field(name="`/find anime`", value="Find an anime on the internet.", inline=False)
        embed.add_field(name="`/find manga`", value="Find a manga on the internet.", inline=False)
        embed.add_field(name="`/find book`", value="Find a book on the internet.", inline=False)

        await ctx.send(embed=embed)
                
    