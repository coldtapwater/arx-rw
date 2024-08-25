import discord
from discord.ext import commands

class Quotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.quote_channels = {}  # Dictionary to store quote channels for each guild

    @commands.command()
    async def quote(self, ctx):
        """Quote a message."""
        if not ctx.message.reference or not ctx.message.reference.message_id:
            await ctx.send("Please reply to a message to quote it.")
            return

        quoted_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        if not quoted_message:
            await ctx.send("Couldn't fetch the quoted message.")
            return

        guild_id = ctx.guild.id
        if guild_id not in self.quote_channels:
            await ctx.send("No quote channel configured. Please ask an admin to set one using `r quote config <channel_id>`.")
            return

        quote_channel_id = self.quote_channels[guild_id]
        quote_channel = self.bot.get_channel(quote_channel_id)
        if not quote_channel:
            await ctx.send("Configured quote channel not found.")
            return

        embed = discord.Embed(
            description=quoted_message.content,
            color=discord.Color.blue()
        )
        embed.set_author(name=quoted_message.author.display_name, icon_url=quoted_message.author.display_avatar.url)
        embed.set_footer(text=f"Quoted by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        await quote_channel.send(embed=embed)
        await ctx.send(f"Quote posted in {quote_channel.mention}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def quote_config(self, ctx, channel: discord.TextChannel):
        """Configure the channel for quotes (Admin only)."""
        self.quote_channels[ctx.guild.id] = channel.id
        await ctx.send(f"Quote channel set to {channel.mention}")
