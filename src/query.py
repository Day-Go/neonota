from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models import Note, Tag, note_links, note_tags
import numpy as np
from openai import OpenAI
import os

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

def print_results(query_name, results):
    print(f"\n--- {query_name} ---")
    for result in results:
        print(result)
    print()

# 1. Get all notes
all_notes = session.query(Note).all()
print_results("All Notes", all_notes)

# 2. Get notes with a specific title
specific_title = "UC - Db Engineering - Course Overview"
notes_with_title = session.query(Note).filter(Note.title == specific_title).all()
print_results(f"Notes with title '{specific_title}'", notes_with_title)

# 3. Get notes containing a specific word in content
keyword = "transaction"
notes_with_keyword = session.query(Note).filter(Note.content.ilike(f"%{keyword}%")).all()
print_results(f"Notes containing '{keyword}'", notes_with_keyword)

# 4. Get notes sorted by title
sorted_notes = session.query(Note).order_by(Note.title).all()
print_results("Notes sorted by title", sorted_notes)

# 5. Get the count of all notes
note_count = session.query(func.count(Note.id)).scalar()
print(f"Total number of notes: {note_count}")

# 6. Get notes with their outgoing links
notes_with_links = session.query(Note).filter(Note.linked_to.any()).all()
for note in notes_with_links:
    print(f"Note: {note.title}")
    print(f"Links to: {[linked_note.title for linked_note in note.linked_to]}")
    print()

# 7. Get notes that are linked to by a specific note
specific_note_title = "UC - Db Engineering - Section 2 - ACID"
linked_by_specific_note = session.query(Note).filter(
    Note.linked_from.any(Note.title == specific_note_title)
).all()
print_results(f"Notes linked by '{specific_note_title}'", linked_by_specific_note)

# 8. Get notes with no outgoing links
notes_without_links = session.query(Note).filter(~Note.linked_to.any()).all()
print_results("Notes without outgoing links", notes_without_links)

# 9. Get notes with a specific file extension
file_extension = ".md"
notes_with_extension = session.query(Note).filter(Note.path.endswith(file_extension)).all()
print_results(f"Notes with file extension '{file_extension}'", notes_with_extension)

# 10. Get notes in a specific subdirectory
subdirectory = "All"
notes_in_subdirectory = session.query(Note).filter(Note.path.startswith(subdirectory)).all()
print_results(f"Notes in subdirectory '{subdirectory}'", notes_in_subdirectory)



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

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def similarity_search(query_text, top_k=5):
    # Get the embedding for the query text
    query_embedding = get_embedding(query_text)
    
    if query_embedding is None:
        print("Failed to get embedding for query text.")
        return []

    # Convert the list to a numpy array
    query_embedding_array = np.array(query_embedding)

    # Fetch all notes with their embeddings
    notes_with_embeddings = session.query(Note).filter(Note.embedding != None).all()

    # Calculate similarities
    similarities = []
    for note in notes_with_embeddings:
        note_embedding = np.array(note.embedding)
        similarity = cosine_similarity(query_embedding_array, note_embedding)
        similarities.append((note, similarity))

    # Sort by similarity (descending) and get top k results
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_results = similarities[:top_k]

    return top_results

# Example usage of the similarity search
print("\n--- Similarity Search Example ---")
query = "database transactions and ACID properties"
results = similarity_search(query, top_k=3)
print(f"Top 3 similar notes to query: '{query}'")
for note, similarity in results:
    print(f"Title: {note.title}")
    print(f"Similarity: {similarity:.4f}")
    print(f"Content preview: {note.content[:100]}...")
    print()

# Close the session
session.close()
