import os
import re
import json
import threading
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
from openai import OpenAI
from watchdog.events import FileSystemEventHandler
from handler_functions import *

class Handler(FileSystemEventHandler):
    def __init__(self, watch_directory: Path):
        self.client = OpenAI()

        self.watch_directory = watch_directory
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
            with open(event.src_path, 'r', encoding='utf-8', errors='ignore') as f:
                contents = f.read()
        elif event.is_directory:
            return
        
        src_path = Path(event.src_path)
        root_path = src_path.parent.parent 
        embedding_path = root_path / 'Embeddings'
        index_path = root_path / 'Index'

        if '/rename' in contents:
            filename = rename_file(self.client, contents) + '.md'
            print(filename)
            
            remove_tag(src_path, contents, '/rename')
            dst_path = src_path.parent / filename
            os.rename(src_path, dst_path)
            src_path = dst_path

            # Check if an embedding exists
            # if it does then rename to the same as the file

        if '/rewrite' in contents:
            pass

        if '/aggr-tags' in contents:
            tags_note = index_path / 'Tags.md'
            embedding_note = embedding_path / 'Tags.json'
            img_path = root_path / 'Media' / 'tag_similarity_heatmap.png'

            # TODO: Don't embed tags that already have embeddings

            tags = get_all_tags(src_path.parent)
            print(tags)
            with open(tags_note, 'w+') as f:
                f.write('![[tag_similarity_heatmap.png]]')
                f.write('\n - '.join(tags)) 

            tags = [tag.replace('_', ' ') for tag in tags]

            embeddings = {tag: embed(self.client, tag) for tag in tags}
            with open(embedding_note, 'w+') as f:
                json.dump(embeddings, f)

            similarity_matrix = generate_similarity_matrix(embeddings)
            print(similarity_matrix)

            fig, ax = plt.subplots(figsize=(10, 8)) 
            sns.heatmap(similarity_matrix, annot=True, cmap='coolwarm', xticklabels=tags, yticklabels=tags)
            ax.set_title('Tag Correlation Matrix')
            plt.subplots_adjust(bottom=0.2, top=0.9) 
            plt.savefig(img_path, bbox_inches='tight')
            plt.close(fig)

            remove_tag(src_path, contents, '/aggr-tags')

        if re.search(r'/c-tags-\d+', contents):
            match = re.search(r'/c-tags-(\d+)', contents)
            num_tags = int(match.group(1))
            tags = create_tags(self.client, contents, num_tags)
            tag_index = contents.find('tags:')
            contents = contents[:tag_index + 6] + tags + contents[tag_index + 6:]
            remove_tag(src_path, contents, match.group(0))

        if re.search(r'/c-links-\d+', contents):
            match = re.search(r'/c-links-(\d+)', contents)
            num_links = int(match.group(1))

            all_embeddings =  load_embeddings(self.watch_directory / "Embeddings")
            if src_path.name in [embed_path.name for embed_path in embedding_path.rglob('*.md')]:
                embedding = all_embeddings[src_path.stem]
                del all_embeddings[src_path.stem]
            else:
                embedding = embed(self.client,contents)
            
            links = []
            for _ in range(num_links):
                best_link = self.create_link(embedding, all_embeddings)
                del all_embeddings[best_link]
                formatted_best_link = '[[' + best_link + ']]'
                links.append(formatted_best_link)

            remove_tag(src_path, contents, match.group(0))
            
            print(links)
            print(src_path)
            with open(src_path, 'a+') as f:
                for i, link in enumerate(links):
                    line = f'{i+1}: {link}\n'
                    print(line)
                    f.write(line)

        if '/embed' in contents:
            create_embedding_file(src_path, contents)
            
        if '/all-embed' in contents:
            remove_tag(src_path, contents, 'all-embed')
            for file in src_path.parent.rglob('*.md'):
                src_path = file
                with open(file, 'r', encoding='utf-8') as f:
                    contents = f.read()
                self.create_embedding_file(src_path, contents)

            self.remove_tag(src_path, contents, '/all-embed')
       
