import discord
from discord.ext import commands
from utils.models.models import BlacklistedUser, AuditedUser
import logging

logger = logging.getLogger('bot')

class BlacklistCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.is_owner()
    async def blacklist(self, ctx, user: discord.User):
        await BlacklistedUser.create(user_id=user.id, reason="Manually blacklisted")
        await user.send("You have been blacklisted and can no longer use the bot.")
        await ctx.send(f"{user} has been blacklisted.")
        logger.info(f"[{user.id}] - [BLACKLISTED] - [{ctx.guild.id}] - blacklist command used")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def audit(self, ctx, user: discord.User):
        await AuditedUser.create(user_id=user.id, reason="Manually audited")
        await user.send("You have been audited for suspicious activity.")
        await ctx.send(f"{user} has been audited.")
        logger.info(f"[{user.id}] - [AUDITED] - [{ctx.guild.id}] - audit command used")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def remove(self, ctx, action: str, user: discord.User):
        if action.lower() == 'audit':
            await AuditedUser.filter(user_id=user.id).delete()
            await ctx.send(f"{user} has been removed from the audit list.")
            logger.info(f"[{user.id}] - [REMOVED_AUDIT] - [{ctx.guild.id}] - remove audit command used")
        elif action.lower() == 'blacklist':
            await BlacklistedUser.filter(user_id=user.id).delete()
            await ctx.send(f"{user} has been removed from the blacklist.")
            logger.info(f"[{user.id}] - [REMOVED_BLACKLIST] - [{ctx.guild.id}] - remove blacklist command used")
        else:
            await ctx.send("Invalid action. Use 'audit' or 'blacklist'.")

async def setup(bot):
    await bot.add_cog(BlacklistCog(bot))