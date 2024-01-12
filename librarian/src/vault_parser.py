import re
import hashlib
from pathlib import Path
from openai import OpenAI
from models import Notes
from database import Session

class VaultParser:
    def __init__(self, vault_path: Path, openai_client: OpenAI):
        self.vault_path = vault_path
        self.openai_client = openai_client
        self.session = Session()

    @staticmethod
    def find_markdown_files(vault_path):
        """Recursively find all markdown files in the given root folder."""
        root = Path(vault_path)
        markdown_files = list(root.rglob("*.md"))
        return markdown_files

    @staticmethod
    def find_wikilinks_and_clean(text):
        # Find all wikilinks first
        pattern = r'\[\[.*?\]\]|\[.*?\]\(.*?\)'
        wikilinks = re.findall(pattern, text)

        # Clean wikilinks by removing everything after the pipe '|' and removing double square brackets
        cleaned_links = [re.sub(r'\|.*?\]\]', ']]', link) for link in wikilinks]
        cleaned_links = [re.sub(r'\[\[(.*?)\]\]', r'\1', link) for link in cleaned_links]
        return cleaned_links

    @staticmethod
    def hash_file(input: str):
        """Generate a SHA-256 hash of a string."""
        sha256_hash = hashlib.sha256()
        sha256_hash.update(input.encode('utf-8'))
        return sha256_hash.hexdigest()

    def create_note(self, filename, filepath, contents, hash, embedding):
        new_note = Notes(
            name=filename, 
            path=filepath, 
            contents=contents,
            hash = hash, 
            embedding=embedding
        )
        self.session.add(new_note)
        self.session.commit()
        return new_note

    def generate_embedding(self, contents):
        response = self.openai_client.embeddings.create(
            input=contents,
            model="text-embedding-ada-002"
        )
        embedding = response.data[0].embedding
        
        return embedding

    def handle_new_note(self, file: Path, contents: str):
        filename = str(file.stem)
        filepath = str(file.parent)
        embedding = self.generate_embedding(contents)
        hash = self.hash_file(contents)

        note = self.create_note(
            filename, 
            filepath, 
            contents, 
            hash, 
            embedding
        )

        links = self.find_wikilinks_and_clean(contents)
        self.link_notes(note, links)

        self.session.commit()
        print(f"New note created...\n")
        

    def handle_existing_note(self, file: Path, contents: str, existing_note: Notes):
        file_hash = self.hash_file(contents)

        filepath = str(file.parent)
        if filepath != existing_note.path:
            existing_note.path = filepath
            self.session.commit()
            print(f"File moved. File path updated...")

        if file_hash != existing_note.hash:
            existing_note.hash = file_hash
            existing_note.contents = contents
            existing_note.embedding = self.generate_embedding(contents)

            links = self.find_wikilinks_and_clean(contents)
            self.link_notes(existing_note, links)

            self.session.commit()
            print(f"Changes found. File updated...\n")
        else:
            print(f"No changes found. Skipping file...\n")

    def parse_vault(self):
        markdown_files = self.find_markdown_files(self.vault_path)
        for file in markdown_files:
            print(f"Processing file: {file.stem}")
            with open(file, "r") as f:
                contents = f.read()

            # Check if the file already exists in the database
            existing_note = self.session.query(Notes) \
                                        .filter_by(name=file.stem) \
                                        .first()
            if existing_note:
                print(f"Note with the same filename found.")
                self.handle_existing_note(file, contents, existing_note)
                continue
            else:
                print(f"Note with the same filename not found. Creating new note...")
                self.handle_new_note(file, contents)

    def link_notes(self, note, link_names):
        for link_name in link_names:
            linked_note = self.session.query(Notes).filter_by(name=link_name).first()
            if linked_note:
                note.linked_notes.append(linked_note)