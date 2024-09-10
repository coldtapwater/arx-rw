import discord
from discord.ext import commands
import random
from utils.models.models import User
from utils.checks import blacklist_check
from tortoise.exceptions import DoesNotExist

# Assuming these are defined elsewhere in your project
from utils.configs import EMBED_COLOR, CURRENCY
import utils.emojis as my_emojis

class BlackjackView(discord.ui.View):
    def __init__(self, ctx, bot, user, player_hand, dealer_hand, deck, wager, message):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.bot = bot
        self.user = user
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.deck = deck
        self.wager = wager
        self.message = message

    def calculate_hand_value(self, hand):
        value = 0
        aces = 0
        for card in hand:
            card_value = card.split()[0]
            if card_value in ['J', 'Q', 'K']:
                value += 10
            elif card_value == 'A':
                aces += 1
            else:
                value += int(card_value)
        
        for _ in range(aces):
            if value + 11 <= 21:
                value += 11
            else:
                value += 1
        return value

    async def update_embed(self):
        player_value = self.calculate_hand_value(self.player_hand)
        dealer_value = self.calculate_hand_value(self.dealer_hand)

        embed = discord.Embed(title=f"{my_emojis.PREFIX} Blackjack", description="Your deal", color=discord.Color.from_str(EMBED_COLOR))
        embed.add_field(name="Your Hand:", value="\n".join(self.player_hand))
        embed.add_field(name="Dealer's Hand:", value="\n".join(self.dealer_hand[:1] + ['?']))
        embed.add_field(name="Your Balance:", value=f"{self.user.wallet} {CURRENCY}")
        embed.add_field(name="Wager:", value=f"{self.wager} {CURRENCY}")
        await self.message.edit(embed=embed, view=self)

    @discord.ui.button(label='Hit', style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.player_hand.append(self.deck.pop())
        player_value = self.calculate_hand_value(self.player_hand)
        if player_value > 21:
            await interaction.response.send_message(f"{my_emojis.PREFIX} oh no yous went over 21! You lost {self.wager} {CURRENCY}", ephemeral=True)
            self.user.wallet -= self.wager
            await self.user.save()
            await self.update_embed()
            self.stop()
        else:
            await self.update_embed()

    @discord.ui.button(label='Stand', style=discord.ButtonStyle.secondary)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        dealer_value = self.calculate_hand_value(self.dealer_hand)
        while dealer_value < 17:
            self.dealer_hand.append(self.deck.pop())
            dealer_value = self.calculate_hand_value(self.dealer_hand)

        await self.finalize_game(interaction)

    @discord.ui.button(label='Double Bet', style=discord.ButtonStyle.success)
    async def double_bet(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user.wallet >= self.wager * 2:
            self.wager *= 2
            self.player_hand.append(self.deck.pop())
            player_value = self.calculate_hand_value(self.player_hand)
            if player_value > 21:
                await interaction.response.send_message(f"{my_emojis.PREFIX} oh darn you went over 21! You lost {self.wager} {CURRENCY}", ephemeral=True)
                self.user.wallet -= self.wager
                await self.user.save()
                await self.update_embed()
                self.stop()
            else:
                await self.update_embed()
        else:
            await interaction.response.send_message(f"{my_emojis.ERROR} you cants double your bet because yous dont have enough {CURRENCY}", ephemeral=True)

    async def finalize_game(self, interaction: discord.Interaction):
        player_value = self.calculate_hand_value(self.player_hand)
        dealer_value = self.calculate_hand_value(self.dealer_hand)

        embed = discord.Embed(title=f"{my_emojis.PREFIX} Blackjack", description="Dealer's deal", color=discord.Color.from_str(EMBED_COLOR))
        embed.add_field(name="Your Hand:", value="\n".join(self.player_hand))
        embed.add_field(name="Dealer's Hand:", value="\n".join(self.dealer_hand))
        embed.add_field(name="Your Balance:", value=f"{self.user.wallet} {CURRENCY}")
        embed.add_field(name="Wager:", value=f"{self.wager} {CURRENCY}")

        if dealer_value > 21:
            embed.add_field(name="Result:", value="Dealer busts! You win!")
            self.user.wallet += int(self.wager * 1.5)
        elif dealer_value > player_value:
            embed.add_field(name="Result:", value="Dealer wins!")
            self.user.wallet -= self.wager
        elif dealer_value < player_value:
            embed.add_field(name="Result:", value="You win!")
            self.user.wallet += int(self.wager * 1.5)
        else:
            embed.add_field(name="Result:", value="Push!")

        await self.user.save()
        embed.add_field(name="New Wallet Balance:", value=f"{self.user.wallet} {CURRENCY}")
        await self.message.edit(embed=embed, view=None)
        self.stop()

class BlackjackCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @blacklist_check()
    async def blackjack(self, ctx, bet: int):
        """Play a blackjack game!"""
        try:
            user = await User.get(id=ctx.author.id)
        except DoesNotExist:
            user = await User.create(id=ctx.author.id, wallet=0, bank=0, gems=0)

        if user.wallet == 0:
            await ctx.send(f"{my_emojis.ERROR} you cants play because yous dont have any {CURRENCY} in your wallet")
            return

        wager = bet

        if wager > user.wallet:
            await ctx.send(f"{my_emojis.ERROR} me thinks you dont have that money in your wallet... maybe in your bankses?")
            return
        
        if wager <= 0:
            await ctx.send(f"{my_emojis.ERROR} how are you going to playses with a bet of 0?")
            return
        
        await ctx.send(f"{my_emojis.PREFIX} Shuffling the deck...")
        cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        deck = []
        for suit in ["♠", "♥", "♦", "♣"]:
            for card in cards:
                deck.append(f"{card} of {suit}")
        random.shuffle(deck)
        
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]
        
        embed = discord.Embed(title=f"{my_emojis.PREFIX} Blackjack", description="Your deal", color=discord.Color.from_str(EMBED_COLOR))
        embed.add_field(name="Your Hand:", value=player_hand[0] + "\n" + player_hand[1])
        embed.add_field(name="Dealer's Hand:", value=dealer_hand[0] + "\n" + '?')
        embed.add_field(name="Your Balance:", value=f"{user.wallet} {CURRENCY}")
        embed.add_field(name="Wager:", value=f"{wager} {CURRENCY}")
        message = await ctx.send(embed=embed)

        view = BlackjackView(ctx, self.bot, user, player_hand, dealer_hand, deck, wager, message)
        await message.edit(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(BlackjackCog(bot))