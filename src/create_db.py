import yaml
from sqlalchemy import create_engine, Index
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from models import Base, Note

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Database setup
user = config['postgres']['user']
password = config['postgres']['password']
host = config['postgres']['host']
database = config['postgres']['database']
port = "5432"

# Connect to default 'postgres' database first
default_engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/postgres")
with default_engine.connect() as conn:
    conn.execute(text("COMMIT"))
    conn.execute(text(f"CREATE DATABASE {database}"))
    print(f"Database '{database}' created successfully.")

# Now connect to the newly created database
engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{database}")

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

# Enable the pgvector extension
session.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
session.commit()

# Create the tables
Base.metadata.create_all(engine)

# Create an approximate index for faster similarity search
index = Index(
    'notes_embedding_idx',
    Note.embedding,
    postgresql_using='hnsw',
    postgresql_with={'m': 16, 'ef_construction': 64},
    postgresql_ops={'embedding': 'vector_cosine_ops'}
)
index.create(engine)

print(f"Tables 'notes', 'note_links', 'tags', 'note_tags', and pgvector extension created successfully.")
session.close()
