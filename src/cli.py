import re
import cmd
from pathlib import Path
import time
import queue
import readline
import threading
import subprocess

class NoteCLI(cmd.Cmd):
    prompt = 'note> '

    def __init__(self, db_client, llm, message_queue):
        super().__init__()
        self.db_client = db_client
        self.llm = llm
        self.message_queue = message_queue
        self.should_run = True
        self.prompt_delay = 0.5

        readline.set_completer(self.complete_note_name)
        readline.parse_and_bind("tab: complete")
        readline.set_completer_delims(' \t\n')

    def do_exit(self, arg):
        """Exit the CLI"""
        print("Exiting...")
        self.should_run = False
        return True

    # TODO: Add regex mathcing for note names
    def do_list_notes(self, arg):
        notes = self.db_client.get_all_names()
        for note in notes:
            print(note)

    def help_list_notes(self):
        print('Get a list of all the note names in the database')

    def do_link(self, arg):
        try:
            args = re.findall(r'(?:"[^"]*"|[^"\s]+)', arg)

            if len(args) != 2:
                print('Usage: link <string> <integer>')
                return

            name = args[0].strip('"')
            n = int(args[1])

            note = self.db_client.get_note_by_name(name)
            if not note:
                print(f'Note named {name} not found.')

            similar_notes = self.db_client.get_similar_notes(note.embedding, n)
            for similar_note in similar_notes:
                print(similar_note.name)

        except ValueError:
            print('Usage: link <string> <integer>')

    def help_link(self):
        print('find x most similar notes')

    def do_open(self, arg):
        args = re.findall(r'(?:"[^"]*"|[^"\s]+)', arg)
        if len(args) != 1:
            print('Usage: open <string>')
            return
        name = args[0].strip('"')

        note = self.db_client.get_note_by_name(name)
        path = Path(note.path)

        if not path.exists():
            print(f"File not found: {path}")
            return

        try:
            subprocess.run(['nvim', path], check=True)
            print(f"Opened {path} in a new terminal pane.")
        except subprocess.CalledProcessError as e:
            print(f"Error opening file: {e}")

    def help_open(self):
        print("Open a specified markdown file in Neovim in a new terminal pane")

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

            # print collected messages
            if messages:
                print()
                for message in messages:
                    print(f"{message}")

                # Delay before showing the prompt
                time.sleep(self.prompt_delay)
                print(self.prompt, end='', flush=True)

            # Short sleep to prevent busy-waiting
            time.sleep(0.1)


    def get_note_names(self):
        return [str(note).rstrip('.md') for note in self.db_client.get_all_names()]

    def complete(self, text, state):
        line = readline.get_line_buffer().split()

        # If we're at the start of the line, complete commands
        if not line:
            return [c + ' ' for c in self.get_names() if c.startswith(text)][state]

        # If we're completing arguments for a command
        cmd = line[0]
        if cmd == 'link' or cmd == 'open':
            if len(line) == 2:  # completing the note name
                return self.complete_note_name(text, state)

        return None

    def complete_note_name(self, text, state):
        names = self.get_note_names()
        matches = [n for n in names if n.startswith(text)]
        if state < len(matches):
            return f'"{matches[state]}"'
        else:
            return None
