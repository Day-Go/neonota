from pathlib import Path
from models import Note, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import re

NOTE_ROOT = Path(r'C:\LiberVulgaris\LiberVulgaris')

# Create engine and session
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

user = config['postgres']['user']
password = config['postgres']['password']
host = config['postgres']['host']
database = config['postgres']['database']
port = "5432"

engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{database}")
Session = sessionmaker(bind=engine)
session = Session()

# Function to extract links from content
def extract_links(content):
    return re.findall(r'\[\[(.*?)\]\]', content)

if __name__ == '__main__':
    subdirs_to_include = ['All']
    notes_dict = {}  # To store notes temporarily for linking

    for item in NOTE_ROOT.iterdir():
        if item.is_dir() and item.name in subdirs_to_include:
            for note_file in item.glob('*.md'):
                with open(note_file, 'r', encoding='utf-8') as f:
                    try:
                        content = f.read().strip()
                        relative_path = str(note_file.relative_to(NOTE_ROOT))
                        title = note_file.stem

                        # Create Note object
                        note = Note(path=relative_path, title=title, content=content)
                        session.add(note)
                        session.flush()  # This will populate the id

                        # Store note in dictionary for later linking
                        notes_dict[title] = note

                        print(f'Added note: Path: {relative_path}, Title: {title}')
                    except Exception as e:
                        print(f"Couldn't read {note_file}: {str(e)}")

    # Now, create links between notes
    for note in notes_dict.values():
        links = extract_links(note.content)
        for link in links:
            if link in notes_dict:
                note.linked_to.append(notes_dict[link])
                print(f"Created link from '{note.title}' to '{link}'")

    # Commit all changes
    session.commit()

print("Finished processing notes and creating links.")
