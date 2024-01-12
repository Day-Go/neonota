from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import tkinter as tk
from tkinter import simpledialog
import os
import threading

class Watcher:
    DIRECTORY_TO_WATCH = "path/to/your/directory"

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
    @staticmethod
    def on_created(event):
        if not event.is_directory:
            threading.Thread(target=popup_rename, args=(event.src_path,)).start()

def popup_rename(file_path):
    root = tk.Tk()
    root.withdraw()
    new_name = simpledialog.askstring("File Renaming", "Enter new name for the file:", parent=root)
    if new_name:
        base_path, ext = os.path.splitext(file_path)
        os.rename(file_path, os.path.join(os.path.dirname(file_path), new_name + ext))
    root.destroy()

if __name__ == "__main__":
    w = Watcher()
    w.run()
