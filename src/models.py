from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()

# Define the association table for note links
note_links = Table('note_links', Base.metadata,
    Column('from_note_id', Integer, ForeignKey('notes.id'), primary_key=True),
    Column('to_note_id', Integer, ForeignKey('notes.id'), primary_key=True)
)

# Define the association table for note-tag relationship
note_tags = Table('note_tags', Base.metadata,
    Column('note_id', Integer, ForeignKey('notes.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    def __repr__(self):
        return f"<Tag(name='{self.name}')>"

# TODO: Add file extension field
class Note(Base):
    __tablename__ = 'notes'

    id = Column(Integer, primary_key=True)
    path = Column(String(255))
    name = Column(String(255))
    extension = Column(String(32))
    content = Column(Text)
    embedding = Column(Vector(1536))

    # Define the many-to-many relationship for note links
    linked_to = relationship('Note', 
                             secondary=note_links,
                             primaryjoin=(note_links.c.from_note_id == id),
                             secondaryjoin=(note_links.c.to_note_id == id),
                             backref='linked_from')

    # Define the many-to-many relationship with Tags
    tags = relationship("Tag", secondary=note_tags, back_populates="notes")

    def __repr__(self):
        return f"<Note(name='{self.name}', tags={[tag.name for tag in self.tags]})>"

# Add back-reference to Note in Tag
Tag.notes = relationship("Note", secondary=note_tags, back_populates="tags")
