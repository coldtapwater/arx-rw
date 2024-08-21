import discord
from discord.ext import commands
import random

class ArxFun(commands.Cog):
    def __init__(self, bot, embed_color):
        self.bot = bot
        self.embed_color = embed_color
        self.sniped_messages = {}

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return  # Ignore bot messages
        self.sniped_messages[message.channel.id] = (message.content, message.author, message.created_at)

    @commands.hybrid_command(name="snipe")
    async def snipe(self, ctx):
        """Snipes the last deleted message in the channel."""
        channel = ctx.channel
        if channel.id not in self.sniped_messages:
            await ctx.send("There's nothing to snipe!")
            return

        content, author, created_at = self.sniped_messages[channel.id]

        embed = discord.Embed(description=content, color=discord.Color.blurple(), timestamp=created_at)
        embed.set_author(name=f"{author}", icon_url=author.avatar.url)
        embed.set_footer(text="Sniped")
        
        await ctx.send(embed=embed)