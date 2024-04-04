import os
import time
import threading
from enum import Enum
from pathlib import Path
from openai import OpenAI
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

DIRECTORY_TO_WATCH = Path(
    r"C:\Users\lucar\Documents\Projects\QuantifiedSelf\src\Example Vault"
)
EMBEDDING_DIRECTORY = DIRECTORY_TO_WATCH / "Embeddings"


class Watcher:


    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, str(DIRECTORY_TO_WATCH), recursive=True)
        self.observer.start()
        try:
            while True:
                pass
        except:
            self.observer.stop()
            print("Observer Stopped")


class Handler(FileSystemEventHandler):
    def __init__(self):
        self.client = OpenAI()
        self.debounce_delay = 0.1 
        self.debounce_timer = None

        self.COMMANDS = {
            '/rename': self.rename, 
            '/rewrite': self.rewrite, 
            '/c-tags': self.create_tags, 
            '/c-links': self.create_links,
            '/embed': self.embed
        }

    def on_modified(self, event):
        if self.debounce_timer is not None:
            self.debounce_timer.cancel()

        self.debounce_timer = threading.Timer(self.debounce_delay, self.process_modified, args=(event,))
        self.debounce_timer.start()

    def process_modified(self, event):
        if not event.is_directory:
            with open(event.src_path, "r") as f:
                contents = f.read()
        elif event.is_directory:
            return
        
        if '/rename' in contents:
            pass
        if '/rewrite' in contents:
            pass
        if '/c-tags' in contents:
            tags = self.create_tags(contents, 3)
            tag_index = contents.find('tags:')
            contents = contents[:tag_index + 6] + tags + contents[tag_index + 6:]
        if '/c-links' in contents:
            pass
        if '/embed' in contents:
            embedding = self.embed(contents)
            with open(EMBEDDING_DIRECTORY / Path(event.src_path).name, 'w') as f:
                f.write(', '.join(str(x) for x in embedding))
            

        for command in self.COMMANDS.keys():
            if command in contents:
                print(f"Found '{command}' tag in {event.src_path}")

                with open(event.src_path, "w") as f:
                    f.write(self.remove_tag(command, contents))


    def remove_tag(self, tag, contents):
        return contents.replace(tag, '')
    
    def rename(self, contents) -> str:
        print("Renaming file...")
        pass

    def rewrite(self, contents) -> str:
        print("Rewriting file...")
        pass

    def create_tags(self, contents: str, n: int) -> list[str]:
        print("Creating tags...")
        response = self.client.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=[
                {"role": "user", "content": f"Output {n} tags (space delimited, snake case) for my note: {contents}"}
            ]
        )

        return response.choices[0].message.content

    def create_links(self, contents) -> list[str]:
        print("Creating links...")
        pass

    def embed(self, contents) -> list[float]:
        print("Embedding text...")
        response = self.client.embeddings.create(
            input=contents,
            model="text-embedding-3-small"
        )

        return response.data[0].embedding
