import numpy as np
import pathlib
from database import Session, create_tables
from models import Notes
from vault_parser import VaultParser
from openai import OpenAI

from sqlalchemy import func, select, desc, asc

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


client = OpenAI()

create_tables()
session = Session()

eg_vault_path = pathlib.Path.cwd() / "eg_vault"
vp = VaultParser(eg_vault_path, client)
# vp.parse_vault()

input = "Do i have any notes about improving my productivity on the computer?"

response = client.embeddings.create(
    input=input,
    model="text-embedding-ada-002"
)
embedding = response.data[0].embedding

neighbours = session.scalars(select(Notes)
                    .order_by(Notes.embedding.l2_distance(embedding))
                    .limit(5))


# Process your result
for row in neighbours:
    print(row.name)

# Close the session
session.close()

