from discord.ext import commands
from utils.models.models import BlacklistedUser, AuditedUser

def blacklist_check():
    async def predicate(ctx):
        is_blacklisted = await BlacklistedUser.filter(user_id=ctx.author.id).exists()
        if is_blacklisted:
            return commands.CheckFailure("You are blacklisted and cannot use this bot.")
        
        is_audited = await AuditedUser.filter(user_id=ctx.author.id).exists()
        if is_audited:
            ctx.bot.dispatch('audited_command_use', ctx)
            return True  # Allow the command to run, but we'll handle the audit message elsewhere
        
        return True
    return commands.check(predicate)