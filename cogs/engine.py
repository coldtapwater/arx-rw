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
        await self.load_patterns()  # Refresh patterns from the database
        message = message.lower()
        return any(re.search(pattern, message, re.IGNORECASE) for pattern in self.patterns)

class iLBEngineCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv('GROQ_API_KEY')
        self.model_cache = {}
        self.contexts = {}
        self.tools = get_all_tools()
        self.jailbreak_detector = JailbreakDetector()
        self.load_config()

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
            {"role": "system", "content": "You are a routing assistant. Your task is to determine the best model for handling the given query."},
            {"role": "user", "content": f"Query: {query}\nPlease select the most appropriate model from the following options:\n1. gemma2-9b-it\n2. llama-3.1-8b-instant\n3. mixtral-8x7b-32768\n4. llama3-70b-8192\nRespond with only the model name."}
        ]
        response = await self.call_groqcloud_api("gemma-7b-it", router_messages)
        if response and "choices" in response:
            return response["choices"][0]["message"]["content"].strip()
        return "llama3-70b-8192"  # Default to the most capable model if routing fails

    async def dynamic_prompting(self, query: str, context: List[Dict[str, str]]) -> str:
        prompt_messages = [
            {"role": "system", "content": "You are an AI assistant tasked with formulating an effective prompt to answer the user's query. Consider the context provided and create a prompt that will guide the AI to give the best possible answer."},
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
        reflection_prompt = f"Reflect on the following query and initial response:\nQuery: {query}\nInitial Response: {initial_response}\nWhat aspects of the response could be improved or expanded upon?"
        reflection_response = await self.call_groqcloud_api("llama3-70b-8192", [{"role": "user", "content": reflection_prompt}])
        
        if reflection_response and "choices" in reflection_response:
            reflection = reflection_response["choices"][0]["message"]["content"].strip()
            
            improvement_prompt = f"Based on the reflection: {reflection}\nProvide an improved and expanded answer to the original query: {query}"
            improved_response = await self.call_groqcloud_api("llama3-70b-8192", [{"role": "user", "content": improvement_prompt}])
            
            if improved_response and "choices" in improved_response:
                return improved_response["choices"][0]["message"]["content"].strip()
        
        return initial_response  # Fallback to initial response if deep thinking fails

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.bot.user in message.mentions:
            await self.process_mention(message)

    async def process_mention(self, message):
        query = re.sub(r'<@!?[0-9]+>', '', message.content).strip()
        context = self.contexts.get(message.author.id, [])
        
        thinking_message = await message.channel.send("Thinking...")
        
        try:
            routed_model = await self.route_query(query)
            dynamic_prompt = await self.dynamic_prompting(query, context)
            tool_results = await self.execute_tools(query)
            
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": f"{dynamic_prompt}\nAdditional context: {json.dumps(tool_results)}"}
            ]
            
            initial_response = await self.call_groqcloud_api(routed_model, messages)
            if initial_response and "choices" in initial_response:
                initial_answer = initial_response["choices"][0]["message"]["content"].strip()
                final_answer = await self.deep_thinking(query, initial_answer)
                
                await thinking_message.edit(content=final_answer)
                self.update_context(message.author.id, query, final_answer)
            else:
                await thinking_message.edit(content="I'm sorry, I couldn't generate a response. Please try again.")
        except Exception as e:
            await thinking_message.edit(content=f"Oops! Something went wrong. Please try again or contact the developer.\nError: {str(e)}")
            logging.error(f"Error in process_mention: {str(e)}")

    def update_context(self, user_id: int, query: str, response: str):
        if user_id not in self.contexts:
            self.contexts[user_id] = []
        self.contexts[user_id].append({"role": "user", "content": query})
        self.contexts[user_id].append({"role": "assistant", "content": response})
        self.contexts[user_id] = self.contexts[user_id][-10:]  # Keep only last 5 turns

    @commands.command(name='jailbreak2')
    @commands.is_owner()
    async def jailbreak(self, ctx, pattern: str):
        # Add jailbreak pattern to database
        await JailbreakPatterns.create(pattern=pattern)
        await self.jailbreak_detector.load_patterns()
        await ctx.send(f"Jailbreak pattern '{pattern}' added to database.")
        await ctx.send("Jailbreak pattern added.")

    @commands.command(name='clear2')
    @commands.is_owner()
    async def clear(self, ctx):
        # Clear caches and contexts
        self.model_cache.clear()
        self.contexts.clear()
        await ctx.send("Caches and contexts cleared.")

async def setup(bot):
    await bot.add_cog(iLBEngineCog(bot))