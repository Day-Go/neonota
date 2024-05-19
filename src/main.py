
from watcher import Watcher
from gui import run_folder_picker

selected_folder_path = run_folder_picker()

if selected_folder_path:
    w = Watcher(selected_folder_path)
    w.run()
else:
    print("No folder selected. Exiting.")