import discord
from discord.ext import commands
import logging
import traceback
import os
import sys

logger = logging.getLogger('bot')

class ErrorHandler:
    @staticmethod
    async def handle_command_error(ctx, error):
        if isinstance(error, commands.CommandNotFound):
            # Ignore command not found errors
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

        # For any other errors, log them and send a generic message
        logger.error(f"Unhandled error in {ctx.command}: {error}", exc_info=True)
        await ctx.send("An unexpected error occurred. The bot administrators have been notified.")

        # Optionally, send more detailed error information to a designated error channel
        error_channel_id = os.getenv('ERROR_CHANNEL_ID')  # Replace with your actual error channel ID
        error_channel = ctx.bot.get_channel(error_channel_id)
        if error_channel:
            tb = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            error_message = f"An error occurred in command '{ctx.command}' used by {ctx.author}:\n```{tb}```"
            await error_channel.send(error_message[:2000])  # Discord message limit

    @staticmethod
    async def handle_general_error(error):
        logger.error(f"Unhandled general error: {error}", exc_info=True)
        # Add any additional general error handling logic here

    @staticmethod
    def setup(bot):
        bot.add_listener(ErrorHandler.handle_command_error, 'on_command_error')

        # Optionally, you can add a general error handler for non-command errors
        @bot.event
        async def on_command_error(ctx, error):
            if isinstance(error, commands.CommandInvokeError):
                original = error.original
                if not isinstance(original, discord.HTTPException):
                    print(f'In {ctx.command.qualified_name}:', file=sys.stderr)
                    traceback.print_tb(original.__traceback__)
                    print(f'{original.__class__.__name__}: {original}', file=sys.stderr)
            elif isinstance(error, commands.CommandNotFound):
                pass  # You can handle command not found errors here
            else:
                print(f'Ignoring exception in command {ctx.command}:', file=sys.stderr)
                traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)