import discord
from discord.ext import commands
import aiosqlite
import asyncio
import random


def uwuify(text):
    # Define replacements with random chance
    def random_replace(text, target, replacement, chance=0.5):
        return ''.join([replacement if char == target and random.random() < chance else char for char in text])

    # Basic replacements
    text = random_replace(text, 'r', 'w')
    text = random_replace(text, 'l', 'w')
    text = random_replace(text, 'R', 'W')
    text = random_replace(text, 'L', 'W')
    
    # Uwuify specific syllables
    text = random_replace(text, 'no', 'nyo')
    text = random_replace(text, 'mo', 'mowo')
    text = random_replace(text, 'na', 'nya')
    text = random_replace(text, 'ne', 'nye')
    text = random_replace(text, 'ni', 'nyi')
    text = random_replace(text, 'nu', 'nyu')
    text = random_replace(text, 'ho', 'hwo')

    # Random stutter addition
    def add_stutter(text):
        words = text.split()
        stuttered_words = []
        for word in words:
            if random.random() < 0.2:  # 20% chance to stutter
                stuttered_words.append(f"{word[0]}-{word}")
            else:
                stuttered_words.append(word)
        return ' '.join(stuttered_words)

    text = add_stutter(text)
    
    # Screams for all caps words
    def add_screams(text):
        words = text.split()
        screamed_words = []
        for word in words:
            if word.isupper():
                screamed_words.append(f"*{word.lower()}* \(・ω・)/ *screams*")
            else:
                screamed_words.append(word)
        return ' '.join(screamed_words)

    text = add_screams(text)

    return text

def loud(text):
    return text.upper()

class ArxUwU(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.webhooks = {}  # Initialize the webhooks dictionary

    @commands.command()
    async def uwu(self, ctx, target: discord.Member):
        """Uwu-ify a target member for 2 minutes for 3000 buckaroos."""
        user_id = ctx.author.id
        target_id = target.id
        cost = 3000
        duration = 120  # 2 minutes

        async with aiosqlite.connect('bot.db') as db:
            async with db.execute("SELECT wallet FROM users WHERE id = ?", (user_id,)) as cursor:
                result = await cursor.fetchone()
                if not result or result[0] < cost:
                    await ctx.send("You don't have enough buckaroos!", ephemeral=True)
                    return

        # Prompt for confirmation
        embed = discord.Embed(
            title="Confirm UwU",
            description=f"Are you sure you want to uwu-ify {target.mention} for 2 minutes at the cost of {cost} buckaroos?",
            color=discord.Color.pink()
        )

        confirm_view = discord.ui.View(timeout=30)
        confirm_button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.green)
        deny_button = discord.ui.Button(label="Deny", style=discord.ButtonStyle.red)

        async def confirm_callback(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return

            # Deduct cost and update database
            async with aiosqlite.connect('bot.db') as db:
                await db.execute("UPDATE users SET wallet = wallet - ? WHERE id = ?", (cost, user_id))
                await db.commit()

            # Create webhook for uwu-ification
            webhook = await ctx.channel.create_webhook(name=target.display_name, avatar=await target.display_avatar.read())
            self.bot.webhooks[target_id] = webhook

            async def uwu_listener(message):
                if message.author.id == target_id:
                    await message.delete()
                    await webhook.send(content=uwuify(message.content), username=target.display_name, avatar_url=target.display_avatar.url)

            self.bot.add_listener(uwu_listener, 'on_message')

            await interaction.response.send_message(f"{target.mention} is now uwu-ified for 2 minutes!", ephemeral=True)
            await asyncio.sleep(duration)

            self.bot.remove_listener(uwu_listener, 'on_message')
            await webhook.delete()
            del self.bot.webhooks[target_id]

        async def deny_callback(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return
            await interaction.response.send_message("UwU-ification cancelled.", ephemeral=True)

        confirm_button.callback = confirm_callback
        deny_button.callback = deny_callback

        confirm_view.add_item(confirm_button)
        confirm_view.add_item(deny_button)

        await ctx.send(embed=embed, view=confirm_view, ephemeral=True)

    @commands.command()
    async def loud(self, ctx, target: discord.Member):
        """Make a target member YELL for 2 minutes for 3000 buckaroos."""
        user_id = ctx.author.id
        target_id = target.id
        cost = 3000
        duration = 120  # 2 minutes

        async with aiosqlite.connect('bot.db') as db:
            async with db.execute("SELECT wallet FROM users WHERE id = ?", (user_id,)) as cursor:
                result = await cursor.fetchone()
                if not result or result[0] < cost:
                    await ctx.send("You don't have enough buckaroos!", ephemeral=True)
                    return

        # Prompt for confirmation
        embed = discord.Embed(
            title="Confirm Loud",
            description=f"Are you sure you want to make {target.mention} YELL for 2 minutes at the cost of {cost} buckaroos?",
            color=discord.Color.pink()
        )

        confirm_view = discord.ui.View(timeout=30)
        confirm_button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.green)
        deny_button = discord.ui.Button(label="Deny", style=discord.ButtonStyle.red)

        async def confirm_callback(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return

            # Deduct cost and update database
            async with aiosqlite.connect('bot.db') as db:
                await db.execute("UPDATE users SET wallet = wallet - ? WHERE id = ?", (cost, user_id))
                await db.commit()

            # Create webhook for loud
            webhook = await ctx.channel.create_webhook(name=target.display_name, avatar=await target.display_avatar.read())
            self.bot.webhooks[target_id] = webhook

            async def loud_listener(message):
                if message.author.id == target_id:
                    await message.delete()
                    await webhook.send(content=loud(message.content), username=target.display_name, avatar_url=target.display_avatar.url)

            self.bot.add_listener(loud_listener, 'on_message')

            await interaction.response.send_message(f"{target.mention} is now YELLING for 2 minutes!", ephemeral=True)
            await asyncio.sleep(duration)

            self.bot.remove_listener(loud_listener, 'on_message')
            await webhook.delete()
            del self.bot.webhooks[target_id]

        async def deny_callback(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return
            await interaction.response.send_message("Yelling cancelled.", ephemeral=True)

        confirm_button.callback = confirm_callback
        deny_button.callback = deny_callback

        confirm_view.add_item(confirm_button)
        confirm_view.add_item(deny_button)

        await ctx.send(embed=embed, view=confirm_view, ephemeral=True)
