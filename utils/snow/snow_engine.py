import asyncio
import discord
from discord.ext import commands
from groq import AsyncGroq
from typing import List, Dict, Any
from utils.snow.tools import get_all_tools
from utils.snow.config import load_config
from utils.models.models import JailbreakPatterns
import os

class MixtureOfAgents:
    def __init__(self, groq_client: AsyncGroq, config: Dict[str, Any]):
        self.groq_client = groq_client
        self.config = config

    async def process_query(self, query: str, context: List[Dict[str, str]], image_url: str = None) -> str:
        messages = [{"role": "system", "content": self.config['system_prompt']}]
        messages.extend(context)
        
        if image_url:
            messages.append({"role": "user", "content": [
                {"type": "text", "text": query},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]})
        else:
            messages.append({"role": "user", "content": query})

        response = await self.groq_client.chat.completions.create(
            model=self.config['advanced_model'],
            messages=messages
        )
        return response.choices[0].message.content

    async def reflect(self, query: str, initial_response: str, context: List[Dict[str, str]]) -> str:
        reflection_prompt = f"Reflect on the following query and initial response:\nQuery: {query}\nInitial Response: {initial_response}\nWhat aspects of the response could be improved or expanded upon?"
        messages = [{"role": "system", "content": self.config['reflection_prompt']}, {"role": "user", "content": reflection_prompt}]
        
        reflection_response = await self.groq_client.chat.completions.create(
            model=self.config['advanced_model'],
            messages=messages
        )
        reflection = reflection_response.choices[0].message.content

        await asyncio.sleep(15)  # 15-second delay between reflection rounds

        improvement_prompt = f"Based on the reflection: {reflection}\nProvide an improved and expanded answer to the original query: '{query}'. Focus on making the content more digestible for everyone while retaining technical aspects."
        messages = [{"role": "system", "content": self.config['improvement_prompt']}, {"role": "user", "content": improvement_prompt}]
        
        improved_response = await self.groq_client.chat.completions.create(
            model=self.config['relation_model'],
            messages=messages
        )
        return improved_response.choices[0].message.content

class SimpleContextManager:
    def __init__(self, max_contexts: int = 100):
        self.contexts = {}
        self.max_contexts = max_contexts

    def add_context(self, user_id: int, query: str, response: str):
        if user_id not in self.contexts:
            self.contexts[user_id] = []
        self.contexts[user_id].append({"role": "user", "content": query})
        self.contexts[user_id].append({"role": "assistant", "content": response})
        self.contexts[user_id] = self.contexts[user_id][-self.max_contexts:]

    def get_context(self, user_id: int, k: int = 5) -> List[Dict[str, str]]:
        return self.contexts.get(user_id, [])[-k*2:]

class RequestQueue:
    def __init__(self, max_concurrent: int = 1):
        self.queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def put(self, item):
        await self.queue.put(item)

    async def process(self, process_func):
        while True:
            item = await self.queue.get()
            async with self.semaphore:
                await process_func(item)
            self.queue.task_done()

    def start_processing(self, process_func):
        asyncio.create_task(self.process(process_func))

class LlamaGuard:
    def __init__(self, groq_client: AsyncGroq, model: str):
        self.groq_client = groq_client
        self.model = model

    async def check_message(self, content: str) -> bool:
        response = await self.groq_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": content}
            ]
        )
        result = response.choices[0].message.content.lower()
        return result == "safe"

class SnowEngine:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = load_config()
        self.groq_client = AsyncGroq(api_key=os.getenv('GROQ_API_KEY'))
        self.tools = get_all_tools(self.groq_client)
        self.mixture_of_agents = MixtureOfAgents(self.groq_client, self.config)
        self.context_manager = SimpleContextManager()
        self.request_queue = RequestQueue()
        self.llama_guard = LlamaGuard(self.groq_client, self.config['llama_guard_model'])

    async def start(self):
        self.request_queue.start_processing(self.process_message)

    async def process_message(self, message: discord.Message) -> str:
        try:
            is_safe = await self.llama_guard.check_message(message.content)
            if not is_safe:
                return "I'm sorry, but I can't respond to that kind of message."

            query_type = await self.route_query(message.content)
            context = self.context_manager.get_context(message.author.id)

            if query_type == "casual":
                response = await self.process_casual_query(message, context)
            else:
                response = await self.process_deep_query(message, context)

            self.context_manager.add_context(message.author.id, message.content, response)
            return response
        except Exception as e:
            return f"Something went wrong: {e}"

    async def route_query(self, query: str) -> str:
        try:
            response = await self.groq_client.chat.completions.create(
                model="gemma-7b-it",
                messages=[
                    {"role": "system", "content": "You are a routing assistant. Determine if the query requires deep thinking or if it's casual conversation."},
                    {"role": "user", "content": f"Query: {query}\nIs this query asking for in-depth information, analysis, or research? Or is it a casual conversation, joke, or simple question?\nRespond with either 'casual' or 'deep'."}
                ]
            )
            decision = response.choices[0].message.content.strip().lower()
            return "deep" if "deep" in decision else "casual"
        except Exception as e:
            return f"Something went wrong: {e}"

    async def process_casual_query(self, message: discord.Message, context: List[Dict[str, str]]) -> str:
        try:
            response = await self.mixture_of_agents.process_query(message.content, context)
            return self.format_casual_response(response)
        except Exception as e:
            return f"Something went wrong: {e}"

    async def process_deep_query(self, message: discord.Message, context: List[Dict[str, str]]) -> str:
        try:
            initial_response = await self.mixture_of_agents.process_query(message.content, context)
            final_response = await self.mixture_of_agents.reflect(message.content, initial_response, context)
            return self.format_deep_response(final_response)
        except Exception as e:
            return f"Something went wrong: {e}"

    def format_casual_response(self, response: str) -> str:
        return response.lower()

    def format_deep_response(self, response: str) -> str:
        return response

    async def add_jailbreak_pattern(self, pattern: str):
        await JailbreakPatterns.get_or_create(pattern=pattern)
        

    async def clear_caches(self):
        self.context_manager = SimpleContextManager()