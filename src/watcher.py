from pathlib import Path
from watchdog.observers import Observer
from handler import Handler


class Watcher:
    def __init__(self, directory_to_watch: Path):
        self.observer = Observer()
        self.directory_to_watch = directory_to_watch

    def run(self):
        event_handler = Handler(self.directory_to_watch)
        self.observer.schedule(event_handler, self.directory_to_watch, recursive=True)
        self.observer.start()
        print(f"Watching {self.directory_to_watch}...")
        try:
            while True:
                pass
        except:
            self.observer.stop()
            print("Observer Stopped")

