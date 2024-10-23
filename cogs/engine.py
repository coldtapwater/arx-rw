from sre_constants import IN
import discord
from discord.ext import commands
from ollama import AsyncClient

import bot


sysPrompt = """

    """
cusPrompt = """

    """
class AetherAI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client = AsyncClient()

    async def generate_response(self, prompt: str):
        if prompt is not str:
            return ""
        response = await self.client.chat(
        model="granite3-moe",
        messages = [
        {"role": "system", "content": sysPrompt},
        {"role": "assistant", "content": cusPrompt},
        {"role": "user", "content": prompt},
        ])
        return response.get("content")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        
        if self.bot.user.mentioned_in(message):
            try:
                await message.reply(await self.generate_response(message.content))
            except Exception as e:
                await message.reply(f"I ran into a wall...\n-# Error: {e}")

    # You can add more commands here if needed

async def setup(bot: commands.Bot):
    await bot.add_cog(AetherAI(bot))