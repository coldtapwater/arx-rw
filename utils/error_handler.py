import discord
from discord.ext import commands
import logging
import traceback
import os
import sys
import inspect
import time

print("Loading error handler...")
logger = logging.getLogger('bot')

class ErrorHandler:
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # Check if the error is a subclass of commands.CommandError
        if not isinstance(error, commands.CommandError):
            return

        # Your existing error handling logic
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param}")
            return
        if isinstance(error, commands.BadArgument):
            await ctx.send(f"Invalid argument provided: {error}")
            return
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have the required permissions to use this command.")
            return
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send("I don't have the required permissions to execute this command.")
            return
        if isinstance(error, commands.CommandOnCooldown):
            # Calculate the time when the cooldown will end
            retry_time = int(time.time() + error.retry_after)
            
            # Use Discord's timestamp format for a relative time display
            await ctx.send(f"This command is on cooldown. Try again <t:{retry_time}:R>.")
            return
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send("This command cannot be used in private messages.")
            return

        # Optionally, send more detailed error information to a designated error channel
        error_channel_id = os.getenv('ERROR_CHANNEL_ID')
        if error_channel_id:
            error_channel = ctx.bot.get_channel(int(error_channel_id))
            if error_channel:
                tb = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
                error_message = f"An error occurred in command '{ctx.command}' used by {ctx.author}:\n```{tb}```"
                await error_channel.send(error_message[:2000])  # Discord message limit

        # Log the error
        logger.error(f"Unhandled command error: {error}", exc_info=True)

    @staticmethod
    async def handle_general_error(error):
        logger.error(f"Unhandled general error: {error}", exc_info=True)

    @staticmethod
    def setup(bot):

        @bot.event
        async def on_error(event, *args, **kwargs):
            error = sys.exc_info()[1]
            await ErrorHandler.handle_general_error(error)