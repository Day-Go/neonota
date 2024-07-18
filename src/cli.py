import os
import yaml
import numpy as np
from openai import OpenAI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Note

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Database setup
user = config['postgres']['user']
password = config['postgres']['password']
host = config['postgres']['host']
database = config['postgres']['database']

engine = create_engine(f'postgresql://{user}:{password}@{host}/{database}')
Session = sessionmaker(bind=engine)
session = Session()

# OpenAI setup
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def get_embedding(text):
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {str(e)}")
        return None

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def similarity_search(query_text, top_k=3):
    query_embedding = get_embedding(query_text)
    if query_embedding is None:
        return []

    query_embedding_array = np.array(query_embedding)
    notes_with_embeddings = session.query(Note).filter(Note.embedding != None).all()

    similarities = []
    for note in notes_with_embeddings:
        note_embedding = np.array(note.embedding)
        similarity = cosine_similarity(query_embedding_array, note_embedding)
        similarities.append((note, similarity))

    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]

def get_relevant_context(query):
    results = similarity_search(query)
    context = ""
    for note, similarity in results:
        context += f"Title: {note.title}\nContent: {note.content}\n\n"
    return context.strip()

def chat_with_gpt(messages):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in chat completion: {str(e)}")
        return None

def main():
    print("Welcome to the RAG-powered CLI tool. Type 'exit' to quit.")

    conversation_history = [
        {"role": "system", "content": "You are a helpful assistant with access to a knowledge base. Use the provided context to answer questions, but also use your general knowledge when appropriate. If the answer isn't in the context, say so. All following queries come from a user whom you must address directly."}
    ]

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break

        context = get_relevant_context(user_input)
        conversation_history.append({"role": "user", "content": f"Context: {context}\n\nQuestion: {user_input}"})
        response = chat_with_gpt(conversation_history)

        if response:
            print(f"\nAssistant: {response}")
            conversation_history.append({"role": "assistant", "content": response})
        else:
            print("\nAssistant: I'm sorry, I encountered an error. Please try again.")

    print("Closing assistant")

if __name__ == "__main__":
    main()
