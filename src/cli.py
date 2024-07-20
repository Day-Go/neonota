import cmd
import time
import queue
import threading

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

    # TODO: Add regex mathcing for note names
    def do_list_notes(self, arg):
        notes = self.db_client.get_all_names()
        for note in notes:
            self.message_queue.put(note)

    def help_list_notes(self):
        self.message_queue.put('Get a list of all the note names in the database')

    def do_link(self, arg):
        try:
            args = arg.split()

            if len(args) != 2:
                self.message_queue.put('Usage: link <string> <integer>')
                return

            name = args[0]
            n = int(args[1])

            note = self.db_client.get_note_by_name(name)
            if not note:
                self.message_queue.put(f'Note named {name} not found.')

            similar_notes = self.db_client.get_similar_notes(note.embedding, n)
            for similar_note in similar_notes:
                self.message_queue.put(similar_note.name)
        except:
            self.message_queue.put('Usage: link <string> <integer>')

    def help_link(self):
        print('find x most similar notes')

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


