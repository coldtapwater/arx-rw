import os
import sys
import time
import subprocess
import git
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class GitMonitorHandler(FileSystemEventHandler):
    def __init__(self, script, repo_path):
        self.script = script
        self.repo_path = repo_path
        self.process = None
        self.repo = git.Repo(self.repo_path)
        self.last_commit = self.repo.head.commit.hexsha
        self.start_bot()

    def start_bot(self):
        if self.process:
            print("Terminating existing bot process...")
            self.process.terminate()
            self.process.wait()  # Wait for the process to actually terminate
        print("Starting bot...")
        self.process = subprocess.Popen([sys.executable, self.script])

    def check_for_updates(self):
        print("Checking for updates...")
        current_branch = self.repo.active_branch
        if current_branch.name != 'master':
            print(f"Currently on branch '{current_branch.name}'. Switching to master...")
            self.repo.git.checkout('master')
        try:
            self.repo.remotes.origin.fetch()
            commits_behind = list(self.repo.iter_commits('master..origin/master'))
            if commits_behind:
                print(f"Found {len(commits_behind)} new commit(s). Pulling updates...")
                self.repo.remotes.origin.pull()
                new_commit = self.repo.head.commit.hexsha
                if new_commit != self.last_commit:
                    self.last_commit = new_commit
                    return True
            else:
                print("Already up to date.")
            return False
        except git.GitCommandError as e:
            print(f"Git error: {e}")
            return False

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.py'):
            print(f"{event.src_path} has changed.")
            if self.check_for_updates():
                print("Updates found. Restarting bot...")
                self.start_bot()
            else:
                print("No updates found. Changes are local.")
                # Optionally restart on local changes:
                # self.start_bot()

if __name__ == "__main__":
    script = 'bot.py'
    repo_path = '.'  # Assumes the script is run from the repository root
    event_handler = GitMonitorHandler(script, repo_path)
    observer = Observer()
    observer.schedule(event_handler, path=repo_path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(60)  # Check for updates every minute
            if event_handler.check_for_updates():
                event_handler.start_bot()
    except KeyboardInterrupt:
        print("Stopping bot and observer...")
        if event_handler.process:
            event_handler.process.terminate()
            event_handler.process.wait()
        observer.stop()
    observer.join()