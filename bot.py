import os
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import discord
from discord.ext import commands
from utils.models import init_db
from utils import emojis
from utils.error_handler import ErrorHandler
from utils.checks import blacklist_check
import utils.configs as uc

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')


# Set up logging
def setup_logging():
    log_directory = 'logs'
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    # Main logger
    logger = logging.getLogger('bot')
    logger.setLevel(logging.INFO)

    # File handler for general logs
    general_handler = RotatingFileHandler(
        filename='logs/bot.log',
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=5
    )
    general_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    general_handler.setLevel(logging.INFO)

    # File handler for errors
    error_handler = RotatingFileHandler(
        filename='logs/error.log',
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=5
    )
    error_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    error_handler.setLevel(logging.ERROR)

    # Stream handler for critical errors only
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    stream_handler.setLevel(logging.CRITICAL)


    # Add handlers to logger
    logger.addHandler(general_handler)
    logger.addHandler(error_handler)
    logger.addHandler(stream_handler)

    # Suppress discord.py's debug logs
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)
    logging.getLogger('discord.gateway').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('groq._base_client').setLevel(logging.WARNING)

    return logger

logger = setup_logging()
logger_ab = logging.getLogger('bot')
handler_ab = logging.FileHandler(filename='logs/usage.log', encoding='utf-8', mode='a')
logger_ab.addHandler(handler_ab)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='t$', intents=intents, help_command=None)
bot.remove_command('help')

@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Bot is in {len(bot.guilds)} guilds.')

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")

@bot.command(name="reload")
@commands.is_owner()
async def reload(ctx):
    await ctx.send("Reloading...")
    try:
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await bot.reload_extension(f'cogs.{filename[:-3]}')
        await ctx.send("Reload complete.")
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

class HelpCog(commands.Cog, name='Help'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help(self, ctx, command_name=None):
        if command_name:
            return await self.command_help(ctx, command_name)
        
        cog_list = [cog for cog in self.bot.cogs if cog != 'Help']
        
        help_text = "Available commands:\n\n"
        
        for cog_name in cog_list:
            cog = self.bot.get_cog(cog_name)
            commands_list = cog.get_commands()
            if commands_list:
                help_text += f"{cog_name.lower()}:\n"
                for command in commands_list:
                    help_text += f"  {command.name} - {command.short_doc or 'No description'}\n"
                help_text += "\n"
        
        help_text += "Use `help <command>` for more info on a command."
        
        await ctx.send(f"```{help_text}```")

    async def command_help(self, ctx, command_name):
        command = self.bot.get_command(command_name)
        
        if not command:
            return await ctx.send(f"Command `{command_name}` not found.")
        
        help_text = f"Help for `{command.name}`:\n\n"
        help_text += f"Description: {command.help or 'No description available.'}\n"
        help_text += f"Usage: {ctx.prefix}{command.name} {command.signature}\n"
        
        if command.aliases:
            help_text += f"Aliases: {', '.join(command.aliases)}\n"
        
        await ctx.send(f"```{help_text}```")

async def setup(bot):
    await bot.add_cog(HelpCog(bot))

async def main():
    async with bot:
        # Initialize the database
        await init_db(DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
        logger.info("Database initialization completed")

        ErrorHandler.setup(bot)
        logger.info("Error handler setup completed")

        # Load cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await bot.load_extension(f'cogs.{filename[:-3]}')
                logger.info(f'Loaded cog: {filename[:-3]}')

        # Load the help cog
        await setup(bot)

        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown initiated by user.")
    except Exception as e:
        logger.critical(f"Critical error occurred: {str(e)}", exc_info=True)