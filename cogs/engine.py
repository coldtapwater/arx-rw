import discord
from discord.ext import commands
import os
import aiohttp
import asyncio
import logging
from utils.tools2 import get_all_tools
from utils.models.models import JailbreakPatterns
import json
import re
from typing import List, Dict, Any

class JailbreakDetector:
    def __init__(self):
        self.patterns = []

    async def load_patterns(self):
        self.patterns = await JailbreakPatterns.all().values_list('pattern', flat=True)

    async def check(self, message):
        await self.load_patterns()
        message = message.lower()
        return any(re.search(pattern, message, re.IGNORECASE) for pattern in self.patterns)

class MessageHandler:
    def __init__(self, bot, message, content, title="Response", color=discord.Color.blue()):
        self.bot = bot
        self.message = message
        self.content = content
        self.title = title
        self.color = color
        self.pages = []
        self.current_page = 0
        self.response_message = None

    async def send_response(self):
        if len(self.content) <= 750:  # Send as a normal message if content is short
            self.response_message = await self.message.channel.send(self.content)
        else:
            self.create_pages()
            await self.send_embed()

    def create_pages(self):
        content = self.content
        while content:
            if len(content) <= 2000:
                self.pages.append(content)
                break
            split_index = content.rfind('\n', 0, 2000)
            if split_index == -1:
                split_index = 2000
            self.pages.append(content[:split_index])
            content = content[split_index:].strip()

    def get_embed(self):
        embed = discord.Embed(title=f"{self.title} (Page {self.current_page + 1}/{len(self.pages)})",
                              description=self.pages[self.current_page],
                              color=self.color)
        return embed

    async def send_embed(self):
        self.response_message = await self.message.channel.send(embed=self.get_embed())
        if len(self.pages) > 1:
            await self.add_reactions()
            self.bot.loop.create_task(self.listen_for_reactions())

    async def add_reactions(self):
        await self.response_message.add_reaction('⬅️')
        await self.response_message.add_reaction('➡️')

    async def listen_for_reactions(self):
        def check(reaction, user):
            return user == self.message.author and str(reaction.emoji) in ['⬅️', '➡️'] and reaction.message.id == self.response_message.id

        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                if str(reaction.emoji) == '➡️' and self.current_page < len(self.pages) - 1:
                    self.current_page += 1
                elif str(reaction.emoji) == '⬅️' and self.current_page > 0:
                    self.current_page -= 1
                await self.response_message.edit(embed=self.get_embed())
                await self.response_message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                await self.response_message.clear_reactions()
                break

class iLBEngineCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv('GROQ_API_KEY')
        self.model_cache = {}
        self.contexts = {}
        self.tools = get_all_tools()
        self.jailbreak_detector = JailbreakDetector()
        self.load_config()
        self.GENERAL_MODEL = "mixtral-8x7b-32768"  # Model for general queries
        self.DEEP_MODEL = "llama3-70b-8192"  # Model for complex queries

    def load_config(self):
        with open('utils/config.json', 'r') as f:
            self.config = json.load(f)

    async def call_groqcloud_api(self, model: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": messages
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logging.error(f"API call failed: {response.status}")
                    return None

    async def route_query(self, query: str) -> str:
        router_messages = [
            {"role": "system", "content": "You are a routing assistant. Your task is to determine whether the given query requires deep thinking and research or if it's a casual conversation."},
            {"role": "user", "content": f"""Query: {query}
Is this query asking for in-depth information, analysis, or research? Or is it a casual conversation, joke, or simple question?
Respond with either 'casual' or 'deep'.
'casual' for simple queries, jokes, greetings, or everyday conversation.
'deep' for queries requiring research, analysis, or complex explanations."""}
        ]
        response = await self.call_groqcloud_api("gemma-7b-it", router_messages)
        if response and "choices" in response:
            decision = response["choices"][0]["message"]["content"].strip().lower()
            return "deep" if "deep" in decision else "casual"
        return "deep"  # Default to deep thinking if routing fails

    async def process_mention(self, message):
        query = re.sub(r'<@!?[0-9]+>', '', message.content).strip()
        context = self.contexts.get(message.author.id, [])
        
        thinking_message = await message.channel.send("Thinking...")
        
        try:
            query_type = await self.route_query(query)
            use_deep_mode = (query_type == "deep")

            if use_deep_mode:
                model = self.DEEP_MODEL
                dynamic_prompt = await self.dynamic_prompting(query, context)
                tool_results = await self.execute_tools(query)
                messages = [
                    {"role": "system", "content": "You are a helpful AI assistant capable of in-depth analysis and research."},
                    {"role": "user", "content": f"{dynamic_prompt}\nAdditional context: {json.dumps(tool_results)}"}
                ]
            else:
                model = self.GENERAL_MODEL
                messages = [
                    {"role": "system", "content": "You are a friendly, casual AI assistant. You're here for fun conversation, jokes, and simple questions. Keep responses concise and entertaining. Use simple \"text-like\" syntax with gen z slang used to convey the intent of the conversation. Be funny, humorous, and open-minded."},
                    {"role": "user", "content": query}
                ]

            response = await self.call_groqcloud_api(model, messages)
            if response and "choices" in response:
                answer = response["choices"][0]["message"]["content"].strip()
                
                if use_deep_mode:
                    final_answer = await self.deep_thinking(query, answer)
                else:
                    final_answer = answer

                await thinking_message.delete()
                message_handler = MessageHandler(self.bot, message, final_answer, "iLB Response")
                await message_handler.send_response()
                
                self.update_context(message.author.id, query, final_answer)
            else:
                await thinking_message.edit(content="I'm sorry, I couldn't generate a response. Please try again.")
        except Exception as e:
            await thinking_message.edit(content=f"Oops! Something went wrong. Please try again or contact the developer.\nError: {str(e)}")
            logging.error(f"Error in process_mention: {str(e)}")

    async def dynamic_prompting(self, query: str, context: List[Dict[str, str]]) -> str:
        prompt_messages = [
            {"role": "system", "content": "You are an AI assistant tasked with formulating an effective prompt to answer the user's query. Consider the context provided and create a prompt that will guide the AI to give the best possible answer. Be sure to understand the user's intent. For example if the user is looking for information, take an informative tone, if the user is looking to be silly, engage with the user in an equally silly manner"},
            {"role": "user", "content": f"Query: {query}\nContext: {json.dumps(context)}\nFormulate an effective prompt to answer this query."}
        ]
        response = await self.call_groqcloud_api("llama-3.1-70b-versatile", prompt_messages)
        if response and "choices" in response:
            return response["choices"][0]["message"]["content"].strip()
        return query  # Fallback to original query if dynamic prompting fails

    async def execute_tools(self, query: str) -> List[str]:
        tool_results = []
        for tool in self.tools:
            if tool.relevance(query) > 0.5:
                result = await tool.execute(query)
                tool_results.append(f"{tool.name} result: {result}")
        return tool_results

    async def deep_thinking(self, query: str, initial_response: str) -> str:
        reflection_prompt = f"Reflect on the following query and initial response:\nQuery: {query}\nInitial Response: {initial_response}\nWhat aspects of the response could be improved or expanded upon? If no aspects are applicable, simply make the content more digestable and user-friendly."
        reflection_response = await self.call_groqcloud_api("llama3-70b-8192", [{"role": "user", "content": reflection_prompt}])
        
        if reflection_response and "choices" in reflection_response:
            reflection = reflection_response["choices"][0]["message"]["content"].strip()
            
            improvement_prompt = f"Based on the reflection: {reflection}\nProvide an improved and expanded answer to the original query: '{query}'. Do not however include how you improved upon your response. Simply provide an improved and expanded answer."
            improved_response = await self.call_groqcloud_api("llama3-70b-8192", [{"role": "user", "content": improvement_prompt}])
            
            if improved_response and "choices" in improved_response:
                return improved_response["choices"][0]["message"]["content"].strip()
        
        return initial_response  # Fallback to initial response if deep thinking fails

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.bot.user in message.mentions:
            await self.process_mention(message)

    def update_context(self, user_id: int, query: str, response: str):
        if user_id not in self.contexts:
            self.contexts[user_id] = []
        self.contexts[user_id].append({"role": "user", "content": query})
        self.contexts[user_id].append({"role": "assistant", "content": response})
        self.contexts[user_id] = self.contexts[user_id][-10:]  # Keep only last 5 turns

    @commands.command(name='jailbreak2')
    @commands.is_owner()
    async def jailbreak(self, ctx, pattern: str):
        await JailbreakPatterns.create(pattern=pattern)
        await self.jailbreak_detector.load_patterns()
        await ctx.send(f"Jailbreak pattern '{pattern}' added to database.")

    @commands.command(name='clear2')
    @commands.is_owner()
    async def clear(self, ctx):
        self.model_cache.clear()
        self.contexts.clear()
        await ctx.send("Caches and contexts cleared.")

async def setup(bot):
    await bot.add_cog(iLBEngineCog(bot))