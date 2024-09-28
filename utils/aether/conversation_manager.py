import asyncio
import discord
from typing import Dict, List
from .mixture_of_agents import MixtureOfAgents

class ConversationManager:
    def __init__(self, bot: discord.Client, mixture_of_agents: MixtureOfAgents):
        self.bot = bot
        self.mixture_of_agents = mixture_of_agents
        self.queue = asyncio.Queue()
        self.active_conversations: Dict[int, asyncio.Task] = {}
        self.context: Dict[int, List[str]] = {}

    async def add_to_queue(self, message: discord.Message):
        await self.queue.put(message)
        position = self.queue.qsize()
        await message.channel.send(f"You are currently {position} in the queue. Please wait.", ephemeral=True)

    async def process_queue(self):
        while True:
            message = await self.queue.get()
            if message.author.id not in self.active_conversations:
                task = asyncio.create_task(self.handle_conversation(message))
                self.active_conversations[message.author.id] = task
                await task

    async def handle_conversation(self, message: discord.Message):
        try:
            user_id = message.author.id
            if user_id not in self.context:
                self.context[user_id] = []

            # Check for direct character mention
            for character in self.mixture_of_agents.characters:
                if character.name.lower() in message.content.lower():
                    response = await self.mixture_of_agents.handle_direct_mention(
                        character.name, message.content, self.context[user_id]
                    )
                    await self.send_response(message.channel, response)
                    self.context[user_id].extend([message.content, response])
                    return

            # Generate response using MixtureOfAgents
            response_dict = await self.mixture_of_agents.generate_response(
                message.content, self.context[user_id]
            )

            # Send primary response
            await self.send_response(message.channel, response_dict['primary'])
            self.context[user_id].extend([message.content, response_dict['primary']])

            # Send interjection if present
            if 'interjection' in response_dict:
                await asyncio.sleep(2)  # Short delay before interjection
                await self.send_response(message.channel, response_dict['interjection'])
                self.context[user_id].append(response_dict['interjection'])

            # Limit context size
            self.context[user_id] = self.context[user_id][-10:]

        finally:
            del self.active_conversations[user_id]

    async def send_response(self, channel: discord.TextChannel, content: str):
        typing_message = await channel.send(f"{content[0]} is typing...")
        await asyncio.sleep(len(content) * 0.05)  # Simulated typing delay
        await typing_message.edit(content=content)