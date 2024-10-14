import keyboard
import win32gui
import win32con

# Переменная для хранения hwnd окон GTO
hwnds = []


def set_global_hotkey(log_text):
    """Set global hotkeys."""
    # Устанавливаем глобальный хоткей для минимизации окон GTO.EXE
    keyboard.add_hotkey('shift+a', lambda: minimize_gto_windows(log_text))
