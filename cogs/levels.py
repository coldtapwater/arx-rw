import discord
from discord.ext import commands
import utils.levels_db as levels_db
import utils.economy_db as economy_db
import utils.general_db as gdb
import utils.configs as uc
import utils.emojis as my_emojis
import time
from utils.models.models import UserLevel

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        is_booster = message.author.premium_since is not None
        xp_gain = await levels_db.calculate_xp_gain(message.content, is_booster)
        xp, level, leveled_up = await levels_db.update_user_xp(message.author.id, message.guild.id, xp_gain)

        if leveled_up:
            bonus = await levels_db.get_level_up_bonus(level)
            await economy_db.update_balance(message.author.id, wallet=bonus)
            await message.channel.send(f"🎉 Congratulations {message.author.mention}! You've reached level {level} and earned a bonus of {bonus} {uc.CURRENCY}!")

    @commands.command(name="profile")
    async def profile(self, ctx, user: discord.Member = None):
        """Shows the user's profile."""
        user = user or ctx.author
        user_level = await levels_db.get_user_level(user.id, ctx.guild.id)
        wallet, bank, gems = await economy_db.get_user_balance(user.id)
        
        next_level_xp = levels_db.calculate_xp_for_next_level(user_level.level)
        progress = f"{user_level.xp}/{next_level_xp}"
        prestige_badges = "🌟" * user_level.prestige

        profile_text = f"""
        ***{user.name}***'s profile {prestige_badges}
        Level: **{user_level.level}**
        XP: **{progress}**
        ---{my_emojis.BANK_EMOJI}---
        Wallet: {my_emojis.CURRENCY_EMOJI}{wallet} {uc.CURRENCY}
        Bank: {my_emojis.CURRENCY_EMOJI}{bank} {uc.CURRENCY}
        Gems: {my_emojis.GEMS}{gems}
        """
        await ctx.send(profile_text)

    @commands.command(name="top")
    async def leaderboard(self, ctx):
        """Shows the XP leaderboard."""
        leaderboard = await levels_db.get_leaderboard(ctx.guild.id)
        supporters = set(supporter.user_id for supporter in await gdb.get_supporters())
        leaderboard_text = f"XP Leaderboard for {ctx.guild.name}:\n\n"
        for i, (user_id, xp, level) in enumerate(leaderboard, 1):
            user = ctx.guild.get_member(user_id)
            supporters_emoji = my_emojis.SUPPORTER if user_id in supporters else ""
            user_text = user.name if user else f"Unknown User ({user_id})"
            leaderboard_text += f"{i}. ***{user_text}***{supporters_emoji}:\n Level: {level}\n XP: {xp}\n\n"
        
        await ctx.send(leaderboard_text)

    @commands.command(name="debug_levels", hidden=True)
    @commands.is_owner()
    async def debug_levels(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        all_entries = await UserLevel.filter(user_id=user.id)
        debug_text = f"Debug info for user {user.name} (ID: {user.id}):\n\n"
        for entry in all_entries:
            debug_text += f"Guild ID: {entry.guild_id}, XP: {entry.xp}, Level: {entry.level}\n"
        await ctx.send(debug_text)


    @commands.command(name="prestige")
    async def prestige(self, ctx):
        success = await levels_db.add_prestige(ctx.author.id, ctx.guild.id)
        if success:
            await ctx.send(f"🎊 Congratulations {ctx.author.mention}! You've prestiged and received 25,000 {uc.CURRENCY}!")
        else:
            await ctx.send("You need to be at least level 100 to prestige.")


async def setup(bot):
    await bot.add_cog(Leveling(bot))