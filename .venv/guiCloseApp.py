import tkinter as tk
from tkinter import scrolledtext, messagebox
import win32gui
import win32process
import psutil
import time
import threading
import win32con
import configparser
import keyboard
import pyautogui  # Импортируем библиотеку для работы с мышью
from menu import create_menu  # Импортируем меню из другого файла


# Global variables for storing the current window position and PID of the process
hwnds = []
current_pids = []
CONFIG_FILE = 'window_position.ini'

def find_windows_by_pid(pid):
    """Find all window handles for a given process ID (PID)."""
    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            found_pid = win32process.GetWindowThreadProcessId(hwnd)[1]
            if found_pid == pid:
                extra.append(hwnd)

    hwnd_list = []
    win32gui.EnumWindows(callback, hwnd_list)
    return hwnd_list

def monitor_gto_process(log_text, start_button, exit_event):
    """Monitor the GTO.EXE processes and log their status."""
    global hwnds, current_pids
    process_name = 'GTO.EXE'

    while not exit_event.is_set():
        gto_pids = []
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'].lower() == process_name.lower():
                gto_pids.append(proc.info['pid'])

        if not gto_pids:
            if current_pids:
                add_log(log_text, "All ended.")
                current_pids = []
                hwnds = []
            time.sleep(1)
            continue

        new_pids = [pid for pid in gto_pids if pid not in current_pids]
        terminated_pids = [pid for pid in current_pids if pid not in gto_pids]

        for pid in new_pids:
            current_pids.append(pid)
            hwnds += find_windows_by_pid(pid)
            add_log(log_text, f"New PID: {pid}")

        for pid in terminated_pids:
            current_pids.remove(pid)

        for hwnd in hwnds:
            if win32gui.IsIconic(hwnd):
                add_log(log_text, "Minimized, ending.")
                try:
                    for pid in current_pids:
                        proc = psutil.Process(pid)
                        proc.terminate()
                        proc.wait(timeout=3)
                    add_log(log_text, "All ended.")
                    current_pids = []
                    hwnds = []
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired) as e:
                    add_log(log_text, f"Error: {e}")
                break  # Terminate only once

        if new_pids:
            add_log(log_text, "New running.")

        for pid in current_pids:
            hwnds = find_windows_by_pid(pid)
            for hwnd in hwnds:
                if win32gui.IsIconic(hwnd):
                    add_log(log_text, f"Minimized PID {pid}.")
                    try:
                        proc = psutil.Process(pid)
                        proc.terminate()
                        proc.wait(timeout=3)
                        add_log(log_text, f"Ended PID {pid}.")
                        current_pids.remove(pid)
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired) as e:
                        add_log(log_text, f"Error PID {pid}: {e}")

        time.sleep(1)

def add_log(log_text, message):
    """Add a log message to the log_text widget, keeping only the last 4 messages."""
    log_text.config(state=tk.NORMAL)
    log_text.insert(tk.END, message + "\n")
    log_lines = log_text.get("1.0", tk.END).splitlines()
    if len(log_lines) > 5:
        log_text.delete("1.0", "2.0")
    log_text.config(state=tk.DISABLED)
    log_text.yview(tk.END)

def minimize_gto_windows(log_text):
    """Minimize all GTO.EXE windows."""
    global hwnds
    if hwnds:
        for hwnd in hwnds:
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        add_log(log_text, "All GTO.EXE windows minimized.")
    else:
        add_log(log_text, "GTO.EXE not found. Cannot minimize.")

def set_global_hotkey(log_text):
    """Set global hotkeys."""
    # Устанавливаем глобальный хоткей для минимизации окон GTO.EXE
    keyboard.add_hotkey('shift+a', lambda: minimize_gto_windows(log_text))

def duplicate_mouse_click():
    """Duplicate the left mouse click."""
    x, y = pyautogui.position()  # Получаем текущую позицию мыши
    pyautogui.click(x, y)  # Выполняем клик

def save_window_position(root):
    """Save the current position of the window to a config file."""
    config = configparser.ConfigParser()
    config['WindowPosition'] = {
        'x': root.winfo_x(),
        'y': root.winfo_y()
    }
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

def load_window_position():
    """Load the window position from the config file."""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if 'WindowPosition' in config:
        x = config.getint('WindowPosition', 'x', fallback=100)
        y = config.getint('WindowPosition', 'y', fallback=100)
        return x, y
    return 100, 100

def main():
    """Main function to set up the Tkinter GUI and start monitoring."""
    global current_pids, hwnds, root, log_text, exit_event

    root = tk.Tk()
    root.title("t2")
    # root.iconbitmap('t2.ico')

    x, y = load_window_position()
    root.geometry(f"180x100+{x}+{y}")
    root.resizable(False, False)

    log_text = scrolledtext.ScrolledText(root, height=4, width=24)
    log_text.pack()

    exit_event = threading.Event()
    monitor_thread = None

    def start_monitor(start_button):
        nonlocal monitor_thread
        exit_event.clear()
        start_button.config(state="disabled")
        stop_button.config(state="normal")
        monitor_thread = threading.Thread(target=monitor_gto_process, args=(log_text, start_button, exit_event))
        monitor_thread.daemon = True
        monitor_thread.start()
        add_log(log_text, "Monitoring.")

    def stop_monitor():
        nonlocal monitor_thread
        exit_event.set()
        if monitor_thread is not None:
            monitor_thread.join()
        start_button.config(state="normal")
        stop_button.config(state="disabled")
        add_log(log_text, "Stopped.")

    def on_closing():
        stop_monitor()
        save_window_position(root)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Добавляем меню
    menu_bar = create_menu(root)
    root.config(menu=menu_bar)

    start_button = tk.Button(root, text="Start", command=lambda: start_monitor(start_button), state="normal")
    start_button.pack(side=tk.LEFT, padx=5, pady=5)

    stop_button = tk.Button(root, text="Stop", command=stop_monitor, state="disabled")
    stop_button.pack(side=tk.LEFT, padx=5, pady=5)

    minimize_button = tk.Button(root, text="_____", command=lambda: minimize_gto_windows(log_text), state="normal")
    minimize_button.pack(side=tk.LEFT, padx=5, pady=5)

    start_monitor(start_button)  # Automatically start the monitor on program launch

    # Устанавливаем глобальные хоткеи
    keyboard.add_hotkey('alt+d', duplicate_mouse_click)  # Добавляем хоткей для дублирования левого клика
    set_global_hotkey(log_text)  # Set the global hotkey

    root.mainloop()

if __name__ == "__main__":
    main()
