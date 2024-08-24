#J_COLDTAPWATER, VERSION 1.3.3

import discord
from discord import Button, ui
from discord.ui import View, Button, TextInput, Modal
import random
from discord.ext import commands, tasks
import sqlite3
import aiosqlite
import os
from langchain_groq import ChatGroq
from langchain_community.chat_message_histories import ChatMessageHistory
from datetime import timedelta, datetime
import time
import asyncio
import aiohttp
import logging
import json
import utils.my_emojis as my_emojis
import cogs.arx_games
import cogs.arx_utils
import cogs.arx_fun
import cogs.arx_owner
import cogs.arx_uwu
import cogs.arx_cah
import cogs.arx_minesweeper
import cogs.arx_quote
import cogs.arx_meme
import cogs.arx_levels
import cogs.arx_ai
import cogs.arx_actions
import cogs.arx_find
import cogs.arx_heck

import utils.db_funcs as db_funcs
from dotenv import load_dotenv


load_dotenv()



logging.basicConfig(level=logging.INFO)
logging.warning("Starting up...")

#INTENTS
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True
intents.presences = True
intents.emojis = True
intents.emojis_and_stickers = True
intents.guilds = True


#PREFIX
bot = commands.Bot(command_prefix=["r ", "R ", "- "], intents=intents)


# bot = commands.Bot(command_prefix=["t$ "], intents=intents) # USED FOR TESTING

#RANDOM CONFIG STUFF
EMBED_COLOR = "#2a2d31"
CURRENCY = "buckaroos"
GAMBLE_BONUS = 1.25
DEP = 0.7
home_server_id = 1254445778466898003
bot_owner_id = 1151230208783945818
#^ WILL BE MOVED LATER


#BASIC EMOJIS
BANK_EMOJI = my_emojis.BANK_EMOJI
WALLET_EMOJI = my_emojis.WALLET_EMOJI
CROWN_EMOJI = my_emojis.CROWN_EMOJI
CURRENCY_EMOJI = my_emojis.CURRENCY_EMOJI
WORK_EMOJI = my_emojis.WORK_EMOJI
SHOP_EMOJI = my_emojis.SHOP_EMOJI
CRIME_EMOJI = my_emojis.CRIME_EMOJI
GOOD_WORK = my_emojis.GOOD_WORK
GEMS = my_emojis.GEMS
FORGE_EMOJI = my_emojis.FORGE

# LAURELS EMOJIS
ELITE = my_emojis.ELITE
ULTRA = my_emojis.ULTRA
PRESTIGE = my_emojis.PRESTIGE
ASCENDENT = my_emojis.ASCENDENT
ECHELON = my_emojis.ECHELON
VANGUARD = my_emojis.VANGUARD
LEGENDARY = my_emojis.LEGENDARY
ETERNAL = my_emojis.ETERNAL

BOT_OWNER = my_emojis.BOT_OWNER
SUPPORTER = my_emojis.SUPPORTER

# FUNCTIONS


async def humanize_time(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    if days > 0:
        return f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"
    if hours > 0 and days == 0:
        return f"{int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"
    if minutes > 0 and hours == 0:
        return f"{int(minutes)} minutes, {int(seconds)} seconds"
    if seconds > 0 and minutes == 0:
        return f"{int(seconds)} seconds"

async def get_home_server():
    return bot.get_guild(home_server_id)

async def is_owner(ctx):
    return ctx.author.id == bot_owner_id

async def humanize_currency(amount):
    if amount >= 1000000000:
        return f"{amount / 1000000000:.2f}B"
    if amount >= 1000000:
        return f"{amount / 1000000:.2f}M"
    if amount >= 1000:
        return f"{amount / 1000:.2f}K"
    if amount < 1000:
        return str(amount)
    return str(amount)

# BOT EVENTS
@bot.event
async def on_ready():
    logging.info(f"Bot is ready! -- {bot.user}")
    await bot.change_presence(activity=discord.Game(name=f"with your mom in {len(bot.guilds)} servers"))
    await bot.add_cog(cogs.arx_games.Games(bot, EMBED_COLOR))
    await bot.add_cog(cogs.arx_games.WordScramble(bot, EMBED_COLOR))
    await bot.add_cog(cogs.arx_games.FastClickGame(bot))
    await bot.add_cog(cogs.arx_utils.ArxUtils(bot, EMBED_COLOR))
    await bot.add_cog(cogs.arx_fun.ArxFun(bot, EMBED_COLOR))
    await bot.add_cog(cogs.arx_owner.updateUtils(bot, EMBED_COLOR))
    await bot.add_cog(cogs.arx_owner.onServerJoin(bot))
    await bot.add_cog(cogs.arx_uwu.UwU(bot))
    await bot.add_cog(cogs.arx_cah.CardsAgainstHumanity(bot, EMBED_COLOR))
    await bot.add_cog(cogs.arx_minesweeper.Minesweeper(bot))
    await bot.add_cog(cogs.arx_quote.Quotes(bot))
    await bot.add_cog(cogs.arx_meme.MemeCog(bot, EMBED_COLOR))
    await bot.add_cog(cogs.arx_levels.Levels(bot, EMBED_COLOR))
    await bot.add_cog(cogs.arx_ai.ArxAI(bot, EMBED_COLOR))
    await bot.add_cog(cogs.arx_actions.ArxActions(bot, EMBED_COLOR))
    await bot.add_cog(cogs.arx_find.Find(bot, EMBED_COLOR))
    await bot.add_cog(cogs.arx_heck.ArxHeck(bot, EMBED_COLOR))



# ERROR HANDLING
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"{my_emojis.ERROR} i thinks yous forgot something in your command hehehe")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"{my_emojis.ERROR} you made an oopsie in the command. hehehehe silly goose try agains")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(f"{my_emojis.ERROR} ayyyy buddy listen i cant let yous do that")
        logging.critical(f"{ctx.author} ({ctx.author.id}) tried to use {ctx.command} in {ctx.guild} in {ctx.channel} --- {error}")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send(f"{my_emojis.ERROR} wut... i cant do that bruv")
        logging.critical(f"{ctx.author} ({ctx.author.id}) tried to use {ctx.command} in {ctx.guild} in {ctx.channel} --- {error}")
    elif isinstance(error, commands.CommandOnCooldown):
        time_left = await humanize_time(error.retry_after)
        await ctx.send(f"{my_emojis.ERROR} heyyyyyyyy slow down! yous gots to wait {time_left}")
    elif isinstance(error, commands.NotOwner):
        await ctx.send(f"{my_emojis.ERROR} Heyyyyyyyy only the owner can use this command!!!! stop it!")
        logging.critical(f"{ctx.author} ({ctx.author.id}) tried to use {ctx.command} in {ctx.guild} in {ctx.channel} --- {error}")
    elif isinstance(error, commands.CommandInvokeError):
        await ctx.send(f"{my_emojis.ERROR} something went wrong with the command. please try again")
        logging.critical(f"{ctx.author} ({ctx.author.id}) tried to use {ctx.command} in {ctx.guild} in {ctx.channel} --- {error}")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(f"{my_emojis.ERROR} that is not a command. please try again")
        logging.critical(f"{ctx.author} ({ctx.author.id}) tried to use {ctx.command} in {ctx.guild} in {ctx.channel} --- {error}")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send(f"{my_emojis.ERROR} yous can't do that. sorry")
        logging.critical(f"{ctx.author} ({ctx.author.id}) tried to use {ctx.command} in {ctx.guild} in {ctx.channel} --- {error}")
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send(f"{my_emojis.ERROR} yous can't do that here. sorry")
        logging.critical(f"{ctx.author} ({ctx.author.id}) tried to use {ctx.command} in {ctx.guild} in {ctx.channel} --- {error}")
    elif isinstance(error, commands.CheckAnyFailure):
        await ctx.send(f"{my_emojis.ERROR} yous can't do that. sorry")
        logging.critical(f"{ctx.author} ({ctx.author.id}) tried to use {ctx.command} in {ctx.guild} in {ctx.channel} --- {error}")
    else:
        raise error


# OWNER COMMANDS
@bot.hybrid_command()
@commands.is_owner()
async def addmoney(ctx, member: discord.Member, amount: int):
    user_id = member.id
    user_data = await db_funcs.get_user_data(user_id)
    if user_data is None:
        await db_funcs.save_user_data(user_id, 0, 0, 0)
        user_data = (0, 0, 0)
    wallet, bank, gems = user_data
    wallet += amount
    await db_funcs.save_user_data(user_id, wallet, bank, gems)
    await ctx.send(f"{my_emojis.PREFIX} Added {amount} {CURRENCY} to {member.display_name}.")
    logging.info(f"{member.display_name} has been given {amount} {CURRENCY} by {ctx.author.display_name} in server: {ctx.guild.name}")


@bot.hybrid_command()
@commands.is_owner()
async def removemoney(ctx, member: discord.Member, amount: float):
    user_id = member.id
    user_data = await db_funcs.get_user_data(user_id)
    if user_data is None:
        await db_funcs.save_user_data(user_id, 0, 0, 0)
        user_data = (0, 0, 0)
    wallet, bank, gems = user_data
    wallet -= amount
    if wallet < 0:
        bank += wallet
        wallet = 0
    await db_funcs.save_user_data(user_id, wallet, bank, gems)
    await ctx.send(f"{my_emojis.PREFIX} Removed {amount} {CURRENCY} from {member.display_name}.")
    logging.info(f"{member.display_name} has removed {amount} {CURRENCY} by {ctx.author.display_name} in server: {ctx.guild.name}")


@bot.hybrid_command()   
async def createaccount(ctx):
    user_id = ctx.author.id
    user_data = await db_funcs.get_user_data(user_id)
    if user_data is None:
        await db_funcs.create_user(user_id)
        logging.info(f"{ctx.author.display_name} has created an account in server: {ctx.guild.name}")
        await ctx.send(f"{my_emojis.PREFIX} Account created.")
    else:
        wallet, bank, gems = user_data
        await db_funcs.save_user_data(user_id, wallet, bank, gems)
        await ctx.send(f"{my_emojis.ERROR} There is already an account for {ctx.author.display_name}.")
    


@bot.hybrid_command(aliases=['bal'])
async def balance(ctx, member: discord.Member = None):
    """Shows your balance"""
    if member is None:
        member = ctx.author
    user_id = str(member.id)
    user_data = await db_funcs.get_user_data(user_id)
    upgrades = await db_funcs.get_upgrades_inventory(user_id)
    if user_data is None:
        await db_funcs.save_user_data(user_id, 0, 0, 0)
        user_data = ('0', '0', '0')
    
    wallet = int(user_data[0])
    bank = int(user_data[1])
    gems = int(user_data[2])

    
    inventory = await db_funcs.get_inventory(user_id)
    items = await db_funcs.get_shop_items()
    
    laurels = ''
    
    for item in inventory:
        item_name, quantity = item[0], item[1]
        for shop_item in items:
            if shop_item[0].lower() == item_name.lower() and 'laurel' in shop_item[0].lower():
                laurels += f"{shop_item[3]} **{shop_item[0]}** \n" * int(quantity)
    
    embed = discord.Embed(title=f"{my_emojis.PREFIX} {ctx.author}'s Balance", color=discord.Color.from_str(EMBED_COLOR))
    if member.id == 1151230208783945818:
        embed.add_field(name="Name: ", value=f"{member.display_name} {BOT_OWNER}\n***arx Developer*** \n-- \nda best dev")
    else:
        embed.add_field(name="Name: ", value=f"{member.display_name}")
    
    if laurels:
        laurels = laurels[:-2]  # Remove the trailing newline
        embed.add_field(name="Laurels: ", value=laurels)
    
    embed.add_field(name=f"{WALLET_EMOJI} Wallet: ", value=f"{CURRENCY_EMOJI} {await humanize_currency(wallet)} {CURRENCY}", inline=False)
    embed.add_field(name=f"{BANK_EMOJI} Bank: ", value=f"{CURRENCY_EMOJI} {await humanize_currency(bank)} {CURRENCY}")
    embed.add_field(name="Net Worth: ", value=f"{CURRENCY_EMOJI} {await humanize_currency(wallet+bank)} {CURRENCY}", inline=False)
    embed.add_field(name=f"{GEMS} Gems: ", value=f"{GEMS} {await humanize_currency(gems)} Gems")
    
    embed.set_thumbnail(url=member.display_avatar.url)

    if upgrades:
        embed.set_image(url="https://i.imgur.com/2pZEnnF.jpeg")

    
    await ctx.send(embed=embed)



# ECONOMY COMMANDS

#STRATEGICALLY CHOOSE ALIASES FOR HYBRID COMMANDS; MAKE SURE THEY DO NOT OVERLAP WITH OTHER HYBRID COMMANDS
@bot.hybrid_command()
async def deposit(ctx, amount: str):
    """Deposits money into your account"""
    user_id = ctx.author.id
    user_data = await db_funcs.get_user_data(user_id)
    if user_data is None:
        await db_funcs.save_user_data(user_id, 0, 0, 0)
        user_data = (0, 0, 0)
    wallet, bank, gems = user_data
    if amount.lower() == "all":
        amount = wallet
    else:
        amount = int(amount)
    if amount <= 0 or amount > wallet:
        await ctx.send(f"{my_emojis.ERROR} Invalid amount to deposit.")
        return
    wallet -= amount
    bank += amount
    await db_funcs.save_user_data(user_id, wallet, bank, gems)
    embed = discord.Embed(title=f"{my_emojis.PREFIX} Deposit Successful", color=discord.Color.from_str(EMBED_COLOR))
    embed.add_field(name="Amount Deposited", value=f"{amount} {CURRENCY}")
    await ctx.send(embed=embed)


@bot.hybrid_command()
async def withdraw(ctx, amount: int):
    """Withdraws money from your account"""
    user_id = ctx.author.id
    user_data = await db_funcs.get_user_data(user_id)
    if user_data is None:
        await db_funcs.save_user_data(user_id, 0, 0, 0)
        user_data = (0, 0, 0)
    wallet, bank, gems = user_data
    if amount <= 0 or amount > bank:
        await ctx.send(f"{my_emojis.ERROR} Invalid amount to withdraw.")
        return
    wallet += amount
    bank -= amount
    await db_funcs.save_user_data(user_id, wallet, bank, gems)
    embed = discord.Embed(title=f"{my_emojis.PREFIX} Withdrawal Successful", color=discord.Color.from_str(EMBED_COLOR))
    embed.add_field(name="Amount Withdrawn", value=f"{amount} {CURRENCY}")
    await ctx.send(embed=embed)


@bot.hybrid_command()
@commands.cooldown(1, 60*60*12, commands.BucketType.user)
async def work(ctx):
    """Gives you money for working"""
    user_id = ctx.author.id
    user_data = await db_funcs.get_user_data(user_id)
    if user_data is None:
        await db_funcs.save_user_data(user_id, 0, 0, 0)
        user_data = (0, 0, 0)
    wallet, bank, gems = user_data
    earnings = random.randint(10000, 100000)
    boost = 1
    inventory = await db_funcs.get_inventory(user_id)
    if any(item[0] == "Coffee" for item in inventory):
        boost = 1.2
        inventory = [item for item in inventory if item[0] != "Coffee"]
        await db_funcs.save_user_data(user_id, wallet, bank, gems)
    wallet += int(boost * earnings)
    await db_funcs.save_user_data(user_id, wallet, bank, gems)
    embed = discord.Embed(title=f"{my_emojis.PREFIX} Great Job!", color=discord.Color.from_str(EMBED_COLOR))
    embed.set_footer(text=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    embed.set_thumbnail(url="https://miro.medium.com/v2/resize:fit:1000/1*xTV_l3RAEocW6zzp7OWspg.gif")
    embed.add_field(name=f"{WORK_EMOJI} You received:", value=f"{CURRENCY_EMOJI} {earnings} {CURRENCY}")
    if boost > 1:
        embed.set_footer(text=f"Your work was boosted by using a Coffee")
    await ctx.send(embed=embed)


@bot.hybrid_command()
async def shop(ctx):
    """View the shop"""
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('SELECT * FROM shop')
    items = c.fetchall()
    conn.close()
    embed = discord.Embed(title=f"{SHOP_EMOJI} Shop", color=discord.Color.from_str(EMBED_COLOR))
    embed.set_thumbnail(url="https://media0.giphy.com/media/V49UiwmIhdtss/200w.gif?cid=6c09b9528qnzp447dx9s95pmm4p5ekiidabn8dziq6qfaz31&ep=v1_gifs_search&rid=200w.gif&ct=g")
    for item in items:
        embed.add_field(name=f"{item[3]}. {item[0]} -- {item[1]} {CURRENCY}", value=f"{item[2]}", inline=False)
    await ctx.send(embed=embed)


@bot.hybrid_command()
@commands.cooldown(1, 60*60*12, commands.BucketType.user)
async def rob(ctx, member: discord.Member):
    """Rob another user"""
    user_id = ctx.author.id
    target_id = member.id
    if ctx.author == member:
        await ctx.send(f"{my_emojis.ERROR} you cant rob yourself silly!")
        return
    if bot.user == member.id:
        await ctx.send(f"{my_emojis.ERROR} You cant rob me ya big meanie!")
        return
    user_data = await db_funcs.get_user_data(user_id)
    target_data = await db_funcs.get_user_data(target_id)
    if target_data is None or target_data[0] == 0:
        await ctx.send(f"{my_emojis.ERROR} this person dont have any money in their wallets!")
        return
    if user_data is None:
        await db_funcs.save_user_data(user_id, 0, 0, 0)
        user_data = (0, 0, 0)
    wallet, bank, gems = user_data
    target_wallet, target_bank, target_gems = target_data
    if random.random() < 0.7:
        amount = random.randint(20, 75)
        wallet -= amount
        await db_funcs.save_user_data(user_id, wallet, bank, gems)
        embed = discord.Embed(title=f"{my_emojis.PREFIX} You failed to steal money", color=discord.Color.from_str(EMBED_COLOR))
        embed.add_field(name="You got fined:", value=f"{amount} {CURRENCY}")
        embed.set_footer(text="You can rob someone again in 12 hours")
        await ctx.send(embed=embed)
    else:
        amount = random.randint(50, 100)
        target_wallet -= amount
        wallet += amount
        await db_funcs.save_user_data(user_id, wallet, bank, gems)
        await db_funcs.save_user_data(target_id, target_wallet, target_bank, target_gems)
        embed = discord.Embed(title=f"{my_emojis.PREFIX} You stole money!", color=discord.Color.from_str(EMBED_COLOR))
        embed.add_field(name="You stole:", value=f"{amount} {CURRENCY}")
        embed.set_footer(text="You can rob someone again in 12 hours")
        await ctx.send(embed=embed)


@bot.hybrid_command()
@commands.cooldown(1, 60*60*12, commands.BucketType.user)
async def crime(ctx):
    """Commit a crime"""
    user_id = ctx.author.id
    user_data = await db_funcs.get_user_data(user_id)
    if user_data is None:
        await db_funcs.save_user_data(user_id, 0, 0, 0)
        user_data = (0, 0, 0)
    wallet, bank, gems = user_data
    if random.random() < 0.75:
        amount = random.randint(70, 100)
        wallet -= amount
        await db_funcs.save_user_data(user_id, wallet, bank, gems)
        embed = discord.Embed(title=f"{my_emojis.PREFIX} You failed to commit a crime", color=discord.Color.from_str(EMBED_COLOR))
        embed.add_field(name="You got fined:", value=f"{amount} {CURRENCY}")
        embed.set_footer(text="You can commit a crime again in 12 hours")
        await ctx.send(embed=embed)
    else:
        amount = random.randint(10000, 500000)
        wallet += amount
        await db_funcs.save_user_data(user_id, wallet, bank, gems)
        embed = discord.Embed(title=f"{CRIME_EMOJI} You committed a crime!", color=discord.Color.from_str(EMBED_COLOR))
        embed.add_field(name="You got:", value=f"{amount} {CURRENCY}")
        embed.set_footer(text="You can commit a crime again in 12 hours")
        await ctx.send(embed=embed)


@bot.hybrid_command(aliases=['lb'])
async def leaderboard(ctx):
    """View the leaderboard"""
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('SELECT id, wallet, bank FROM users')
    users = c.fetchall()
    c.execute('SELECT user_id, item_name FROM inventory')
    inventory_items = c.fetchall()
    shop_items = await db_funcs.get_shop_items()  # Fetching the shop items from the database
    # Create a dictionary to map item names to their details for laurels
    laurels = {item[0].lower(): item for item in shop_items if 'laurel' in item[0].lower()}

    leaderboard_data = []
    inventory_dict = {}
    

    for user_id, wallet, bank in users:
        inventory = {}
        for inventory_user_id, item_name in inventory_items:
            if inventory_user_id == user_id:
                inventory[item_name] = inventory.get(item_name, 0) + 1
        total_balance = wallet + bank
        user = await bot.fetch_user(user_id)
        user_laurels = ''
        for item_name, quantity in inventory.items():
            if item_name.lower() in laurels and quantity > 0:
                user_laurels += laurels[item_name.lower()][3] * quantity  # Accessing the emoji from the tuple
        leaderboard_data.append((user, total_balance, user_laurels))
        inventory_dict[user_id] = inventory

    leaderboard_data.sort(key=lambda x: x[1], reverse=True)

    embed = discord.Embed(title=f"{my_emojis.PREFIX} Leaderboard", description="Top 10 players by net worth", color=discord.Color.from_str(EMBED_COLOR))
    for idx, (user, balance, user_laurels) in enumerate(leaderboard_data[:10], 1):
        user_display = f"{user.name}"
        supporters = ["526526821873876994", "824400229645418497", "1151230208783945818", "1152768275818741780"]
        if str(user.id) in supporters:
            user_display += f"{SUPPORTER}"
        
        inventory_str = ''
        if user.id in inventory_dict:
            for item_name, quantity in inventory_dict[user.id].items():
                if item_name.lower() in laurels:
                    inventory_str += f"{laurels[item_name.lower()][3]}"  # Accessing the emoji from the tuple
        if idx == 1:
            embed.add_field(name=f"{CROWN_EMOJI} {user_display} ", value=f"{user_laurels}\n{balance} {CURRENCY}", inline=False)
        else:
            embed.add_field(name=f"{idx}. {user_display} ", value=f"{user_laurels}\n{balance} {CURRENCY}", inline=False)


    await ctx.send(embed=embed)


@commands.cooldown(1, 60*60*24, commands.BucketType.user)
@bot.hybrid_command()
async def daily(ctx):
    """Claim your daily reward"""
    user_id = ctx.author.id
    user_data = await db_funcs.get_user_data(user_id)
    if user_data is None:
        await db_funcs.save_user_data(user_id, 0, 0, 0)
        user_data = (0, 0, 0)
    wallet, bank, gems = user_data
    amount = random.randint(1000, 50000)
    wallet += amount
    await db_funcs.save_user_data(user_id, wallet, bank, gems)
    embed = discord.Embed(title=f"{my_emojis.PREFIX} {ctx.author}'s Daily", description=f"You received {amount} {CURRENCY}!", color=discord.Color.from_str(EMBED_COLOR))
    await ctx.send(embed=embed)


@commands.cooldown(1, 60*60*24*7, commands.BucketType.user)
@bot.hybrid_command()
async def weekly(ctx):
    """Claim your weekly reward"""
    user_id = ctx.author.id
    user_data = await db_funcs.get_user_data(user_id)
    if user_data is None:
        await db_funcs.save_user_data(user_id, 0, 0, 0)
        user_data = (0, 0, 0)
    wallet, bank, gems = user_data
    amount = random.randint(1000, 50000)
    wallet += amount
    await db_funcs.save_user_data(user_id, wallet, bank, gems)
    embed = discord.Embed(title=f"{my_emojis.PREFIX} {ctx.author}'s Weekly", description=f"You received {amount} {CURRENCY}!", color=discord.Color.from_str(EMBED_COLOR))
    await ctx.send(embed=embed)


@commands.cooldown(1, 60*60*24*30, commands.BucketType.user)
@bot.hybrid_command()
async def monthly(ctx):
    """Claim your monthly reward"""
    user_id = ctx.author.id
    user_data = await db_funcs.get_user_data(user_id)
    if user_data is None:
        await db_funcs.save_user_data(user_id, 0, 0, 0)
        user_data = (0, 0, 0)
    wallet, bank, gems = user_data
    amount = random.randint(100000, 500000)
    wallet += amount
    await db_funcs.save_user_data(user_id, wallet, bank, gems)
    embed = discord.Embed(title=f"{my_emojis.PREFIX} {ctx.author}'s Monthly", description=f"You received {amount} {CURRENCY}!", color=discord.Color.from_str(EMBED_COLOR))
    await ctx.send(embed=embed)


@bot.hybrid_command()
async def slots(ctx, amount: int):
    """Play slots and win big!"""
    emojis = "🍎🍊🍐🍋🍉🍇🍓🍒"
    user_id = ctx.author.id
    user_data = await db_funcs.get_user_data(user_id)
    if user_data is None:
        await db_funcs.save_user_data(user_id, 0, 0, 0)
        user_data = (0, 0, 0)
    wallet, bank, gems = user_data
    if amount > wallet:
        await ctx.send(f"{my_emojis.ERROR} {ctx.author.mention} You don't have that much money!")
        return
    winning_amount = GAMBLE_BONUS * amount
    await ctx.send(f"{my_emojis.PREFIX} Pulling a slot... with a your potential winnings being: {winning_amount} {CURRENCY}")
    await asyncio.sleep(1)
    content = discord.Embed(title=f"{my_emojis.PREFIX} {ctx.author.name}'s Casino", color=discord.Color.from_str(EMBED_COLOR))
    content.add_field(name=f"You bet {amount} {CURRENCY}", value=f"Picking emojis...")
    msg = await ctx.send(embed=content)
    a = random.choice(emojis)
    b = random.choice(emojis)
    c = random.choice(emojis)
    await asyncio.sleep(2)
    pulled = discord.Embed(title=f"{my_emojis.PREFIX} {ctx.author.name}'s Casino", color=discord.Color.from_str(EMBED_COLOR))
    pulled.add_field(name=f"You pulled:", value=f"**{a}** **{b}** **{c}**")
    await msg.edit(embed=pulled)
    await asyncio.sleep(4)
    if a == b == c:
        wallet += winning_amount
        await db_funcs.save_user_data(user_id, wallet, bank, gems)
        all_three = discord.Embed(title=f"{my_emojis.PREFIX} {ctx.author.name}'s Casino", color= discord.Color.from_str(EMBED_COLOR))
        all_three.add_field(name=f"You won {GAMBLE_BONUS*amount} {CURRENCY}!", value=f"**{a}** **{b}** **{c}**")
        await msg.edit(embed=all_three)
    elif a == c:
        wallet += amount
        await db_funcs.save_user_data(user_id, wallet, bank, gems)
        twot = discord.Embed(title=f"{my_emojis.PREFIX} {ctx.author.name}'s Casino", color = discord.Color.from_str(EMBED_COLOR))
        twot.add_field(name=f"You won back your original bet {amount} {CURRENCY}!", value=f"**{a}** **{b}** **{c}**")
        await msg.edit(embed=twot)
    else:
        wallet -= GAMBLE_BONUS*amount
        await db_funcs.save_user_data(user_id, wallet, bank, gems)
        lose = discord.Embed(title=f"{ctx.author.name}'s Casino", color = discord.Color.from_str(EMBED_COLOR))
        lose.add_field(name=f"You lost {GAMBLE_BONUS*amount} {CURRENCY}!", value=f"**{a}** **{b}** **{c}**")
        await msg.edit(embed=lose)


@bot.hybrid_command()
async def convert(ctx, quantity: int):
    """Convert your gems into buckaroos!"""
    user_id = ctx.author.id
    user_data = await db_funcs.get_user_data(user_id)
    if user_data is None:
        await db_funcs.save_user_data(user_id, 0, 0, 0)
        user_data = (0, 0, 0)
    wallet, bank, gems = user_data
    if gems >= quantity * 2:
        wallet += quantity * 1000
        gems -= quantity * 2
        await db_funcs.save_user_data(user_id, wallet, bank, gems)
        await ctx.send(f"{my_emojis.PREFIX} {ctx.author.mention} converted {quantity} gems into {quantity * 1000} buckaroos!")
    else:
        await ctx.send(f"{my_emojis.ERROR} {ctx.author.mention} you don't have enough gems to convert!")


@bot.hybrid_command()
async def buy(ctx, *, item_name: str, quantity: int = 1):
    """Buy an item from the shop"""
    user_id = ctx.author.id
    user_data = await db_funcs.get_user_data(user_id)
    if user_data is None:
        await db_funcs.save_user_data(user_id, 0, 0, 0)
        user_data = (0, 0, 0)
    wallet, bank, gems = user_data
    items = await db_funcs.get_shop_items()

    item = next((i for i in items if i[0].lower() == item_name.lower()), None)  # Access by index
    if not item:
        await ctx.send(f"{my_emojis.ERROR} This item does not exist in the shop.")
        return
    item_name, item_price, item_description, item_emoji, item_sellable, item_stackable = item

    if wallet < item_price * quantity:
        await ctx.send(f"{my_emojis.ERROR} You don't have enough credits to buy this item.")
        return
    wallet -= item_price * quantity
    inventory = await db_funcs.get_inventory(user_id)
    inventory_dict = {item[0]: item[1] for item in inventory}

    # Update inventory or add the item
    if item_name in inventory_dict:
        inventory_dict[item_name] += quantity
    else:
        inventory_dict[item_name] = quantity

    # Save only the updated item in inventory_dict
    await db_funcs.save_inventory(user_id, item_name, inventory_dict[item_name])

    # Update the user's wallet
    await db_funcs.save_user_data(user_id, wallet, bank, gems)

    await ctx.send(f"{my_emojis.PREFIX} You have purchased {quantity} {item_name} for {item_price * quantity} credits. You now have {inventory_dict[item_name]} {item_name} in your inventory.")


@bot.hybrid_command()
async def send(ctx, member: discord.Member, amount: int):
    """Sends money to another user"""
    user_id = ctx.author.id
    member_id = member.id
    user_data = await db_funcs.get_user_data(user_id)
    member_data = await db_funcs.get_user_data(member_id)
    if user_data is None:
        await ctx.send(f"{my_emojis.ERROR} hmmm i dont see yous in my system. try using me to get some {CURRENCY}.")
        return
    if amount > user_data[0]:
        await ctx.send(f"{my_emojis.ERROR} You don't have that much money!")
        return
    if amount > 1000:
        await ctx.send(f"{my_emojis.ERROR} woah woah woahs! you cants send more than 1000 {CURRENCY} at once. try `/banktransfer` insteads.")
        return
    if member_data is None:
        await db_funcs.save_user_data(member_id, 0, 0, 0)
        member_data = (0, 0, 0)
    user_wallet, user_bank, user_gems = user_data
    member_wallet, member_bank, member_gems = member_data
    user_wallet -= amount
    member_wallet += amount
    await db_funcs.save_user_data(user_id, user_wallet, user_bank, user_gems)
    await db_funcs.save_user_data(member_id, member_wallet, member_bank, member_gems)
    await ctx.send(f"{my_emojis.PREFIX} Sent {amount} {CURRENCY} to {member.mention}.")


@bot.hybrid_command(aliases=["bt", "transfer"])
async def banktransfer(ctx, member: discord.Member, amount: int):
    """Transfers money from one user to another"""
    user_id = ctx.author.id
    member_id = member.id
    user_data = await db_funcs.get_user_data(user_id)
    member_data = await db_funcs.get_user_data(member_id)
    FEE = 0.05
    if user_data is None:
        await ctx.send(f"{my_emojis.ERROR} hmmm i dont see yous in my system. try using me to get some {CURRENCY}.")
        return
    if amount*(1 + FEE) > user_data[1]:
        await ctx.send(f"{my_emojis.ERROR} You don't have that much money!")
        return
    if amount < 1000:
        await ctx.send(f"{my_emojis.ERROR} ahoy there! you cants send less than 1000 {CURRENCY}.")
        return
    if member_data is None:
        await db_funcs.save_user_data(member_id, 0, 0, 0)
        member_data = (0, 0, 0)
    user_wallet, user_bank, user_gems = user_data
    member_wallet, member_bank, member_gems = member_data
    user_wallet -= amount * (1 + FEE)
    member_wallet += amount
    await db_funcs.save_user_data(user_id, user_wallet, user_bank, user_gems)
    await db_funcs.save_user_data(member_id, member_wallet, member_bank, member_gems)
    await ctx.send(f"{my_emojis.PREFIX} Sent {amount} {CURRENCY} to {member.mention} for a fee of {amount * FEE} {CURRENCY}.")


@bot.hybrid_command()
@commands.cooldown(1, 15, commands.BucketType.user)
async def beg(ctx):
    """Begs for money"""
    user_id = ctx.author.id
    user_data = await db_funcs.get_user_data(user_id)
    if user_data is None:
        await db_funcs.save_user_data(user_id, 0, 0, 0)
        user_data = (0, 0, 0)
    wallet, bank, gems = user_data
    chance = random.randint(1, 100)
    if chance > 85:
        amount = random.randint(1, 100)  # Random amount of currency
        wallet += amount
        await db_funcs.save_user_data(user_id, wallet, bank, gems)
        embed = discord.Embed(title=f"{my_emojis.PREFIX} You Begged", color=discord.Color.from_str(EMBED_COLOR))
        embed.add_field(name="You got:", value=f"{amount} {CURRENCY}")
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"{my_emojis.ERROR} You didn't get anything. Try again in 15 seconds.")


@bot.hybrid_command(aliases=["inv", "invent"])
async def inventory(ctx, member: discord.Member = None):
    """Shows your inventory"""
    if member is None:
        member = ctx.author
    user_id = str(member.id)
    inventory = await db_funcs.get_inventory(user_id)
    shop = await db_funcs.get_shop_items()

    # Debugging: Print the inventory structure
    logging.info(f"Inventory structure for user {user_id}: {inventory}")

    if not inventory:
        await ctx.send(f"{my_emojis.ERROR} {member.display_name}, you dont gots anything.")
        return

    # Create pages of the inventory, each with a maximum of 25 fields
    pages = []
    current_page = discord.Embed(title=f"{my_emojis.PREFIX} {member.display_name}'s Inventory", color=discord.Color.from_str(EMBED_COLOR))
    current_page.set_thumbnail(url=member.display_avatar.url)
    field_count = 0

    for item_data in inventory:
        logging.info(f"Processing item_data: {item_data}")

        # Ensure item_data is a tuple or list and has at least two elements
        if isinstance(item_data, (tuple, list)) and len(item_data) >= 2:
            item_name, quantity = item_data[0], item_data[1]
        else:
            logging.warning(f"Unexpected item_data structure: {item_data}")
            continue

        # Assuming shop items are tuples in the form (name, price, description, emoji, sellable, stackable)
        emoji = next((item[3] for item in shop if item[0] == item_name), None)
        if emoji is None:
            logging.warning(f"No emoji found for item {item_name}")
            emoji = "\u200b"

        if field_count == 25:
            pages.append(current_page)
            current_page = discord.Embed(title=f"{my_emojis.PREFIX} {member.display_name}'s Inventory", color=discord.Color.from_str(EMBED_COLOR))
            current_page.set_thumbnail(url=member.display_avatar.url)
            field_count = 0

        current_page.add_field(name=f"{emoji} **{item_name}**  --  {quantity}", value="\u200b", inline=False)
        field_count += 1

    if field_count > 0:
        pages.append(current_page)

    # Send the pages
    for page in pages:
        await ctx.send(embed=page)


@bot.hybrid_command()
async def give(ctx, member: discord.Member, item: str):
    """Gives an item to another user"""
    user_id = ctx.author.id
    member_id = member.id
    item = item.title()
    inventory = await db_funcs.get_inventory(user_id)

    if not inventory:
        await ctx.send(f"{my_emojis.ERROR} you dont gots anything to give {member.mention}.")
        return
    
    if item not in [item[0] for item in inventory]:
        await ctx.send(f"{my_emojis.ERROR} i dont thinks thats in ur inventory {member.mention}.")
        return

    if 'Laurel' in item:
        await ctx.send(f"{my_emojis.ERROR} i sorry {member.mention}, but you can't give that away i wonts let you.")
        return

    await db_funcs.give_item(user_id, member_id, item)
    await ctx.send(f"{my_emojis.PREFIX} Given {item} to {member.mention}.")


@bot.hybrid_command()
@commands.cooldown(1, 60, commands.BucketType.user)
async def dig(ctx):
    """Dig for coins"""
    user_id = ctx.author.id
    user_data = await db_funcs.get_user_data(user_id)
    chance = random.randint(1, 100)
    if user_data is None:
        await db_funcs.save_user_data(user_id, 0, 0, 0)
        user_data = (0, 0, 0)
    inventory = await db_funcs.get_inventory(user_id)
    inventory_dict = {item[0]: item[1] for item in inventory}
    if 'Shovel' not in inventory_dict or inventory_dict['Shovel'] <= 0:
        await ctx.send(f"{my_emojis.ERROR} yous needs a shovel to do the great digging! me thinks you can buys one from the shop.")
        return
    bonus = 0
    if "Shiny Detector" in inventory_dict and inventory_dict["Shiny Detector"] > 0:
        for item_name, quantity in inventory_dict.items():
            await db_funcs.save_inventory(user_id, item_name, quantity)
        bonus = random.randint(10000, 100000)
    
    amount = random.randint(10, 100000)  # Random reward amount
    wallet, bank, gems = user_data
    wallet += amount + bonus
    
    if amount > 10000:
        embed = discord.Embed(title=f"{my_emojis.PREFIX} You found something huge!", color=discord.Color.from_str(EMBED_COLOR))
        embed.add_field(name=f"Wowzas, you founds a lot of {CURRENCY}! mayhaps this was a treasure chest?", value="\u200b")
        embed.add_field(name="You Found", value=f"{amount} {CURRENCY}")
        if bonus > 0:
            embed.set_footer(text=f"Bonus: {bonus} {CURRENCY} from Shiny Detector")
        else:
            embed.set_footer(text="Want a bonus from Shiny Detector? Buy one from the shop first.")
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title=f"{my_emojis.PREFIX} You found something!", color=discord.Color.from_str(EMBED_COLOR))
        embed.add_field(name="You Found", value=f"{amount} {CURRENCY}")
        await ctx.send(embed=embed)

    await db_funcs.save_user_data(user_id, wallet, bank, gems)


@bot.hybrid_command()
async def hunt(ctx):
    """Hunt for animals"""
    user_id = ctx.author.id
    user_data = await db_funcs.get_user_data(user_id)
    if user_data is None:
        await db_funcs.save_user_data(user_id, 0, 0, 0)
        user_data = (0, 0, 0)
    inventory = await db_funcs.get_inventory(user_id)
    inventory_dict = {item[0]: item[1] for item in inventory}
    if 'Pistol' not in inventory_dict or inventory_dict['Pistol'] <= 0:
        await ctx.send(f"{my_emojis.ERROR} to do the shooty shooty you need a Pistol! me thinks you can buys one from the shop.")
        return
    chance = random.randint(1, 100)
    animals = ["Rabbit", "Turtle", "Penguin", "Snake", "Lizard", "Spider", "Squirrel", "Deer", "Caterpillar", "Fox", "Raccoon", "Bear", "Pig", "Chicken", "Horse", "Dog", "Cat", "Dolphin", "Whale", "Shark"]
    if 'Rifle' in inventory_dict and inventory_dict['Rifle'] > 0:
        chance += 20
        logging.info(f"{ctx.author} has a high chance of finding a wild animal. -- from guild: {ctx.guild}")
    amount = random.randint(10, 1000)  # Random reward amount
    wallet, bank, gems = user_data
    wallet += amount
    await db_funcs.save_user_data(user_id, wallet, bank, gems)
    if chance >= 70:
        animal = random.choice(animals)
        embed = discord.Embed(title=f"{my_emojis.PREFIX} You found a {animal}... and then yous killed it", color=discord.Color.from_str(EMBED_COLOR))
        embed.add_field(name="You sold it for", value=f"{amount} {CURRENCY}")
        await ctx.send(embed=embed)
    elif 70 > chance >= 40:
        animal = random.choice(animals)
        embed = discord.Embed(title=f"{my_emojis.PREFIX} you did the shooty shooty at a wild {animal} but missed!", color=discord.Color.from_str(EMBED_COLOR))
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title=f"{my_emojis.ERROR} you didn't find anything. nows you gots to wait", color=discord.Color.from_str(EMBED_COLOR))
        await ctx.send(embed=embed)


@bot.hybrid_command()
async def wack(ctx, target: discord.Member=None):
    """Wack someone!"""
    user_id = ctx.author.id
    user_data = await db_funcs.get_user_data(user_id)
    if user_data is None:
        await db_funcs.save_user_data(user_id, 0, 0, 0)
        user_data = (0, 0, 0)
    if target is None:
        await ctx.send(f"{my_emojis.ERROR} You didn't tell me who to wack!")
        return
    if target == ctx.author:
        await ctx.send(f"{my_emojis.ERROR} You can't wack yourself!")
        return
    if target == bot.user:
        amount = random.randint(10, 100)
        await ctx.send(f"{my_emojis.PREFIX} OWWWWW! THAT HURT ME! IM TAKING AWAY SOME OF YOUR MONEY!")
        if user_data[0] >= amount:
            wallet, bank, gems = user_data
            wallet -= amount
            await db_funcs.save_user_data(user_id, wallet, bank, gems)
    inventory = await db_funcs.get_inventory(user_id)
    inventory_dict = {item[0]: item[1] for item in inventory}
    if 'Big Wacker' not in inventory_dict or inventory_dict['Big Wacker'] <= 0:
        await ctx.send(f"{my_emojis.ERROR} to wacketh someone you need a Big Wacker! me thinks you can buys one from the shop.")
        return
    chance = random.randint(1, 100)
    if chance >= 50:
        embed = discord.Embed(title=f"{my_emojis.PREFIX} you wacked {target}! such rude activity smh", color=discord.Color.from_str(EMBED_COLOR))
        await ctx.send(embed=embed)
        inventory_dict['Big Wacker'] -= 1
    elif 50 > chance:
        embed = discord.Embed(title=f"{my_emojis.PREFIX} yous tried to wacketh {target} but missed by so much! hehe", color=discord.Color.from_str(EMBED_COLOR))
        await ctx.send(embed=embed)


@bot.hybrid_command()
async def userole(ctx, color: str, *, role_name: str):
    """Create a role with the color (#000000 as an example) and name you want!"""
    user_id = ctx.author.id
    user_data = await db_funcs.get_user_data(user_id)
    inventory = await db_funcs.get_inventory(user_id)
    inventory_dict = {item[0]: item[1] for item in inventory}
    if user_data is None or "Custom Role" not in inventory_dict or inventory_dict["Custom Role"] <= 0:
        await ctx.send(f"{my_emojis.ERROR} you dont gots the Custom Role in your inventory, so you can't create a role")
        return
    try:
        role_color = discord.Color(int(color.lstrip('#'), 16))
    except ValueError:
        await ctx.send(f"{my_emojis.ERROR} Invalid color. Please provide a hex color code.")
        return
    role = await ctx.guild.create_role(name=role_name, color=role_color)
    await ctx.author.add_roles(role)
    
    
    inventory_dict["Custom Role"] - 1
    if inventory_dict["Custom Role"] == 0:
        del inventory_dict["Custom Role"]
    for item_name, quantity in inventory_dict.items():
        await db_funcs.save_inventory(user_id, item_name, quantity)
    await ctx.send(f"{my_emojis.PREFIX} da role '{role_name}' with da color '{color}' has been bestowed upon yous!")


@bot.hybrid_command()
async def mine(ctx):
    """Mine for some time!"""
    user_id = ctx.author.id
    user_data = await db_funcs.get_user_data(user_id)
    inventory = await db_funcs.get_inventory(user_id)
    inventory_dict = {item[0]: item[1] for item in inventory}
    if user_data is None:
        await db_funcs.save_user_data(user_id, 0, 0, 0)
        user_data = (0, 0, 0)
    wallet, bank, gems = user_data
    if 'Pickaxe' not in inventory_dict or inventory_dict['Pickaxe'] <= 0:
        await ctx.send(f"{my_emojis.ERROR} how are you going to mine without a pickaxe? such silly activity, but me thinks you should buy one.")
        return
    
    await db_funcs.save_user_data(user_id, wallet, bank, gems)
    embed = discord.Embed(title=f"{my_emojis.PREFIX} You mined for some time...", color=discord.Color.from_str(EMBED_COLOR))
    first = await ctx.send(embed=embed)

    await asyncio.sleep(5)
    new_gems = random.randint(1, 5)
    gems += new_gems
    embed2 = discord.Embed(title=f"{my_emojis.PREFIX} You mined for an eternity", color=discord.Color.from_str(EMBED_COLOR))
    embed2.add_field(name="You found something", value=f"{new_gems} {GEMS} Gems")
    await db_funcs.save_user_data(user_id, wallet, bank, gems)   
    await first.edit(embed=embed2)



topics = ["The History of the Rubber Chicken", "Why Do We Call It a \"Cat Nap\"?", "The Science of Belly Button Lint",
          "Why Do Cats Eat Cars?", "Why Do Cats Sleep?", "What Does It Take to Get an Orange?", "What Does It Take to Get an Apple?",
          "How Many Licks Does It Take to Get to the Center of a Tootsie Pop?", "The Evolution of Dad Jokes", "The Great Spaghetti Tree Hoax",
          "Do Fish Get Thirsty?", "The Mystery of the Missing Left Socks", "Is There Anything About Cats That Could Be True?", "Why Do Dogs Chase Their Tails?"
          "The Physics of Jello", "How Many Bubbles Are in a Bar of Soap?", "The Secret Life of Garden Gnomes", "Why Do Pigeons Bob Their Heads?", "The Art of Sandwich Making",
          "The Truth About Santa’s Reindeer", "Why Do People Talk to Plants?", "The Enigma of the Potato Battery", "The Legend of the Snipe Hunt", "Why Are Flamingos Pink?",
          "The Cultural Impact of the Whoopee Cushion"]

@bot.hybrid_command()
async def research(ctx):
    """Research something!"""
    user_id = ctx.author.id
    user_data = await db_funcs.get_user_data(user_id)
    if user_data is None:
        await db_funcs.save_user_data(user_id, 0, 0, 0)
        user_data = (0, 0, 0)
    wallet, bank, gems = user_data
    inventory = await db_funcs.get_inventory(user_id)
    inventory_dict = {item[0]: item[1] for item in inventory}

    if 'Test Tube' not in inventory_dict or inventory_dict['Test Tube'] <= 0:
        await ctx.send(f"{my_emojis.PREFIX} yous cant do the scienciest things without the test tubes. yous should buy one.")
        return
    
    topic = random.choice(topics)

    new_gems = 500
    gems = gems + new_gems


    embed = discord.Embed(title=f"{my_emojis.PREFIX} Researching...", color=discord.Color.from_str(EMBED_COLOR))
    first = await ctx.send(embed=embed)
    await asyncio.sleep(5)
    embed2 = discord.Embed(title=f"{my_emojis.PREFIX} Research Complete!", color=discord.Color.from_str(EMBED_COLOR))
    embed2.add_field(name="You researched: ", value=topic)
    if new_gems > 0:
        embed2.add_field(name="You earned: ", value=f"{GEMS} {new_gems} Gems")

    await db_funcs.save_user_data(user_id, wallet, bank, gems)
    await first.edit(embed=embed2)
    

@bot.hybrid_command()
async def deathmatch(ctx, target: discord.Member, wager: int):
    """Play a deathmatch!"""
    user_id = ctx.author.id
    target_id = target.id
    
    if user_id == target_id:
        await ctx.send(f"{my_emojis.ERROR} You cannot battle yourself silly!")
        return
    
    user_data = await db_funcs.get_user_data(user_id)
    target_data = await db_funcs.get_user_data(target_id)
    user_wallet, user_bank, user_gems = user_data
    target_wallet, target_bank, target_gems = target_data
    
    if user_data is None or target_data is None:
        await ctx.send(f"{my_emojis.ERROR} hmmmmmmm one of yous dont has an account. u both needeth an account to battle.")
        return
    
    user_wallet = user_data[0]
    target_wallet = target_data[0]
    
    if user_wallet < wager:
        await ctx.send(f"{my_emojis.ERROR} You need to have enough balance for the wager.")
        return
    
    battle_embed = discord.Embed(title=f"{my_emojis.PREFIX} Death Battle!", description=f"{ctx.author.display_name} vs {target.display_name}", color=discord.Color.from_str(EMBED_COLOR))
    battle_embed.set_thumbnail(url="https://media4.giphy.com/media/2iihYCdY959OC4xZTP/giphy.gif?cid=6c09b952h43aketh8axhwngpbva8cessldw04aplgi4s9cwa&ep=v1_gifs_search&rid=giphy.gif&ct=g")
    first = await ctx.send(embed=battle_embed)
    
    await asyncio.sleep(2)
    
    user_hp = 100
    target_hp = 100
    while user_hp > 0 and target_hp > 0:
        user_damage = random.randint(5, 30)
        target_damage = random.randint(5, 30)
        
        target_hp -= user_damage
        user_hp -= target_damage
        
        damage_embed = discord.Embed(title=f"{my_emojis.PREFIX} Death Match", color=discord.Color.from_str(EMBED_COLOR))
        damage_embed.add_field(name=f"{ctx.author.display_name} hits {target.display_name}", value=f"Damage: {user_damage}\n{target.display_name} HP: {max(0, target_hp)}")
        damage_embed.add_field(name=f"{target.display_name} hits {ctx.author.display_name}", value=f"Damage: {target_damage}\n{ctx.author.display_name} HP: {max(0, user_hp)}")
        await first.edit(embed=damage_embed)
        
        await asyncio.sleep(2)
    
    if user_hp > 0:
        winner = ctx.author
        loser = target
    else:
        winner = target
        loser = ctx.author
    
    result_embed = discord.Embed(title=f"{my_emojis.PREFIX} Battle Result", description=f"{winner.display_name} has won the deathmatch and takes the wager of {wager * 2} {CURRENCY}!", color=discord.Color.from_str(EMBED_COLOR))
    await ctx.send(embed=result_embed)
    
    if winner == ctx.author:
        user_wallet += wager*2
    else:
        user_wallet -= wager
        target_wallet += wager*2
    
    await db_funcs.save_user_data(user_id, user_wallet, user_bank, user_gems)
    await db_funcs.save_user_data(target_id, target_wallet, target_bank, target_gems)

    
@bot.hybrid_command()
async def grab(ctx):
    """Grab an emoji from another message!"""
    if not ctx.message.reference:
        await ctx.send(f"{my_emojis.ERROR} reply to a message with an emoji for me so i can grabs it.")
        return

    replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    emoji = None

    for part in replied_message.content.split():
        if part.startswith('<') and part.endswith('>'):
            emoji = part
            break

    if not emoji:
        await ctx.send(f"{my_emojis.ERROR} oh dears... this message doesnt has an emoji.")
        return

    emoji_id = emoji.split(':')[-1].strip('>')
    is_animated = emoji.startswith('<a:')
    emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{'gif' if is_animated else 'png'}"
    emoji_name = emoji.split(':')[1]

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(emoji_url) as response:
                if response.status != 200:
                    await ctx.send(f"{my_emojis.ERROR} uh ohs... something went wrong...  wasnt able to get the emoji for yous")
                    return
                emoji_data = await response.read()

        new_emoji = await ctx.guild.create_custom_emoji(name=emoji_name, image=emoji_data)
        embed = discord.Embed(title=f"{my_emojis.PREFIX} Emoji Added", description=f"Emoji {new_emoji} added to this server!", color=discord.Color.from_str(EMBED_COLOR))
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Emoji ID: {new_emoji.id}")
        await ctx.send(embed=embed)
        logging.info(f"Emoji {new_emoji} added to this server by {ctx.author.display_name} in server: {ctx.guild.name}")
    except discord.Forbidden:
        await ctx.send(f"{my_emojis.ERROR} i cant do this. i think i dont have enough perms to add this emoji")
    except discord.HTTPException as e:
        await ctx.send(f"{my_emojis.ERROR} i couldnt gets the emoji. something went wrong....\n\n Error: {e}")


class BlackjackView(discord.ui.View):
    def __init__(self, ctx, bot, user_id, user_wallet, user_bank, user_gems, player_hand, dealer_hand, deck, wager, message):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.bot = bot
        self.user_id = user_id
        self.user_wallet = user_wallet
        self.user_bank = user_bank
        self.user_gems = user_gems
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.deck = deck
        self.wager = wager
        self.message = message

    def calculate_hand_value(self, hand):
        value = 0
        aces = 0
        for card in hand:
            card_value = card.split()[0]
            if card_value in ['J', 'Q', 'K']:
                value += 10
            elif card_value == 'A':
                aces += 1
            else:
                value += int(card_value)
        
        for _ in range(aces):
            if value + 11 <= 21:
                value += 11
            else:
                value += 1
        return value

    async def update_embed(self):
        player_value = self.calculate_hand_value(self.player_hand)
        dealer_value = self.calculate_hand_value(self.dealer_hand)

        embed = discord.Embed(title=f"{my_emojis.PREFIX} Blackjack", description="Your deal", color=discord.Color.from_str(EMBED_COLOR))
        embed.add_field(name="Your Hand:", value="\n".join(self.player_hand))
        embed.add_field(name="Dealer's Hand:", value="\n".join(self.dealer_hand[:1] + ['?']))
        embed.add_field(name="Your Balance:", value=f"{self.user_wallet} {CURRENCY}")
        embed.add_field(name="Wager:", value=f"{self.wager} {CURRENCY}")
        await self.message.edit(embed=embed, view=self)

    @discord.ui.button(label='Hit', style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.player_hand.append(self.deck.pop())
        player_value = self.calculate_hand_value(self.player_hand)
        if player_value > 21:
            await interaction.response.send_message(f"{my_emojis.PREFIX} oh no yous went over 21! You lost {self.wager} {CURRENCY}", ephemeral=True)
            self.user_wallet -= self.wager
            await db_funcs.save_user_data(self.user_id, self.user_wallet, self.user_bank, self.user_gems)
            await self.update_embed()
            self.stop()
        else:
            await self.update_embed()

    @discord.ui.button(label='Stand', style=discord.ButtonStyle.secondary)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        dealer_value = self.calculate_hand_value(self.dealer_hand)
        while dealer_value < 17:
            self.dealer_hand.append(self.deck.pop())
            dealer_value = self.calculate_hand_value(self.dealer_hand)

        await self.finalize_game(interaction)

    @discord.ui.button(label='Double Bet', style=discord.ButtonStyle.success)
    async def double_bet(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user_wallet >= self.wager * 2:
            self.wager *= 2
            self.player_hand.append(self.deck.pop())
            player_value = self.calculate_hand_value(self.player_hand)
            if player_value > 21:
                await interaction.response.send_message(f"{my_emojis.PREFIX} oh darn you went over 21! You lost {self.wager} {CURRENCY}", ephemeral=True)
                self.user_wallet -= self.wager
                await db_funcs.save_user_data(self.user_id, self.user_wallet, self.user_bank, self.user_gems)
                await self.update_embed()
                self.stop()
            else:
                await self.update_embed()
        else:
            await interaction.response.send_message(f"{my_emojis.ERROR} you cants double your bet because yous dont have enough {CURRENCY}", ephemeral=True)

    async def finalize_game(self, interaction: discord.Interaction):
        player_value = self.calculate_hand_value(self.player_hand)
        dealer_value = self.calculate_hand_value(self.dealer_hand)

        embed = discord.Embed(title=f"{my_emojis.PREFIX} Blackjack", description="Dealer's deal", color=discord.Color.from_str(EMBED_COLOR))
        embed.add_field(name="Your Hand:", value="\n".join(self.player_hand))
        embed.add_field(name="Dealer's Hand:", value="\n".join(self.dealer_hand))
        embed.add_field(name="Your Balance:", value=f"{self.user_wallet} {CURRENCY}")
        embed.add_field(name="Wager:", value=f"{self.wager} {CURRENCY}")

        if dealer_value > 21:
            embed.add_field(name="Result:", value="Dealer busts! You win!")
            self.user_wallet += self.wager * 1.5
        elif dealer_value > player_value:
            embed.add_field(name="Result:", value="Dealer wins!")
            self.user_wallet -= self.wager
        elif dealer_value < player_value:
            embed.add_field(name="Result:", value="You win!")
            self.user_wallet += self.wager * 1.5
        else:
            embed.add_field(name="Result:", value="Push!")

        embed.add_field(name="New Wallet Balance:", value=f"{self.user_wallet} {CURRENCY}")
        await db_funcs.save_user_data(self.user_id, self.user_wallet, self.user_bank, self.user_gems)
        await self.message.edit(embed=embed, view=None)
        self.stop()

@bot.hybrid_command()
async def blackjack(ctx, bet: int):
    """Play a blackjack game!"""
    user_id = str(ctx.author.id)
    user_wallet, user_bank, user_gems = await db_funcs.get_user_data(user_id)
    if user_wallet == 0:
        await ctx.send(f"{my_emojis.ERROR} you cants play because yous dont have any {CURRENCY} in your wallet")
        return
    wager = bet

    if wager > user_wallet:
        await ctx.send(f"{my_emojis.ERROR} me thinks you dont have that money in your wallet... maybe in your bankses?")
        return
    
    if wager <= 0:
        await ctx.send(f"{my_emojis.ERROR} how are you going to playses with a bet of 0?")
        return
    
    await ctx.send(f"{my_emojis.PREFIX} Shuffling the deck...")
    cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    deck = []
    for suit in ["♠", "♥", "♦", "♣"]:
        for card in cards:
            deck.append(f"{card} of {suit}")
    random.shuffle(deck)
    
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]
    
    embed = discord.Embed(title=f"{my_emojis.PREFIX} Blackjack", description="Your deal",color=discord.Color.from_str(EMBED_COLOR))
    embed.add_field(name="Your Hand:", value=player_hand[0] + "\n" + player_hand[1])
    embed.add_field(name="Dealer's Hand:", value=dealer_hand[0] + "\n" + '?')
    embed.add_field(name="Your Balance:", value=f"{user_wallet} {CURRENCY}")
    embed.add_field(name="Wager:", value=f"{wager} {CURRENCY}")
    message = await ctx.send(embed=embed)

    view = BlackjackView(ctx, bot, user_id, user_wallet, user_bank, user_gems, player_hand, dealer_hand, deck, wager, message)
    await message.edit(embed=embed, view=view)


class UpgradeButton(ui.Button):
    def __init__(self, label, item_name, item_price):
        super().__init__(label=label, style=discord.ButtonStyle.green)
        self.item_name = item_name
        self.item_price = item_price

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        conn = sqlite3.connect('bot.db')
        c = conn.cursor()
        c.execute('SELECT wallet FROM users WHERE id = ?', (user_id,))
        user_data = c.fetchone()
        if user_data is None:
            await interaction.response.send_message(f"{my_emojis.ERROR} you hasnt got an account yet", ephemeral=True)
            conn.close()
            return

        user_wallet = user_data[0]
        if user_wallet < self.item_price:
            await interaction.response.send_message(f"{my_emojis.ERROR} you hasnt gots enough money for this upgrade", ephemeral=True)
            conn.close()
            return

        c.execute('UPDATE users SET wallet = wallet - ? WHERE id = ?', (self.item_price, user_id))
        c.execute('INSERT INTO upgrades_inventory (user_id, item_name) VALUES (?, ?)', (user_id, self.item_name))
        conn.commit()
        conn.close()

        await interaction.response.send_message(f"{my_emojis.PREFIX} You have successfully purchased {self.item_name}!", ephemeral=True)

@bot.hybrid_command()
async def upgrades(ctx):
    """View the upgrades"""
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('SELECT * FROM upgrades')
    items = c.fetchall()
    conn.close()
    
    embed = discord.Embed(title=f"{SHOP_EMOJI} Upgrades", color=discord.Color.from_str(EMBED_COLOR))
    view = ui.View()

    for item in items:
        item_name, item_price, item_description, item_emoji = item
        embed.add_field(name=f"{item_emoji}. {item_name} -- {item_price} {CURRENCY}", value=f"{item_description}")
        button = UpgradeButton(label=f"Buy {item_name}", item_name=item_name, item_price=item_price)
        view.add_item(button)
    
    await ctx.send(embed=embed, view=view)


class NumberBetModal(Modal):
    def __init__(self, user_id, bet, bot):
        super().__init__(title="Number Bet")
        self.user_id = user_id
        self.bet = bet
        self.bot = bot
        self.add_item(TextInput(label="Number (1-36)", placeholder="Enter a number between 1 and 36", required=True))

    async def on_submit(self, interaction: discord.Interaction):
        number = self.children[0].value
        if not number.isdigit() or not 1 <= int(number) <= 36:
            await interaction.response.send_message("Please enter a valid number between 1 and 36.", ephemeral=True)
            return

        number = int(number)
        await handle_roulette_bet(interaction, self.user_id, self.bet, number, self.bot)

class RouletteView(View):
    def __init__(self, user_id, bet, bot):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.bet = bet
        self.bot = bot

    @discord.ui.button(label='Red', style=discord.ButtonStyle.danger)
    async def red(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_roulette_bet(interaction, self.user_id, self.bet, "red", self.bot)

    @discord.ui.button(label='Black', style=discord.ButtonStyle.primary)
    async def black(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_roulette_bet(interaction, self.user_id, self.bet, "black", self.bot)

    @discord.ui.button(label='Number', style=discord.ButtonStyle.success)
    async def number(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(NumberBetModal(self.user_id, self.bet, self.bot))

async def handle_roulette_bet(interaction: discord.Interaction, user_id, bet, choice, bot):
    user_data = await db_funcs.get_user_data(user_id)
    wallet, bank, gems = map(int, user_data)

    if wallet < bet:
        await interaction.response.send_message(f"{my_emojis.ERROR} you dont gots the money for this", ephemeral=True)
        return

    # Define the roulette wheel
    roulette_wheel = {
        "red": [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36],
        "black": [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
    }
    all_numbers = roulette_wheel["red"] + roulette_wheel["black"]

    spin = random.choice(all_numbers)
    color = "red" if spin in roulette_wheel["red"] else "black"

    if (isinstance(choice, int) and spin == choice) or (isinstance(choice, str) and choice.lower() == color):
        if isinstance(choice, int):
            winnings = bet * 36
            result = f"{my_emojis.PREFIX} wowowowow the ball landed on exactly {spin} ({color}) and you won {winnings}! THATS 36x YOUR BET!"
        else:
            winnings = bet * 2
            result = f"{my_emojis.PREFIX} wowowowo the ball landed on {spin} ({color}) and you won {winnings}! That's 2x your bet!"
        wallet += winnings
    else:
        wallet -= bet
        result = f"{my_emojis.PREFIX} awwww the ball landed on {spin} ({color}). maybe next time :>"

    await db_funcs.save_user_data(user_id, wallet, bank, gems)
    await interaction.response.send_message(result, ephemeral=True)

@bot.hybrid_command()
async def roulette(ctx, bet: int):
    """Play Roulette with the bot!"""
    user_id = str(ctx.author.id)
    user_data = await db_funcs.get_user_data(user_id)
    wallet, bank, gems = map(int, user_data)

    if wallet < bet:
        await ctx.send(f"{my_emojis.ERROR} you dont gots the money for this")
        return

    embed = discord.Embed(title=f"{my_emojis.PREFIX} Roulette", color=discord.Color.from_str(EMBED_COLOR))
    embed.add_field(name="How to Play:", value="Choose to bet on either a specific number, or the color red or black. "
                                               "If the ball lands on your choice, you win! Good luck!")
    embed.add_field(name="Bet:", value=f"{bet} {CURRENCY}")
    embed.add_field(name="Wallet:", value=f"{wallet} {CURRENCY}")

    view = RouletteView(user_id, bet, bot)

    await ctx.send(embed=embed, view=view)


# UTILITIES
@bot.hybrid_command()
async def ping(ctx):
    """Pong!"""
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")

@bot.hybrid_command()
async def info(ctx):
    """Shows info about the bot"""
    embed = discord.Embed(title="Bot Info", description="Some info about this bot", color=discord.Color.from_str(EMBED_COLOR))
    embed.add_field(name="Creator: ", value="j_coldtapwater")
    embed.add_field(name="Version: ", value="1.3.3")
    embed.add_field(name="Language: ", value="Python")
    embed.add_field(name="Servers: ", value=f"{len(bot.guilds)}")
    embed.add_field(name="Users: ", value=f"{len(bot.users)}")
    embed.add_field(name="Prefix: ", value=f"{bot.command_prefix}")
    embed.set_thumbnail(url=bot.user.display_avatar.url)

    await ctx.send(embed=embed)

@bot.hybrid_command()
async def avatar(ctx, member: discord.Member = None):
    """Shows the avatar of a user"""
    if member is None:
        member = ctx.author
    embed = discord.Embed(title=f"{member}'s Avatar", color=discord.Color.from_str(EMBED_COLOR))
    embed.set_image(url=member.display_avatar.url)

    await ctx.send(embed=embed)

@bot.hybrid_command()
async def contact(ctx, message: str):
    """Send a message to the developer"""
    if message:
        embed = discord.Embed(title="Issue Submitted", description=f"{ctx.author.mention}", color=discord.Color.from_str(EMBED_COLOR))
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(name=f"Message: -- from GUILD {ctx.guild}", value=f"{message}")
        await ctx.bot.get_user(1151230208783945818).send(embed=embed)
        await ctx.send("Thank you for your message. The developer will resolve this issue shortly.")
    else:
        await ctx.send("Please provide an issue message.")


@bot.hybrid_command()
async def addbot(ctx):
    """Add the bot to your server"""
    embed = discord.Embed(title=f"{my_emojis.PREFIX} Add Bot", description="Add the bot to your server", color=discord.Color.from_str(EMBED_COLOR))
    embed.add_field(name="Invite Link", value="https://discord.com/oauth2/authorize?client_id=1226933981786804314", inline=False)
    embed.add_field(name="Support Server", value="https://discord.gg/vypVzwNn8F", inline=False)
    embed.add_field(name="Top.gg Page", value="https://top.gg/bot/1226933981786804314?s=0dfd0a000b29c", inline=False)

    # buttons
    view = discord.ui.View()
    button = discord.ui.Button(label="Invite Link", url="https://discord.com/oauth2/authorize?client_id=1226933981786804314")
    button2 = discord.ui.Button(label="Support Server", url="https://discord.gg/vypVzwNn8F")
    button3 = discord.ui.Button(label="Top.gg Page", url="https://top.gg/bot/1226933981786804314?s=0dfd0a000b29c")
    view.add_item(button)
    view.add_item(button2)
    view.add_item(button3)
    
    await ctx.send(embed=embed, view=view) 



# SOME MORE OWNER COMMANDS
@bot.hybrid_command()
@commands.is_owner()
async def sync(ctx):
    try:
        await bot.tree.sync()
        await ctx.send("Commands synced!")
    except Exception as e:
        await ctx.send(f"Error syncing commands: {e}")

@bot.command(aliases=["servers"])
@commands.is_owner()
async def serverlist(ctx):
    servers = bot.guilds
    embed = discord.Embed(title="Servers Bot is in:", color=discord.Color.from_str(EMBED_COLOR))

    for server in servers:
        embed.add_field(name=server.name, value=server.id)

    await ctx.send(embed=embed)


@bot.command(aliases=["users"])
@commands.is_owner()
async def totalusers(ctx):
    embed = discord.Embed(title="Total Users", description=f"{len(bot.users)}", color=discord.Color.from_str(EMBED_COLOR))
    await ctx.send(embed=embed)

@bot.command(aliases=["econ"])
@commands.is_owner()
async def economy(ctx):
    # get total number of buckaroos in system
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute("SELECT SUM(wallet) + SUM(bank) FROM users")
    buckaroos = c.fetchone()[0]
    embed = discord.Embed(title="Economy", description=f"Total buckaroos in circulation: {await humanize_currency(buckaroos)}", color=discord.Color.from_str(EMBED_COLOR))
    await ctx.send(embed=embed)



bot.run(os.getenv("DISCORD_TOKEN"))

