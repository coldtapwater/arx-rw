#LEBRON-KRILL, VERSION 1.0.0
#J_COLDTAPWATER, VERSION 1.0.1
import discord
from discord.ext import commands
from random import choice
import utils.configs as uc

class Actions(commands.Cog):
    def __init__(self, bot, embed_color):
        self.bot = bot
        self.embed_color = embed_color

        self.hit_gifs = [
            "https://media1.tenor.com/m/g_9NDHUmUdgAAAAC/anime.gif",
            "https://media1.tenor.com/m/fz-V6dZ1PiQAAAAC/how-to-raise-a-boring-girlfriend-saenai.gif",
            "https://media1.tenor.com/m/vZnHUMCUU6AAAAAC/handa-naru-barakamon.gif",
            "https://media1.tenor.com/m/LW2jedlX6gQAAAAC/hit-stupid.gif",
            "https://media1.tenor.com/m/BY3j-feOLDkAAAAC/zero-no-tsukaima-saito-hiraga.gif"
        ]
        self.bite_gifs = [
            "https://media1.tenor.com/m/9dOzFGFZxnoAAAAC/bite-anime.gif",
            "https://media1.tenor.com/m/72KXBuH1vQgAAAAC/anime-acchi-kocchi.gif",
            "https://media1.tenor.com/m/ECCpi63jZlUAAAAC/anime-bite.gif"
        ]
        self.hit_and_bite_messages = [
            "That must have hurt.",
            "OUCH!!!",
            "Owww :c",
        ]

        self.kill_gifs = [
            "https://media1.tenor.com/m/SIrXZQWK9WAAAAAC/me-friends.gif",
            "https://media1.tenor.com/m/b7UhYIWfmXEAAAAC/yumeko-mirai-nikki.gif",
            "https://media1.tenor.com/m/CWsbJDl70tsAAAAC/shimoneta.gif",
            "https://media1.tenor.com/m/yrTmruTQ-YIAAAAC/anime-ready-to-fight.gif"
        ]
        self.kill_messages = [
            "Bye.",
            "RIP 🪦",
            "See ya!"
        ]

        self.stare_gifs = [
            "https://media1.tenor.com/m/YfqM8h3_6NEAAAAC/rin-anime.gif",
            "https://media1.tenor.com/m/IwyNIipPItQAAAAC/anime-naruto.gif",
            "https://media1.tenor.com/m/SEEMSDLdDugAAAAd/anya-forger.gif",
            "https://media1.tenor.com/m/0Zrxg3b0nMwAAAAC/anime-girl.gif"
        ]

        self.wave_gifs = [
            "https://media1.tenor.com/m/1MfQk9vFF7MAAAAC/anime-bye-bye-maki.gif",
            "https://media1.tenor.com/m/ILT5-vuNzB8AAAAC/anime-anime-wave-bye.gif",
            "https://media1.tenor.com/m/9aXyxmnYW7oAAAAC/my-dress-up-darling-sono-bisque-doll-wa-koi-wo-suru.gif",
            "https://media1.tenor.com/m/tzbVcnK8iGsAAAAC/keai-cute.gif",
        ]


    def generate_embed(self, content: str, gif: str) -> discord.Embed:
        embed = discord.Embed(description=content, color=discord.Colour.from_str(self.embed_color))
        embed.set_image(url=gif)
        return embed
        
    @commands.command()
    async def hit(self, ctx: commands.Context, target: discord.Member):
        """Hit another member."""
        if ctx.author.id == target.id:
            return await ctx.send("You can't hit yourself silly")

        embed = self.generate_embed("{} hits {}! {}".format(ctx.author.name, target.name,choice(self.hit_and_bite_messages)), choice(self.hit_gifs))
        await ctx.send(embed=embed)

    @commands.command()
    async def bite(self, ctx: commands.Context, target: discord.Member):
        """Bite another member."""
        if ctx.author.id == target.id:
            return await ctx.send("Why would you try bite yourself??")

        embed = self.generate_embed("{} bites {}! {}.".format(ctx.author.name, target.name, choice(self.hit_and_bite_messages)), choice(self.bite_gifs))
        await ctx.send(embed=embed)

    @commands.command()
    async def kill(self, ctx: commands.Context, target: discord.Member):
        """Kill another member."""
        if ctx.author.id == target.id:
            return await ctx.send("Hey... maybe don't do this?")

        embed = self.generate_embed("{} hits {}! {}".format(ctx.author.name, target.name, choice(self.kill_messages)), choice(self.kill_gifs))
        await ctx.send(embed=embed)

    @commands.command()
    async def stare(self, ctx: commands.Context, target: discord.Member):
        """Stare at another member."""
        if ctx.author.id == target.id:
            return await ctx.send("Weirdo...")

        embed = self.generate_embed("{} stares at {}.".format(ctx.author.name, target.name), choice(self.stare_gifs))
        await ctx.send(embed=embed)

    @commands.command()
    async def wave(self, ctx: commands.Context, target: discord.Member):
        """Wave at another member."""
        if ctx.author.id == target.id:
            return await ctx.send("Wow... waving at yourself...")

        embed = self.generate_embed("{} waves at {}.".format(ctx.author.name, target.name), choice(self.wave_gifs))
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Actions(bot,uc.EMBED_COLOR))