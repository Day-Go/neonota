import os
import yaml
from openai import OpenAI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

from models import Note


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

# Initialize OpenAI client
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

def update_embeddings():
    # Get all notes
    notes = session.query(Note).all()

    for note in tqdm(notes, desc="Processing notes"):
        # Combine title and content for embedding
        text_to_embed = f"{note.title}\n\n{note.content}"

        # Get embedding
        embedding = get_embedding(text_to_embed)

        if embedding:
            # Update note with new embedding
            note.embedding = embedding
            session.add(note)

    # Commit all changes
    session.commit()
    print("All embeddings updated successfully.")

if __name__ == "__main__":
    update_embeddings()

# Close the session
session.close()
