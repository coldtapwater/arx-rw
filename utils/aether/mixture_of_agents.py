import random
from typing import List, Dict
from groq import AsyncGroq
from .character_agent import CharacterAgent

class MixtureOfAgents:
    def __init__(self, characters: List[CharacterAgent], llm: AsyncGroq):
        self.characters = characters
        self.llm = llm

    async def route_query(self, query: str, context: List[str]) -> CharacterAgent:
        # Use the LLM to determine the most appropriate character
        prompt = self._create_routing_prompt(query, context)
        response = await self.llm.chat.completions.create(
            model="llama3-70b-8192",  # You can adjust the model as needed
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": query}
            ],
            max_tokens=50
        )
        character_name = response.choices[0].message.content.strip()
        return next((char for char in self.characters if char.name.lower() == character_name.lower()), random.choice(self.characters))

    def _create_routing_prompt(self, query: str, context: List[str]) -> str:
        character_descriptions = "\n".join([f"{char.name}: {', '.join(char.traits)} - Specialties: {', '.join(char.specialties)}" for char in self.characters])
        return f"""Given the following query and context, determine which character would be best suited to respond.
        Characters:
        {character_descriptions}

        Recent conversation context: {' '.join(context[-5:])}

        Respond with only the name of the most appropriate character."""

    async def generate_response(self, query: str, context: List[str]) -> Dict[str, str]:
        primary_character = await self.route_query(query, context)
        primary_response = await primary_character.generate_response(query, context)
        
        # Determine if there should be an interjection
        if random.random() < 0.3:  # 30% chance of interjection
            secondary_character = random.choice([char for char in self.characters if char != primary_character])
            interjection = await secondary_character.generate_response(query, context + [primary_response])
            return {
                "primary": f"{primary_character.emoji}: {primary_response}",
                "interjection": f"{secondary_character.emoji} wants to add: {interjection}"
            }
        else:
            return {
                "primary": f"{primary_character.emoji}: {primary_response}"
            }

    async def handle_direct_mention(self, character_name: str, query: str, context: List[str]) -> str:
        character = next((char for char in self.characters if char.name.lower() == character_name.lower()), None)
        if character:
            response = await character.generate_response(query, context)
            return f"{character.emoji} {character.name}: {response}"
        else:
            return "I'm sorry, I couldn't find that character."