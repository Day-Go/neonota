from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Note, Tag

def get_db_session():
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    user = config['postgres']['user']
    password = config['postgres']['password']
    host = config['postgres']['host']
    database = config['postgres']['database']
    port = "5432"

    engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{database}")
    Session = sessionmaker(bind=engine)
    return Session()

def add_note(title, content, embedding, tags):
    session = get_db_session()
    new_note = Note(title=title, content=content, embedding=embedding)
    for tag_name in tags:
        tag = session.query(Tag).filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
        new_note.tags.append(tag)
    session.add(new_note)
    session.commit()
    session.close()

def get_notes_by_tag(tag_name):
    session = get_db_session()
    notes = session.query(Note).filter(Note.tags.any(Tag.name == tag_name)).all()
    session.close()
    return notes

