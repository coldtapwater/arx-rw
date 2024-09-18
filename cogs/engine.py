import discord
from discord.ext import commands
from utils.snow.snow_engine import SnowEngine
import io
import base64

class MessageHandler:
    def __init__(self, bot, message, content, title="Response", color=discord.Color.blue()):
        self.bot = bot
        self.message = message
        self.content = content
        self.title = title
        self.color = color
        self.pages = []
        self.current_page = 0
        self.response_message = None

    def create_pages(self):
        content = self.content
        while content:
            if len(content) <= 1500:
                self.pages.append(content)
                break
            split_index = content.rfind('\n', 0, 1500)
            if split_index == -1:
                split_index = 1500
            self.pages.append(content[:split_index])
            content = content[split_index:].strip()

    def get_embed(self):
        embed = discord.Embed(title=f"{self.title} (Page {self.current_page + 1}/{len(self.pages)})",
                              description=self.pages[self.current_page],
                              color=self.color)
        return embed

    async def send_response(self):
        self.create_pages()
        if len(self.pages) == 1 and len(self.pages[0]) <= 2000:
            await self.message.channel.send(self.pages[0])
        else:
            await self.send_embed()

    async def send_embed(self):
        self.response_message = await self.message.channel.send(embed=self.get_embed())
        if len(self.pages) > 1:
            await self.add_reactions()
            self.bot.loop.create_task(self.listen_for_reactions())

    async def add_reactions(self):
        await self.response_message.add_reaction('⬅️')
        await self.response_message.add_reaction('➡️')

    async def listen_for_reactions(self):
        def check(reaction, user):
            return user == self.message.author and str(reaction.emoji) in ['⬅️', '➡️'] and reaction.message.id == self.response_message.id

        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', check=check)
                if str(reaction.emoji) == '➡️' and self.current_page < len(self.pages) - 1:
                    self.current_page += 1
                elif str(reaction.emoji) == '⬅️' and self.current_page > 0:
                    self.current_page -= 1
                await self.response_message.edit(embed=self.get_embed())
                await self.response_message.remove_reaction(reaction, user)
            except Exception as e:
                print(f"An error occurred while listening for reactions: {e}")
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
                try:
                    print(f"Message from {message.author}: {message.content}")
                    response = await self.snow_engine.process_message(message)
                    handler = MessageHandler(self.bot, message, response, "Snow Response")
                    if response.startswith("data:image/png;base64,"):
                        # It's a base64 encoded image, likely from LaTeX rendering
                        image_data = base64.b64decode(response.split(',')[1])
                        file = discord.File(io.BytesIO(image_data), filename="latex.png")
                        await message.reply(file=file)
                    else:
                        await handler.send_response()
                except Exception as e:
                    await message.reply(f"Error: {str(e)}")

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

    @commands.command(name="forcetype")
    async def force_conversation_type(self, ctx: commands.Context, conv_type: str):
        if conv_type.lower() not in ["casual", "deep"]:
            await ctx.send("Invalid conversation type. Please use 'casual' or 'deep'.")
            return
        
        await self.snow_engine.force_conversation_type(ctx.author.id, conv_type.lower())
        await ctx.send(f"Conversation type forced to {conv_type.lower()}.")

async def setup(bot: commands.Bot):
    await bot.add_cog(SnowCog(bot))