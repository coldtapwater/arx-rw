import discord
from discord.ext import commands
from datetime import timedelta
from utils.mod_db import ModDB

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = ModDB()

    def cog_unload(self):
        self.db.close()

    async def log_action(self, guild, action, user, mod, reason, duration=None):
        channel_id = self.db.get_modlog_channel(guild.id)
        if not channel_id:
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        embed = discord.Embed(title=f"{action.capitalize()} Action", color=discord.Color.red())
        embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=False)
        embed.add_field(name="Moderator", value=f"{mod.mention} ({mod.id})", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)

        if duration:
            expiry_time = discord.utils.utcnow() + duration
            embed.add_field(name="Duration", value=f"{duration}\nExpires: {discord.utils.format_dt(expiry_time, 'R')}", inline=False)

        await channel.send(embed=embed)
        self.db.add_action(guild.id, action, user.id, mod.id, reason, duration)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        await member.kick(reason=reason)
        await ctx.send(f"{member.mention} has been kicked.")
        await self.log_action(ctx.guild, "kick", member, ctx.author, reason)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        await member.ban(reason=reason)
        await ctx.send(f"{member.mention} has been banned.")
        await self.log_action(ctx.guild, "ban", member, ctx.author, reason)

        ban_message = self.db.get_ban_message(ctx.guild.id)
        try:
            await member.send(f"{ban_message}\nReason: {reason}\n\nYou can appeal this ban by using the `r appeal` command in this DM.")
        except discord.HTTPException:
            pass  # Member had DMs closed or left the server before we could send the message

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, duration: str, *, reason="No reason provided"):
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        time_value = int(duration[:-1])
        time_unit = duration[-1].lower()
        
        if time_unit not in time_units:
            await ctx.send("Invalid time unit. Use s for seconds, m for minutes, h for hours, or d for days.")
            return

        mute_duration = timedelta(seconds=time_value * time_units[time_unit])
        await member.timeout(mute_duration, reason=reason)
        await ctx.send(f"{member.mention} has been muted for {duration}.")
        await self.log_action(ctx.guild, "mute", member, ctx.author, reason, mute_duration)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason="No reason provided"):
        self.db.add_warning(ctx.guild.id, member.id, reason)
        await ctx.send(f"{member.mention} has been warned. Reason: {reason}")
        await self.log_action(ctx.guild, "warn", member, ctx.author, reason)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int = 5, member: discord.Member = None):
        if member:
            def check(m):
                return m.author == member

            deleted = await ctx.channel.purge(limit=amount, check=check)
        else:
            deleted = await ctx.channel.purge(limit=amount)

        await ctx.send(f"Deleted {len(deleted)} messages.", delete_after=5)
        await self.log_action(ctx.guild, "purge", member or ctx.guild, ctx.author, f"Purged {len(deleted)} messages")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set_modlog(self, ctx, channel: discord.TextChannel):
        self.db.set_modlog_channel(ctx.guild.id, channel.id)
        await ctx.send(f"Modlog channel set to {channel.mention}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set_ban_message(self, ctx, *, message):
        self.db.set_ban_message(ctx.guild.id, message)
        await ctx.send("Custom ban message set successfully.")

    @commands.command()
    async def appeal(self, ctx, *, reason):
        if not isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("This command can only be used in DMs.")
            return

        for guild in self.bot.guilds:
            if ctx.author in guild.bans():
                channel_id = self.db.get_modlog_channel(guild.id)
                if channel_id:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        embed = discord.Embed(title="Ban Appeal", color=discord.Color.blue())
                        embed.add_field(name="User", value=f"{ctx.author.mention} ({ctx.author.id})", inline=False)
                        embed.add_field(name="Reason for Appeal", value=reason, inline=False)
                        await channel.send(embed=embed)
                        await ctx.author.send("Your appeal has been sent to the server moderators.")
                        return

        await ctx.author.send("You are not currently banned from any server where I can send appeals.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def modlog(self, ctx, user: discord.User):
        warnings = self.db.get_warnings(ctx.guild.id, user.id)
        actions = self.db.get_actions(ctx.guild.id, user.id)

        if not warnings and not actions:
            await ctx.send(f"No moderation history found for {user.mention}")
            return

        embed = discord.Embed(title=f"Moderation History for {user}", color=discord.Color.orange())
        
        for i, (reason, timestamp) in enumerate(warnings, 1):
            embed.add_field(name=f"Warning {i}", value=f"Reason: {reason}\nDate: {timestamp}", inline=False)

        for action_type, user_id, mod_id, reason, timestamp, duration in actions:
            value = f"Reason: {reason}\nDate: {timestamp}\nModerator: <@{mod_id}>"
            if duration:
                value += f"\nDuration: {duration}"
            embed.add_field(name=f"{action_type.capitalize()}", value=value, inline=False)

        await ctx.send(embed=embed)