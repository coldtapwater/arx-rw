import aiohttp
import json
import os
from dotenv import load_dotenv

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

async def search_unix_rice(query: str):
    """
    Search for riced UNIX systems using Google Programmable Search Engine.
    """
    async with aiohttp.ClientSession() as session:
        search_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_CSE_ID,
            'q': f"unix rice {query} site:reddit.com/r/unixporn",
            'num': 5,  # Number of results to return
            'searchType': 'image'  # This ensures we get image results
        }
        async with session.get(search_url, params=params) as response:
            if response.status != 200:
                return json.dumps({"error": f"Search request failed with status {response.status}"})
            
            data = await response.json()
    
    results = []
    for item in data.get('items', []):
        results.append({
            'title': item.get('title', ''),
            'image_url': item.get('link', ''),
            'source_url': item.get('image', {}).get('contextLink', ''),
            'snippet': item.get('snippet', '')
        })
    
    return json.dumps({"results": results})