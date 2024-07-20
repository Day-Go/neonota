import cmd
import time
import yaml
import queue
import threading
from llm import LLM
from database_client import DbClient
from watcher import Watcher, NoteHandler


class NoteCLI(cmd.Cmd):
    prompt = 'note> '

    def __init__(self, db_client, llm, message_queue):
        super().__init__()
        self.db_client = db_client
        self.llm = llm
        self.message_queue = message_queue
        self.should_run = True
        self.prompt_delay = 0.5

    def do_exit(self, arg):
        """Exit the CLI"""
        print("Exiting...")
        self.should_run = False
        return True

    def cmdloop(self, intro=None):
        print(intro)
        while self.should_run:
            try:
                super().cmdloop(intro='')
                break
            except KeyboardInterrupt:
                print("^C")

    def preloop(self):
        self.check_messages_thread = threading.Thread(target=self.check_messages)
        self.check_messages_thread.daemon = True
        self.check_messages_thread.start()

    def check_messages(self):
        while self.should_run:
            messages = []

            # Collect all available messages
            while True:
                try:
                    message = self.message_queue.get_nowait()
                    messages.append(message)
                except queue.Empty:
                    break

            # Print collected messages
            if messages:
                print()
                for message in messages:
                    print(f"{message}")

                # Delay before showing the prompt
                time.sleep(self.prompt_delay)
                print(self.prompt, end='', flush=True)

            # Short sleep to prevent busy-waiting
            time.sleep(0.1)

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



