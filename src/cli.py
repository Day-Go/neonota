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


