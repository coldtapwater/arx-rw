import utils.configs as uc
import asyncio
import discord
from discord.ext import commands
import random
import aiosqlite
from typing import List, Dict, Optional
import json
import utils.checks

class Card:
    def __init__(self, color: str, value: str):
        self.color = color
        self.value = value

    def __str__(self):
        return f"{self.color} {self.value}"

    def to_dict(self):
        return {"color": self.color, "value": self.value}

    @classmethod
    def from_dict(cls, data):
        return cls(data["color"], data["value"])

class Player:
    def __init__(self, user: discord.User):
        self.user = user
        self.hand: List[Card] = []

class UnoGame:
    def __init__(self, host: discord.User):
        self.host = host
        self.players: List[Player] = []
        self.current_player_index = 0
        self.deck: List[Card] = []
        self.discard_pile: List[Card] = []
        self.direction = 1
        self.turn_count = 0
        self.started = False

    def create_deck(self):
        colors = ['Red', 'Blue', 'Green', 'Yellow']
        values = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'Skip', '+2']
        
        for color in colors:
            for value in values:
                self.deck.append(Card(color, value))
                if value != '0':
                    self.deck.append(Card(color, value))
        
        for _ in range(4):
            self.deck.append(Card('Wild', 'Wild'))
            self.deck.append(Card('Wild', '+4'))
        
        random.shuffle(self.deck)

    def deal_cards(self):
        for player in self.players:
            for _ in range(7):
                player.hand.append(self.deck.pop())

    def start_game(self):
        self.create_deck()
        self.deal_cards()
        random.shuffle(self.players)
        self.discard_pile.append(self.deck.pop())
        while self.discard_pile[-1].color == 'Wild':
            self.discard_pile.append(self.deck.pop())
        self.started = True

    def next_turn(self):
        self.current_player_index = (self.current_player_index + self.direction) % len(self.players)
        self.turn_count += 1

    def get_current_player(self) -> Player:
        return self.players[self.current_player_index]

    def is_valid_play(self, card: Card) -> bool:
        top_card = self.discard_pile[-1]
        return (
            card.color == top_card.color or
            card.value == top_card.value or
            card.color == 'Wild'
        )

    def play_card(self, player: Player, card: Card):
        player.hand.remove(card)
        self.discard_pile.append(card)

    def draw_cards(self, player: Player, count: int):
        for _ in range(count):
            if not self.deck:
                self.deck = self.discard_pile[:-1]
                self.discard_pile = [self.discard_pile[-1]]
                random.shuffle(self.deck)
            player.hand.append(self.deck.pop())

    def to_dict(self):
        return {
            "host": self.host.id,
            "players": [{"id": player.user.id, "hand": [card.to_dict() for card in player.hand]} for player in self.players],
            "current_player_index": self.current_player_index,
            "deck": [card.to_dict() for card in self.deck],
            "discard_pile": [card.to_dict() for card in self.discard_pile],
            "direction": self.direction,
            "turn_count": self.turn_count,
            "started": self.started
        }

    @classmethod
    def from_dict(cls, data, bot):
        game = cls(bot.get_user(data["host"]))
        game.players = [Player(bot.get_user(player["id"])) for player in data["players"]]
        for player, player_data in zip(game.players, data["players"]):
            player.hand = [Card.from_dict(card_data) for card_data in player_data["hand"]]
        game.current_player_index = data["current_player_index"]
        game.deck = [Card.from_dict(card_data) for card_data in data["deck"]]
        game.discard_pile = [Card.from_dict(card_data) for card_data in data["discard_pile"]]
        game.direction = data["direction"]
        game.turn_count = data["turn_count"]
        game.started = data["started"]
        return game

class Uno(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        pass

    async def save_game(self, channel_id: int, game: UnoGame):
        game_data = json.dumps(game.to_dict())
        await UnoGame.update_or_create(channel_id=channel_id, defaults={"game_data": game_data})

    async def load_game(self, channel_id: int) -> Optional[UnoGame]:
        game_record = await UnoGame.get_or_none(channel_id=channel_id)
        if game_record:
            game_data = json.loads(game_record.game_data)
            return UnoGame.from_dict(game_data, self.bot)
        return None

    async def delete_game(self, channel_id: int):
        await UnoGame.filter(channel_id=channel_id).delete()

    @commands.group(invoke_without_command=True)
    async def uno(self, ctx):
        await ctx.send("Invalid UNO command. Use 'r uno help' for more information.")

    @uno.command()
    @utils.checks.blacklist_check()
    async def play(self, ctx):
        """Start a new game of Uno!"""
        game = await self.load_game(ctx.channel.id)
        if game:
            if game.started:
                await ctx.send(f"A game is already in progress. It's currently on turn {game.turn_count}. You can join at any time using 'r uno join'.")
            else:
                await ctx.send("A game is being set up. Use 'r uno join' to join the game.")
        else:
            game = UnoGame(ctx.author)
            await self.save_game(ctx.channel.id, game)
            await ctx.send(f"{ctx.author.mention} has started a new UNO game! Use 'r uno join' to join the game.")

    @uno.command()
    @utils.checks.blacklist_check()
    async def join(self, ctx):
        """Join a game of Uno!"""
        game = await self.load_game(ctx.channel.id)
        if not game:
            await ctx.send("No UNO game is currently being set up. Use 'r uno play' to start a new game.")
            return

        if game.started:
            await ctx.send("The game has already started. You can join in the next round.")
            return

        if any(player.user == ctx.author for player in game.players):
            await ctx.send("You've already joined this game.")
            return

        if len(game.players) >= 10:
            await ctx.send("This game is full (max 10 players).")
            return

        game.players.append(Player(ctx.author))
        await self.save_game(ctx.channel.id, game)
        await ctx.send(f"{ctx.author.mention} has joined the UNO game!")

    @uno.command()
    @utils.checks.blacklist_check()
    async def start(self, ctx):
        """
        Start the game
        """
        game = await self.load_game(ctx.channel.id)
        if not game:
            await ctx.send("No UNO game is currently being set up. Use 'r uno play' to start a new game.")
            return

        if game.host != ctx.author:
            await ctx.send("Only the game host can start the game.")
            return

        if game.started:
            await ctx.send("The game has already started.")
            return

        if len(game.players) < 3:
            await ctx.send("At least 3 players are required to start the game.")
            return

        game.start_game()
        await self.save_game(ctx.channel.id, game)
        await ctx.send("The UNO game has started!")
        await self.show_game_state(ctx)
        await self.show_hand(ctx, game.get_current_player().user)

    @uno.command()
    @utils.checks.blacklist_check()
    async def hand(self, ctx):
        game = await self.load_game(ctx.channel.id)
        if not game:
            await ctx.send("No UNO game is currently in progress.")
            return

        player = next((p for p in game.players if p.user == ctx.author), None)
        if not player:
            await ctx.send("You're not in this game.")
            return

        await self.show_hand(ctx, ctx.author)

    @uno.command()
    @utils.checks.blacklist_check()
    async def draw(self, ctx, count: int = 1):
        game = await self.load_game(ctx.channel.id)
        if not game:
            await ctx.send("No UNO game is currently in progress.")
            return

        if count > 2:
            await ctx.send("You can draw a maximum of 2 cards.")
            return

        player = game.get_current_player()
        if player.user != ctx.author:
            await ctx.send("It's not your turn.")
            return

        game.draw_cards(player, count)
        await self.save_game(ctx.channel.id, game)
        await ctx.send(f"{ctx.author.mention} drew {count} card(s).")
        
        if not any(game.is_valid_play(card) for card in player.hand):
            await ctx.send(f"{ctx.author.mention} has no valid plays. Turn passed.")
            game.next_turn()
            await self.save_game(ctx.channel.id, game)
            await self.show_game_state(ctx)
            await self.show_hand(ctx, game.get_current_player().user)
        else:
            await self.show_hand(ctx, ctx.author)

    @uno.command()
    @utils.checks.blacklist_check()
    async def set(self, ctx, card_id: int):
        """Set a card onto the table."""
        game = await self.load_game(ctx.channel.id)
        if not game:
            await ctx.send("No UNO game is currently in progress.")
            return

        player = game.get_current_player()
        if player.user != ctx.author:
            await ctx.send("It's not your turn.")
            return

        if card_id < 1 or card_id > len(player.hand):
            await ctx.send("Invalid card ID.")
            return

        card = player.hand[card_id - 1]
        if not game.is_valid_play(card):
            await ctx.send("That's not a valid play. The card must match the color or value of the top card, or be a Wild card.")
            return

        game.play_card(player, card)
        await ctx.send(f"{ctx.author.mention} played {card}.")

        if card.color == 'Wild':
            def check(m):
                return m.author == ctx.author and m.content.lower() in ['red', 'blue', 'green', 'yellow', 'r', 'b', 'g', 'y']

            await ctx.send("What color do you want to pick? (Red, Blue, Green, Yellow)")
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=30.0)
                color = msg.content.lower()
                if color in ['r', 'b', 'g', 'y']:
                    color = {'r': 'Red', 'b': 'Blue', 'g': 'Green', 'y': 'Yellow'}[color]
                else:
                    color = color.capitalize()
                card.color = color
                await ctx.send(f"{ctx.author.mention} chose {color}.")
            except asyncio.TimeoutError:
                card.color = random.choice(['Red', 'Blue', 'Green', 'Yellow'])
                await ctx.send(f"{ctx.author.mention} didn't choose a color in time. Randomly selected {card.color}.")

        if card.value == 'Skip':
            game.next_turn()
            await ctx.send(f"{game.get_current_player().user.mention}'s turn was skipped!")

        if card.value in ['+2', '+4']:
            next_player = game.players[(game.current_player_index + game.direction) % len(game.players)]
            draw_count = 2 if card.value == '+2' else 4
            game.draw_cards(next_player, draw_count)
            await ctx.send(f"{next_player.user.mention} draws {draw_count} cards and their turn is skipped!")
            game.next_turn()

        game.next_turn()

        if len(player.hand) == 1:
            await ctx.send(f"**UNO!** {ctx.author.mention} has only one card left!")
        elif len(player.hand) == 0:
            await ctx.send(f"**{ctx.author.mention} has won the game!**")
            await self.delete_game(ctx.channel.id)
            return

        await self.save_game(ctx.channel.id, game)
        await self.show_game_state(ctx)
        await self.show_hand(ctx, game.get_current_player().user)

    @uno.command()
    @utils.checks.blacklist_check()
    async def skip(self, ctx):
        """Skip the current player's turn."""
        game = await self.load_game(ctx.channel.id)
        if not game:
            await ctx.send("No UNO game is currently in progress.")
            return

        player = game.get_current_player()
        if player.user != ctx.author:
            await ctx.send("It's not your turn.")
            return

        game.next_turn()
        await self.save_game(ctx.channel.id, game)
        await ctx.send(f"{ctx.author.mention} passed their turn.")
        await self.show_game_state(ctx)
        await self.show_hand(ctx, game.get_current_player().user)

    @uno.command()
    @utils.checks.blacklist_check()
    async def end(self, ctx):
        """End the current game."""
        game = await self.load_game(ctx.channel.id)
        if not game:
            await ctx.send("No UNO game is currently in progress.")
            return

        if game.host != ctx.author:
            await ctx.send(f"{game.host.mention}, {ctx.author.mention} wants to end the game. Do you agree?")
            return

        await self.delete_game(ctx.channel.id)
        await ctx.send("The UNO game has been ended.")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} is ready.")
async def setup(bot):
    await bot.add_cog(Uno(bot))
