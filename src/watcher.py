import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent 
from llm import LLM
from models import Note, Tag, note_tags, note_links
from database_client import DbClient

class NoteHandler(FileSystemEventHandler):
    def __init__(self, db_client: DbClient, llm_client: LLM):
        self.db_client = db_client
        self.llm_client = llm_client
        self.last_modified = {}
        self.debounce_seconds = 1
        self.src_type = {
            '.md': 'Markdown',
            '': 'Folder'
        }
        self.existing_titles = self.db_client.get_all_titles()
        self.existing_files = self.db_client.get_all_filepaths()
        print(self.existing_files)

    @staticmethod
    def get_file_info(path):
        stat_info = path.stat()

        return {
            'creation_time': stat_info.st_ctime,
            'last_accessed': stat_info.st_atime,
            'file_size': stat_info.st_size
        }

    def is_valid_md_file(self, path: Path) -> bool:
        return path.is_file() and path.name.endswith('.md') and not path.name.endswith('~')

    def is_bouncing(self, event_type: str, path: Path) -> bool:
        key = f'{event_type}_{path.name}'
        if key in self.last_modified:
            if time.time() - self.last_modified[key] < self.debounce_seconds:
                print('Debounced..\n')
                return True

        self.last_modified[key] = time.time()
        return False

    def is_existing_note(self, path: Path) -> bool:
        return str(path) in self.existing_files

    def handle_existing_note(self, path: Path, event_type: str):
        if time.time() - self.get_file_info(path)['creation_time'] < self.debounce_seconds:
            return
        note = self.db_client.get_note_by_path(str(path))
        if note is None:
            note = Note(path=str(path))
        print(f"Handling existing note: {path}")
        print(f"Event type: {event_type}\n")
        with open(path, 'r') as f:
            content = f.read()
        embedding = self.llm_client.embed(content)
        note.title = path.name
        note.content = content
        note.embedding = embedding
        self.db_client.upsert_note(note)


    def handle_new_note(self, path: Path, event_type: str):
        print(f"Handling new note: {path}")
        print(f"Event type: {event_type}\n")

        with open(path, 'r') as f:
            content = f.read()

        embedding = self.llm_client.embed(content)
        note = Note(path=str(path), title=path.name, content=content, embedding=embedding)

        self.db_client.upsert_note(note)
        self.existing_files.append(str(path))
        print(self.existing_files)

    def on_any_event(self, event: FileSystemEvent) -> None:
        path = Path(event.src_path)
        if not self.is_valid_md_file(path) or self.is_bouncing(event.event_type, path):
            return

        if self.is_existing_note(path) and event.event_type == 'modified':
            self.handle_existing_note(path, event.event_type)
        elif not self.is_existing_note(path) and event.event_type == 'created':
            self.handle_new_note(path, event.event_type)

class Watcher:
    def __init__(self, event_handler: FileSystemEventHandler):
        path = Path('C:/LiberVulgaris/LiberVulgaris')
        self.observer = Observer()
        self.observer.schedule(event_handler, path, recursive=True)
        self.observer.start()
        try:
            while self.observer.is_alive():
                self.observer.join(1)
        finally:
            self.observer.stop()
            self.observer.join()

    def on_modified(self):
        pass

