import discord
from discord.ext import commands
import logging
import traceback
import os
import sys
import inspect

print("Loading error handler...")
logger = logging.getLogger('bot')

class ErrorHandler:
    @staticmethod
    async def handle_command_error(ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            original = error.original
            if isinstance(original, TypeError) and "Moderation.is_mod()" in str(original):
                # Detailed logging for this specific error
                error_message = f"Intercepted Moderation.is_mod() error:\n"
                error_message += f"Full error: {str(original)}\n"
                error_message += f"Command: {ctx.command}\n"
                error_message += f"Cog: {ctx.cog}\n"
                error_message += f"User: {ctx.author} (ID: {ctx.author.id})\n"
                error_message += f"Guild: {ctx.guild} (ID: {ctx.guild.id})\n"
                error_message += f"Channel: {ctx.channel} (ID: {ctx.channel.id})\n"
                error_message += f"Message content: {ctx.message.content}\n"
                
                # Get the full stack trace
                stack_trace = ''.join(traceback.format_tb(original.__traceback__))
                error_message += f"Stack trace:\n{stack_trace}\n"

                # Attempt to find the source of the is_mod call
                for frame_info in inspect.trace():
                    if 'is_mod' in frame_info.code_context[0]:
                        error_message += f"is_mod call found in {frame_info.filename} at line {frame_info.lineno}\n"
                        error_message += f"Code context: {frame_info.code_context[0].strip()}\n"

                logger.error(error_message)
                return  # Suppress further handling of this error

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
            await ctx.send(f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds.")
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
        bot.add_listener(ErrorHandler.handle_command_error, 'on_command_error')

        @bot.event
        async def on_error(event, *args, **kwargs):
            error = sys.exc_info()[1]
            await ErrorHandler.handle_general_error(error)