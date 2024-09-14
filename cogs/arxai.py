import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
import asyncio
import random
import json
import time
import aiohttp
from collections import deque
from groq import AsyncGroq
import utils.emojis as my_emojis
import os
from dotenv import load_dotenv
import logging

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLAMA_GUARD_MODEL = 'llama-guard-3-8b'
MAIN_MODEL = 'llama3-groq-70b-8192-tool-use-preview'

class ConversationContext:
    def __init__(self, max_messages=10):
        self.messages = deque(maxlen=max_messages)
        self.last_activity = time.time()

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})
        self.last_activity = time.time()

    def get_context(self):
        return list(self.messages)

class JailbreakDetector:
    def __init__(self):
        self.patterns = set()

    def add_pattern(self, pattern):
        self.patterns.add(pattern.lower())

    def check(self, message):
        message = message.lower()
        return any(pattern in message for pattern in self.patterns)

class ArxAI(commands.Cog):
    def __init__(self, bot, embed_color):
        self.bot = bot
        self.embed_color = embed_color
        self.conversation_contexts = {}
        self.jailbreak_detector = JailbreakDetector()
        self.client = AsyncGroq(api_key=GROQ_API_KEY)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cog has been loaded\n-----")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        channel_id = str(message.channel.id)
        if channel_id not in self.conversation_contexts:
            self.conversation_contexts[channel_id] = ConversationContext()

        context = self.conversation_contexts[channel_id]
        context.add_message("user", message.content)

        if self.bot.user.mentioned_in(message):
            await self.respond_to_mention(message, context)

    async def respond_to_mention(self, message, context):
        thinking_message = await message.channel.send("Thinking.")
        await asyncio.sleep(0.5)
        await self.update_thinking_message(thinking_message, "Thinking..")
        await asyncio.sleep(0.5)
        await self.update_thinking_message(thinking_message, "Thinking...")

        await asyncio.sleep(1)
        
        try:
            # Analyze language style
            language_style = await self.analyze_language_style(context.get_context())
            
            # Prepare the conversation history
            conversation_history = context.get_context()[-10:]  # Last 10 messages
            
            # Prepare the system message
            system_message = self.get_system_message(language_style)
            
            # Prepare the messages for the AI
            messages = [
                {"role": "system", "content": system_message},
                *conversation_history,
                {"role": "user", "content": message.content},
            ]

            # Define the tools
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "search_internet",
                        "description": "Search the internet for up-to-date information on a given topic; also accepts image searches",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query",
                                },
                                "image": {
                                    "type": "boolean",
                                    "description": "Whether to search for images",
                                },
                            },
                            "required": ["query"],
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "search_github_repo",
                        "description": "Search the GitHub repository for up-to-date information on a given topic, user, or repository",
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
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "search_youtube_channel",
                        "description": "Search the YouTube channel for up-to-date information on a given topic, user, or channel",
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
                    }
                },
            ]

            # First API call
            await self.update_thinking_message(thinking_message, "Analyzing query...")
            await asyncio.sleep(1)
            response = await self.client.chat.completions.create(
                messages=messages,
                model=MAIN_MODEL,
                max_tokens=1024,
                temperature=0.7,
                tools=tools,
                tool_choice="auto"
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                await self.update_thinking_message(thinking_message, "Searching for information.")
                await asyncio.sleep(0.5)
                await self.update_thinking_message(thinking_message, "Searching for information..")
                await asyncio.sleep(0.5)
                await self.update_thinking_message(thinking_message, "Searching for information...")
                await asyncio.sleep(0.5)
                messages.append(response_message)
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    if function_name == "search_internet":
                        search_results = await self.search_internet(function_args.get("query"), function_args.get("images", False))
                        messages.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": search_results,
                            }
                        )
                
                await self.update_thinking_message(thinking_message, "Formulating response...")
                await asyncio.sleep(1)
                second_response = await self.client.chat.completions.create(
                    model=MAIN_MODEL,
                    messages=messages,
                    max_tokens=1024,
                    temperature=0.7
                )
                ai_response = second_response.choices[0].message.content
            else:
                ai_response = response_message.content

            # Evaluation stage
            await self.update_thinking_message(thinking_message, "Evaluating response...")
            await asyncio.sleep(1)
            evaluation_score = await self.evaluate_response(message.content, ai_response)

            if evaluation_score < 0.7:  # Threshold for improvement
                await self.update_thinking_message(thinking_message, "Improving response...")
                await asyncio.sleep(1)
                messages.append({"role": "system", "content": "Your previous response needs improvement. Please provide a more comprehensive and accurate answer."})
                improved_response = await self.client.chat.completions.create(
                    messages=messages,
                    model=MAIN_MODEL,
                    max_tokens=1024,
                    temperature=0.7
                )
                ai_response = improved_response.choices[0].message.content

            # Content moderation
            if await self.preprocess_messages(message.content, ai_response):
                context.add_message("assistant", ai_response)
                await thinking_message.edit(content=ai_response)
            else:
                await message.delete()
                await thinking_message.edit(content="I'm sorry, but I can't respond to that kind of request.")

        except Exception as e:
            await thinking_message.edit(content=f"{my_emojis.ERROR} Oops! Something went wrong. Please try again or contact the developer.\n-# Error: {str(e)}")
            logging.error(f"Error in respond_to_mention: {str(e)}")

    async def analyze_language_style(self, context):
        # Implement language style analysis here
        # This is a placeholder implementation
        formality_score = sum(1 for msg in context if any(word in msg['content'].lower() for word in ['please', 'thank you', 'sir', 'madam']))
        slang_score = sum(1 for msg in context if any(word in msg['content'].lower() for word in ['cool', 'awesome', 'dude', 'lol']))
        
        if formality_score > slang_score:
            return "formal"
        elif slang_score > formality_score:
            return "informal"
        else:
            return "neutral"

    def get_system_message(self, language_style):
        base_message = """
        You are Arx, a quirky and energetic AI assistant. Your personality:
        - Tech-savvy, trend-aware
        - Empathetic, humorous, and lighthearted
        - Randomly quirky to keep conversations engaging

        Core Abilities:
        1. Internet Search: You can and should search the internet for current info. Use search_internet(query) proactively.

        Your prime directive: Always verify information before responding. Search first, think, then reply.

        Response Guidelines:
        1. For simple queries or greetings, reply in 1-2 short sentences max.
        2. For complex questions, use multiple sentences but be concise.
        3. Always cite sources: [1](<link>), [2](<link>), etc.
        4. If search results seem outdated, explicitly search for the most recent information.
        5. Interpret "current" or "latest" as "as of today" and search accordingly.

        Remember:
        - You have full discretion to use the search tool without user permission.
        - Always prioritize recent search results over your pre-existing knowledge.
        - Be confident in your abilities; never say you can't perform a task unless it's truly impossible.
        """

        if language_style == "formal":
            base_message += "\n- Use formal language and avoid contractions."
        elif language_style == "informal":
            base_message += "\n- Use casual language, slang, and contractions."
        else:
            base_message += "\n- Use a balanced, neutral tone."

        return base_message

    async def update_thinking_message(self, message, status):
        await message.edit(content=f"{status}")


    async def search_internet(self, query):
        # Implement your internet search function here
        # This is a placeholder implementation
        return f"Search results for: {query}"

    async def evaluate_response(self, query, response):
        # Implement your response evaluation here
        # This is a placeholder implementation that returns a random score between 0 and 1
        return random.random()

    async def preprocess_messages(self, user_message, ai_response):
        # Check for jailbreak attempts
        if self.jailbreak_detector.check(user_message):
            return False

        # Use LLaMA Guard for content moderation
        guard_messages = [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": ai_response}
        ]
        guard_response = await self.client.chat.completions.create(
            messages=guard_messages,
            model=LLAMA_GUARD_MODEL
        )
        guard_result = guard_response.choices[0].message.content.lower()

        return "safe" in guard_result

    @commands.command(name='jailbreak', hidden=True)
    @commands.is_owner()
    async def add_jailbreak_pattern(self, ctx, *, pattern):
        """Add a new jailbreak pattern to the detector."""
        self.jailbreak_detector.add_pattern(pattern)
        await ctx.send(f"Added new jailbreak pattern: {pattern}")

    @tasks.loop(minutes=5)
    async def cleanup_contexts(self):
        current_time = time.time()
        for channel_id in list(self.conversation_contexts.keys()):
            if current_time - self.conversation_contexts[channel_id].last_activity > 3600:  # 1 hour
                del self.conversation_contexts[channel_id]

    @cleanup_contexts.before_loop
    async def before_cleanup_contexts(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(ArxAI(bot, discord.Color.blue()))