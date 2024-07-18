from sqlalchemy import create_engine, select 
from sqlalchemy.orm import sessionmaker
from models import Note, Tag, note_links, note_tags
from contextlib import contextmanager

class DbClient:
    def __init__(self, host: str, database: str, user: str, password: str):
        connection_string = f'postgresql://{user}:{password}@{host}/{database}'
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)

    @contextmanager
    def session_scope(self):
        session = self.Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def get_all_notes(self):
        with self.session_scope() as session:
            return session.query(Note).all()

    def get_all_titles(self):
        with self.session_scope() as session:
            return session.scalars(select(Note.title)).all()

    def get_all_filepaths(self):
        with self.session_scope() as session:
            return session.scalars(select(Note.path)).all()

    # TODO: Add error handling
    def add_note(self, note: Note):
        with self.session_scope() as session:
            session.add(note)

    def get_notes_by_tag(self, tag_name):
        with self.session_scope() as session:
            return session.query(Note).filter(Note.tags.any(Tag.name == tag_name)).all()

    def close(self):
        self.engine.dispose()
