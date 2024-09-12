import discord
from discord.ext import commands, tasks
import asyncio
import random
from datetime import datetime, timedelta
import json
from utils import economy_db

class PlagueGame(commands.Cog):
    """A plague-themed game for your server!"""

    def __init__(self, bot):
        self.bot = bot
        self.config = {}  # We'll use a dictionary instead of Config
        self.load_config()
        self.random_events.start()

    def load_config(self):
        # In a real implementation, you'd load this from a file or database
        self.config = {
            "plague_name": "The Plague",
            "infection_rate": 75,
            "cure_rate": 60,
            "event_frequency": 3600,  # in seconds
            "last_event": None,
            "users": {}
        }

    def save_config(self):

        with open('config.json', 'w') as f:
            json.dump(self.config, f, indent=4)
        pass

    def cog_unload(self):
        self.random_events.cancel()

    @tasks.loop(seconds=60)  # Check every minute
    async def random_events(self):
        if self.config["last_event"] is None or \
           (datetime.now() - self.config["last_event"]) > timedelta(seconds=self.config["event_frequency"]):
            event = random.choice(["Outbreak", "Medical Breakthrough", "Mutation"])
            await self.trigger_event(event)

    async def trigger_event(self, event: str):
        self.config["last_event"] = datetime.now()
        
        if event == "Outbreak":
            self.config["infection_rate"] = 90
            await self.plague_announcement("An outbreak has occurred! Infection rates have increased for the next hour!")
        elif event == "Medical Breakthrough":
            self.config["cure_rate"] = 80
            await self.plague_announcement("A medical breakthrough has been achieved! Cure rates have increased for the next hour!")
        elif event == "Mutation":
            await self.plague_announcement("The plague has mutated! Plaguebearers' infection abilities have been boosted for the next hour!")

        # Reset event after an hour
        await asyncio.sleep(3600)
        self.config["infection_rate"] = 75
        self.config["cure_rate"] = 60

    async def plague_announcement(self, message: str):
        for guild in self.bot.guilds:
            if guild.system_channel:
                await guild.system_channel.send(f"**Plague Announcement:** {message}")

    @commands.group(invoke_without_command=True)
    async def plague(self, ctx):
        """Plague game commands"""
        await ctx.send_help(ctx.command)

    @plague.command()
    async def infect(self, ctx, target: discord.Member):
        """Attempt to infect another user"""
        user_data = self.config["users"].get(str(ctx.author.id), {"role": "User", "state": "Healthy", "plague_points": 0, "cure_points": 0})
        target_data = self.config["users"].get(str(target.id), {"role": "User", "state": "Healthy", "plague_points": 0, "cure_points": 0})

        if user_data["state"] != "Infected" and user_data["role"] != "Plaguebearer":
            return await ctx.send("You must be infected or a Plaguebearer to infect others.")

        if target_data["state"] == "Infected":
            return await ctx.send(f"{target.display_name} is already infected.")

        if target_data["role"] == "Doctor":
            return await ctx.send(f"{target.display_name} is a doctor and cannot be infected.")

        if random.randint(1, 100) <= self.config["infection_rate"]:
            target_data["state"] = "Infected"
            user_data["plague_points"] += 1
            self.config["users"][str(target.id)] = target_data
            self.config["users"][str(ctx.author.id)] = user_data
            await self.notify_user(ctx, target, f"You have been infected by {ctx.author.display_name}!")
            await ctx.send(f"You have successfully infected {target.display_name}!")
        else:
            await ctx.send(f"Your attempt to infect {target.display_name} failed.")

        self.save_config()

    @plague.command()
    async def cure(self, ctx, target: discord.Member):
        """Attempt to cure another user"""
        user_data = self.config["users"].get(str(ctx.author.id), {"role": "User", "state": "Healthy", "plague_points": 0, "cure_points": 0})
        target_data = self.config["users"].get(str(target.id), {"role": "User", "state": "Healthy", "plague_points": 0, "cure_points": 0})

        if user_data["role"] != "Doctor":
            return await ctx.send("Only doctors can cure others.")

        if target_data["state"] != "Infected":
            return await ctx.send(f"{target.display_name} is not infected.")

        if random.randint(1, 100) <= self.config["cure_rate"]:
            target_data["state"] = "Healthy"
            user_data["cure_points"] += 1
            self.config["users"][str(target.id)] = target_data
            self.config["users"][str(ctx.author.id)] = user_data
            await self.notify_user(ctx, target, f"You have been cured by {ctx.author.display_name}!")
            await ctx.send(f"You have successfully cured {target.display_name}!")
        else:
            await ctx.send(f"Your attempt to cure {target.display_name} failed.")

        self.save_config()

    @plague.command(name="profile")
    async def plague_profile(self, ctx, user: discord.Member = None):
        """View your or another user's plague profile"""
        user = user or ctx.author
        data = self.config["users"].get(str(user.id), {"role": "User", "state": "Healthy", "plague_points": 0, "cure_points": 0})
        
        embed = discord.Embed(title=f"Plague Profile - {user.display_name}", color=discord.Color.blue())
        embed.add_field(name="Role", value=data["role"])
        embed.add_field(name="State", value=data["state"])
        embed.add_field(name="Plague Points", value=data["plague_points"])
        embed.add_field(name="Cure Points", value=data["cure_points"])
        embed.set_thumbnail(url=user.avatar.url)
        
        await ctx.send(embed=embed)

    @plague.command()
    async def doctor(self, ctx):
        """Become a doctor for a fee"""
        user_data = self.config["users"].get(str(ctx.author.id), {"role": "User", "state": "Healthy", "plague_points": 0, "cure_points": 0})
        if user_data["role"] == "Doctor":
            return await ctx.send("You are already a doctor.")

        cost = 10000  # Set the cost to become a doctor
        balance = await economy_db.get_user_balance(ctx.author.id)
        
        if balance[0] < cost:
            return await ctx.send(f"You need {cost} coins to become a doctor. You only have {balance[0]} coins.")

        await economy_db.update_balance(ctx.author.id, wallet=-cost)
        user_data["role"] = "Doctor"
        user_data["state"] = "Healthy"
        self.config["users"][str(ctx.author.id)] = user_data
        await ctx.send(f"You have spent {cost} coins to become a doctor.")
        self.save_config()

    @plague.command()
    async def plaguebearer(self, ctx):
        """Become a plaguebearer for a fee"""
        user_data = self.config["users"].get(str(ctx.author.id), {"role": "User", "state": "Healthy", "plague_points": 0, "cure_points": 0})
        if user_data["role"] == "Plaguebearer":
            return await ctx.send("You are already a plaguebearer.")

        cost = 10000  # Set the cost to become a plaguebearer
        balance = await economy_db.get_user_balance(ctx.author.id)
        
        if balance[0] < cost:
            return await ctx.send(f"You need {cost} coins to become a plaguebearer. You only have {balance[0]} coins.")

        await economy_db.update_balance(ctx.author.id, wallet=-cost)
        user_data["role"] = "Plaguebearer"
        user_data["state"] = "Infected"
        self.config["users"][str(ctx.author.id)] = user_data
        await ctx.send(f"You have spent {cost} coins to become a plaguebearer.")
        self.save_config()

    @plague.command()
    async def resign(self, ctx):
        """Resign from your current role"""
        user_data = self.config["users"].get(str(ctx.author.id), {"role": "User", "state": "Healthy", "plague_points": 0, "cure_points": 0})
        if user_data["role"] == "User":
            return await ctx.send("You don't have a special role to resign from.")

        cost = 5000  # Set the cost to resign
        balance = await economy_db.get_user_balance(ctx.author.id)
        
        if balance[0] < cost:
            return await ctx.send(f"You need {cost} coins to resign. You only have {balance[0]} coins.")

        await economy_db.update_balance(ctx.author.id, wallet=-cost)
        user_data["role"] = "User"
        self.config["users"][str(ctx.author.id)] = user_data
        await ctx.send(f"You have spent {cost} coins to resign from your role as {user_data['role']}.")
        self.save_config()

    @plague.command()
    async def leaderboard(self, ctx):
        """View the leaderboard of healthiest users"""
        sorted_users = sorted(self.config["users"].items(), key=lambda x: (x[1]['state'] == 'Healthy', x[1]['cure_points']), reverse=True)
        
        embed = discord.Embed(title="Plague Game Leaderboard", color=discord.Color.green())
        for i, (user_id, data) in enumerate(sorted_users[:10], start=1):
            user = self.bot.get_user(int(user_id))
            if user:
                embed.add_field(name=f"{i}. {user.display_name}", value=f"State: {data['state']}\nCure Points: {data['cure_points']}", inline=False)
        
        await ctx.send(embed=embed)

    async def notify_user(self, ctx, user: discord.Member, message: str):
        """Notify a user about a plague-related event"""
        await ctx.send(f"{user.mention} {message}")
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} is ready.")

async def setup(bot):
    await bot.add_cog(PlagueGame(bot))