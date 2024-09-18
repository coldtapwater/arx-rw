import discord
from discord.ext import commands
from utils.snow.snow_engine import SnowEngine
import io
import base64
class SnowCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.snow_engine = SnowEngine(bot)

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
            async with message.channel.typing():
                print(f"Message from {message.author}: {message.content}")
                response = await self.snow_engine.process_message(message)
                if response.startswith("data:image/png;base64,"):
                    # It's a base64 encoded image, likely from LaTeX rendering
                    image_data = base64.b64decode(response.split(',')[1])
                    file = discord.File(io.BytesIO(image_data), filename="latex.png")
                    await message.reply(file=file)
                else:
                    await message.reply(response)

    @commands.command(name='jailbreak')
    @commands.is_owner()
    async def jailbreak(self, ctx: commands.Context, *, pattern: str):
        await self.snow_engine.add_jailbreak_pattern(pattern)
        await ctx.send(f"Jailbreak pattern '{pattern}' added to database.")

    @commands.command(name='clear')
    @commands.is_owner()
    async def clear(self, ctx: commands.Context):
        await self.snow_engine.clear_caches()
        await ctx.send("Caches and contexts cleared.")

async def setup(bot: commands.Bot):
    await bot.add_cog(SnowCog(bot))