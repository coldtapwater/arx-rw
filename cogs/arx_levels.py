import discord
from discord.ext import commands
import aiosqlite
import utils.my_emojis as my_emojis


class ArxLevels(commands.Cog):
    def __init__(self, bot, embed_color):
        self.bot = bot
        self.embed_color = embed_color
        self.PROGRESS_BAR_FILLED = '▰'
        self.PROGRESS_BAR_EMPTY = '▱'

    async def calculate_progress_bar(self, progress: float, length: int = 20) -> str:
        """Calculate the progress bar."""
        progress_percentage = progress / length
        segments = int(progress_percentage * 20)
        
        progress_bar = [] # start with the opening bracket
        for i in range(20):
            if i < segments:
                progress_bar.append(self.PROGRESS_BAR_FILLED)
            else:
                progress_bar.append(self.PROGRESS_BAR_EMPTY)
        
        
        return ''.join(progress_bar)

    async def xp_needed_for_next_level(self, level):
        """Calculate the XP required to reach the next level."""
        if level == 1:
            return 100
        else:
            return int(100 * (1.5 ** (level - 1)))

    async def create_tables(self):
        async with aiosqlite.connect('bot.db') as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_xp (
                    user_id INTEGER,
                    guild_id INTEGER,
                    xp INTEGER,
                    level INTEGER,
                    PRIMARY KEY (user_id, guild_id)
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS guild_config (
                    guild_id INTEGER PRIMARY KEY,
                    enabled TEXT
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS level_roles (
                    guild_id INTEGER,
                    role_id INTEGER,
                    level INTEGER,
                    PRIMARY KEY (guild_id, role_id)
                )
            ''')
            await db.commit()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.create_tables()
        print(f'{self.__class__.__name__} cog has been loaded')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        guild_id = str(message.guild)
        user_id = str(message.author.id)
        
        async with aiosqlite.connect('bot.db') as db:
            cursor = await db.execute('SELECT enabled FROM guild_config WHERE guild_id = ?', (guild_id,))
            row = await cursor.fetchone()
            if not row or row[0] != 'true':
                return
            
            cursor = await db.execute('SELECT xp, level FROM user_xp WHERE user_id = ? AND guild_id = ?', (user_id, guild_id))
            row = await cursor.fetchone()
            if row:
                xp, level = row
                xp += 1
                next_level_xp = await self.xp_needed_for_next_level(level)
                new_level = level
                while xp >= next_level_xp:
                    new_level += 1
                    xp -= next_level_xp
                    next_level_xp = await self.xp_needed_for_next_level(new_level)
                if new_level > level:
                    await message.channel.send(f"Congratulations {message.author.mention}, you leveled up to {new_level}!")
                    await self.assign_roles(message.author, new_level)
                await db.execute('UPDATE user_xp SET xp = ?, level = ? WHERE user_id = ? AND guild_id = ?', (xp, new_level, user_id, guild_id))
            else:
                xp, level = 1, 1
                await db.execute('INSERT INTO user_xp (user_id, guild_id, xp, level) VALUES (?, ?, ?, ?)', (user_id, guild_id, xp, level))
            await db.commit()
        # await self.bot.process_commands(message)

    async def assign_roles(self, member, level):
        guild_id = str(member.guild.id)
        async with aiosqlite.connect('bot.db') as db:
            cursor = await db.execute('SELECT role_id FROM level_roles WHERE guild_id = ? AND level <= ?', (guild_id, level))
            roles = await cursor.fetchall()
            for role_id, in roles:
                role = member.guild.get_role(int(role_id))
                if role:
                    await member.add_roles(role)
    
    @commands.command()
    async def pf(self, ctx, member: discord.Member = None):
        """Displays the user's profile with leveling progress."""
        if member is None:
            member = ctx.author
        user_id = str(member.id)
        guild_id = str(ctx.guild.id)

        async with aiosqlite.connect('bot.db') as db:
            cursor = await db.execute('SELECT xp, level FROM user_xp WHERE user_id = ? AND guild_id = ?', (user_id, guild_id))
            row = await cursor.fetchone()

        if row:
            current_xp, level = row
        else:
            current_xp, level = 0, 1

        next_level_xp = await self.xp_needed_for_next_level(level)
        progress_bar = await self.calculate_progress_bar(current_xp, next_level_xp)

        embed = discord.Embed(title=f"{my_emojis.PREFIX} {member.display_name}'s Profile", color=discord.Color.from_str(self.embed_color))
        embed.add_field(name="Level:", value=str(level), inline=False)
        embed.add_field(name="Progress:", value=f"{progress_bar} {current_xp}/{next_level_xp} XP", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)

        await ctx.send(embed=embed)

    @commands.command()
    async def top(self, ctx):
        """Shows the leaderboard for the most active users."""
        guild_id = str(ctx.guild.id)
        async with aiosqlite.connect('bot.db') as db:
            cursor = await db.execute(
                'SELECT user_id, xp, level FROM user_xp WHERE guild_id = ? ORDER BY level DESC, xp DESC LIMIT 10',
                (guild_id,)
            )
            rows = await cursor.fetchall()
            embed = discord.Embed(title=f"{my_emojis.PREFIX} Leaderboard", color=discord.Color.gold())
            for i, (user_id, xp, level) in enumerate(rows, start=1):
                user = self.bot.get_user(int(user_id))
                if user:
                    if i == 1:
                        embed.add_field(name=f"{my_emojis.CROWN_EMOJI} {user}", value=f"Level: {level} | XP: {xp}", inline=False)
                    else:
                        embed.add_field(name=f"{i}. {user}", value=f"Level: {level} | XP: {xp}", inline=False)
            await ctx.send(embed=embed)

    @commands.group()
    async def levels(self, ctx):
        """Group command for leveling settings."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand passed. Use `/levels help` to see the available subcommands.")

    @levels.command()
    async def help(self, ctx):
        """Displays the help embed for the leveling system."""
        embed = discord.Embed(title=f"{my_emojis.PREFIX} Levels Help", color=discord.Color.from_str(self.embed_color))
        embed.add_field(name="/levels enable", value="Enables the leveling system.")
        embed.add_field(name="/levels disable", value="Disables the leveling system.")
        embed.add_field(name="/levels settings", value="Shows the configuration settings for the leveling system.")
        embed.add_field(name="/levels addrole <role> <level>", value="Adds a role to be assigned at a specific level.")
        embed.add_field(name="/levels remrole <role>", value="Removes a role from the leveling system.")
        embed.add_field(name="/levels reset", value="Resets all users' XP.")
        await ctx.send(embed=embed)

    @levels.command()
    @commands.has_permissions(administrator=True)
    async def enable(self, ctx):
        """Enables the leveling system."""
        guild_id = str(ctx.guild.id)
        async with aiosqlite.connect('bot.db') as db:
            await db.execute('INSERT OR REPLACE INTO guild_config (guild_id, enabled) VALUES (?, ?)', (guild_id, 'true'))
            await db.commit()
        await ctx.send(f"{my_emojis.PREFIX} Leveling system enabled.")

    @levels.command()
    @commands.has_permissions(administrator=True)
    async def disable(self, ctx):
        """Disables the leveling system."""
        guild_id = str(ctx.guild.id)
        async with aiosqlite.connect('bot.db') as db:
            await db.execute('INSERT OR REPLACE INTO guild_config (guild_id, enabled) VALUES (?, ?)', (guild_id, 'false'))
            await db.commit()
        await ctx.send("Leveling system disabled.")

    @levels.command()
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        """Shows the configuration settings for the leveling system."""
        guild_id = str(ctx.guild.id)
        async with aiosqlite.connect('bot.db') as db:
            cursor = await db.execute('SELECT enabled FROM guild_config WHERE guild_id = ?', (guild_id,))
            row = await cursor.fetchone()
            enabled = row[0] if row else 'false'
            cursor = await db.execute('SELECT role_id, level FROM level_roles WHERE guild_id = ?', (guild_id,))
            roles = await cursor.fetchall()
        
        embed = discord.Embed(title=f"{my_emojis.PREFIX} Leveling System Settings", color=discord.Color.from_str(self.embed_color))
        embed.add_field(name="Enabled", value=enabled)
        for role_id, level in roles:
            role = ctx.guild.get_role(int(role_id))
            if role:
                embed.add_field(name=f"Level: {level}", value=f"<:discord_reply:1255744704168071189> Reward: {role.mention}", inline=False)
        
        await ctx.send(embed=embed)

    @levels.command()
    @commands.has_permissions(administrator=True)
    async def addrole(self, ctx, role: discord.Role, level: int):
        """Adds a role to the leveling system."""
        guild_id = str(ctx.guild.id)
        async with aiosqlite.connect('bot.db') as db:
            await db.execute('INSERT OR REPLACE INTO level_roles (guild_id, role_id, level) VALUES (?, ?, ?)', (guild_id, str(role.id), level))
            await db.commit()
        await ctx.send(f"{my_emojis.PREFIX} Role {role.name} will now be assigned at level {level}.")

    @levels.command()
    @commands.has_permissions(administrator=True)
    async def remrole(self, ctx, role: discord.Role):
        """Removes a role from the leveling system."""
        guild_id = str(ctx.guild.id)
        async with aiosqlite.connect('bot.db') as db:
            await db.execute('DELETE FROM level_roles WHERE guild_id = ? AND role_id = ?', (guild_id, str(role.id)))
            await db.commit()
        await ctx.send(f"{my_emojis.PREFIX} Role {role.name} has been removed from the leveling system.")

    @levels.command()
    @commands.has_permissions(administrator=True)
    async def reset(self, ctx):
        """Resets all users' XP."""
        guild_id = str(ctx.guild.id)
        async with aiosqlite.connect('bot.db') as db:
            await db.execute('DELETE FROM user_xp WHERE guild_id = ?', (guild_id,))
            await db.commit()
        await ctx.send(f"{my_emojis.PREFIX} All users' XP has been reset.")

    @commands.command()
    async def rewards(self, ctx):
        """Displays the available roles and their required levels."""
        guild_id = str(ctx.guild.id)
        async with aiosqlite.connect('bot.db') as db:
            cursor = await db.execute('SELECT role_id, level FROM level_roles WHERE guild_id = ? ORDER BY level', (guild_id,))
            roles = await cursor.fetchall()
        
        embed = discord.Embed(title=f"{my_emojis.PREFIX} Available Roles", color=discord.Color.from_str(self.embed_color))
        for role_id, level in roles:
            role = ctx.guild.get_role(int(role_id))
            if role:
                required_xp = await self.xp_needed_for_next_level(level)
                embed.add_field(name=f"Level: {level}", value=f"<:discord_reply:1255744704168071189> Reward: {role.mention}\nRequired XP: {required_xp}", inline=False)
        
        await ctx.send(embed=embed)