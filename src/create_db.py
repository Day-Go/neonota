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

# Create the database
engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{database}")
conn = engine.connect()
conn.execute(text("COMMIT"))
conn.execute(text(f"CREATE DATABASE {db_name}"))
conn.close()

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

print(f"Database '{db_name}', tables 'notes', 'note_links', 'tags', 'note_tags', and pgvector extension created successfully.")

session.close()
