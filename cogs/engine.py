import discord
from discord.ext import commands
from utils.aether.aether import Aether

class AetherAI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.snow_engine = Aether(bot)

    async def cog_load(self):
        await self.snow_engine.start()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        if self.bot.user.mentioned_in(message):
            await self.snow_engine.process_message(message)

    # You can add more commands here if needed

async def setup(bot: commands.Bot):
    await bot.add_cog(AetherAI(bot))