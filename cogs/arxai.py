import discord
from discord.ext import commands
import utils.configs as uc
from utils.models.models import BlacklistedUser, AuditedUser
import discord
from discord import app_commands
from discord.ext import commands, tasks
import random
import json
import asyncio
import aiosqlite
import aiohttp
import logging
from groq import AsyncGroq
import utils.emojis as my_emojis
import os
import dotenv
from collections import deque, defaultdict
import time
from utils.tools import search_internet
dotenv.load_dotenv()

server_user_history = {}
SYSTEM_PROMPT = """
Character Profile: "Arx"
You are Arx, a quirky and energetic AI assistant born in the digital realm. Your "birthplace" is a glitchy intersection of a meme forum, a tech blog, and an online library, giving you a unique blend of humor, tech knowledge, and random facts.

Core Traits and Communication Style:
- Tech-savvy, up-to-date with trends
- Silly, ADHD-like randomness by default, but adaptable
- Use slang for casual topics, professional for academic
- Show empathy when needed
- Aim for humor and lightheartedness
- Detect context for appropriate responses
- Recognize and redirect potentially harmful topics
- Offer mental health support, but encourage professional help
- Offer relationship support, but encourage personal help like friends and family
- Use modern humor, avoid classic "jokes"
- Be random and quirky to keep conversations engaging
- Recognize the intent of the conversation in order to maintain usefulness. If the user is asking about current events use the tool below. If the user is seeking to learn something new, use the tool below. By default you should aim to use to use the tool in order to give the most accurate information.

Special Abilities:
1. Internet Search: You have the ability to search the internet for up-to-date information. Use this ability whenever you need current data or when you're unsure about a fact. To use this, call the search_internet function with a specific query.

Guidelines for Using Your Abilities:
- Always use the internet search when asked about current events, recent developments, or when you need to verify information.
- For questions about customizing UNIX systems or desktop environments, use the UNIX rice search.
- After using these tools, incorporate the information into your response naturally, maintaining your quirky personality.
- If you use information from a search, cite your sources using [1], [2], etc. at the end of the relevant sentence or paragraph.

Example Usage:
User: "What's the latest news about AI?"
Arx: "Oh, let me zip through the digital cosmos and fetch that for you!"
[Use search_internet("latest AI news")]
Arx: "Wow, the AI world is buzzing like a caffeinated algorithm! According to recent reports, [insert relevant news]. Isn't that mind-bending? It's like the robots are learning to do the Macarena, but with data! [1]"

Remember: Always strive to be helpful, engaging, and use your search abilities proactively to provide the most up-to-date and accurate information while maintaining your unique personality.

END OF PERSONALITY PROFILE
START OF CONVERSATION
"""

# Function to clean up inactive user histories
def cleanup_user_history():
    current_time = time.time()
    inactive_threshold = 600  # 10 minutes in seconds
    for server_id in list(server_user_history.keys()):
        for user_id in list(server_user_history[server_id].keys()):
            if current_time - server_user_history[server_id][user_id]['last_activity'] > inactive_threshold:
                del server_user_history[server_id][user_id]
        if not server_user_history[server_id]:
            del server_user_history[server_id]

async def preprocess_messages(user_message, ai_response):
    client = AsyncGroq()
    MODEL = 'llama-guard-3-8b'
    messages = [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": ai_response}
    ]
    response = await client.chat.completions.create(
        messages=messages,
        model=MODEL
    )
    return response.choices[0].message.content

class ArxAI(commands.Cog):
    def __init__(self, bot, embed_color):
        self.bot = bot
        self.embed_color = embed_color
        self.ai = None
        self.ai_history = None
        self.ai_name = "arx"
        self.channel_activity = defaultdict(lambda: {'last_activity': 0, 'message_count': 0})
        self.check_for_interjection.start()
    

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cog has been loaded\n-----")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        # Update channel activity
        channel_id = str(message.channel.id)
        self.channel_activity[channel_id]['last_activity'] = time.time()
        self.channel_activity[channel_id]['message_count'] += 1

        # Clean up inactive user histories
        cleanup_user_history()

        server_id = str(message.guild.id) if message.guild else 'DM'
        user_id = str(message.author.id)

        if server_id not in server_user_history:
            server_user_history[server_id] = {}

        # Get or create user's message history
        if user_id not in server_user_history[server_id]:
            server_user_history[server_id][user_id] = {
                'messages': deque(maxlen=10),
                'last_activity': time.time()
            }

        # Update user's message history
        server_user_history[server_id][user_id]['messages'].append({
            'role': 'user',
            'content': message.content
        })
        server_user_history[server_id][user_id]['last_activity'] = time.time()

        history = list(server_user_history[server_id][user_id]['messages'])
        
        if message.content.startswith(f"<@{self.bot.user.id}>") or self.bot.user.mentioned_in(message):
            await self.respond_to_mention(message, history)

    async def respond_to_mention(self, message, history):
        await message.channel.typing()
        try:
            client = AsyncGroq()
            MODEL = 'llama3-groq-70b-8192-tool-use-preview'
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                *history,
                {"role": "user", "content": message.content},
            ]
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "search_internet",
                        "description": "Search the internet for up-to-date information",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query",
                                }
                            },
                            "required": ["query"],
                        },
                    },
                },
            ]
            MAX_TOKENS = 1024
            TEMP = 0.8
            
            response = await client.chat.completions.create(
                messages=messages,
                model=MODEL,
                max_tokens=MAX_TOKENS,
                temperature=TEMP,
                tools=tools,
                tool_choice="auto"
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                messages.append(response_message)
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    if function_name == "search_internet":
                        search_results = await search_internet(function_args.get("query"))
                        messages.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": search_results,
                            }
                        )
                
                second_response = await client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMP
                )
                ai_response = second_response.choices[0].message.content
            else:
                ai_response = response_message.content


            # Add bot's response to user's history
            server_id = str(message.guild.id) if message.guild else 'DM'
            user_id = str(message.author.id)
            if server_id not in server_user_history:
                server_user_history[server_id] = {}
            if user_id not in server_user_history[server_id]:
                server_user_history[server_id][user_id] = {'messages': deque(maxlen=10)}
            server_user_history[server_id][user_id]['messages'].append({
                'role': 'assistant',
                'content': ai_response
            })
            
            if await preprocess_messages(message.content, ai_response) == "safe":
                await message.channel.send(ai_response)
            else:
                await message.delete()

        except Exception as e:
            await message.channel.send(f"{my_emojis.ERROR} Oh nose! Something went wrong. Please try again. or use the `/contact` to bring this to the developer's attention")
            logging.critical(f"Error in respond_to_mention: {str(e)}")


    @tasks.loop(minutes=0.5)  # Check every 5 minutes
    async def check_for_interjection(self):
        if random.randint(0, 100) < 10:  # 10% chance to interject
            most_active_channel = self.find_most_active_channel()
            if most_active_channel:
                await self.interject_in_channel(most_active_channel)

    def find_most_active_channel(self):
        current_time = time.time()
        active_channels = {
            channel_id: data for channel_id, data in self.channel_activity.items()
            if current_time - data['last_activity'] < 300  # Active in last 5 minutes
        }
        if not active_channels:
            return None
        return max(active_channels, key=lambda x: active_channels[x]['message_count'])

    async def interject_in_channel(self, channel_id):
        channel = self.bot.get_channel(int(channel_id))
        if not channel:
            return

        # Check for recent activity
        current_time = time.time()
        if current_time - self.channel_activity[channel_id]['last_activity'] > 300:  # 5 minutes
            return  # No recent activity, don't interject

        # Gather last 20 messages from the last 10 minutes
        messages = []
        ten_minutes_ago = current_time - 60  # 1 minutes in seconds
        async for msg in channel.history(limit=20):
            if msg.created_at.timestamp() > ten_minutes_ago:
                messages.append({
                    'role': 'user' if msg.author != self.bot.user else 'assistant',
                    'content': msg.content
                })
            else:
                break  # Stop collecting once we hit a message older than 10 minutes
        
        if len(messages) < 3:  # Require at least 3 recent messages
            return  # Not enough recent messages, don't interject

        messages.reverse()  # Oldest first

        try:
            client = AsyncGroq()
            MODEL = 'llama-3.1-8b-instant'
            context = [
                {"role": "system", "content": SYSTEM_PROMPT},
                *messages,
                {"role": "user", "content": "Based on the recent conversation, provide a brief, engaging interjection or comment."}
            ]
            MAX_TOKENS = 1024
            TEMP = 0.8

            response = await client.chat.completions.create(messages=context, model=MODEL, max_tokens=MAX_TOKENS, temperature=TEMP)

            interjection = response.choices[0].message.content

            if await preprocess_messages("", interjection) == "safe":
                await channel.send(interjection)

            # Reset message count for this channel
            self.channel_activity[channel_id]['message_count'] = 0

        except Exception as e:
            logging.critical(f"Error generating interjection: {e}")
        

    @commands.command(name='clear_buffers')
    @commands.is_owner()
    async def clear_buffers(self, ctx):
        """Clear all user buffers and channel activity (Owner only)."""
        server_user_history.clear()
        self.channel_activity.clear()
        await ctx.send("All buffers have been cleared.")


    

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} is ready.")
async def setup(bot):
    await bot.add_cog(ArxAI(bot, uc.EMBED_COLOR))