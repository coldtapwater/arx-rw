# J_COLDTAPWATER, VERSION 1.0.0

import discord
from discord.ext import commands
from discord.ui import View, Button

class HelpMenu(commands.Cog):
    def __init__(self, bot, embed_color):
        self.bot = bot
        self.embed_color = embed_color

    @commands.hybrid_command()
    async def help(self, ctx):
        embed = self.get_help_embed(1)  # Start on page 1
        view = HelpView(embed, self.bot, ctx)
        await ctx.send(embed=embed, view=view)

    def get_help_embed(self, page):
        commands_per_page = 5
        start = (page - 1) * commands_per_page
        end = start + commands_per_page
        embed = discord.Embed(title="Arx Bot Help", description="Use the buttons to navigate.", color=discord.Color.from_str(self.embed_color))

        for i, (command_name, command) in enumerate(list(self.bot.commands)[start:end], start=1):
            embed.add_field(name=f"{i}. {command_name}", value=command.help or "No description", inline=False)

        embed.set_footer(text=f"Page {page}/{(len(self.bot.commands) + commands_per_page - 1) // commands_per_page}")
        return embed

class HelpView(View):
    def __init__(self, embed, bot, ctx):
        super().__init__(timeout=60)
        self.embed = embed
        self.bot = bot
        self.ctx = ctx
        self.current_page = 1

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous(self, button: Button, interaction: discord.Interaction):
        if self.current_page > 1:
            self.current_page -= 1
            self.embed = self.ctx.cog.get_help_embed(self.current_page)
            await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next(self, button: Button, interaction: discord.Interaction):
        max_pages = (len(self.bot.commands) + 4) // 5
        if self.current_page < max_pages:
            self.current_page += 1
            self.embed = self.ctx.cog.get_help_embed(self.current_page)
            await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, button: Button, interaction: discord.Interaction):
        await interaction.message.delete()