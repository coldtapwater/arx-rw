import discord
from discord.ext import commands
import random

class CardsAgainstHumanity(commands.Cog):
    def __init__(self, bot, embed_color):
        self.bot = bot
        self.embed_color = embed_color
        self.games = {}

    @commands.group()
    async def cah_nsfw(self, ctx):
        """Cards Against Humanity commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand passed")

    @cah_nsfw.command()
    @commands.is_nsfw()
    async def start(self, ctx):
        """Start a NSFW Cards Against Humanity game."""
        if ctx.channel.id in self.games:
            await ctx.send("A game is already in progress in this channel.")
            return

        self.games[ctx.channel.id] = {
            'players': [ctx.author],
            'czar': ctx.author,
            'round': 0,
            'black_card': None,
            'white_cards': {},
            'responses': {},
            'submitted': set(),
        }
        await ctx.send(f"{ctx.author.mention} has started a game of Cards Against Humanity! Type `/join_cah` to join the game.")

    @cah_nsfw.command()
    @commands.is_nsfw()
    async def join(self, ctx):
        """Join a Cards Against Humanity game."""
        if ctx.channel.id not in self.games:
            await ctx.send("No game is currently in progress in this channel. Type `/start_cah` to start a game.")
            return

        game = self.games[ctx.channel.id]
        if ctx.author in game['players']:
            await ctx.send("You are already in the game.")
            return

        game['players'].append(ctx.author)
        await ctx.send(f"{ctx.author.mention} has joined the game!")

    @cah_nsfw.command()
    @commands.is_nsfw()
    async def deal(self, ctx):
        """Deal cards and start a new round."""
        if ctx.channel.id not in self.games:
            await ctx.send("No game is currently in progress in this channel.")
            return

        game = self.games[ctx.channel.id]
        if ctx.author != game['czar']:
            await ctx.send("Only the current Czar can deal cards.")
            return

        black_cards = [
            "Why can't I sleep at night?",
            "I got 99 problems but ___ ain't one.",
            "What's a girl's best friend?",
            "What's that smell?",
            "This is the way the world ends: not with a bang but with ___.",
            "___: good to the last drop.",
            "What did I bring back from Mexico?",
            "What don't you want to find in your Chinese food?",
            "Life for American Indians was forever changed when the White Man introduced them to ___.",
            "How am I maintaining my relationship status?",
            "How do I get a group of neanderthals to do my bidding?",
            "What's the most emo emoji?",
            "What's the most inappropriate thing to say to a 12 year old?",
            "What's the most overused word in the English language?",
            "What's the most underrated video game?",
            "What's the most overrated video game?",
            "What's the most ridiculous thing you've ever heard of?",
            "What's the most ridiculous thing you've ever done?",
            "In the next episode, you'll see how ___ changed everything.",
            "My guilty pleasure is ___.",
            "I never leave the house without ___.",
            "What's the weirdest thing you've ever done for money?",
            "Instead of going to the gym, I just ___.",
            "Why does my back hurt all the time? ___",
            "The secret to a happy life is ___.",
            "My biggest regret in life is ___.",
            "What’s the strangest thing you've found on the internet?",
            "Why did I wake up covered in ___.",
            "What did I find in the back of my fridge?",
            "My therapist says I have a problem with ___.",
            "How did I ruin the family reunion this time?",
            "I can't believe I forgot to pack ___.",
            "What's the worst advice you've ever received?",
            "My most embarrassing moment involved ___.",
            "What’s the last thing you’d expect to find in your bed?",
            "Why did I get banned from the internet?",
            "What’s my superpower?",
            "What's the secret ingredient in grandma's cookies?",
        ]

        white_cards = [
            "A bag of magic beans",
            "A balanced breakfast",
            "A big black dick",
            "A bleached asshole",
            "A brain tumor",
            "A can of whoop-ass",
            "A cooler full of organs",
            "A crucifixion",
            "A death ray",
            "A defective condom",
            "A falcon in your pyjamas",
            "A fender bender",
            "A gentle caress",
            "A girl's best friend",
            "A group of semicolons",
            "AIDS",
            "An ass disaster",
            "An ass to mouth",
            "An all nighter",
            "An American dream",
            "An ass disaster",
            "An ass to mouth",
            "An ass to your head",
            "A moist nugget",
            "A moldy sandwich",
            "A naked grandma",
            "A naughty librarian",
            "A naughty nurse",
            "A naughty teacher",
            "A nipple tassel",
            "A noisy vibrator",
            "A non-consensual hug",
            "A not-so-silent fart",
            "A nuclear wedgie",
            "A nudist colony",
            "A one-eyed trouser snake",
            "A pants-less party",
            "A party pooper",
            "A peanut butter jelly sandwich",
            "A peek-a-boo thong",
            "A penis-shaped cookie",
            "A pink taco",
            "A pirate's booty",
            "A pixelated genitalia",
            "A plumber's crack",
            "A pre-owned sex toy",
            "A prickly pear",
            "A purple rag",
            "A purple square",
            "A red nose",
            "A sad clown",
            "Sadomasochism",
            "A sadomasochist",
            "A screwdriver",
            "A sexless marriage",
            "Damn you fucked up",
            "A lifetime of regret.",
            "Accidentally sexting your mom.",
            "Getting drunk before noon.",
            "Impromptu breakdancing.",
            "The awkward silence after a fart.",
            "A four-hour conversation about cheese.",
            "Being mistaken for a homeless person.",
            "An ill-timed erection.",
            "Your browser history.",
            "The last breath of a dying man.",
            "A shocking amount of child nudity.",
            "Casually discussing euthanasia.",
            "Falling in love with a stranger.",
            "A fart so powerful that it wakes the neighbors.",
            "Being caught naked by the mailman.",
            "The sound of a thousand farts.",
            "The look on her face when you tell her you’re into that.",
            "A supermassive black hole.",
            "Learning the hard way that you shouldn't microwave metal.",
            "The tiny shred of hope that keeps you going.",
            "An intense need for validation.",
            "The overwhelming desire to punch something cute.",
            "Finally finding Waldo.",
            "An unexpected furry convention.",
            "Your worst nightmare coming true.",
            "Being abducted by aliens and returned because they weren't impressed.",
            "Realizing you’ve been wrong about everything.",
            "An existential crisis in a grocery store.",
            "Trying to explain memes to your grandparents.",
            "Being turned on by something you absolutely shouldn't be.",

        ]

        game['black_card'] = random.choice(black_cards)
        for player in game['players']:
            game['white_cards'][player] = random.sample(white_cards, 7)
        game['responses'] = {}
        game['submitted'] = set()

        
        embed = discord.Embed(title="New Round Started", description="The black card is:", color=discord.Color.dark_grey())
        embed.add_field(name=game["black_card"], value="\u200b", inline=False)
        await ctx.send(embed=embed)
        await player.send(f"Your cards are:")
        for player in game['players']:
            for card in game['white_cards'][player]:
                await player.send(f"{card}")
        await player.send(f"Copy and paste the card you want to play using the command `/play_cah <card>` where `<card>` is the card you want to play.")

    @cah_nsfw.command()
    @commands.is_nsfw()
    async def play(self, ctx, *, response):
        """Play a white card."""
        if ctx.channel.id not in self.games:
            await ctx.send("No game is currently in progress in this channel.")
            return

        game = self.games[ctx.channel.id]
        if ctx.author == game['czar']:
            await ctx.send("The Czar cannot play a card.")
            return

        if ctx.author not in game['players']:
            await ctx.send("You are not in the game.")
            return

        if ctx.author in game['submitted']:
            await ctx.send("You have already submitted a card.")
            return

        if response not in game['white_cards'][ctx.author]:
            await ctx.send("You do not have that card.")
            return

        game['responses'][ctx.author] = response
        game['submitted'].add(ctx.author)

        await ctx.send(f"{ctx.author.mention} has submitted a card.")

        if len(game['submitted']) == len(game['players']) - 1:
            await self.end_round(ctx)
    
    async def end_round(self, ctx):
        game = self.games[ctx.channel.id]
        responses = list(game['responses'].values())
        random.shuffle(responses)

        embed = discord.Embed(title="Submissions", description="Choose the best response #.", color=discord.Color.blue())
        for i, response in enumerate(responses):
            embed.add_field(name=f"Response {i + 1}", value=response, inline=False)

        await ctx.send(embed=embed)
        game['round'] += 1

        def check(m):
            return m.author == game['czar'] and m.content.isdigit() and 1 <= int(m.content) <= len(responses)

        msg = await self.bot.wait_for('message', check=check)
        winner_index = int(msg.content) - 1
        winner = list(game['responses'].keys())[winner_index]

        await ctx.send(f"The Czar has chosen a winner! Congratulations, {winner.mention}!")

        game['czar'] = game['players'][game['round'] % len(game['players'])]
        await self.deal_cah(ctx)

    @cah_nsfw.command()
    async def end(self, ctx):
        """End the current Cards Against Humanity game."""
        if ctx.channel.id not in self.games:
            await ctx.send("No game is currently in progress in this channel.")
            return

        del self.games[ctx.channel.id]
        await ctx.send("The game has been ended.")

    @commands.group()
    async def cah_sfw(self, ctx):
        """Cards Against Humanity commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand passed")

    @cah_sfw.command()
    async def start(self, ctx):
        """Start a SFW Cards Against Humanity game."""
        if ctx.channel.id in self.games:
            await ctx.send("A game is already in progress in this channel.")
            return

        self.games[ctx.channel.id] = {
            'players': [ctx.author],
            'czar': ctx.author,
            'round': 0,
            'black_card': None,
            'white_cards': {},
            'responses': {},
            'submitted': set(),
        }
        await ctx.send(f"{ctx.author.mention} has started a game of Cards Against Humanity! Type `/join_cah` to join the game.")

    @cah_sfw.command()
    async def join(self, ctx):
        """Join a Cards Against Humanity game."""
        if ctx.channel.id not in self.games:
            await ctx.send("No game is currently in progress in this channel. Type `/start_cah` to start a game.")
            return

        game = self.games[ctx.channel.id]
        if ctx.author in game['players']:
            await ctx.send("You are already in the game.")
            return

        game['players'].append(ctx.author)
        await ctx.send(f"{ctx.author.mention} has joined the game!")

    @cah_sfw.command()
    async def deal(self, ctx):
        """Deal cards and start a new round."""
        if ctx.channel.id not in self.games:
            await ctx.send("No game is currently in progress in this channel.")
            return

        game = self.games[ctx.channel.id]
        if ctx.author != game['czar']:
            await ctx.send("Only the current Czar can deal cards.")
            return

        black_cards_sfw = [
            "What never fails to liven up a party? ___",
            "In the future, historians will agree that ___ marked the beginning of a new era.",
            "My life would be perfect if it weren't for ___.",
            "What’s my secret talent? ___",
            "The best part of waking up is ___ in your cup.",
            "What’s the next big thing in fitness? ___",
            "What’s the most awkward thing to bring to a potluck? ___",
            "Why did I get fired this time? ___",
            "What’s the strangest thing I’ve ever seen on public transportation? ___",
            "If I could have any superpower, it would be ___.",
            "My dream vacation involves ___.",
            "What’s my guilty pleasure? ___",
            "The last thing I Googled was ___.",
            "What’s my spirit animal? ___",
            "The key to a successful relationship is ___.",
            "What’s the most useless thing I learned in school? ___",
            "If I could turn back time, I would change ___.",
            "The weirdest dream I ever had was about ___.",
            "What’s the best way to spend a rainy day? ___",
            "What's the secret to a great weekend? ___",
            "How did I ruin my last relationship? ___",
            "My biggest fear is ___.",
            "What always makes me smile? ___",
            "What’s the worst thing that could happen at a family gathering? ___",
            "The most surprising thing I found in my closet was ___.",
            "What's the most ridiculous thing I've ever heard? ___",
            "What did I do last weekend? ___",
            "My go-to karaoke song is about ___.",
            "What’s my favorite childhood memory? ___",
            "What’s the most creative way to solve a problem? ___",
            "If I won the lottery, the first thing I’d buy is ___.",
            "My favorite way to relax is ___.",
            "What’s the secret to a perfect morning routine? ___",
            "What’s the most embarrassing thing I've done in public? ___",
            "My life motto is ___.",
            "If I could swap lives with someone for a day, I’d choose ___.",
            "What’s the best gift I’ve ever received? ___",
            "What’s my worst habit? ___",
            "The first thing I do when I get home is ___.",
            "What’s the most important lesson I’ve learned? ___",
            "If I could live anywhere in the world, I’d choose ___.",
            "My favorite thing to do on a day off is ___.",
            "What’s the strangest food I’ve ever tried? ___",
            "What’s the best advice I've ever been given? ___",
            "My hidden talent is ___.",
            "The most unusual job I’ve ever had was ___.",
            "If I could have dinner with any historical figure, it would be ___.",
            "What’s the best way to start the day? ___",
            "What’s the last thing I would ever give up? ___",
        ]

        white_cards_sfw = [
            "An awkward family photo.",
            "A surprising amount of glitter.",
            "A bucket of puppies.",
            "A cheerful robot.",
            "A magical unicorn.",
            "A piece of toast.",
            "A really cool hat.",
            "A rubber ducky.",
            "A snowman that won’t melt.",
            "A treasure chest.",
            "Accidentally liking an old photo on social media.",
            "Adorable baby animals.",
            "An extra long hug.",
            "An unexpected friendship.",
            "Being a good sport.",
            "Being a good listener.",
            "Being a role model.",
            "Blowing bubbles.",
            "Building a pillow fort.",
            "Bumping into someone you know at the grocery store.",
            "Catching a shooting star.",
            "Catching snowflakes on your tongue.",
            "Complimenting a stranger.",
            "Dancing like nobody's watching.",
            "Drawing with chalk on the sidewalk.",
            "Eating breakfast for dinner.",
            "Finding a lucky penny.",
            "Finding a parking spot right by the entrance.",
            "Finding money in your pocket.",
            "Friendly banter.",
            "Getting a high-five.",
            "Getting a letter in the mail.",
            "Giving the perfect gift.",
            "Going on a spontaneous adventure.",
            "Having a good hair day.",
            "Hearing your favorite song on the radio.",
            "Helping someone in need.",
            "Jumping into a pile of leaves.",
            "Keeping a secret.",
            "Listening to the rain.",
            "Making a new friend.",
            "Making someone smile.",
            "Making s'mores.",
            "Opening a jar on the first try.",
            "Petting a fluffy cat.",
            "Picking flowers.",
            "Planning a surprise party.",
            "Playing a board game.",
            "Playing a musical instrument.",
            "Playing with puppies.",
            "Receiving a compliment.",
            "Remembering someone’s birthday.",
            "Roasting marshmallows.",
            "Seeing a double rainbow.",
            "Sharing a meal with friends.",
            "Sharing a secret.",
            "Sharing your umbrella.",
            "Skipping rocks on a pond.",
            "Smelling fresh-baked cookies.",
            "Spending time with family.",
            "Spontaneous laughter.",
            "Starting a new hobby.",
            "Staying up late to watch the stars.",
            "Successfully parallel parking.",
            "Telling a joke.",
            "Thanking someone for their help.",
            "Trying something new.",
            "Unexpectedly finding a favorite snack.",
            "Volunteering at a charity.",
            "Waking up before your alarm.",
            "Wearing cozy pajamas.",
            "Winking at a stranger.",
            "Writing a thank you note.",
            "Writing in a journal.",
            "Your first day of school.",
            "Your favorite book.",
            "Your favorite movie.",
            "Your favorite teacher.",
            "Your lucky socks.",
            "Your pet's unconditional love."

        ]

        game['black_card'] = random.choice(black_cards_sfw)
        for player in game['players']:
            game['white_cards'][player] = random.sample(white_cards_sfw, 7)
        game['responses'] = {}
        game['submitted'] = set()

        
        embed = discord.Embed(title="New Round Started", description="The black card is:", color=discord.Color.dark_grey())
        embed.add_field(name=game["black_card"], value="\u200b", inline=False)
        await ctx.send(embed=embed)
        await player.send(f"Your cards are:")
        for player in game['players']:
            for card in game['white_cards'][player]:
                await player.send(f"{card}")
        await player.send(f"Copy and paste the card you want to play using the command `/play_cah <card>` where `<card>` is the card you want to play.")

    @cah_sfw.command()
    async def play(self, ctx, *, response):
        """Play a white card."""
        if ctx.channel.id not in self.games:
            await ctx.send("No game is currently in progress in this channel.")
            return

        game = self.games[ctx.channel.id]
        if ctx.author == game['czar']:
            await ctx.send("The Czar cannot play a card.")
            return

        if ctx.author not in game['players']:
            await ctx.send("You are not in the game.")
            return

        if ctx.author in game['submitted']:
            await ctx.send("You have already submitted a card.")
            return

        if response not in game['white_cards'][ctx.author]:
            await ctx.send("You do not have that card.")
            return

        game['responses'][ctx.author] = response
        game['submitted'].add(ctx.author)

        await ctx.send(f"{ctx.author.mention} has submitted a card.")

        if len(game['submitted']) == len(game['players']) - 1:
            await self.end_round(ctx)

    async def end_round(self, ctx):
        game = self.games[ctx.channel.id]
        responses = list(game['responses'].values())
        random.shuffle(responses)

        embed = discord.Embed(title="Submissions", description="Choose the best response #.", color=discord.Color.blue())
        for i, response in enumerate(responses):
            embed.add_field(name=f"Response {i + 1}", value=response, inline=False)

        await ctx.send(embed=embed)
        game['round'] += 1

        def check(m):
            return m.author == game['czar'] and m.content.isdigit() and 1 <= int(m.content) <= len(responses)

        msg = await self.bot.wait_for('message', check=check)
        winner_index = int(msg.content) - 1
        winner = list(game['responses'].keys())[winner_index]

        await ctx.send(f"The Czar has chosen a winner! Congratulations, {winner.mention}!")

        game['czar'] = game['players'][game['round'] % len(game['players'])]
        await self.deal_cah(ctx)

    @cah_sfw.command()
    async def end(self, ctx):
        """End the current Cards Against Humanity game."""
        if ctx.channel.id not in self.games:
            await ctx.send("No game is currently in progress in this channel.")
            return

        del self.games[ctx.channel.id]
        await ctx.send("The game has been ended.")
