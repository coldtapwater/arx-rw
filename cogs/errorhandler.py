import discord
from discord.ext import commands
import traceback
import sys
import inspect

class ComprehensiveErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
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

                print(error_message, file=sys.stderr)
                return  # Suppress further handling of this error

        # Handle other errors as before
        print(f'Ignoring exception in command {ctx.command}:', file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

async def setup(bot):
    await bot.add_cog(ComprehensiveErrorHandler(bot))