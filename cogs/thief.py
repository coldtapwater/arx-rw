import discord
from discord.ext import commands
import aiohttp
import utils.configs as uc
import utils.emojis as emojis
import io

class StealTools(commands.Cog, name="Steal Tools"):
    def __init__(self, bot):
        self.bot = bot


    @commands.group()
    async def steal(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand. Use 'r steal info' to see the steal command.")

    @steal.command()
    async def emoji(self, ctx, target_guild_id: int = None):
        """
        Grab an emoji from another message and add it to a server!
        """
        await self._steal_media(ctx, target_guild_id, media_type='emoji')

    @steal.command()
    async def sticker(self, ctx, target_guild_id: int = None):
        """
        Grab a sticker from another message and add it to a server!
        """
        await self._steal_media(ctx, target_guild_id, media_type='sticker')

    async def _steal_media(self, ctx, target_guild_id: int = None, media_type: str = 'emoji'):
        if target_guild_id:
            target_guild = self.bot.get_guild(target_guild_id)
            if not target_guild:
                await ctx.send(f"{emojis.ERROR} I couldn't find a server with that ID.")
                return
        else:
            target_guild = ctx.guild

        if not ctx.message.reference:
            await ctx.send(f"{emojis.ERROR} Reply to a message with a {media_type} for me to grab it.")
            return

        replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        
        if media_type == 'emoji':
            media = self._find_emoji(replied_message.content)
        else:  # sticker
            media = replied_message.stickers[0] if replied_message.stickers else None

        if not media:
            await ctx.send(f"{emojis.ERROR} This message doesn't have a {media_type}.")
            return

        try:
            if media_type == 'emoji':
                new_media = await self._create_emoji(target_guild, media)
            else:  # sticker
                new_media = await self._create_sticker(target_guild, media)
            
            text = f"{emojis.PREFIX} {media_type.capitalize()} Added\n"
            text += f"{media_type.capitalize()} added to {'this' if target_guild == ctx.guild else 'the target'} server!"
            text += f"\n- Added by {ctx.author.display_name}"
            await ctx.send(text)

        except discord.Forbidden:
            await ctx.send(f"{emojis.ERROR} I don't have permission to add this {media_type} to the server.")
        except discord.HTTPException as e:
            if 'Maximum number of stickers reached' in str(e):
                await ctx.send(f"{emojis.ERROR} The server has reached its maximum number of stickers.")
            elif 'Invalid image' in str(e):
                await ctx.send(f"{emojis.ERROR} The {media_type} image is invalid or unsupported.")
            else:
                await ctx.send(f"{emojis.ERROR} An error occurred while adding the {media_type}: {str(e)}")
        except Exception as e:
            await ctx.send(f"{emojis.ERROR} An unexpected error occurred: {str(e)}")

    def _find_emoji(self, content):
        for part in content.split():
            if part.startswith('<') and part.endswith('>'):
                return part
        return None

    async def _create_emoji(self, guild, emoji_string):
        emoji_id = emoji_string.split(':')[-1].strip('>')
        is_animated = emoji_string.startswith('<a:')
        emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{'gif' if is_animated else 'png'}"
        emoji_name = emoji_string.split(':')[1]

        async with aiohttp.ClientSession() as session:
            async with session.get(emoji_url) as response:
                if response.status != 200:
                    raise discord.HTTPException(response, 'Failed to get emoji')
                emoji_data = await response.read()

        return await guild.create_custom_emoji(name=emoji_name, image=emoji_data)

    async def _create_sticker(self, guild, sticker):
        sticker_url = sticker.url
        
        async with aiohttp.ClientSession() as session:
            async with session.get(sticker_url) as response:
                if response.status != 200:
                    raise discord.HTTPException(response, 'Failed to get sticker')
                sticker_data = await response.read()

        # Create a BytesIO object from the sticker data
        file = discord.File(io.BytesIO(sticker_data), filename="sticker.png")

        try:
            return await guild.create_sticker(
                name=sticker.name, 
                description="Stolen sticker",  # Default description
                emoji="🔥",
                file=file
            )
        except discord.HTTPException as e:
            if 'Invalid image' in str(e):
                # If the sticker is animated (GIF), try with .gif extension
                file = discord.File(io.BytesIO(sticker_data), filename="sticker.gif")
                return await guild.create_sticker(
                    name=sticker.name, 
                    description="Stolen sticker",
                    emoji="🔥",
                    file=file
                )
            else:
                raise

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} is ready.")

async def setup(bot):
    await bot.add_cog(StealTools(bot))