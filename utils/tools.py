import aiohttp
import json
from duckduckgo_search import DDGS
from github import Github
from googleapiclient.discovery import build
import asyncio
import os
from functools import lru_cache

# Load environment variables
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")

# Initialize clients
github_client = Github(GITHUB_ACCESS_TOKEN)
youtube_client = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def truncate_string(string, max_chars=2000):
    """Truncate a string to a maximum number of characters."""
    return string[:max_chars] if len(string) > max_chars else string

@lru_cache(maxsize=100)
async def search_internet(query: str, images: bool = False):
    """
    Perform an internet search using DuckDuckGo and return the top results.
    """
    async with DDGS() as ddgs:
        if images:
            results = [r for r in ddgs.images(query, max_results=5)]
        else:
            results = [r for r in ddgs.text(query, max_results=5)]
    
    return truncate_string(json.dumps({"results": results}))

@lru_cache(maxsize=100)
async def search_github_repo(query: str):
    """
    Search for a GitHub repository and return relevant information.
    """
    repos = github_client.search_repositories(query)
    results = []
    for repo in repos[:5]:
        try:
            readme = repo.get_readme().decoded_content.decode()
            summary = readme[:500] + "..." if len(readme) > 500 else readme
        except:
            summary = "No README found"
        
        results.append({
            "name": repo.name,
            "owner": repo.owner.login,
            "url": repo.html_url,
            "readme_summary": summary
        })
    
    return truncate_string(json.dumps({"results": results}))

@lru_cache(maxsize=100)
async def search_youtube_channel(query: str):
    """
    Search for a YouTube channel and return relevant information.
    """
    search_response = youtube_client.search().list(
        q=query,
        type='channel',
        part='id,snippet',
        maxResults=5
    ).execute()

    results = []
    for item in search_response.get('items', []):
        channel_id = item['id']['channelId']
        channel_response = youtube_client.channels().list(
            part='snippet,statistics,topicDetails',
            id=channel_id
        ).execute()

        channel_info = channel_response['items'][0]
        results.append({
            "name": channel_info['snippet']['title'],
            "url": f"https://www.youtube.com/channel/{channel_id}",
            "topics": channel_info.get('topicDetails', {}).get('topicCategories', [])
        })
    
    return truncate_string(json.dumps({"results": results}))

@lru_cache(maxsize=100)
async def search_movie(title: str):
    """
    Search for a movie using OMDB API, falling back to internet search if not found.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}") as response:
            if response.status == 200:
                data = await response.json()
                if data.get("Response") == "True":
                    return truncate_string(json.dumps(data))
    
    # If movie not found, fall back to internet search
    return await search_internet(f"movie {title}")

async def search_anime(query: str):
    """
    Search for an anime using the Jikan API.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.jikan.moe/v4/anime?q={query}") as response:
            if response.status == 200:
                data = await response.json()
                return truncate_string(json.dumps(data['data'][:5]))
    return await search_internet(f"anime {query}")

async def search_manga(query: str):
    """
    Search for a manga using the Jikan API.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.jikan.moe/v4/manga?q={query}") as response:
            if response.status == 200:
                data = await response.json()
                return truncate_string(json.dumps(data['data'][:5]))
    return await search_internet(f"manga {query}")

async def search_book(query: str):
    """
    Search for a book using the Google Books API.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://www.googleapis.com/books/v1/volumes?q={query}") as response:
            if response.status == 200:
                data = await response.json()
                return truncate_string(json.dumps(data['items'][:5]))
    return await search_internet(f"book {query}")