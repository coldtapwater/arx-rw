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
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io



# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

OWNER_ID = os.getenv('OWNER_ID')
version = '2.0.3'

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

bot = commands.Bot(command_prefix=['r ', 'R ', 'r!', 'R!', '- ' ], intents=intents, owner_id=OWNER_ID)

async def is_owner(ctx):
    return ctx.author.id == OWNER_ID

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
        try: 
            await ctx.send("Reloading the DB...")
            await init_db(DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
            await ctx.send("Reload complete.")
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

@bot.command(name='testerror', hidden=True)
@commands.is_owner()
async def test_error(ctx):
    raise ValueError("This is a test error to check the error handler.")

@bot.command()
async def info(ctx):
    # Prepare the info text
    info = [
        f"name: {bot.user.name}",
        f"version: {version}",
        f"prefix: {bot.command_prefix}",
        f"owner: j_coldtapwater",
        f"guilds: {len(bot.guilds)}",
        f"users: {len(set(bot.get_all_members()))}",
        f"discord.py version: {discord.__version__}",
        f"powered by iLBEngine"
    ]

    # Create a new image
    width, height = 800, 400
    image = Image.new('RGB', (width, height), color=f"#36393e")
    draw = ImageDraw.Draw(image)

    # Load and paste the logo
    logo = Image.open("C:\Users\Jason\Desktop\\arx-rw\logo.png")
    logo = logo.resize((500, 500))  # Resize if necessary
    image.paste(logo, (width - 500, 0), logo if logo.mode == 'RGBA' else None)

    # Add the text
    font = ImageFont.truetype("C:\Users\Jason\Desktop\\arx-rw\Gendy.otf", 20)  # Replace with path to a font file
    y_text = 50
    for line in info:
        draw.text((52, y_text+2), line, font=font, fill=(0, 0, 0, 128))
        draw.text((50, y_text), line, font=font, fill=(255, 255, 255, 255))
        y_text += 40

    # Save the image to a byte stream
    byte_io = io.BytesIO()
    image.save(byte_io, 'PNG')
    byte_io.seek(0)

    # Send the image
    await ctx.send(file=discord.File(fp=byte_io, filename='info.png'))

@bot.event
async def on_command_error(ctx, error):
    print(f"Error caught: {type(error).__name__}")
    if isinstance(error, commands.CommandInvokeError):
        original = error.original
        print(f"Original error: {type(original).__name__}")
        if isinstance(original, ValueError) and "This is a test error" in str(original):
            await ctx.send("Test error successfully caught by the inline error handler!")
            return
    # Handle other errors as needed
    print("Error wasn't handled by any specific case")
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

        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
        ErrorHandler.setup(bot)
        logger.info("Error handler setup completed")
    except KeyboardInterrupt:
        logger.info("Bot shutdown initiated by user.")
    except Exception as e:
        logger.critical(f"Critical error occurred: {str(e)}", exc_info=True)