import os
import sys
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RestartBotHandler(FileSystemEventHandler):
    def __init__(self, script):
        self.script = script
        self.process = None
        self.start_bot()

    def start_bot(self):
        if self.process:
            print("Terminating existing bot process...")
            self.process.terminate()
            self.process.wait()  # Wait for the process to actually terminate

        print("Starting bot...")
        self.process = subprocess.Popen([sys.executable, self.script])

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.py'):
            print(f"{event.src_path} has changed. Restarting bot...")
            self.start_bot()

if __name__ == "__main__":
    script = 'bot.py'
    event_handler = RestartBotHandler(script)
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping bot and observer...")
        if event_handler.process:
            event_handler.process.terminate()
            event_handler.process.wait()
        observer.stop()
    observer.join()