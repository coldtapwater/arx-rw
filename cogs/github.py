import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
from github import Github
from github.GithubException import GithubException
import os
from datetime import datetime, timezone
from groq import AsyncGroq

class GitHubUpdates(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_name = "coldtapwater/arx-rw"
        self.channel_id = 1233083109847859330
        self.g = Github(self.github_token)
        self.repo = self.g.get_repo(self.repo_name)
        self.last_commit = {}
        self.check_github_updates.start()
        self.groq_client = AsyncGroq(api_key=os.getenv('GROQ_API_KEY'))

    def cog_unload(self):
        self.check_github_updates.cancel()

    @tasks.loop(minutes=5)  # Check for updates every 5 minutes
    async def check_github_updates(self):
        for branch in self.repo.get_branches():
            try:
                latest_commit = branch.commit
                if branch.name not in self.last_commit or self.last_commit[branch.name].sha != latest_commit.sha:
                    if branch.name in self.last_commit:
                        await self.send_update(branch.name, self.last_commit[branch.name], latest_commit)
                    self.last_commit[branch.name] = latest_commit
            except GithubException as e:
                print(f"Error checking branch {branch.name}: {e}")

    async def send_update(self, branch_name, old_commit, new_commit):
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            print(f"Channel with ID {self.channel_id} not found")
            return

        # Get commit messages
        old_message = old_commit.commit.message
        new_message = new_commit.commit.message

        # Get changed files (limited to top 2)
        changed_files = new_commit.files[:2]
        files_info = "\n".join([f"{file.filename} ({file.status})" for file in changed_files])

        # Generate AI description
        ai_description = await self.generate_ai_description(old_message, new_message, files_info)

        # Create embed
        embed = discord.Embed(
            title=f"New Commit on {branch_name}",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Commit Message", value=new_message, inline=False)
        embed.add_field(name="Changed Files", value=files_info or "No files changed", inline=False)
        embed.add_field(name="AI Generated Update", value=ai_description, inline=False)
        embed.set_footer(text=f"Branch: {branch_name}")

        await channel.send(embed=embed)

    async def generate_ai_description(self, old_message, new_message, files_info):
        prompt = f"""
        Compare the following commit messages and changed files, then generate a concise update log:

        Previous commit: {old_message}
        New commit: {new_message}
        Changed files:
        {files_info}

        Please provide a brief, clear description of the changes and their potential impact.
        """

        try:
            response = self.groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes GitHub commits."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating AI description: {e}")
            return "Unable to generate AI description."

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} Cog has been loaded")

async def setup(bot):
    await bot.add_cog(GitHubUpdates(bot))