import os
import sys
import time
import subprocess
import git
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class SingleInstance:
    def __init__(self, pid_file):
        self.pid_file = pid_file
        if os.path.exists(self.pid_file):
            with open(self.pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            if psutil.pid_exists(old_pid):
                print(f"Another instance (PID: {old_pid}) is already running. Exiting.")
                sys.exit(1)
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))

    def __del__(self):
        if os.path.exists(self.pid_file):
            os.unlink(self.pid_file)

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
            self.terminate_bot()
        print("Starting bot...")
        self.process = subprocess.Popen([sys.executable, self.script])

    def terminate_bot(self):
        if self.process:
            try:
                parent = psutil.Process(self.process.pid)
                for child in parent.children(recursive=True):
                    child.terminate()
                parent.terminate()
                gone, alive = psutil.wait_procs([parent] + parent.children(recursive=True), timeout=5)
                for p in alive:
                    p.kill()
            except psutil.NoSuchProcess:
                pass
            self.process = None

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

if __name__ == "__main__":
    pid_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot_monitor.pid')
    single_instance = SingleInstance(pid_file)
    
    script = 'bot.py'
    repo_path = '.'
    event_handler = GitMonitorHandler(script, repo_path)
    observer = Observer()
    observer.schedule(event_handler, path=repo_path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(60)
            if event_handler.check_for_updates():
                event_handler.start_bot()
    except KeyboardInterrupt:
        print("Stopping bot and observer...")
        event_handler.terminate_bot()
        observer.stop()
        observer.join()