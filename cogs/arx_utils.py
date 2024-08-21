import discord
from discord.ext import commands
import psutil
import platform

class ArxUtils(commands.Cog):
    def __init__(self, bot, embed_color):
        self.bot = bot
        self.embed_color = embed_color
    
    @commands.command(aliases=["sys"])
    @commands.is_owner()
    async def sysinfo(self, ctx):
        """Shows the system information"""
        embed = discord.Embed(title="System Information", color=discord.Color.blue())
        embed.add_field(name="Python Version", value=platform.python_version())
        embed.add_field(name="Discord.py Version", value=discord.__version__)
        embed.add_field(name="CPU", value=f"{psutil.cpu_count(logical=False)}x {psutil.cpu_count(logical=True)}")
        embed.add_field(name="RAM", value=f"{psutil.virtual_memory().percent}%")
        await ctx.send(embed=embed)
    
    
    
