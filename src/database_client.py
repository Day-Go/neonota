from typing import List, Union
from sqlalchemy import create_engine, func, select 
from sqlalchemy.orm import sessionmaker, class_mapper
from sqlalchemy.dialects.postgresql import insert
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

    def get_note_by_path(self, path: str) -> Union[Note, None]:
        with self.session_scope() as session:
            stmt = select(Note).where(Note.path == path)
            result = session.execute(stmt).scalar_one_or_none()
            if result:
                return session.expunge(result)
            return None

    def get_all_notes(self):
        with self.session_scope() as session:
            return list(session.query(Note).all())

    def get_all_titles(self):
        with self.session_scope() as session:
            return list(session.scalars(select(Note.title)).all())

    def get_all_filepaths(self):
        with self.session_scope() as session:
            return list(session.scalars(select(Note.path)).all())

    def upsert_note(self, note: Note):
        with self.session_scope() as session:
            try:
                # Check if a note with this path already exists
                existing_note = session.query(Note).filter(Note.path == note.path).first()

                if existing_note:
                    # Update existing note
                    for key, value in note.__dict__.items():
                        if key != '_sa_instance_state':
                            setattr(existing_note, key, value)
                else:
                    # Add new note
                    session.add(note)

                session.commit()
                return note
            except Exception as e:
                session.rollback()
                print(f"Error in upsert_note: {str(e)}")
                raise

    def get_notes_by_tag(self, tag_name):
        with self.session_scope() as session:
            return session.query(Note).filter(Note.tags.any(Tag.name == tag_name)).all()

    def add_embedding(self, note_id: int, embedding: List[float]):
        with self.session_scope() as session:
            note = session.query(Note).filter(Note.id == note_id).first()
            if note:
                note.embedding = embedding
                session.commit()
            else:
                raise ValueError(f"Note with id {note_id} not found")

    def get_similar_notes(self, query_embedding: List[float], n: int = 5):
        with self.session_scope() as session:
            # Assuming your Note model has an 'embedding' column of type vector
            results = session.query(Note).order_by(
                func.cosine_similarity(Note.embedding, query_embedding).desc()
            ).limit(n).all()
            return results

    def bulk_add_embeddings(self, note_ids: List[int], embeddings: List[List[float]]):
        with self.session_scope() as session:
            for note_id, embedding in zip(note_ids, embeddings):
                note = session.query(Note).filter(Note.id == note_id).first()
                if note:
                    note.embedding = embedding
            session.commit()

    def delete_note(self, note_id: int):
        with self.session_scope() as session:
            note = session.query(Note).filter(Note.id == note_id).first()
            if note:
                session.delete(note)
                session.commit()
            else:
                raise ValueError(f"Note with id {note_id} not found")

    def close(self):
        self.engine.dispose()
