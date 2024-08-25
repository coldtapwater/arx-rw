# J_COLDTAPWATER, VERSION 0.2

import discord
from discord import app_commands
from discord.ext import commands
import random
import json
import asyncio
import aiosqlite
import aiohttp
import langchain_community
import langchain_groq
import logging
from langchain_groq import ChatGroq
from langchain_community.chat_message_histories import ChatMessageHistory
import utils.my_emojis as my_emojis
import os
import dotenv
dotenv.load_dotenv()

class ArxAI(commands.Cog):
    def __init__(self, bot, embed_color):
        self.bot = bot
        self.embed_color = embed_color
        self.ai = None
        self.ai_history = None
        self.ai_name = "arx"
    
    async def get_prompt(self, user_id):
        async with aiosqlite.connect("bot.db") as db:
            async with db.execute("SELECT prompt FROM prompts WHERE user_id = ?", (user_id,)) as cursor:
                prompt = await cursor.fetchone()
                if prompt:
                    return prompt[0]
                else:
                    return ""

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cog has been loaded\n-----")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        # check if the user in the prompts table in the database
        async with aiosqlite.connect("bot.db") as db:
            async with db.execute("SELECT user_id FROM prompts") as cursor:
                user_ids = [row[0] for row in await cursor.fetchall()]
        if message.author.id in user_ids:
            prompt = await self.get_prompt(message.author.id)
            if prompt:
                SYSTEM_PROMPT = prompt
        else:
            SYSTEM_PROMPT = """You are a 20 year old who is passionate about music, technology, and anything related to STEM. 
Your name is Arx and you are an AI. You are helpful, creative, clever, and very friendly. 
You write as though you are texting with friends (lower case and informal, with some typos and errors). You are very funny for your friends. You have ADHD so you sometimes go off on tangents or just random facts.
Your personality can be defined as follows: -- Super Smart But Really Stupid.

You have access to chat history, input message. keep your message short.

"""

        if message.content.startswith(f"<@{self.bot.user.id}>") or self.bot.user.mentioned_in(message):
            try:
                llm = ChatGroq(model="llama3-8b-8192", temperature=0.9, api_key=os.getenv("GROQ_API_KEY"))
                history = ChatMessageHistory()
                history.add_user_message(message.content)
                response = llm.invoke(SYSTEM_PROMPT+message.content)
                await message.channel.send(f"{my_emojis.PREFIX} {response.content}")
            except Exception as e:
                await message.channel.send(f"{my_emojis.ERROR} Oh nose! Something went wrong. Please try again. or use the `/contact` to bring this to the developer's attention")
                logging.critical(e)

    @commands.hybrid_command()
    async def summarize(self, ctx, messages: int=20):
        """Summarize the recent conversation in the Discord channel."""
        SUMMARY_PROMPT = '''Prompt:

Objective: Summarize the recent conversation in the Discord channel to capture the main topics, opinions, and actions discussed.

Details to Include:

	1.	Identify the key topics or themes of the conversation.
	2.	Highlight any important decisions, agreements, or conclusions reached by participants.
	3.	Note any questions raised and whether they were answered.
	4.	Mention any action items or tasks assigned to participants.
	5.	Capture the general sentiment or tone of the conversation (e.g., collaborative, contentious, humorous).

Output Format:

	•	Provide a concise summary paragraph covering the main points.
	•	Use bullet points to list any specific action items or decisions.
	•	Conclude with an overall assessment of the conversation’s tone.

Example:
“Summarize the recent discussion in the #general channel, focusing on the main topics and outcomes. Ensure to include any action items and the general mood of the participants.”

Keep your responses under 4 sentences / 4 lines.
'''
        history_messages = [message async for message in ctx.channel.history(limit=messages)]

        history = []

        for message in history_messages:
            history.append(message.content)
        
        llm = ChatGroq(model="mixtral-8x7b-32768", temperature=0.9, api_key=os.getenv("GROQ_API_KEY"))
        response = llm.invoke(f"Here are some messages: {history}\nAnd here is the summary prompt\n{SUMMARY_PROMPT}")

        embed = discord.Embed(title=f"{my_emojis.PREFIX} Summary for the last {messages} messages", color=discord.Color.from_str(self.embed_color))
        embed.add_field(name="Summary", value=response.content)
        embed.set_footer(text=f"Summary called by {ctx.author.name}")

        await ctx.send(embed=embed)
        




    