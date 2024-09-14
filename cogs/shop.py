import discord
from discord.ext import commands
from utils.economy_db import *
import utils.configs as uc
import utils.checks

class Shop(commands.Cog):
    def __init__(self, bot, embed_color):
        self.bot = bot
        self.embed_color = embed_color

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} is ready.")

    @commands.group(name="shop")
    async def shop(self, ctx):
        """Shop commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand. Use 'r shop view' to see the shop.")

    @shop.command(name="view")
    @utils.checks.blacklist_check()
    async def view(self, ctx):
        """View the shop"""
        await get_shop_items()
        message = "***Shop***\n\n\t"
        for item in await get_shop_items():
            message+=f"\t{item.emoji + item.name}\n\t({item.description} | Price: {item.price}{uc.CURRENCY})\n\t"
        await ctx.send(message)
    
    @shop.command(name="add_item")
    @commands.is_owner()
    async def add_item(self, ctx, *, item_info: str):
        """Add an item to the shop (Owner Only)"""
        try:
            # Split the input into name, description, and price
            parts = item_info.split('|')
            if len(parts) != 6:
                raise ValueError("Invalid format. Please use: name | description | price")

            name = parts[0].strip()
            price = int(parts[1].strip())
            description = parts[2].strip()
            emoji = parts[3].strip().replace("<", "").replace(">", "")
            sellable = parts[4].strip()
            stackable = parts[5].strip()

            # Call the add_items_to_shop function with separate arguments
            await add_items_to_shop(ctx, name=name, description=description, price=price, emoji=emoji, sellable=sellable, stackable=stackable)
        except ValueError as e:
            await ctx.send(f"Error: {str(e)}")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @shop.command(name="remove_item")
    @commands.is_owner()
    async def remove_item(self, ctx, name: str):
        """Remove an item from the shop (Owner Only)"""
        await remove_items_from_shop(ctx, name)

    @shop.command(name="buy")
    @utils.checks.blacklist_check()
    async def buy(self, ctx, name: str):
        """Buy an item from the shop"""
        await buy_item(ctx, name)

    @shop.command(name="sell")
    @utils.checks.blacklist_check()
    async def sell(self, ctx, name: str):
        """Sell an item back to the shop"""
        await sell_item(ctx, name)

    @commands.command(name="inventory", aliases=["inv, i"])
    @utils.checks.blacklist_check()
    async def inventory(self, ctx, user: discord.User = None):
        """Shows your inventory or another user's inventory"""
        if user is None:
            user = ctx.author
        await get_user_inventory(ctx, user_id=user.id)


async def setup(bot):
    await bot.add_cog(Shop(bot, uc.EMBED_COLOR))