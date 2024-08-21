import discord

from discord.ext import commands, tasks
import asyncio
import json
import logging

class updateUtils(commands.Cog):
    def __init__(self, bot, embed_color):
        self.bot = bot
        self.embed_color = embed_color
        self.update_file = 'update.json'
        self.current_update = None
        self.seen_users = set()
        self.load_update()
        self.alert_tasks = {}

    def load_update(self):
        try:
            with open(self.update_file, 'r') as f:
                data = json.load(f)
                self.current_update = data.get("update_text", None)
                self.seen_users = set(data.get("seen_users", []))
        except (FileNotFoundError, json.JSONDecodeError):
            self.current_update = None
            self.seen_users = set()

    def save_update(self, update_text):
        with open(self.update_file, 'w') as f:
            json.dump({"update_text": update_text, "seen_users": []}, f, indent=4)
        self.current_update = update_text
        self.seen_users.clear()

    def save_seen_users(self):
        with open(self.update_file, 'w') as f:
            json.dump({"update_text": self.current_update, "seen_users": list(self.seen_users)}, f, indent=4)

    @commands.hybrid_command()
    @commands.is_owner()
    async def setupdate(self, ctx, *, update_text: str):
        """Set the update text."""
        self.save_update(update_text)
        await ctx.send("Update text has been set successfully.")

    @commands.hybrid_command()
    async def alert(self, ctx):
        """Show the latest update."""
        if self.current_update:
            embed = discord.Embed(title="Latest Update", description=self.current_update, color=discord.Color.blue())
            await ctx.send(embed=embed, ephemeral=True)
            self.seen_users.add(ctx.author.id)
            self.save_seen_users()
        else:
            await ctx.send("No updates available at the moment.", ephemeral=True)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        if self.current_update and ctx.command.name != "alert" and ctx.author.id not in self.seen_users:
            if ctx.author.id not in self.alert_tasks:
                self.alert_tasks[ctx.author.id] = self.bot.loop.create_task(self.send_alert(ctx))

    async def send_alert(self, ctx):
        await ctx.send("Hey, there's a new update! Run `/alert` to see the latest update.")
        await self.clear_alert_task(ctx.author.id)

    async def clear_alert_task(self, user_id):
        await asyncio.sleep(1)  # Slight delay to ensure the alert is sent after the command's response
        if user_id in self.alert_tasks:
            del self.alert_tasks[user_id]

class onServerJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Sends a message to newly joined guilds asking users to run the /helpme command."""
        embed = discord.Embed(title="Hello!", description="Thanks for inviting me to your server! To get started, please run the </helpme:1255312627366629438> command to learn more about my features and how to use me. If you have any questions or need any help, feel free to contact me using `/contact`. Have fun!", color=discord.Color.blue())
        await guild.system_channel.send(embed=embed)
        logging.info(f"New guild joined: {guild.name} ({guild.id})")
        await self.bot.change_presence(activity=discord.Game(name=f"with your mom in {len(self.bot.guilds)} servers"))

