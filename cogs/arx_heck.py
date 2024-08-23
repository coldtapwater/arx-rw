import discord
from discord.ext import commands
import random

import utils.my_emojis as my_emojis


class ArxHeck(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["hack"])
    async def heck(self, ctx, target: discord.Member):
        message1 = await ctx.send(f"Hacking {target.mention}...")

        last_dms=["omg i just texted my crush ‘goodnight mom’ 😳", "bro i called my teacher ‘dad’ in class today 😭", "why did i dream about marrying my toaster tho? 😂", "i can’t believe i asked if chicken wings come from pigs 🤦‍♂️", "dude i tried to unlock my house door with my car key fob…", "i just realized i wore my shirt backwards all day 🥲", "why did i think narwhals weren’t real until now?", "i just asked my boss for a ‘bathroom break’ in an email 🤦‍♀️", "i accidentally sent a heart emoji to my dentist… help 😅", "i legit forgot how to spell ‘because’ today… twice", "bro i was today years old when i learned how to boil an egg 😭", "i just walked into a door because i thought it was automatic...", "i replied ‘love you too’ to my pizza delivery guy 💀", "how did i manage to drop my phone in the toilet again?", "dude i just texted the wrong person and now they think i’m in love with pineapples 🍍"]

        message2 = await ctx.edit("Fetching IP address...")

        octets = [str(random.randint(1, 255)) for _ in range(4)]
        await message2.edit(f"Fetching IP address: {'.'.join(octets)}")

        await message1.edit(content=f"Fetching last dm... {random.choice(last_dms)}")


        embed = discord.Embed(
            title="Summary of Hack against " + target.name,
            description=f"**IP address:** {'. '.join(octets)}\n**Last DM:** {random.choice(last_dms)}",
            color=discord.Color.from_str("ff0000")
        )
        await ctx.send(embed=embed)
