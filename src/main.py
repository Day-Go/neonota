import yaml
import queue
import threading
from llm import LLM
from cli import NoteCLI
from database_client import DbClient
from watcher import Watcher, NoteHandler



def run_watcher(event_handler):
    watcher = Watcher(event_handler)
    watcher.run()

if __name__ == '__main__':
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    user = config['postgres']['user']
    password = config['postgres']['password']
    host = config['postgres']['host']
    database = config['postgres']['database']
    chat_model = 'gpt-4o-mini'
    embed_model = 'text-embedding-3-small'

    message_queue = queue.Queue()

    db_client = DbClient(host, database, user, password)
    llm = LLM(chat_model, embed_model, db_client)
    event_handler = NoteHandler(db_client, llm, message_queue)

    # Start the watcher in a separate thread
    watcher_thread = threading.Thread(target=run_watcher, args=(event_handler,))
    watcher_thread.daemon = True
    watcher_thread.start()

    cli = NoteCLI(db_client, llm, message_queue)
    cli.cmdloop("Welcome to the Note CLI. Type 'help' for commands.")



