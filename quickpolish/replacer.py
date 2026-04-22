import subprocess
import time
import pyperclip


def replace_selected(text: str, target_app: str) -> None:
    """
    Writes text to clipboard, restores focus to target_app, simulates Cmd+V.
    target_app is the name of the process that had focus before the preview
    window opened (e.g. "Mail", "Google Chrome").
    """
    pyperclip.copy(text)

    subprocess.run(
        ["osascript", "-e", f'tell application "{target_app}" to activate'],
        capture_output=True,
    )
    time.sleep(0.1)

    subprocess.run(
        ["osascript", "-e",
         'tell application "System Events" to keystroke "v" using command down'],
        capture_output=True,
    )
