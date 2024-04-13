import os
import re
import json
import threading
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
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

        self.COMMANDS = ['/rename', '/rewrite', '/c-tags',
                         '/c-link', '/embed']

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
        
        src_path = Path(event.src_path)
        root_path = src_path.parent.parent 
        embedding_path = root_path / 'Embeddings'
        index_path = root_path / 'Index'

        if '/rename' in contents:
            filename = self.rename_file(contents) + '.md'
            print(filename)
            
            self.remove_tag(src_path, contents, '/rename')
            dst_path = src_path.parent / filename
            os.rename(src_path, dst_path)
            src_path = dst_path

            # Check if an embedding exists
            # if it does then rename to the same as the file

        if '/aggr-tags' in contents:
            tags_note = index_path / 'Tags.md'
            embedding_note = embedding_path / 'Tags.json'
            img_path = root_path / 'Media' / 'tag_similarity_heatmap.png'

            # TODO: Don't embed tags that already have embeddings

            tags = self.get_all_tags(src_path.parent)
            with open(tags_note, 'w+') as f:
                f.write('![[tag_similarity_heatmap.png]]')

                f.write('\n - '.join(tags)) 

            tags = [tag.replace('_', ' ') for tag in tags]

            embeddings = {tag: self.embed(tag) for tag in tags}
            with open(embedding_note, 'w+') as f:
                json.dump(embeddings, f)

            similarity_matrix = self.generate_similarity_matrix(embeddings)
            print(similarity_matrix)

            fig, ax = plt.subplots(figsize=(10, 8)) 
            sns.heatmap(similarity_matrix, annot=True, cmap='coolwarm', xticklabels=tags, yticklabels=tags)
            ax.set_title('Tag Correlation Matrix')
            plt.subplots_adjust(bottom=0.2, top=0.9) 
            plt.savefig(img_path, bbox_inches='tight')
            plt.close(fig)

            self.remove_tag(src_path, contents, '/aggr-tags')

        if '/rewrite' in contents:
            pass

        if re.search(r'/c-tags-\d+', contents):
            match = re.search(r'/c-tags-(\d+)', contents)
            num_tags = int(match.group(1))
            tags = self.create_tags(contents, num_tags)
            tag_index = contents.find('tags:')
            contents = contents[:tag_index + 6] + tags + contents[tag_index + 6:]
            self.remove_tag(src_path, contents, match.group(0))

        if re.search(r'/c-links-\d+', contents):
            match = re.search(r'/c-links-(\d+)', contents)
            num_links = int(match.group(1))

            all_embeddings =  self.load_embeddings(EMBEDDING_DIRECTORY)
            if src_path.name in [embed_path.name for embed_path in embedding_path.rglob('*.md')]:
                embedding = all_embeddings[src_path.stem]
                del all_embeddings[src_path.stem]
            else:
                embedding = self.embed(contents)
            
            links = []
            for _ in range(num_links):
                best_link = self.create_link(embedding, all_embeddings)
                del all_embeddings[best_link]
                formatted_best_link = '[[' + best_link + ']]'
                links.append(formatted_best_link)

            self.remove_tag(src_path, contents, match.group(0))
            
            print(links)
            print(src_path)
            with open(src_path, 'a+') as f:
                for i, link in enumerate(links):
                    line = f'{i+1}: {link}\n'
                    print(line)
                    f.write(line)

           

        if '/embed' in contents:
            self.create_embedding_file(src_path, contents)
            
        if '/all-embed' in contents:
            self.remove_tag(src_path, contents, 'all-embed')
            for file in src_path.parent.rglob('*.md'):
                src_path = file
                with open(file, 'r') as f:
                    contents = f.read()
                self.create_embedding_file(src_path, contents)

            
    def remove_tag(self, path, contents, tag) -> None:
        with open(path, "w") as f:
            f.write(contents.replace(tag, ''))
    
    def rename_file(self, contents: str) -> str:
        print("Renaming file...")
        response = self.client.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=[
                {"role": "user", 
                 "content": f"Using a maximum of 5 words, summarise the following: {contents}"}
            ]
        )
        filename = response.choices[0].message.content.strip('\'\"') \
                                                      .replace(':', ' -')
        return filename

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


    def create_link(self, embedding: float, all_embeddings: dict[str, float]) -> str:
        print("Creating links...")
        max_similarity = 0
        
        for key, value in all_embeddings.items():
            similarity = self.calc_cosine_similarity(embedding, value)
            print(f"Similarity between content and {key}: {similarity}")
            if similarity > max_similarity:
                max_similarity = similarity
                max_key = key

        return max_key

    def embed(self, contents) -> list[float]:
        print("Embedding text...")
        response = self.client.embeddings.create(
            input=contents,
            model="text-embedding-3-large"
        )

        return response.data[0].embedding

    def create_embedding_file(self, src_path: Path, contents: str) -> None:
        embedding = self.embed(contents)
        with open(EMBEDDING_DIRECTORY / src_path.name, 'w') as f:
            f.write(', '.join(str(x) for x in embedding))
        self.remove_tag(src_path, contents, '/embed')

    @staticmethod
    def embedding_str2float(file_path: Path) -> float:
        with open(file_path, 'r') as file:
            content = file.read().strip()
            embedding = [float(x) for x in content.split(',')]

        return embedding

    def load_embeddings(self, directory: str) -> dict:
        embedding_dict = {}
        for file_name in Path(directory).rglob('*.md'):
            file_path = os.path.join(directory, file_name)
            if os.path.isfile(file_path):
                embedding = self.embedding_str2float(file_path)
                key = Path(file_name).stem
                embedding_dict[key] = embedding

        return embedding_dict
    
    def calc_cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
    def get_all_tags(self, root_folder):
        all_tags = []
        for file_path in Path(root_folder).rglob('*.md'):
            with file_path.open() as file:
                file_content = file.read()
                tags = self.extract_tags(file_content)
                all_tags.extend(tags)
        return list(set(all_tags))

    @staticmethod
    def extract_tags(file_content):
        tags = []
        tag_block = re.search(r'tags:\s*(.*?)\s*relations:', file_content, re.DOTALL)
        if tag_block:
            tag_content = tag_block.group(1).strip()
            tag_lines = tag_content.split('\n')
            for line in tag_lines:
                tag = line.strip().lstrip('- ')
                if tag:
                    tags.append(tag)
        return tags
    
    def generate_similarity_matrix(self, tag_embeddings: dict):
        n = len(tag_embeddings)
        similarity_matrix = np.zeros((n, n))

        tag_keys = list(tag_embeddings.keys())
        for i in range(n):
            for j in range(i, n):
                similarity = self.calc_cosine_similarity(
                    tag_embeddings[tag_keys[i]], tag_embeddings[tag_keys[j]]
                )
                similarity_matrix[i][j] = similarity
                similarity_matrix[j][i] = similarity

        return similarity_matrix