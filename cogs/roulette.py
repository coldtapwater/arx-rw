import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, View
import random
from utils.models.models import User
from utils import economy_db, configs, emojis

class NumberBetModal(Modal):
    def __init__(self, user_id: int, bet: int):
        super().__init__(title="Number Bet")
        self.user_id = user_id
        self.bet = bet
        self.add_item(TextInput(label="Number (1-36)", placeholder="Enter a number between 1 and 36", required=True))

    async def on_submit(self, interaction: discord.Interaction):
        number = self.children[0].value
        if not number.isdigit() or not 1 <= int(number) <= 36:
            await interaction.response.send_message("Please enter a valid number between 1 and 36.", ephemeral=True)
            return

        number = int(number)
        await handle_roulette_bet(interaction, self.user_id, self.bet, number)

class RouletteView(View):
    def __init__(self, user_id: int, bet: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.bet = bet

    @discord.ui.button(label='Red', style=discord.ButtonStyle.danger)
    async def red(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_roulette_bet(interaction, self.user_id, self.bet, "red")

    @discord.ui.button(label='Black', style=discord.ButtonStyle.primary)
    async def black(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_roulette_bet(interaction, self.user_id, self.bet, "black")

    @discord.ui.button(label='Number', style=discord.ButtonStyle.success)
    async def number(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(NumberBetModal(self.user_id, self.bet))

async def handle_roulette_bet(interaction: discord.Interaction, user_id: int, bet: int, choice):
    wallet, bank, gems = await economy_db.get_user_balance(user_id)

    if wallet < bet:
        await interaction.response.send_message(f"{configs.ERROR_EMOJI} You don't have enough money for this bet.", ephemeral=True)
        return

    roulette_wheel = {
        "red": [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36],
        "black": [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
    }
    all_numbers = roulette_wheel["red"] + roulette_wheel["black"]

    spin = random.choice(all_numbers)
    color = "red" if spin in roulette_wheel["red"] else "black"

    if (isinstance(choice, int) and spin == choice) or (isinstance(choice, str) and choice.lower() == color):
        if isinstance(choice, int):
            winnings = bet * 36
            result = f"{configs.PREFIX_EMOJI} Wow! The ball landed on exactly {spin} ({color}) and you won {winnings}! That's 36x your bet!"
        else:
            winnings = bet * 2
            result = f"{configs.PREFIX_EMOJI} Nice! The ball landed on {spin} ({color}) and you won {winnings}! That's 2x your bet!"
        await economy_db.update_balance(user_id, wallet=winnings)
    else:
        await economy_db.update_balance(user_id, wallet=-bet)
        result = f"{configs.PREFIX_EMOJI} Aww, the ball landed on {spin} ({color}). Maybe next time!"

    await interaction.response.send_message(result, ephemeral=True)

class Roulette(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roulette(self, interaction: discord.Interaction, bet: int):
        """Play Roulette with the bot!"""
        user_id = interaction.user.id
        wallet, bank, gems = await economy_db.get_user_balance(user_id)

        if wallet < bet:
            await interaction.response.send_message(f"{emojis.ERROR} You don't have enough money for this bet.")
            return

        embed = discord.Embed(title=f"{emojis.PREFIX} Roulette", color=discord.Color.from_str(configs.EMBED_COLOR))
        embed.add_field(name="How to Play:", value="Choose to bet on either a specific number, or the color red or black. "
                                                   "If the ball lands on your choice, you win! Good luck!")
        embed.add_field(name="Bet:", value=f"{bet} {configs.CURRENCY}")
        embed.add_field(name="Wallet:", value=f"{wallet} {configs.CURRENCY}")

        view = RouletteView(user_id, bet)

        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Roulette(bot))