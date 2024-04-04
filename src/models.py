from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from database import Base
from pgvector.sqlalchemy import Vector

# Association table for the many-to-many relationship
note_links = Table('note_links', Base.metadata,
    Column('note_id', Integer, ForeignKey('notes.id'), primary_key=True),
    Column('linked_note_id', Integer, ForeignKey('notes.id'), primary_key=True)
)

class Notes(Base):
    __tablename__ = 'notes'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=True)
    path = Column(String, nullable=True)
    contents = Column(String, nullable=True)
    hash = Column(String(64), nullable=True)
    embedding = Column(Vector(1536), nullable=True)

    # Relationship for the many-to-many links
    linked_notes = relationship('Notes', 
                                secondary=note_links, 
                                primaryjoin=id==note_links.c.note_id,
                                secondaryjoin=id==note_links.c.linked_note_id)
