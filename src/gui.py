import tkinter as tk
from tkinter import filedialog

def run_folder_picker():
    root = tk.Tk()
    root.withdraw()

    selected_folder_path = filedialog.askdirectory(title="Select Folder")

    root.destroy()
    return selected_folder_path
