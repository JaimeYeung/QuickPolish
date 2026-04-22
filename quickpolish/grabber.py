import subprocess
import time
import pyperclip


def get_selected_text() -> str | None:
    """
    Simulates Cmd+C to copy whatever is selected, then reads the clipboard.
    Returns None if nothing was selected (clipboard didn't change).
    """
    original = pyperclip.paste()

    sentinel = "\x00__qp_sentinel__\x00"
    pyperclip.copy(sentinel)

    subprocess.run(
        ["osascript", "-e",
         'tell application "System Events" to keystroke "c" using command down'],
        capture_output=True,
    )

    time.sleep(0.15)

    result = pyperclip.paste()

    if result == sentinel:
        pyperclip.copy(original)
        return None

    return result


def get_frontmost_app() -> str:
    """Returns the name of the currently focused application."""
    result = subprocess.run(
        ["osascript", "-e",
         'tell application "System Events" to get name of first application process '
         'whose frontmost is true'],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()
