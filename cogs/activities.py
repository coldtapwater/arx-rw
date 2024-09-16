import discord
from discord.ext import commands
import random
import time
from utils import economy_db
import utils.emojis as my_emojis
import utils.configs as uc

class Activities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}

    async def check_cooldown(self, user_id, activity):
        current_time = int(time.time())
        if user_id in self.cooldowns and activity in self.cooldowns[user_id]:
            if current_time < self.cooldowns[user_id][activity]:
                return self.cooldowns[user_id][activity]
        return None

    async def set_cooldown(self, user_id, activity):
        current_time = int(time.time())
        cooldown_time = current_time + 28800  # 8 hours in seconds
        if user_id not in self.cooldowns:
            self.cooldowns[user_id] = {}
        self.cooldowns[user_id][activity] = cooldown_time

    @commands.command()
    async def dig(self, ctx):
        cooldown = await self.check_cooldown(ctx.author.id, "dig")
        if cooldown:
            return await ctx.send(f"You can dig again <t:{cooldown}:R>")

        inventory = await economy_db.get_user_inventory(ctx.author.id)
        has_shovel = any(item.item_name == "shovel" for item in inventory)
        has_spade = any(item.item_name == "spade" for item in inventory)

        if not (has_shovel or has_spade):
            return await ctx.send("You need a shovel or spade to dig!")

        buckaroos = random.randint(50, 200) if has_shovel else random.randint(25, 100)
        await economy_db.update_balance(ctx.author.id, wallet=buckaroos)
        await self.set_cooldown(ctx.author.id, "dig")

        await ctx.send(f"You dug and found {buckaroos} {uc.CURRENCY}!")

    @commands.command()
    async def hunt(self, ctx):
        cooldown = await self.check_cooldown(ctx.author.id, "hunt")
        if cooldown:
            return await ctx.send(f"You can hunt again <t:{cooldown}:R>")

        inventory = await economy_db.get_user_inventory(ctx.author.id)
        has_axe = any(item.item_name == "axe" for item in inventory)
        has_pistol = any(item.item_name == "pistol" for item in inventory)
        has_rifle = any(item.item_name == "rifle" for item in inventory)

        if not (has_axe or has_pistol or has_rifle):
            return await ctx.send("You need an axe, pistol, or rifle to hunt!")

        animals = [
            ("Rabbit", 50, 0.3),
            ("Deer", 200, 0.25),
            ("Wolf", 500, 0.2),
            ("Bear", 1000, 0.15),
            ("Lion", 2000, 0.08),
            ("Rhino", 10000, 0.02)
        ]

        if has_rifle:
            animal = random.choices(animals, weights=[a[2] for a in animals])[0]
        elif has_pistol:
            animal = random.choices(animals[:-1], weights=[a[2] for a in animals[:-1]])[0]
        else:
            animal = random.choices(animals[:-2], weights=[a[2] for a in animals[:-2]])[0]

        await economy_db.update_balance(ctx.author.id, wallet=animal[1])
        await self.set_cooldown(ctx.author.id, "hunt")

        await ctx.send(f"You hunted a {animal[0]} and earned {animal[1]} {uc.CURRENCY}!")

    @commands.command()
    async def research(self, ctx):
        await ctx.send("Research action is coming soon!")

    @commands.command()
    async def mine(self, ctx):
        cooldown = await self.check_cooldown(ctx.author.id, "mine")
        if cooldown:
            return await ctx.send(f"You can mine again <t:{cooldown}:R>")

        inventory = await economy_db.get_user_inventory(ctx.author.id)
        has_pickaxe = any(item.item_name == "pickaxe" for item in inventory)
        has_tnt = any(item.item_name == "tnt" for item in inventory)
        has_tunnel_blast = any(item.item_name == "tunnel blast" for item in inventory)

        if not (has_pickaxe or has_tnt or has_tunnel_blast):
            return await ctx.send("You need a pickaxe, TNT, or tunnel blast to mine!")

        if has_tunnel_blast:
            gems = random.randint(25, 50)
            await economy_db.update_balance(ctx.author.id, gems=gems)
            await economy_db.remove_item_from_inventory(ctx.author.id, "tunnel blast", 1)
        elif has_tnt:
            gems = random.randint(5, 10)
            await economy_db.update_balance(ctx.author.id, gems=gems)
            await economy_db.remove_item_from_inventory(ctx.author.id, "tnt", 1)
        else:
            gems = random.randint(1, 3)
            await economy_db.update_balance(ctx.author.id, gems=gems)

        await self.set_cooldown(ctx.author.id, "mine")
        await ctx.send(f"You mined and found {gems} gems!")

    @commands.command()
    async def search(self, ctx):
        await ctx.send("Search action is coming soon!")

    @commands.command()
    async def detect(self, ctx):
        cooldown = await self.check_cooldown(ctx.author.id, "detect")
        if cooldown:
            return await ctx.send(f"You can detect again <t:{cooldown}:R>")

        inventory = await economy_db.get_user_inventory(ctx.author.id)
        has_metal_detector = any(item.item_name == "metal detector" for item in inventory)
        has_shovel = any(item.item_name == "shovel" for item in inventory)

        if not (has_metal_detector or has_shovel):
            return await ctx.send("You need a metal detector or shovel to detect!")

        if random.random() < 0.5:
            if has_metal_detector:
                buckaroos = random.randint(100, 500)
                await economy_db.update_balance(ctx.author.id, wallet=buckaroos)
                message = f"You detected and found {buckaroos} {uc.CURRENCY}!"
            else:
                message = "You didn't find anything valuable this time."
        else:
            if has_shovel:
                gems = random.randint(1, 5)
                await economy_db.update_balance(ctx.author.id, gems=gems)
                message = f"You detected and dug up {gems} gems!"
            else:
                message = "You detected something, but you need a shovel to dig it up!"

        await self.set_cooldown(ctx.author.id, "detect")
        await ctx.send(message)

    @commands.command()
    async def rob(self, ctx, target: discord.Member):
        if target.id == ctx.author.id:
            return await ctx.send("You can't rob yourself!")

        cooldown = await self.check_cooldown(ctx.author.id, "rob")
        if cooldown:
            return await ctx.send(f"You can rob again <t:{cooldown}:R>")

        inventory = await economy_db.get_user_inventory(ctx.author.id)
        has_ski_mask = any(item.item_name == "ski mask" for item in inventory)
        has_pistol = any(item.item_name == "pistol" for item in inventory)
        has_getaway_car = any(item.item_name == "getaway car" for item in inventory)

        success_rate = 0.1 if not has_ski_mask else 0.4

        if random.random() > success_rate:
            await economy_db.update_balance(ctx.author.id, wallet=-100)
            await self.set_cooldown(ctx.author.id, "rob")
            return await ctx.send(f"Your robbery failed! You've been fined 100 {uc.CURRENCY}.")

        target_wallet, _, _ = await economy_db.get_user_balance(target.id)
        stolen_amount = min(random.randint(100, 500), target_wallet)

        if has_pistol:
            stolen_amount += 150

        await economy_db.update_balance(ctx.author.id, wallet=stolen_amount)
        await economy_db.update_balance(target.id, wallet=-stolen_amount)

        if has_getaway_car:
            await economy_db.add_badge(ctx.author.id, "criminal on the run")

        await self.set_cooldown(ctx.author.id, "rob")
        await ctx.send(f"You successfully robbed {stolen_amount} {uc.CURRENCY} from {target.name}!")

async def setup(bot):
    await bot.add_cog(Activities(bot))