import tkinter as tk
from tkinter import messagebox


def create_menu(root):
    """Create a menu bar with a Help item that directly shows hotkeys."""
    menu_bar = tk.Menu(root)

    # Добавляем пункт Help, который сразу вызывает show_hotkeys при нажатии
    menu_bar.add_command(label="Help", command=show_hotkeys)

    return menu_bar


def show_hotkeys():
    """Display a window with the list of hotkeys."""
    hotkeys_info = (
        "Hotkey List:\n\n"
        "Shift + A:\n\n"
        "Minimize and close all GTO.EXE windows.\n"
        "Close Chrome.\n\n"
        "'Shift' OR 'D': Left Click.\n\n"
        "Start Button: Start monitoring.\n\n"
        "Stop Button: Stop monitoring."
    )
    messagebox.showinfo("Hotkeys", hotkeys_info)
