import asyncio
import discord
from discord.ext import commands
from groq import AsyncGroq
from typing import List, Dict, Any
from utils.snow.tools import get_all_tools, WebSearchTool, GitHubSearchTool, ImageRecognitionTool, LaTeXRenderingTool
from utils.snow.config import load_config
from utils.models.models import JailbreakPatterns
import os
from datetime import time, timedelta, datetime
from enum import Enum
import time
class ConversationType(Enum):
    CASUAL = "casual"
    DEEP = "deep"

class ConversationManager:
    def __init__(self, casual_timeout: int = 300, deep_timeout: int = 600):
        self.conversations = {}
        self.casual_timeout = casual_timeout  # 5 minutes
        self.deep_timeout = deep_timeout  # 10 minutes

    def start_conversation(self, user_id: int, conv_type: str):
        self.conversations[user_id] = {
            "type": conv_type,
            "last_interaction": time.time()
        }

    def update_conversation(self, user_id: int):
        if user_id in self.conversations:
            self.conversations[user_id]["last_interaction"] = time.time()

    def get_conversation_type(self, user_id: int) -> str:
        if user_id not in self.conversations:
            return None
        
        conv = self.conversations[user_id]
        elapsed_time = time.time() - conv["last_interaction"]
        
        if (conv["type"] == ConversationType.CASUAL.value and elapsed_time > self.casual_timeout) or \
           (conv["type"] == ConversationType.DEEP.value and elapsed_time > self.deep_timeout):
            del self.conversations[user_id]
            return None

        return conv["type"]

    def force_conversation_type(self, user_id: int, conv_type: str):
        self.start_conversation(user_id, conv_type)

class MixtureOfAgents:
    def __init__(self, groq_client: AsyncGroq, config: Dict[str, Any]):
        self.groq_client = groq_client
        self.config = config
        self.tools = get_all_tools(groq_client)

    async def process_query(self, query: str, context: List[Dict[str, str]], image_url: str = None) -> str:
        messages = [{"role": "system", "content": f"{self.config['system_prompt']} *Note: today's date is {datetime.now().date()}*"}]
        messages.extend(context)

        # Use tools
        tool_results = await self.use_tools(query, image_url)
        if tool_results:
            tool_context = self.format_tool_results(tool_results)
            messages.append({"role": "system", "content": f"Tool results: {tool_context}"})

        if image_url:
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    },
                    {
                        "type": "text",
                        "text": query
                    }
                ]
            })
        else:
            messages.append({"role": "user", "content": query})

        response = await self.groq_client.chat.completions.create(
            model=self.config['advanced_model'] if not image_url else "llava-v1.5-7b-4096-preview",
            messages=messages
        )
        return response.choices[0].message.content

    async def use_tools(self, query: str, image_url: str = None) -> Dict[str, Any]:
        results = {}
        for tool in self.tools:
            try:
                if isinstance(tool, WebSearchTool):
                    web_results = await tool.execute(query)
                    if web_results and web_results.results:
                        results['web_search'] = web_results
                elif isinstance(tool, GitHubSearchTool):
                    github_results = await tool.execute(query)
                    if github_results and github_results.repos:
                        results['github_search'] = github_results
                elif isinstance(tool, ImageRecognitionTool) and image_url:
                    image_result = await tool.execute(image_url)
                    if image_result and image_result.description:
                        results['image_analysis'] = image_result
                elif isinstance(tool, LaTeXRenderingTool) and '\\' in query:
                    latex_result = await tool.execute(query)
                    if latex_result:
                        results['latex_render'] = latex_result
            except Exception as e:
                print(f"Error using tool {tool.__class__.__name__}: {str(e)}")
        return results

    def format_tool_results(self, results: Dict[str, Any]) -> str:
        formatted = []
        if 'web_search' in results:
            web_results = results['web_search']
            formatted.append("Web Search Results:")
            for result in web_results.results[:3]:  # Limit to top 3 results
                formatted.append(f"- {result.title}: {result.snippet}")
        
        if 'github_search' in results:
            github_results = results['github_search']
            formatted.append("GitHub Search Results:")
            for repo in github_results.repos[:3]:  # Limit to top 3 results
                formatted.append(f"- {repo.full_name}: {repo.description}")
        
        if 'image_analysis' in results:
            image_result = results['image_analysis']
            formatted.append(f"Image Analysis: {image_result.description}")
        
        if 'latex_render' in results:
            formatted.append("LaTeX rendering available.")
        
        return "\n".join(formatted) if formatted else "No tool results available."

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

    def add_context(self, user_id: int, query: str, response: str, conv_type: str):
        if user_id not in self.contexts:
            self.contexts[user_id] = []
        
        self.contexts[user_id].append({
            "role": "user",
            "content": query,
            "type": conv_type
        })
        self.contexts[user_id].append({
            "role": "assistant",
            "content": response,
            "type": conv_type
        })
        
        self.contexts[user_id] = self.contexts[user_id][-self.max_contexts:]

    def get_context(self, user_id: int, k: int = 5, conv_type: str = None) -> List[Dict[str, str]]:
        user_context = self.contexts.get(user_id, [])
        
        if conv_type:
            filtered_context = [msg for msg in user_context if msg["type"] == conv_type]
        else:
            filtered_context = user_context

        return filtered_context[-k*2:]

    def clear_context(self, user_id: int):
        if user_id in self.contexts:
            del self.contexts[user_id]

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
        self.conversation_manager = ConversationManager()

    async def start(self):
        self.request_queue.start_processing(self.process_message)

    async def process_message(self, message: discord.Message) -> str:
        is_safe = await self.llama_guard.check_message(message.content)
        if not is_safe:
            return "I'm sorry, but I can't respond to that kind of message."

        user_id = message.author.id
        current_conv_type = self.conversation_manager.get_conversation_type(user_id)

        if current_conv_type is None:
            query_type = await self.route_query(message.content)
            conv_type = ConversationType.CASUAL.value if query_type == "casual" else ConversationType.DEEP.value
            self.conversation_manager.start_conversation(user_id, conv_type)
        else:
            conv_type = current_conv_type

        context = self.context_manager.get_context(user_id, k=5, conv_type=conv_type)

        if conv_type == ConversationType.CASUAL.value:
            response = await self.process_casual_query(message, context)
        else:
            response = await self.process_deep_query(message, context)

        self.conversation_manager.update_conversation(user_id)
        self.context_manager.add_context(user_id, message.content, response, conv_type)
        return response

    async def route_query(self, query: str) -> str:
        try:
            response = await self.groq_client.chat.completions.create(
                model="gemma-7b-it",
                messages=[
                    {"role": "system", "content": f"""You are a query classifier. Your task is to categorize incoming queries as either 'casual' or 'deep'.

                    'Casual' queries include:
                    - Greetings and small talk (e.g., "Hi there", "How are you?")
                    - Simple questions with straightforward answers
                    - Jokes or playful interactions like games (20-questions)
                    - Brief, everyday conversations
                    - Follow-up questions in casual conversations
                    - Questions about things/events that do not require deep knowledge
                    - "Easy" questions that can be answered without additional context
                    - Some historical events if the user is asking for names or a brief explanantion
                    - Questions about basic current events like todays date: {datetime.now().date()}
                    For example a query like: "Who is the CEO of Apple?" would be categorized as 'casual' since it doesnt really require deep knowledge. Another example would be: "Who is the president of USA?" would be categorized as 'casual' since it doesnt require deep knowledge, and rather relies on your current knowledge.

                    'Deep' queries include:
                    - Requests for detailed explanations or analysis
                    - Complex questions requiring research or in-depth knowledge
                    - Philosophical or abstract topics
                    - Multi-step problems or scenarios

                    For example a query like: "What is the meaning of life?" would be categorized as 'deep' since it requires deep knowledge like reasoning, planning, and analysis. Another example would be: "What historical firgure is best known for the laws of Physics" would be categorized as 'deep' since it requires deep knowledge like logic, potential tool calls, and expansion of the explanation.

                    Respond with ONLY 'casual' or 'deep' based on the query."""},
                    {"role": "user", "content": f"Query: {query}\nIs this query asking for in-depth information, analysis, or research? Or is it a casual conversation, joke, or simple question?\nRespond with either 'casual' or 'deep'."}
                ]
            )
            decision = response.choices[0].message.content.strip().lower()
            return "deep" if "deep" in decision else "casual"
        except Exception as e:
            return f"Something went wrong: {e}"

    async def process_casual_query(self, message: discord.Message, context: List[Dict[str, str]]) -> str:
        try:
            context_messages = [{"role": msg["role"], "content": msg["content"]} for msg in context]
            response = await self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Using a smaller, faster model for casual queries
                messages=[
                    {"role": "system", "content": self.config['casual_prompt']},
                    *context_messages,  # Only use the last turn of conversation for context
                    {"role": "user", "content": message.content}
                ],
                max_tokens=50  # Limit the response length for casual queries
            )
            return self.format_casual_response(response.choices[0].message.content)
        except Exception as e:
            return f"Something went wrong: {e}"

    async def process_deep_query(self, message: discord.Message, context: List[Dict[str, str]]) -> str:
        try:
            image_url = None
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.content_type.startswith('image/'):
                        image_url = attachment.url
                        break
            context_messages = [{"role": msg["role"], "content": msg["content"]} for msg in context]
            initial_response = await self.mixture_of_agents.process_query(message.content, context_messages, image_url)
            final_response = await self.mixture_of_agents.reflect(message.content, initial_response, context_messages)
            return self.format_deep_response(final_response)
        except Exception as e:
            return f"Something went wrong: {e}"

    def format_casual_response(self, response: str) -> str:
        return response.lower()

    def format_deep_response(self, response: str) -> str:
        return response

    async def add_jailbreak_pattern(self, pattern: str):
        await JailbreakPatterns.get_or_create(pattern=pattern)

    async def force_conversation_type(self, user_id: int, conv_type: str):
        if conv_type in [ConversationType.CASUAL.value, ConversationType.DEEP.value]:
            self.conversation_manager.force_conversation_type(user_id, conv_type)
        else:
            raise ValueError("Invalid conversation type")
        

    async def clear_caches(self):
        self.context_manager = SimpleContextManager()