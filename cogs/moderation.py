import discord
from discord.ext import commands
from utils.moderation_db import get_guild_config, update_guild_config, add_mod_log, get_mod_logs
from utils.error_handler import ErrorHandler
import asyncio
import logging
import utils.configs as uc
import io
import utils.checks

logger = logging.getLogger('bot')

class Moderation(commands.Cog):
    def __init__(self, bot, embed_color):
        self.bot = bot
        self.embed_color = embed_color

    async def cog_check(self, ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        return True

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def setmodrole(self, ctx, role: discord.Role):
        """Set the moderator role for the server."""
        await update_guild_config(ctx.guild.id, mod_role_id=role.id)
        await ctx.send(f"Moderator role set to {role.name}")

    @commands.command()
    @utils.checks.blacklist_check()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """Kick a member from the server."""
        try:
            await member.kick(reason=reason)
            await add_mod_log(ctx.guild.id, member.id, ctx.author.id, 'kick', reason)
            await ctx.send(f"{member} has been kicked. Reason: {reason}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to kick that member.")

    @commands.command()
    @utils.checks.blacklist_check()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """Ban a member from the server."""
        try:
            await member.ban(reason=reason)
            await add_mod_log(ctx.guild.id, member.id, ctx.author.id, 'ban', reason)
            await ctx.send(f"{member} has been banned. Reason: {reason}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to ban that member.")

    @commands.command()
    @utils.checks.blacklist_check()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user: discord.User, *, reason=None):
        """Unban a user from the server."""
        try:
            await ctx.guild.unban(user, reason=reason)
            await add_mod_log(ctx.guild.id, user.id, ctx.author.id, 'unban', reason)
            await ctx.send(f"{user} has been unbanned. Reason: {reason}")
        except discord.NotFound:
            await ctx.send("This user is not banned.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to unban users.")

    @commands.command()
    @utils.checks.blacklist_check()
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, duration: int, *, reason=None):
        """Mute a member for a specified duration (in minutes)."""
        config = await get_guild_config(ctx.guild.id)
        mute_role = ctx.guild.get_role(config.mute_role_id)
        
        if not mute_role:
            return await ctx.send("Mute role not set. Use `!setmuterole` to set it.")

        try:
            await member.add_roles(mute_role, reason=reason)
            await add_mod_log(ctx.guild.id, member.id, ctx.author.id, 'mute', reason)
            await ctx.send(f"{member} has been muted for {duration} minutes. Reason: {reason}")

            await asyncio.sleep(duration * 60)
            if mute_role in member.roles:
                await member.remove_roles(mute_role, reason="Mute duration expired")
                await ctx.send(f"{member}'s mute has expired.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to mute that member.")

    @commands.command()
    @utils.checks.blacklist_check()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member, *, reason=None):
        """Unmute a member."""
        config = await get_guild_config(ctx.guild.id)
        mute_role = ctx.guild.get_role(config.mute_role_id)
        
        if not mute_role:
            return await ctx.send("Mute role not set. Use `!setmuterole` to set it.")

        if mute_role not in member.roles:
            return await ctx.send(f"{member} is not muted.")

        try:
            await member.remove_roles(mute_role, reason=reason)
            await add_mod_log(ctx.guild.id, member.id, ctx.author.id, 'unmute', reason)
            await ctx.send(f"{member} has been unmuted. Reason: {reason}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to unmute that member.")

    @commands.command()
    @utils.checks.blacklist_check()
    @commands.has_permissions(manage_guild=True)
    async def setmuterole(self, ctx, role: discord.Role):
        """Set the mute role for the server."""
        await update_guild_config(ctx.guild.id, mute_role_id=role.id)
        await ctx.send(f"Mute role set to {role.name}")

    @commands.command()
    @utils.checks.blacklist_check()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason):
        """Warn a member."""
        await add_mod_log(ctx.guild.id, member.id, ctx.author.id, 'warn', reason)
        await ctx.send(f"{member} has been warned. Reason: {reason}")
        try:
            await member.send(f"You have been warned in {ctx.guild.name}. Reason: {reason}")
        except discord.Forbidden:
            await ctx.send("I couldn't DM the user about the warning.")

    @commands.command()
    @utils.checks.blacklist_check()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, limit: int, member: discord.Member = None):
        """Bulk delete messages from a member or the whole server."""
        try:
            deleted = await ctx.channel.purge(limit=limit, check=lambda m: m.author == member if member else True)
            await ctx.send(f"Deleted {len(deleted)} message{'s' if len(deleted) > 1 else ''} from {member if member else 'the channel'}.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to delete messages.")

    @commands.command()
    @utils.checks.blacklist_check()
    @commands.has_permissions(manage_messages=True)
    async def modlogs(self, ctx, member: discord.Member = None):
        """View moderation logs for a member or the whole server."""
        try:
            logs = await get_mod_logs(ctx.guild.id, member.id if member else None)
            
            if not logs:
                return await ctx.send("No moderation logs found.")

            log_text = "\n".join([f"{log.timestamp}: {log.action.upper()} - User: {log.user_id}, Mod: {log.moderator_id}, Reason: {log.reason}" for log in logs])
            
            if len(log_text) > 2000:
                # If the log is too long, send it as a file
                file = discord.File(io.StringIO(log_text), filename="mod_logs.txt")
                await ctx.send("Moderation logs:", file=file)
            else:
                await ctx.send(f"Moderation logs:\n```{log_text}```")
        except Exception as e:
            logger.error(f"Error in modlogs command: {str(e)}", exc_info=True)
            await ctx.send("An error occurred while fetching moderation logs.")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You don't have permission to use this command.")
        else:
            await ErrorHandler.handle_command_error(ctx, error)

async def setup(bot):
    await bot.add_cog(Moderation(bot, uc.EMBED_COLOR))