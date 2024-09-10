import discord
from discord.ext import commands
from utils.models.models import BlacklistedUser, AuditedUser, User, Supporters
import utils.configs as uc
import utils.checks
import utils.error_handler as eh
import utils.emojis as my_emojis
import utils.economy_db as db
import utils.configs as uc
import random
import os
import logging
import asyncio
import utils.general_db as gdb


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emoji = my_emojis
        self.logger = logging.getLogger('bot')

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info('Economy cog loaded')
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You don't have permission to use this command.")
        else:
            await eh.ErrorHandler.handle_command_error(ctx, error)

    @commands.Cog.listener()
    async def on_audited_command_use(self, ctx):
        await ctx.send("Your account has been audited for suspicious activities regarding bot usage. Head over to the Support Server for help.")
        self.logger.warning(f"[{ctx.author.id}] - [AUDITED] - [{ctx.guild.id if ctx.guild else 'DM'}] - {ctx.command.name} command used")

        # Send alert to a specific channel
        alert_channel = self.get_channel(1227354334279372841)  # Replace with your actual channel ID
        if alert_channel:
            await alert_channel.send(f"Audited user {ctx.author} (ID: {ctx.author.id}) used command: {ctx.command.name}")

    @commands.Cog.listener()
    async def on_blacklisted_user(self, ctx):
        await ctx.send("You are blacklisted and cannot use this bot.")
        self.logger.warning(f"[{ctx.author.id}] - [BLACKLISTED] - [{ctx.guild.id if ctx.guild else 'DM'}] - {ctx.command.name} command used")

        # Send alert to a specific channel
        alert_channel = self.get_channel(1227354334279372841)  # Replace with your actual channel ID
        if alert_channel:
            await alert_channel.send(f"Blacklisted user {ctx.author} (ID: {ctx.author.id}) used command: {ctx.command.name}")

    @commands.command(aliases=['bal'])
    @utils.checks.blacklist_check()
    async def balance(self, ctx, user: discord.User = None):
        if not user:
            user = ctx.author
        balance = await db.get_user_balance(str(user.id))
        await ctx.send(f"{my_emojis.BANK_EMOJI} - {user} | has **{balance[0]+balance[1]}** {my_emojis.CURRENCY_EMOJI} {uc.CURRENCY} and **{balance[2]}** {my_emojis.GEMS} gems.\n")

    @commands.command()
    @commands.cooldown(1, 60*60*8, type=commands.BucketType.user) # 8 hours
    async def work(self, ctx):
        message1 = await ctx.send("working...")
        await asyncio.sleep(3)
        salary = random.randint(500, 1000)
        await db.update_balance(ctx.author.id, wallet=salary)
        await message1.edit(content=f"earned.. | salary: {my_emojis.CURRENCY_EMOJI} {salary} {uc.CURRENCY}")
    
    @commands.command()
    @utils.checks.blacklist_check()
    async def daily(self, ctx):
        daily_bonus = random.randint(100, 500)
        await db.update_balance(ctx.author.id, wallet=daily_bonus)
        await ctx.send(f"Earned.. | Daily: {my_emojis.CURRENCY_EMOJI} {daily_bonus} {uc.CURRENCY}\n-# do `r bal` to see your total balance")
    
    @commands.command()
    @utils.checks.blacklist_check()
    async def leaderboard(self, ctx):
        """Display the wealth leaderboard"""
        leaderboard = await db.get_leaderboard(10)
        supporters = set(supporter.user_id for supporter in await gdb.get_supporters())
        
        message = "**Leaderboard**\n\n"
        for i, (user_id, wealth) in enumerate(leaderboard, 1):
            user = self.bot.get_user(user_id)
            name = user.name if user else f"User {user_id}"
            
            supporter_emoji = my_emojis.SUPPORTER if user_id in supporters else ""
            
            message += f"{i}. **{name}** - Net Worth: {wealth:,} {my_emojis.CURRENCY_EMOJI} {supporter_emoji}\n"
        
        await ctx.send(message)
    
    @commands.command(hidden=True)
    @commands.is_owner()
    @utils.checks.blacklist_check()
    async def addmoney(self, ctx, user: discord.User, amount: int):
        await ctx.send(f"current balance: {await db.get_user_balance(user.id)}")
        await db.update_balance(user.id, wallet=amount)
        await ctx.send(f"added {my_emojis.CURRENCY_EMOJI} {amount} {uc.CURRENCY} to {user}")

    @commands.command(hidden=True)
    @commands.is_owner()
    @utils.checks.blacklist_check()
    async def removemoney(self, ctx, user: discord.User, amount: int):
        await ctx.send(f"current balance: {await db.get_user_balance(user.id)}")
        await db.update_balance(user.id, wallet=-amount)
        await ctx.send(f"removed {my_emojis.CURRENCY_EMOJI} {amount} {uc.CURRENCY} from {user}")

    @commands.command(hidden=True)
    @commands.is_owner()
    @utils.checks.blacklist_check()
    async def addgems(self, ctx, user: discord.User, amount: int):
        await ctx.send(f"current balance: {await db.get_user_balance(user.id)}")
        await db.update_balance(user.id, gems=amount)
        await ctx.send(f"added {my_emojis.GEMS} {amount} {uc.GEMS} to {user}")

    @commands.command(hidden=True)
    @commands.is_owner()
    @utils.checks.blacklist_check()
    async def removegems(self, ctx, user: discord.User, amount: int):
        await ctx.send(f"current balance: {await db.get_user_balance(user.id)}")
        await db.update_balance(user.id, gems=-amount)
        await ctx.send(f"removed {my_emojis.GEMS} {amount} {uc.GEMS} from {user}")

    @commands.command(aliases=['econ'], hidden=True)
    @commands.is_owner()
    @utils.checks.blacklist_check()
    async def economy(self, ctx):
        await ctx.send(f"total {uc.CURRENCY} in circulation: **{await db.get_total_buckaroos()}** {my_emojis.CURRENCY_EMOJI}")


    

async def setup(bot):
    await bot.add_cog(Economy(bot))