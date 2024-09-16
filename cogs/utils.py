import discord
import psutil  # For system information
import platform  # For system information
import time
from discord.ext import commands
from datetime import datetime, timedelta
from utils.models.models import Supporters
import utils.general_db as gdb
import logging

logger = logging.getLogger('bot')

class DeveloperUtilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.now()

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

    @commands.command(name="uptime")
    @commands.is_owner()
    async def uptime(self, ctx):
        """Shows the bot's uptime."""
        uptime = self.get_uptime()
        await ctx.send(f"**Uptime:** {uptime}")

    @commands.command(name="systeminfo", aliases=["sysinfo", "si", "sys"])
    @commands.is_owner()
    async def systeminfo(self, ctx):
        """Shows advanced system information."""
        system_info = self.get_system_info()
        embed = discord.Embed(title="System Information", color=discord.Color.blue())
        for key, value in system_info.items():
            embed.add_field(name=key, value=value, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="downtime")
    @commands.is_owner()
    async def downtime(self, ctx):
        """Shows the last time the bot was down."""
        downtime = self.get_last_downtime()
        await ctx.send(downtime)

    @commands.command(name="supporter")
    @commands.is_owner()
    async def supporter(self, ctx, user: discord.User):
        """Add a user to the list of supporters."""
        await gdb.add_supporter(user.id)
        logging.info(f"Added {user.mention} to the list of supporters.")
        await ctx.send(f"Added {user.mention} to the list of supporters.")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} is ready.")

async def setup(bot):
    await bot.add_cog(DeveloperUtilities(bot))