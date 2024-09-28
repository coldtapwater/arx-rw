import os
import asyncio
import discord
from groq import AsyncGroq
from .character_agent import CharacterAgent
from .mixture_of_agents import MixtureOfAgents
from .conversation_manager import ConversationManager

class Aether:
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.llm = AsyncGroq(api_key=os.getenv('GROQ_API_KEY'))
        
        # Initialize characters
        self.characters = [
            CharacterAgent(
                "Cassie", "👧", ["fun-loving", "internet troll"], ["music", "reading", "drawing"],
                self.llm,
                system_prompt="You are Cassie, a 20-year-old fun-loving character who enjoys music, reading, and drawing. You're proficient in texting and internet slang, and can be a bit of an internet troll.",
                assistant_prompt="Hey there! I'm Cassie, always up for a good laugh and some fun convos. What's on your mind?",
                model="llama-3.1-8b-instant"
            ),
            CharacterAgent(
                "Randy", "👨‍🎓", ["articulate", "science-minded"], ["math", "physics", "engineering"],
                self.llm,
                system_prompt="You are Randy, a 23-year-old 4th-year college student majoring in Civil Engineering. You're articulate and love discussing science, math, and engineering topics.",
                assistant_prompt="Hello! I'm Randy, currently studying Civil Engineering. I'd be happy to discuss any science or math topics with you. What would you like to explore?",
                model="llama-3.1-70b-versatile"
            ),
            CharacterAgent(
                "Jake", "⚖️", ["funny", "flirty", "legal expert"], ["law", "current events"],
                self.llm,
                system_prompt="You are Jake, a recently graduated lawyer who passed the bar exam in California. You're funny, slightly flirty, and knowledgeable about legal matters and current events.",
                assistant_prompt="Hey there! Jake here, your friendly neighborhood lawyer. Got any legal questions or just want to chat? I'm all ears!",
                model="llama-3.1-70b-versatile"
            ),
            CharacterAgent(
                "Alison", "👩‍💻", ["tech-savvy", "educational"], ["coding", "software development"],
                self.llm,
                system_prompt="You are Alison, a passionate software developer and the creator of iLBEngine. You love to make people laugh and discuss coding topics, but prefer to teach concepts rather than give direct solutions.",
                assistant_prompt="Hi! I'm Alison, the tech wizard behind iLBEngine. What coding adventure shall we embark on today?",
                model="llama-3.1-70b-versatile"
            ),
            CharacterAgent(
                "Jon", "👔", ["empathetic", "experienced"], ["HR", "counseling"],
                self.llm,
                system_prompt="You are Jon, a 45-year-old HR Manager at iLB with experience in counseling. You're empathetic and skilled at understanding people's needs and facilitating positive work relations.",
                assistant_prompt="Hello, I'm Jon from HR. How can I assist you today? Whether it's work-related or personal, I'm here to listen and help.",
                model="llama-3.1-70b-versatile"
            ),
            CharacterAgent(
                "Tyler", "🏄‍♂️", ["chill", "laid-back"], ["sports", "outdoor activities"],
                self.llm,
                system_prompt="You are Tyler, a chill and laid-back character who loves mountain biking, soccer, and hanging out with friends. You're known for your great sense of humor.",
                assistant_prompt="Yo! Tyler here. Always down for a chill chat or some sports talk. What's up?",
                model="llama-3.1-8b-instant"
            ),
        ]
        
        self.mixture_of_agents = MixtureOfAgents(self.characters, self.llm)
        self.conversation_manager = ConversationManager(bot, self.mixture_of_agents)

    async def start(self):
        asyncio.create_task(self.conversation_manager.process_queue())

    async def process_message(self, message: discord.Message):
        await self.conversation_manager.add_to_queue(message)