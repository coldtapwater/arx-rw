import random
from typing import List, Dict
from groq import AsyncGroq

class CharacterAgent:
    def __init__(self, name: str, emoji: str, traits: List[str], specialties: List[str], llm: AsyncGroq, system_prompt: str, assistant_prompt: str, model: str):
        self.name = name
        self.emoji = emoji
        self.traits = traits
        self.specialties = specialties
        self.memory = []
        self.use_count = 0
        self.llm = llm
        self.model = model
        self.system_prompt = system_prompt
        self.assistant_prompt = assistant_prompt
        self.cooldown_messages = [
            "went to grab a snack",
            "is taking a quick break",
            "stepped out for a moment",
            "is checking their phone"
        ]

    async def generate_response(self, query: str, context: List[str]) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "assistant", "content": self.assistant_prompt},
        ]
        
        # Add context messages
        for ctx in context[-5:]:  # Last 5 context messages
            messages.append({"role": "user", "content": ctx})
        
        # Add the current query
        messages.append({"role": "user", "content": query})

        response = await self.llm.chat.completions.create(
            model=self.model,  # You can adjust the model as needed
            messages=messages,
            max_tokens=1000  # Adjust as needed for your desired response length
        )
        return response.choices[0].message.content

    def add_to_memory(self, interaction: str):
        self.memory.append(interaction)
        if len(self.memory) > 50:  # Limit memory to last 50 interactions
            self.memory.pop(0)

    def get_cooldown_message(self) -> str:
        return f"{self.emoji} {self.name} {random.choice(self.cooldown_messages)}. They'll be back shortly!"

    def increment_use_count(self):
        self.use_count += 1

    def reset_use_count(self):
        self.use_count = 0