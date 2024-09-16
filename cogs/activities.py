import discord
from discord.ext import commands
import utils.configs as uc
import random
import utils.emojis as my_emojis
import utils.general_db as gdb
import utils.economy_db as edb


class Activities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command()
    async def dig(self, ctx):
        inventory = await edb.get_user_inventory(ctx.author.id)
        if 'shovel' not in inventory:
            await ctx.send("You don't have a shovel. you can buy one with `r shop buy shovel`")
        else:
            coins = random.randint(1, 100)
            current_bal = await edb.get_user_balance(ctx.author.id)
            await ctx.send(f"you dug and found {my_emojis.CURRENCY_EMOJI} ***{coins}*** {uc.CURRENCY}! use them wisely :P\n-# you had {my_emojis.CURRENCY_EMOJI} {current_bal[0]} {uc.CURRENCY}")
            await edb.update_balance(ctx.author.id, wallet=coins)
    
    @commands.command()
    async def hunt(self, ctx):
        inventory = await edb.get_user_inventory(ctx.author.id)
        if 'axe' or 'rifle'not in inventory:
            await ctx.send("You don't have an axe/rifle. you can buy one with `r shop buy axe` or `r shop buy rifle`")
        else:
            if 'axe' in inventory:
                coins = random.randint(1, 100)
                current_bal = await edb.get_user_balance(ctx.author.id)
                await ctx.send(f"you hunted and found {my_emojis.CURRENCY_EMOJI} ***{coins}*** {uc.CURRENCY}! use them wisely :P\n-# you had {my_emojis.CURRENCY_EMOJI} {current_bal[0]} {uc.CURRENCY}")
                await edb.update_balance(ctx.author.id, wallet=coins)
            if 'rifle' in inventory:
                coins = random.randint(50, 200)
                current_bal = await edb.get_user_balance(ctx.author.id)
                await ctx.send(f"you hunted and found {my_emojis.CURRENCY_EMOJI} ***{coins}*** {uc.CURRENCY}! use them wisely :P\n-# you had {my_emojis.CURRENCY_EMOJI} {current_bal[0]} {uc.CURRENCY}")
                await edb.update_balance(ctx.author.id, wallet=coins)
            


async def setup(bot):
    await bot.add_cog(Activities(bot))
