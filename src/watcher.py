import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from models import Note, Tag, note_tags, note_links
from database_client import DbClient

class NoteHandler(FileSystemEventHandler):
    def __init__(self, db_client: DbClient):
        self.db_client = db_client
        self.last_modified = {}
        self.debounce_seconds = 1
        self.src_type = {
            '.md': 'Markdown',
            '': 'Folder'
        }
        self.existing_titles = self.db_client.get_all_titles()
        self.existing_files = self.db_client.get_all_filepaths()
        print(self.existing_files)


    def should_handle_created_event(self, path: Path):
        if path.name.endswith('~') or not path.name.endswith('.md'):
            print('Source path is temporary file or not markdown\n')
            return False

        if str(path) in self.existing_files:
            print('File already in db')
            return False

        if path.name in self.last_modified:
            if time.time() - self.last_modified[path.name] < self.debounce_seconds:
                print('Debounced..\n')
                return False

        self.last_modified[path.name] = time.time()

        print('handle event!\n')
        return True

    def on_created(self, event):
        path = Path(event.src_path)
        print(f'{event.event_type} trigger')

        if self.should_handle_created_event(path):
            print(f'New {self.src_type[path.suffix]} file {path.name} has been created.')
            note = Note(path=str(path), title=path.name)
            self.db_client.add_note(note)
            print('Note added to database')


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

if __name__ == '__main__':
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    user = config['postgres']['user']
    password = config['postgres']['password']
    host = config['postgres']['host']
    database = config['postgres']['database']

    db_client = DbClient(host, database, user, password)
    event_handler = NoteHandler(db_client)
    w = Watcher(event_handler)


