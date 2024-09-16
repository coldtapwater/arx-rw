import aiohttp
import asyncio
import base64
import re
from PIL import Image, ImageOps
import io
import os
from github import Github
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import sympy
from sympy.parsing.latex import parse_latex
from urllib import parse

class Tool:
    def __init__(self, name):
        self.name = name

    async def execute(self, query):
        raise NotImplementedError

    def relevance(self, query):
        raise NotImplementedError

class WebSearchTool(Tool):
    def __init__(self):
        super().__init__("Web Search")
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.search_engine_id = os.getenv('GOOGLE_CSE_ID')

    async def execute(self, query):
        async with aiohttp.ClientSession() as session:
            params = {
                'q': query,
                'key': self.api_key,
                'cx': self.search_engine_id,
                'num': 5  # Limit to 5 results
            }
            url = 'https://www.googleapis.com/customsearch/v1'
            async with session.get(url, params=params) as response:
                data = await response.json()
                results = []
                for item in data.get('items', []):
                    results.append(f"Title: {item['title']}\nSnippet: {item['snippet']}\nLink: {item['link']}")
                return results

    def relevance(self, query):
        return 0.8 if any(keyword in query.lower() for keyword in ['search', 'find', 'look up']) else 0.5

class GitHubSearchTool(Tool):
    def __init__(self):
        super().__init__("GitHub Search")
        self.github = Github(os.getenv('GITHUB_TOKEN'))

    async def execute(self, query):
        loop = asyncio.get_event_loop()
        repos = await loop.run_in_executor(None, self.github.search_repositories, query, 'stars', 'desc')
        results = []
        for repo in repos[:5]:
            results.append(f"{repo.full_name}: {repo.description}")
        return results

    def relevance(self, query):
        return 0.9 if any(keyword in query.lower() for keyword in ['github', 'repository', 'code']) else 0.3

class ImageRecognitionTool(Tool):
    def __init__(self):
        super().__init__("Image Recognition")
        self.api_key = os.getenv('GROQ_API_KEY')
        self.model = "llava-v1.5-7b-4096-preview"

    async def execute(self, image_url: str) -> str:
        async with aiohttp.ClientSession() as session:
            # Download the image
            async with session.get(image_url) as response:
                image_data = await response.read()
            
            # Encode the image
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare the API request
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{encoded_image}"
                                }
                            },
                            {
                                "type": "text",
                                "text": "Describe this image in detail. Include information about what you see, the setting, any activities or objects, and the overall mood or atmosphere of the image."
                            }
                        ]
                    }
                ],
                "max_tokens": 300
            }
            
            # Make the API call
            async with session.post(url, headers=headers, json=payload) as response:
                result = await response.json()
                
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
                else:
                    return "Sorry, I couldn't analyze the image."

    def relevance(self, query):
        image_keywords = ['image', 'picture', 'photo', 'img', 'pic', 'photograph']
        return 0.9 if any(keyword in query.lower() for keyword in image_keywords) else 0.2

class LaTeXRenderingTool(Tool):
    def __init__(self):
        super().__init__("LaTeX Rendering")
        self.session = aiohttp.ClientSession()
        self.START_CODE_BLOCK_RE = re.compile(r"^((```(la)?tex)(?=\s)|(```))")

    def cleanup_code_block(self, content):
        if content.startswith("```") and content.endswith("```"):
            return self.START_CODE_BLOCK_RE.sub("", content)[:-3]
        return content.strip("` \n")

    async def execute(self, equation):
        base_url = "https://latex.codecogs.com/gif.latex?%5Cbg_white%20%5CLARGE%20"
        equation = self.cleanup_code_block(equation)
        equation = parse.quote(equation)
        url = f"{base_url}{equation}"
        
        try:
            async with self.session.get(url) as r:
                image_data = await r.read()
            image = Image.open(io.BytesIO(image_data)).convert("RGBA")
            image = ImageOps.expand(image, border=10, fill="white")
            
            image_file_object = io.BytesIO()
            image.save(image_file_object, format="png")
            image_file_object.seek(0)
            
            # Convert to base64 for easy transmission
            base64_image = base64.b64encode(image_file_object.getvalue()).decode('utf-8')
            return f"data:image/png;base64,{base64_image}"
        except Exception as e:
            return f"Error rendering LaTeX: {str(e)}"

    def relevance(self, query):
        return 0.9 if '\\' in query or '$' in query or 'latex' in query.lower() else 0.1

    async def close(self):
        await self.session.close()

class PythonEvaluationTool(Tool):
    def __init__(self):
        super().__init__("Python Evaluation")

    async def execute(self, code):
        try:
            # Set up a secure environment
            allowed_modules = {'math', 'random', 'datetime'}
            restricted_builtins = {
                '__import__': lambda name, *args: __import__(name, *args) if name in allowed_modules else None
            }
            
            # Add safe builtins
            for name in __builtins__:
                if name not in ['eval', 'exec', 'compile', 'open', '__import__']:
                    restricted_builtins[name] = getattr(__builtins__, name)
            
            # Set up globals for execution
            safe_globals = {'__builtins__': restricted_builtins}
            
            # Execute the code
            exec(code, safe_globals)
            
            # Capture the output
            output = safe_globals.get('_output_', 'No output')
            
            return output
        except Exception as e:
            return f"Error executing Python code: {str(e)}"

    def relevance(self, query):
        return 0.9 if any(keyword in query.lower() for keyword in ['python', 'code', 'script']) else 0.3

def get_all_tools():
    return [
        WebSearchTool(),
        GitHubSearchTool(),
        ImageRecognitionTool(),
        LaTeXRenderingTool(),
        PythonEvaluationTool()
    ]