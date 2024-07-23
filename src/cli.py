import re
import cmd
from pathlib import Path
import time
import yaml
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
        self.exit()

    def exit(self):
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
        if not note:
            print('Could not retrieve note: {name}')
            return

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

    def do_crit(self, arg):
        args = re.findall(r'(?:"[^"]*"|[^"\s]+)', arg)
        if len(args) != 1:
            print('Usage: crit <string>')
            return

        name = args[0].strip('"')
        note = self.db_client.get_note_by_name(name)
        if not note:
            print('Could not retrieve note: {name}')
            return

        path = Path(note.path)
        if not path.exists():
            print('File not found: {path}')

        system_prompt = ('You are an expert on whatever topic you are presented. '
                         'Your task is to evaluate the correctness of information presented to you. '
                         'Be as critical as possible. Your response should outline information you '
                         'believe is correct, the information that is incorrect, and suggestions on how '
                         'to improve the correctness of the text.')
        result = self.llm.chat(system_prompt, note.content)
        print(str(result))
        llm_note = path.with_stem(f'{path.stem}.llm')
        with open(llm_note, 'w') as f:
            f.write(str(result))

        try:
            subprocess.run(['nvim', llm_note], check=True)
            print(f"Opened {path} in a new terminal pane.")
        except subprocess.CalledProcessError as e:
            print(f"Error opening file: {e}")

    def help_crit(self, arg):
        print('Get an LLMs critical opinion on your note')

    def do_crit_diff(self, arg):
        args = re.findall(r'(?:"[^"]*"|[^"\s]+)', arg)
        if len(args) != 1:
            print('Usage: crit <string>')
            return

        name = args[0].strip('"')
        note = self.db_client.get_note_by_name(name)
        if not note:
            print('Could not retrieve note: {name}')
            return

        path = Path(note.path)
        if not path.exists():
            print('File not found: {path}')

        system_prompt = ('You are an expert on whatever topic you are presented. '
                         'Your task is to evaluate the correctness of information presented to you. '
                         'Be as critical as possible. Consider which information is correct, '
                         'which is not correct, and what changes need to be made to fix the information. '
                         'Focus on the information presented rather than grammar, punctuation and wording. '
                         'Return an improved version of the original note while remaining as close '
                         'as possible to the style and structure of the original.')
        result = self.llm.chat(system_prompt, note.content)
        print(str(result))
        llm_note = path.with_stem(f'{path.stem}.llm_diff')
        with open(llm_note, 'w') as f:
            f.write(str(result))

        try:
            subprocess.run(['nvim', '-d', note.path, llm_note], check=True)
            print(f"Opened {path} in a new terminal pane.")
        except subprocess.CalledProcessError as e:
            print(f"Error opening file: {e}")

    def help_crit_diff(self):
        print('Get an LLMs critical opinion on your note and return a corrected version in neovims diff view')

    def do_ask(self, arg):
        question = ' '.join(arg.split(' '))
        result = self.llm.chat('', question)
        print(str(result))

    def help_ask(self):
        print("Ask the LLM a question without injecting any context")

    def do_set_root(self, arg):
        if len(arg.split(' ')) != 1:
            print('Usage: set_root <string>')
            return 

        if not Path(arg).is_dir():
            print('Directory not found!')
            return

        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)

        config['dir']['root'] = arg 

        with open('config.yaml', 'w') as file:
            yaml.dump(config, file, default_flow_style=False)

    def help_set_root(self):
        print('Set the note root folder')

    def do_new(self, arg):
        NotImplemented()

    def help_new(self):
        print('Create a new markdown directory in the root folder')

    def do_add_tags(self, arg):
        NotImplemented()

    def help_add_tags(self):
        print('Use llm to add tags to the note. The llm will check if a relevant tag exists in the db first')

    def do_dream(self, arg):
        desc = ' '.join(arg.split(' '))
        self.llm.dream(desc)

    def help_dream(self):
        print('Generate an image from a description')

    def cmdloop(self, intro=None):
        print(intro)
        while self.should_run:
            try:
                super().cmdloop(intro='')
                break
            except KeyboardInterrupt:
                print("^C")
                self.exit()

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
        if len(line) <= 1:
            return [c[3:] + ' ' for c in self.get_names() if c.startswith(f'do_{text}')][state]

        # If we're completing arguments for a command
        cmd = line[0]
        cmds = ['link', 'open', 'crit', 'crit_diff']
        if cmd in cmds: 
            if len(line) == 2:
                return self.complete_note_name(text, state)

        if cmd == 'set_root':
            if len(line) == 2:
                return self.complete_path(text, state)

        return None

    def complete_note_name(self, text, state):
        names = self.get_note_names()
        matches = [n for n in names if n.startswith(text)]
        if state < len(matches):
            return f'"{matches[state]}"'
        else:
            return None

    def complete_path(self, text, state):
        # Expand user directory if path starts with ~
        text = Path(text).expanduser()

        if text == Path('.'):
            # If no text, suggest current directory contents
            completions = list(Path('.').iterdir())
        elif text.is_dir():
            # If text is a directory, suggest its contents
            completions = list(text.iterdir())
        else:
            # If text is a partial path, suggest matching directories
            parent = text.parent
            completions = [p for p in parent.iterdir() if p.is_dir() and p.name.startswith(text.name)]

        # Sort completions and add trailing slash to directories
        completions = sorted(str(p) + ('/' if p.is_dir() else '') for p in completions)
        return completions[state] if state < len(completions) else None
