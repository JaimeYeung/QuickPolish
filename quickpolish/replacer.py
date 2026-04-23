import subprocess
import time
import pyperclip


def replace_selected(text: str, target_app: str) -> None:
    """
    Writes text to clipboard, restores focus to target_app, simulates Cmd+V.
    Matches the design in docs/superpowers/plans — no extra mouse clicks, so
    the original selection (preserved across Cmd+C) is replaced cleanly.
    """
    pyperclip.copy(text)

    subprocess.run(
        ["osascript", "-e", f'tell application "{target_app}" to activate'],
        capture_output=True,
    )
    time.sleep(0.15)

    subprocess.run(
        ["osascript", "-e",
         'tell application "System Events" to keystroke "v" using command down'],
        capture_output=True,
    )


def get_frontmost_app() -> str:
    result = subprocess.run(
        ["osascript", "-e",
         'tell application "System Events" to get name of first application process '
         'whose frontmost is true'],
        capture_output=True, text=True,
    )
    return result.stdout.strip()
