import yaml
from llm import LLM
from database_client import DbClient
from watcher import Watcher, NoteHandler

if __name__ == '__main__':
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    user = config['postgres']['user']
    password = config['postgres']['password']
    host = config['postgres']['host']
    database = config['postgres']['database']

    chat_model = 'gpt-4o-mini'
    embed_model = 'text-embedding-3-small'

    db_client = DbClient(host, database, user, password)
    llm = LLM(chat_model, embed_model, db_client)
    event_handler = NoteHandler(db_client, llm)
    watcher = Watcher(event_handler)
