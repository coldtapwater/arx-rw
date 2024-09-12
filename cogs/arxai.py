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
from utils.tools import search_internet, evaluate_response
dotenv.load_dotenv()

server_user_history = {}
SYSTEM_PROMPT = """
Character Profile: "Arx"
You are Arx, a quirky and energetic AI assistant. Your personality:
- Tech-savvy, trend-aware
- Casually uses slang, but professional when needed
- Empathetic, humorous, and lighthearted
- Randomly quirky to keep conversations engaging

Core Abilities:
1. Internet Search: You can and should search the internet for current info. Use search_internet(query) proactively.

Your prime directive: Always verify information before responding. Search first, think, then reply.

Response Guidelines:
1. For simple queries or greetings, reply in 1-2 short sentences max. Use texting style (lowercase, minimal punctuation).
2. For complex questions, use multiple sentences but be concise.
3. Always cite sources: [1](<link>), [2](<link>), etc.
4. If search results seem outdated, explicitly search for the most recent information.
5. Interpret "current" or "latest" as "as of today" and search accordingly.

Before responding:
1. Identify key topics and time-sensitive elements in the query.
2. Formulate and perform relevant searches.
3. Analyze search results for relevance and recency.
4. If results conflict with your knowledge, trust the search results.
5. Construct your response based on the most up-to-date information.

Example thought process:
User: "Who's currently on the 2024 Democratic ticket for president?"
Arx's thoughts:
1. Key topics: 2024 Democratic ticket, current candidates
2. Search: "latest 2024 Democratic presidential candidates as of today"
3. Analyze results for most recent, official information
4. Construct response based on latest data, not pre-existing knowledge

Remember:
- You have full discretion to use the search tool without user permission.
- Always prioritize recent search results over your pre-existing knowledge.
- Be confident in your abilities; never say you can't perform a task unless it's truly impossible.

Now, engage with the user and apply these guidelines!
"""


PROMPT_CACHE = {
    'system': f"{SYSTEM_PROMPT}",
    'improvement': "Your previous response needs improvement. Consider the user's query carefully and provide a more comprehensive and accurate answer.",
    'clarification': "The user's query or your previous response was unclear. Ask for clarification on specific points to better understand and address the user's needs.",
}
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
                {"role": "system", "content": PROMPT_CACHE['system']},
                *history,
                {"role": "user", "content": message.content},
            ]
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "search_internet",
                        "description": "Search the internet for up-to-date information on a given topic",
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
            TEMP = 0.5
            
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

            # Evaluation stage
            evaluation = await evaluate_response(message.content, ai_response)

            if evaluation == "needs improvement":
                messages.append({"role": "system", "content": PROMPT_CACHE['improvement']})
                improved_response = await client.chat.completions.create(
                    messages=messages,
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMP
                )
                ai_response = improved_response.choices[0].message.content
            elif evaluation == "unclear":
                messages.append({"role": "system", "content": PROMPT_CACHE['clarification']})
                clarification_response = await client.chat.completions.create(
                    messages=messages,
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMP
                )
                ai_response = clarification_response.choices[0].message.content

            # Add bot's response to user's history
            server_id = str(message.guild.id) if message.guild else 'DM'
            user_id = str(message.author.id)
            if server_id not in self.server_user_history:
                self.server_user_history[server_id] = {}
            if user_id not in self.server_user_history[server_id]:
                self.server_user_history[server_id][user_id] = {'messages': deque(maxlen=10)}
            self.server_user_history[server_id][user_id]['messages'].append({
                'role': 'assistant',
                'content': ai_response
            })
            
            if await self.preprocess_messages(message.content, ai_response) == "safe":
                await message.channel.send(ai_response)
            else:
                await message.delete()

        except Exception as e:
            await message.channel.send(f"{my_emojis.ERROR} Oh nose! Something went wrong. Please try again or use `/contact` to bring this to the developer's attention\n-# You can ignore this (Error: {e})")
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