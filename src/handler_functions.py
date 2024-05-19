import re
import numpy as np
from pathlib import Path
from openai import OpenAI


def remove_tag(path, contents, tag) -> None:
    with open(path, "w", encoding='utf-8') as f:
        f.write(contents.replace(tag, ''))

def rename_file(client: OpenAI, contents: str) -> str:
    print("Renaming file...")
    response = client.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=[
            {"role": "user", 
                "content": f"Using a maximum of 5 words, summarise the following: {contents}"}
        ]
    )
    filename = response.choices[0].message.content.strip('\'\"') \
                                                  .replace(':', ' -')
    return filename

def rewrite(contents: str) -> str:
    print("Rewriting file...")
    pass

def create_tags(client: OpenAI, contents: str, n: int) -> list[str]:
    print("Creating tags...")
    response = client.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=[
            {"role": "user", "content": f"Output {n} tags (space delimited, snake case) for my note: {contents}"}
        ]
    )
    return response.choices[0].message.content

def create_link(embedding: float, all_embeddings: dict[str, float]) -> str:
    print("Creating links...")
    max_similarity = 0
    for key, value in all_embeddings.items():
        similarity = calc_cosine_similarity(embedding, value)
        print(f"Similarity between content and {key}: {similarity}")
        if similarity > max_similarity:
            max_similarity = similarity
            max_key = key
    return max_key

def embed(client: OpenAI, contents: str) -> list[float]:
    print("Embedding text...")
    response = client.embeddings.create(
        input=contents,
        model="text-embedding-3-large"
    )
    return response.data[0].embedding

def create_embedding_file(src_path: Path, embedding_dir: Path, contents: str) -> None:
    embedding = embed(contents)
    with open(embedding_dir / src_path.name, 'w') as f:
        f.write(', '.join(str(x) for x in embedding))
    remove_tag(src_path, contents, '/embed')


def embedding_str2float(file_path: Path) -> float:
    with open(file_path, 'r') as file:
        content = file.read().strip()
        embedding = [float(x) for x in content.split(',')]
    return embedding

def load_embeddings(directory: Path) -> dict:
    embedding_dict = {}
    for file_path in directory.rglob('*.md'):
        if file_path.is_file():
            embedding = embedding_str2float(str(file_path))
            key = file_path.stem
            embedding_dict[key] = embedding
    return embedding_dict

def calc_cosine_similarity(a: np.ndarray, b: np.ndarray):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
def get_all_tags(root_folder: Path) -> list[str]:
    all_tags = []
    for file_path in root_folder.rglob('*.md'):
        print(file_path)
        with open(file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()
            tags = extract_tags(file_content)
            all_tags.extend(tags)
    return list(set(all_tags))


def extract_tags(file_content: str):
    tags = []
    tag_block = re.findall(r'tags:\s*\n([\s\S]*?)\n---', file_content)
    if tag_block:
        for block in tag_block:
            tag_lines = block.strip().split('\n')
            for line in tag_lines:
                tag = line.strip().lstrip('- ')
                if tag:
                    tags.append(tag)
    return tags
    
def generate_similarity_matrix(tag_embeddings: dict):
    n = len(tag_embeddings)
    similarity_matrix = np.zeros((n, n))

    tag_keys = list(tag_embeddings.keys())
    for i in range(n):
        for j in range(i, n):
            similarity = calc_cosine_similarity(
                tag_embeddings[tag_keys[i]], tag_embeddings[tag_keys[j]]
            )
            similarity_matrix[i][j] = similarity
            similarity_matrix[j][i] = similarity

    return similarity_matrix