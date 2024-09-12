import aiohttp
import json
import os
from dotenv import load_dotenv
from groq import AsyncGroq
load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')

async def search_internet(query: str):
    """
    Perform an internet search using Google Custom Search API and return the top results.
    """
    async with aiohttp.ClientSession() as session:
        search_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_CSE_ID,
            'q': query,
            'num': 5  # Number of results to return
        }
        async with session.get(search_url, params=params) as response:
            if response.status != 200:
                return json.dumps({"error": f"Search request failed with status {response.status}"})
            
            data = await response.json()
    
    results = []
    for item in data.get('items', []):
        results.append({
            'title': item.get('title', ''),
            'url': item.get('link', ''),
            'snippet': item.get('snippet', '')
        })
    
    return json.dumps({"results": results})

async def evaluate_response(user_query: str, ai_response: str):
    """
    Evaluate the AI's response to the user's query.
    Returns: "good", "needs improvement", or "unclear"
    """
    client = AsyncGroq()
    MODEL = 'llama3-groq-70b-8192-tool-use-preview'
    
    prompt = f"""
    Analyze the following AI response to a user query. Evaluate whether the response:
    1. Fully answers the user's question (return "good")
    2. Partially answers the question but needs improvement (return "needs improvement")
    3. Doesn't address the question or is unclear (return "unclear")

    User Query: {user_query}
    AI Response: {ai_response}

    Return ONLY ONE of these three words: "good", "needs improvement", or "unclear".
    """

    response = await client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=MODEL,
        max_tokens=1,  # We only need a single word response
        temperature=0.2  # Lower temperature for more consistent outputs
    )

    evaluation = response.choices[0].message.content.strip().lower()
    
    # Ensure we only return one of the three expected outputs
    if evaluation not in ["good", "needs improvement", "unclear"]:
        evaluation = "needs improvement"  # Default to this if unexpected output

    return evaluation