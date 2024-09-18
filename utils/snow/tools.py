import aiohttp
import base64
import json
from PIL import Image, ImageOps
import io
import os
from github import Github
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional
import instructor
from groq import AsyncGroq

class SearchResult(BaseModel):
    title: str
    snippet: str
    link: str

class WebSearchResults(BaseModel):
    results: List[SearchResult]

class WebSearchTool:
    def __init__(self, groq_client: AsyncGroq):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.search_engine_id = os.getenv('GOOGLE_CSE_ID')
        self.groq_client = groq_client

    async def execute(self, query: str) -> WebSearchResults:
        params = {
            'q': query,
            'key': self.api_key,
            'cx': self.search_engine_id,
            'num': 5
        }
        url = 'https://www.googleapis.com/customsearch/v1'
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                results = [
                    SearchResult(
                        title=item['title'],
                        snippet=item['snippet'],
                        link=item['link']
                    )
                    for item in data.get('items', [])
                ]
                return WebSearchResults(results=results)

    async def get_html_summary(self, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()
                summary = await summarize_html(html, self.groq_client)
                return summary

class GitHubRepo(BaseModel):
    full_name: str
    description: Optional[str]
    url: str
    stars: int

class GitHubSearchResults(BaseModel):
    repos: List[GitHubRepo]

class GitHubSearchTool:
    def __init__(self):
        self.github = Github(os.getenv('GITHUB_TOKEN'))

    async def execute(self, query: str) -> GitHubSearchResults:
        repos = self.github.search_repositories(query, 'stars', 'desc')
        results = [
            GitHubRepo(
                full_name=repo.full_name,
                description=repo.description,
                url=repo.html_url,
                stars=repo.stargazers_count
            )
            for repo in repos[:5]
        ]
        return GitHubSearchResults(repos=results)

class ImageAnalysisResult(BaseModel):
    description: str

class ImageRecognitionTool:
    def __init__(self, groq_client: AsyncGroq):
        self.groq_client = groq_client
        self.model = "llava-v1.5-7b-4096-preview"

    async def execute(self, image_url: str) -> ImageAnalysisResult:
        prompt = """
        Analyze the image in detail. Follow these steps:
        1. Describe the main subject(s) of the image.
        2. List all objects you can see in the image.
        3. Describe the colors present in the image.
        4. Describe the setting or background.
        5. Note any text visible in the image.
        6. Describe any actions or interactions happening in the image.
        7. Mention the overall mood or atmosphere of the image.
        
        Be specific and accurate. If you're unsure about any detail, say so rather than guessing.
        """

        response = await self.groq_client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        return ImageAnalysisResult(description=response.choices[0].message.content)

class LaTeXRenderingTool:
    def __init__(self):
        self.base_url = "https://latex.codecogs.com/png.latex?"

    async def execute(self, latex: str) -> str:
        encoded_latex = aiohttp.helpers.quote(latex)
        image_url = f"{self.base_url}{encoded_latex}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    return base64.b64encode(image_data).decode('utf-8')
                else:
                    raise Exception(f"Failed to render LaTeX. Status: {response.status}")

async def summarize_html(html: str, groq_client: AsyncGroq) -> str:
    text = html.replace('<', ' <').replace('>', '> ').strip()
    
    response = await groq_client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": "You are an AI assistant tasked with summarizing web page content."},
            {"role": "user", "content": f"Please summarize the following web page content in a concise manner:\n\n{text[:4000]}"}
        ],
        max_tokens=300
    )
    return response.choices[0].message.content

def get_all_tools(groq_client: AsyncGroq):
    return [
        WebSearchTool(groq_client),
        GitHubSearchTool(),
        ImageRecognitionTool(groq_client),
        LaTeXRenderingTool()
    ]