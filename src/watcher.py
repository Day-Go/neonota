import os
import time
import threading
import pyautogui
import tkinter as tk
from win32gui import SetForegroundWindow
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from openai import OpenAI

client = OpenAI()

class Watcher:
    DIRECTORY_TO_WATCH = r"C:\Users\lucar\Documents\Dago\Example Vault"

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                # Keep the thread alive
                pass
        except:
            self.observer.stop()
            print("Observer Stopped")

class Handler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            with open(event.src_path, "r") as f:
                contents = f.read()
        elif event.is_directory:
            return 
        
        if '/nv' in contents:
            print(f"Found '/nv' tag in {event.src_path}")

            # Remove the '/nv' tag from the contents
            modified_contents = contents.replace('/nv', '')

            # Write the modified contents back to the file
            with open(event.src_path, "w") as f:
                f.write(modified_contents)

            print(f"'/nv' tag removed and file saved.")
            
            threading.Thread(target=popup_command, args=(event.src_path, contents,)).start()
        else:
            print(f"No '/nv' tag found in {event.src_path}")
            return

def popup_command(file_path, contents):
    # Create the main window
    print(file_path)
    root = tk.Tk()

    # Function to handle enter key press in entry widget
    def on_enter(event, file_path):
        command = entry.get()
        print(f"Command entered: {command}")

        if command == 'name':
            print(contents)
            query = (f'Come up with a concise, appropriate, and descriptive file name for the' 
                     'following markdown file. '
                     'Output only the file name.'
                     f'\n\n{contents}\n\n')

            response = client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": query},
                ]
            )

            new_file_name = response.choices[0].message.content \
                .strip("\"") \
                .replace("_", " ") \
                .replace("-", " ")
            
            if not new_file_name.endswith('.md'):
                new_file_name = new_file_name + '.md'

            file_path = Path(file_path)
            parent = file_path.parent
            new_file_path = parent / f"{new_file_name}"
            os.rename(file_path, new_file_path)

            print(f"File name: {new_file_name}")
        elif command == 'concepts':
            print(contents)
            query = (f'Come up with a list of concepts for the following markdown file. '
                     'Output only the concepts.'
                     f'\n\n{contents}\n\n')

            response = client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": query},
                ]
            )

            concepts = response.choices[0].message.content

            print(f"Concepts: {concepts}\n")

            query = (f'Given the list of concepts and the following markdown file, '
                     'Split the file into sections based on the concepts.'
                     'Output the sections with the concepts as headers.'
                     f'\n\nConcepts:\n{concepts}\n\nContents:\n{contents}\n\n')
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": query},
                ]
            )

            sections = response.choices[0].message.content
            print(f"Sections: {sections}")

        root.destroy()

    # Create an entry widget for command input
    entry = tk.Entry(root)
    entry.pack(fill=tk.BOTH, expand=True)

    # Bind the enter key to the on_enter function
    entry.bind("<Return>", lambda event, arg=file_path: on_enter(event, arg))

    hwnd = root.winfo_id()
    pyautogui.press("alt")
    try:
        SetForegroundWindow(hwnd)
    except Exception as e:
        print(f"Error setting window to foreground: {e}")

    # Automatically focus the entry widget and bring the window to the front
    root.attributes('-topmost', True)
    root.focus_force()
    entry.focus_set()

    root.mainloop()


if __name__ == "__main__":
    w = Watcher()
    w.run()
