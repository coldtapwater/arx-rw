# J_COLDTAPWATER, VERSION 1.1.0

import discord
from discord.ext import commands
import utils.my_emojis as my_emojis

class HelpMenu(commands.Cog):
    def __init__(self, bot, embed_color):
        self.bot = bot
        self.embed_color = embed_color

    @commands.command(name='help')
    async def help_command(self, ctx):
        """Displays this help message"""
        embed = discord.Embed(
            title=f"{my_emojis.PREFIX} Help",
            description="Here are the available commands:",
            color=discord.Color.from_str(self.embed_color)
        )

        for cog_name, cog in self.bot.cogs.items():
            command_list = [f"`{command.name}` - {command.help or 'No description provided'}" for command in cog.get_commands()]
            command_str = "\n".join(command_list)
            embed.add_field(
                name=f"{cog_name} Commands",
                value=command_str if command_str else "No commands",
                inline=False
            )

        embed.set_footer(text=f"Use {self.bot.command_prefix}command for more info on a command.")
        await ctx.send(embed=embed)