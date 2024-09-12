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
        shop_embed = discord.Embed(
            title="Shop",
            color=discord.Color.from_str(self.embed_color)
        )
        for item in await get_shop_items():
            shop_embed.add_field(name=item.name, value=item.description)
        await ctx.send(
            embed=shop_embed
        )
    
    @shop.command(name="add_item")
    @commands.is_owner()
    async def add_item(self, ctx, name: str, description: str, price: int):
        """Add an item to the shop (Owner Only)"""
        await add_items_to_shop(ctx, name, description, 0)

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