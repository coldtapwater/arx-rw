import discord
from discord.ext import commands
import utils.configs as uc
import utils.checks
import utils.emojis as my_emojis
import utils.error_handler as eh
import utils.general_db as gdb
import utils.economy_db as db
import utils.moderation_db as mdb


class UserTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    async def contact(self, ctx, message: str):
        """Sends a message to the developer"""
        if message:
            embed = discord.Embed(title="Issue Submitted", description=f"{ctx.author.mention}", color=discord.Color.from_str(uc.EMBED_COLOR))
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            embed.add_field(name=f"Message: -- from GUILD {ctx.guild}", value=f"{message}")
            await ctx.bot.get_user(1151230208783945818).send(embed=embed)
            await ctx.send("Thank you for your message. The developer will resolve this issue shortly.")

        else:
            await ctx.send("Please provide an issue message.")
    @commands.command()
    async def avatar(ctx, member: discord.Member = None):
        """Shows the avatar of a user"""
        if member is None:
            member = ctx.author
        embed = discord.Embed(title=f"{member}'s Avatar", color=discord.Color.from_str(uc.EMBED_COLOR))
        embed.set_image(url=member.display_avatar.url)

        await ctx.send(embed=embed)





async def setup(bot):
    await bot.add_cog(UserTools(bot))