import discord
from discord.ext import commands
import psutil
import platform
from datetime import datetime
import time


class ArxUtils(commands.Cog):
    def __init__(self, bot, embed_color):
        self.bot = bot
        self.embed_color = embed_color

    def get_uptime(self):
        now = datetime.now()
        uptime_duration = now - self.start_time
        days, seconds = uptime_duration.days, uptime_duration.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{days}d {hours}h {minutes}m {seconds}s"

    def get_system_info(self):
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        memory_usage = memory_info.percent
        disk_info = psutil.disk_usage('/')
        disk_usage = disk_info.percent
        system_info = platform.uname()
        return {
            "CPU Usage": f"{cpu_usage}%",
            "Memory Usage": f"{memory_usage}%",
            "Disk Usage": f"{disk_usage}%",
            "System": f"{system_info.system} {system_info.release}",
            "Machine": f"{system_info.machine}",
            "Processor": f"{system_info.processor}",
            "Uptime": self.get_uptime()
        }
    
    def get_last_downtime(self):
        now = datetime.now()
        downtime_duration = now - self.start_time
        return f"Last downtime: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} ({downtime_duration.total_seconds()} seconds ago)"

    @commands.command(hidden=True)
    @commands.is_owner()
    async def uptime(self, ctx):
        """Shows the bot's uptime"""
        embed = discord.Embed(title="Uptime", color=self.embed_color)
        embed.add_field(name="Uptime", value=self.get_uptime())
        embed.add_field(name="Last downtime", value=self.get_last_downtime())
        await ctx.send(embed=embed)
    
    @commands.command(aliases=["sys"], hidden=True)
    @commands.is_owner()
    async def sysinfo(self, ctx):
        """Shows the system information"""
        embed = discord.Embed(title="System Information", color=self.embed_color)
        for key, value in self.get_system_info().items():
            embed.add_field(name=key, value=value, inline=False)
        await ctx.send(embed=embed)
        
    
    
    
