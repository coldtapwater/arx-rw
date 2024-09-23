import discord
from discord.ext import commands, tasks
import random
import logging
import datetime

logger = logging.getLogger('bot')

class DynamicStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status_messages = [
            ("Playing", "Calculating the meaning of life...42?", None),
            ("Listening", "The sound of silence (it's pretty loud).", None),
            ("Watching", "Paint dry in 4K resolution.", "https://youtu.be/PLOPygVcaVE"),
            ("Streaming", "My nonexistent Twitch channel.", "https://www.twitch.tv/theprimeagen"),
            ("Playing", "Hide and Seek... you can't find me!", None),
            ("Listening", "Elevator music on repeat.", "https://youtu.be/leEQ3nz8O-I"),
            ("Watching", "Cats chase lasers on YouTube.", "https://youtu.be/iPDqI9p8Foo"),
            ("Playing", "Rock, Paper, Scissors with AI (I never win).", None),
            ("Listening", "The voices in my circuits.", None),
            ("Watching", "Users type... 👀", None)
        ]
        self.change_status.start()

    def cog_unload(self):
        self.change_status.cancel()

    @tasks.loop(minutes=10)  # Change status every 10 minutes
    async def change_status(self):
        status_type, status_message, url = random.choice(self.status_messages)
        
        # Set a start time for activities that benefit from a duration
        start_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=random.randint(5, 60))

        if status_type == "Playing":
            activity = discord.Game(name=status_message, start=start_time)
        elif status_type == "Listening":
            activity = discord.Activity(type=discord.ActivityType.listening, name=status_message)
        elif status_type == "Watching":
            activity = discord.Activity(type=discord.ActivityType.watching, name=status_message, url=url)
        elif status_type == "Streaming":
            activity = discord.Streaming(name=status_message, url=url)
        else:
            # Default to Playing if an unknown type is encountered
            activity = discord.Game(name=status_message)

        await self.bot.change_presence(status=discord.Status.online, activity=activity)
        logger.info(f"Changed status to: {status_type} {status_message}")

    @change_status.before_loop
    async def before_change_status(self):
        await self.bot.wait_until_ready()

    @commands.command()
    async def status(self, ctx):
        await ctx.send("I'm currently " + random.choice(self.status_messages)[0] + " " + random.choice(self.status_messages)[1])

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f'{self.bot.user} has connected to Discord!')
        logger.info(f'Dynamic status cog loaded')
        await self.change_status()  # Set initial status

async def setup(bot):
    await bot.add_cog(DynamicStatus(bot))