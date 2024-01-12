import pathlib
from database import Session, create_tables
from models import Notes
from vault_parser import VaultParser
from openai import OpenAI
from sqlalchemy import select

client = OpenAI()

create_tables()
session = Session()

eg_vault_path = pathlib.Path.cwd() / "eg_vault"
vp = VaultParser(eg_vault_path, client)
# vp.parse_vault()

while True:
    user_input = input("Enter your query (or type 'exit' to quit): ")
    if user_input.lower() in ['exit', 'quit']:
        break

    response = client.embeddings.create(
        input=user_input,
        model="text-embedding-ada-002"
    )
    embedding = response.data[0].embedding

    neighbours = session.scalars(select(Notes)
                        .order_by(Notes.embedding.l2_distance(embedding))
                        .limit(5))

    # Process and print results
    for row in neighbours:
        print(row.name)

# Close the session
session.close()
