import pathlib
from database import Session, create_tables
from models import Notes
from vault_parser import VaultParser
from watcher import Watcher
from openai import OpenAI
from sqlalchemy import select

client = OpenAI()

create_tables()
session = Session()

w = Watcher()
w.run()

# Close the session
session.close()
