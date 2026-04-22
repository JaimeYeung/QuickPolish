# QuickPolish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a macOS background app that rewrites selected text via OpenAI API when the user presses ⌥Space, showing a preview window with three modes (Natural / Professional / Shorter) before replacing.

**Architecture:** A single Python process with tkinter on the main thread (hidden root, polling a queue every 100ms) and a pynput hotkey listener on a daemon background thread. When the hotkey fires, it puts a job on the queue; the main thread grabs the selected text, fires 3 parallel OpenAI requests in a ThreadPoolExecutor, and shows a floating preview window. On Enter, it restores focus to the original app and simulates Cmd+V.

**Tech Stack:** Python 3.11+, openai, pynput, pyperclip, tkinter (stdlib), pytest, pytest-mock

---

## File Map

| File | Responsibility |
|------|----------------|
| `requirements.txt` | All dependencies pinned |
| `main.py` | Entry point — starts the app |
| `quickpolish/__init__.py` | Empty |
| `quickpolish/config.py` | Read/write `~/.quickpolish/config.json` |
| `quickpolish/rewriter.py` | 3 parallel OpenAI requests with correct prompts |
| `quickpolish/grabber.py` | Simulate Cmd+C, read clipboard, detect empty selection |
| `quickpolish/replacer.py` | Restore app focus, write clipboard, simulate Cmd+V |
| `quickpolish/window_state.py` | Pure Python state machine: modes, results, cycling |
| `quickpolish/window.py` | tkinter preview window — loading, results, keyboard handling |
| `quickpolish/app.py` | Main loop: queue polling, pipeline orchestration |
| `tests/test_config.py` | Config read/write/defaults |
| `tests/test_rewriter.py` | OpenAI calls with mocked client |
| `tests/test_window_state.py` | Mode cycling, state transitions |

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `quickpolish/__init__.py`
- Create: `tests/__init__.py`
- Create: `.gitignore`

- [ ] **Step 1: Create requirements.txt**

```
openai>=1.30.0
pynput>=1.7.6
pyperclip>=1.8.2
pytest>=8.0.0
pytest-mock>=3.14.0
```

- [ ] **Step 2: Create directory structure**

```bash
mkdir -p quickpolish tests
touch quickpolish/__init__.py tests/__init__.py
```

- [ ] **Step 3: Create .gitignore**

```
__pycache__/
*.pyc
.env
*.egg-info/
dist/
.pytest_cache/
```

- [ ] **Step 4: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 5: Commit**

```bash
git init
git add requirements.txt quickpolish/__init__.py tests/__init__.py .gitignore
git commit -m "chore: project setup"
```

---

## Task 2: Config Module

**Files:**
- Create: `quickpolish/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_config.py
import json
import pytest
from pathlib import Path
from quickpolish.config import Config


def test_defaults_when_no_file(tmp_path):
    cfg = Config(config_dir=tmp_path)
    assert cfg.get("hotkey") == "alt+space"
    assert cfg.get("model") == "gpt-4o"
    assert cfg.get("openai_api_key") is None


def test_saves_and_loads(tmp_path):
    cfg = Config(config_dir=tmp_path)
    cfg.set("openai_api_key", "sk-test")
    cfg2 = Config(config_dir=tmp_path)
    assert cfg2.get("openai_api_key") == "sk-test"


def test_has_api_key_false_when_missing(tmp_path):
    cfg = Config(config_dir=tmp_path)
    assert cfg.has_api_key() is False


def test_has_api_key_true_when_set(tmp_path):
    cfg = Config(config_dir=tmp_path)
    cfg.set("openai_api_key", "sk-test")
    assert cfg.has_api_key() is True
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError` or `ImportError` — config module doesn't exist yet.

- [ ] **Step 3: Implement config.py**

```python
# quickpolish/config.py
import json
from pathlib import Path

DEFAULTS = {
    "hotkey": "alt+space",
    "model": "gpt-4o",
    "openai_api_key": None,
}


class Config:
    def __init__(self, config_dir: Path = None):
        self._dir = config_dir or Path.home() / ".quickpolish"
        self._path = self._dir / "config.json"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self) -> dict:
        if self._path.exists():
            with open(self._path) as f:
                return {**DEFAULTS, **json.load(f)}
        return dict(DEFAULTS)

    def get(self, key: str):
        return self._data.get(key)

    def set(self, key: str, value):
        self._data[key] = value
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2)

    def has_api_key(self) -> bool:
        key = self._data.get("openai_api_key")
        return bool(key and key.strip())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_config.py -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add quickpolish/config.py tests/test_config.py
git commit -m "feat: config module with read/write and defaults"
```

---

## Task 3: Rewriter Module

**Files:**
- Create: `quickpolish/rewriter.py`
- Create: `tests/test_rewriter.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_rewriter.py
import pytest
from unittest.mock import MagicMock, patch
from quickpolish.rewriter import Rewriter, MODES


def make_mock_response(text: str):
    msg = MagicMock()
    msg.content[0].text = text
    choice = MagicMock()
    choice.message.content = text
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def test_modes_are_correct():
    assert set(MODES) == {"natural", "professional", "shorter"}


def test_rewrite_all_returns_all_modes(mocker):
    client = MagicMock()
    client.chat.completions.create.return_value = make_mock_response("fixed text")
    rewriter = Rewriter(client=client, model="gpt-4o")

    results = rewriter.rewrite_all("some text")

    assert set(results.keys()) == {"natural", "professional", "shorter"}
    assert results["natural"] == "fixed text"
    assert results["professional"] == "fixed text"
    assert results["shorter"] == "fixed text"


def test_rewrite_all_makes_3_api_calls(mocker):
    client = MagicMock()
    client.chat.completions.create.return_value = make_mock_response("ok")
    rewriter = Rewriter(client=client, model="gpt-4o")

    rewriter.rewrite_all("hello")

    assert client.chat.completions.create.call_count == 3


def test_rewrite_all_on_api_error_returns_error_string(mocker):
    client = MagicMock()
    client.chat.completions.create.side_effect = Exception("network error")
    rewriter = Rewriter(client=client, model="gpt-4o")

    results = rewriter.rewrite_all("hello")

    for mode in MODES:
        assert "error" in results[mode].lower()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_rewriter.py -v
```

Expected: `ImportError` — rewriter module doesn't exist yet.

- [ ] **Step 3: Implement rewriter.py**

```python
# quickpolish/rewriter.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

MODES = ["natural", "professional", "shorter"]

SYSTEM_PROMPT = """You are a text rewriter. The user will give you text that may be in English, Chinese, or a mix of both.

Your job: understand the intended meaning and express it in natural American English.

Rules:
- Always output English only
- Do not translate literally — understand the intent and express it the way a native speaker would
- Do not add meaning that wasn't there
- Do not sound like AI. No "Certainly!", no "I hope this helps", no filler
- Return ONLY the rewritten text, nothing else. No quotes, no explanation."""

USER_PROMPTS = {
    "natural": (
        "Rewrite this in casual, natural American English — the way you'd text a friend. "
        "Keep it chill and real.\n\nText: {text}"
    ),
    "professional": (
        "Rewrite this for a professional email. Sound confident, direct, and warm — like a real person, not a robot. "
        "No corporate filler: no 'I hope this email finds you well', no 'please don't hesitate to reach out', "
        "no 'as per my previous email'.\n\nText: {text}"
    ),
    "shorter": (
        "Rewrite this in natural American English, then trim it down. "
        "Keep the meaning and tone. Remove redundancy without losing the point.\n\nText: {text}"
    ),
}


class Rewriter:
    def __init__(self, client: OpenAI = None, model: str = "gpt-4o"):
        self._client = client
        self._model = model

    def _call_one(self, mode: str, text: str) -> tuple[str, str]:
        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_PROMPTS[mode].format(text=text)},
                ],
                max_tokens=1000,
                temperature=0.7,
            )
            return mode, resp.choices[0].message.content.strip()
        except Exception as e:
            return mode, f"[error: {e}]"

    def rewrite_all(self, text: str) -> dict[str, str]:
        results = {}
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {pool.submit(self._call_one, mode, text): mode for mode in MODES}
            for future in as_completed(futures):
                mode, result = future.result()
                results[mode] = result
        return results
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_rewriter.py -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add quickpolish/rewriter.py tests/test_rewriter.py
git commit -m "feat: rewriter module with 3 parallel OpenAI requests"
```

---

## Task 4: Grabber and Replacer Modules

**Files:**
- Create: `quickpolish/grabber.py`
- Create: `quickpolish/replacer.py`

No unit tests for these — they wrap macOS system calls (Cmd+C/V via osascript). They'll be validated during manual integration testing.

- [ ] **Step 1: Implement grabber.py**

```python
# quickpolish/grabber.py
import subprocess
import time
import pyperclip


def get_selected_text() -> str | None:
    """
    Simulates Cmd+C to copy whatever is selected, then reads the clipboard.
    Returns None if nothing was selected (clipboard didn't change).
    Saves and restores the original clipboard content on failure.
    """
    original = pyperclip.paste()

    # Use a sentinel to detect "nothing was copied"
    sentinel = "\x00__qp_sentinel__\x00"
    pyperclip.copy(sentinel)

    subprocess.run(
        ["osascript", "-e",
         'tell application "System Events" to keystroke "c" using command down'],
        capture_output=True,
    )

    time.sleep(0.15)  # wait for clipboard to update

    result = pyperclip.paste()

    if result == sentinel:
        # Nothing was selected — restore original
        pyperclip.copy(original)
        return None

    return result
```

- [ ] **Step 2: Implement replacer.py**

```python
# quickpolish/replacer.py
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

    # Bring back the original app
    subprocess.run(
        ["osascript", "-e", f'tell application "{target_app}" to activate'],
        capture_output=True,
    )
    time.sleep(0.1)  # wait for focus to transfer

    # Simulate Cmd+V
    subprocess.run(
        ["osascript", "-e",
         'tell application "System Events" to keystroke "v" using command down'],
        capture_output=True,
    )


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
```

- [ ] **Step 3: Commit**

```bash
git add quickpolish/grabber.py quickpolish/replacer.py
git commit -m "feat: grabber and replacer modules for clipboard + keystroke simulation"
```

---

## Task 5: Window State Machine

**Files:**
- Create: `quickpolish/window_state.py`
- Create: `tests/test_window_state.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_window_state.py
import pytest
from quickpolish.window_state import WindowState

RESULTS = {
    "natural": "Hey, sounds good to me.",
    "professional": "That works for me.",
    "shorter": "Works for me.",
}


def test_initial_mode_is_natural():
    state = WindowState()
    assert state.current_mode == "natural"


def test_is_loading_before_results():
    state = WindowState()
    assert state.is_loading is True


def test_not_loading_after_results_set():
    state = WindowState()
    state.set_results(RESULTS)
    assert state.is_loading is False


def test_current_text_after_results():
    state = WindowState()
    state.set_results(RESULTS)
    assert state.current_text == "Hey, sounds good to me."


def test_cycle_mode_natural_to_professional():
    state = WindowState()
    state.set_results(RESULTS)
    state.cycle_mode()
    assert state.current_mode == "professional"
    assert state.current_text == "That works for me."


def test_cycle_mode_wraps_around():
    state = WindowState()
    state.set_results(RESULTS)
    state.cycle_mode()  # professional
    state.cycle_mode()  # shorter
    state.cycle_mode()  # back to natural
    assert state.current_mode == "natural"


def test_has_error_when_result_starts_with_error():
    state = WindowState()
    state.set_results({
        "natural": "[error: network error]",
        "professional": "[error: network error]",
        "shorter": "[error: network error]",
    })
    assert state.has_error is True


def test_no_error_on_normal_results():
    state = WindowState()
    state.set_results(RESULTS)
    assert state.has_error is False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_window_state.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement window_state.py**

```python
# quickpolish/window_state.py
from quickpolish.rewriter import MODES


class WindowState:
    def __init__(self):
        self._results: dict[str, str] = {}
        self._mode_index: int = 0
        self.is_loading: bool = True

    @property
    def current_mode(self) -> str:
        return MODES[self._mode_index]

    @property
    def current_text(self) -> str:
        return self._results.get(self.current_mode, "")

    @property
    def has_error(self) -> bool:
        return any(v.startswith("[error:") for v in self._results.values())

    def set_results(self, results: dict[str, str]) -> None:
        self._results = results
        self.is_loading = False

    def cycle_mode(self) -> None:
        self._mode_index = (self._mode_index + 1) % len(MODES)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_window_state.py -v
```

Expected: 8 tests pass.

- [ ] **Step 5: Commit**

```bash
git add quickpolish/window_state.py tests/test_window_state.py
git commit -m "feat: window state machine for mode cycling"
```

---

## Task 6: Preview Window (tkinter UI)

**Files:**
- Create: `quickpolish/window.py`

No unit tests — tkinter rendering. Tested manually during integration.

- [ ] **Step 1: Implement window.py**

```python
# quickpolish/window.py
import tkinter as tk
from quickpolish.window_state import WindowState
from quickpolish.rewriter import MODES

BG = "#1e1e1e"
FG = "#f0f0f0"
ACCENT = "#5b9cf6"
MUTED = "#666666"
FONT_MAIN = ("SF Pro Display", 14)
FONT_SMALL = ("SF Pro Display", 11)
FONT_TITLE = ("SF Pro Display", 12, "bold")
WIDTH = 420


class PreviewWindow(tk.Toplevel):
    def __init__(self, root: tk.Tk, state: WindowState, on_accept, on_cancel):
        super().__init__(root)
        self._state = state
        self._on_accept = on_accept
        self._on_cancel = on_cancel
        self._setup_window()
        self._build_ui()
        self._render()
        self.bind("<Tab>", self._on_tab)
        self.bind("<Return>", self._on_enter)
        self.bind("<Escape>", self._on_esc)
        self.focus_force()

    def _setup_window(self):
        self.title("QuickPolish")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.overrideredirect(True)  # borderless
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{WIDTH}+{(sw - WIDTH) // 2}+{(sh - 260) // 2}")

    def _build_ui(self):
        # Title bar
        title_bar = tk.Frame(self, bg="#2a2a2a", padx=14, pady=10)
        title_bar.pack(fill="x")
        tk.Label(title_bar, text="✦ QuickPolish", bg="#2a2a2a", fg=FG,
                 font=FONT_TITLE).pack(side="left")

        # Text area
        self._text_frame = tk.Frame(self, bg=BG, padx=14, pady=14)
        self._text_frame.pack(fill="both", expand=True)
        self._text_label = tk.Label(
            self._text_frame, text="", bg=BG, fg=FG,
            font=FONT_MAIN, wraplength=WIDTH - 28, justify="left", anchor="nw",
        )
        self._text_label.pack(fill="both", expand=True)

        # Mode bar
        mode_bar = tk.Frame(self, bg="#2a2a2a", padx=14, pady=8)
        mode_bar.pack(fill="x")
        self._mode_labels = {}
        for mode in MODES:
            lbl = tk.Label(mode_bar, text=mode.capitalize(), bg="#2a2a2a",
                           fg=MUTED, font=FONT_SMALL)
            lbl.pack(side="left", padx=6)
            self._mode_labels[mode] = lbl

        # Footer
        footer = tk.Frame(self, bg="#2a2a2a", padx=14, pady=6)
        footer.pack(fill="x")
        tk.Label(footer, text="↩ Replace    Tab Switch    Esc Cancel",
                 bg="#2a2a2a", fg=MUTED, font=FONT_SMALL).pack(side="left")

    def _render(self):
        if self._state.is_loading:
            self._text_label.config(text="Rewriting…", fg=MUTED)
            for lbl in self._mode_labels.values():
                lbl.config(fg=MUTED)
        else:
            text = self._state.current_text
            self._text_label.config(
                text=text,
                fg="#ff6b6b" if self._state.has_error else FG,
            )
            for mode, lbl in self._mode_labels.items():
                if mode == self._state.current_mode:
                    lbl.config(fg=ACCENT, font=(*FONT_SMALL[:2], "bold"))
                else:
                    lbl.config(fg=MUTED, font=FONT_SMALL)

    def update_state(self):
        self._render()

    def _on_tab(self, _event):
        if not self._state.is_loading:
            self._state.cycle_mode()
            self._render()
        return "break"

    def _on_enter(self, _event):
        if not self._state.is_loading and not self._state.has_error:
            text = self._state.current_text
            self.destroy()
            self._on_accept(text)
        return "break"

    def _on_esc(self, _event):
        self.destroy()
        self._on_cancel()
        return "break"
```

- [ ] **Step 2: Commit**

```bash
git add quickpolish/window.py
git commit -m "feat: tkinter preview window with loading state and mode cycling"
```

---

## Task 7: App Orchestration

**Files:**
- Create: `quickpolish/app.py`

- [ ] **Step 1: Implement app.py**

```python
# quickpolish/app.py
import queue
import threading
import tkinter as tk

from openai import OpenAI
from pynput import keyboard

from quickpolish.config import Config
from quickpolish.grabber import get_frontmost_app, get_selected_text
from quickpolish.replacer import replace_selected
from quickpolish.rewriter import Rewriter
from quickpolish.window import PreviewWindow
from quickpolish.window_state import WindowState


class App:
    def __init__(self):
        self._config = Config()
        self._queue: queue.Queue = queue.Queue()
        self._root = tk.Tk()
        self._root.withdraw()  # hidden root window
        self._active_window: PreviewWindow | None = None

        if not self._config.has_api_key():
            self._prompt_for_api_key()

        client = OpenAI(api_key=self._config.get("openai_api_key"))
        self._rewriter = Rewriter(client=client, model=self._config.get("model"))

    def _prompt_for_api_key(self):
        key = input("Enter your OpenAI API key: ").strip()
        self._config.set("openai_api_key", key)

    def _on_hotkey(self):
        self._queue.put("trigger")

    def _poll_queue(self):
        try:
            self._queue.get_nowait()
            self._run_pipeline()
        except queue.Empty:
            pass
        self._root.after(100, self._poll_queue)

    def _run_pipeline(self):
        if self._active_window and self._active_window.winfo_exists():
            return  # already open

        target_app = get_frontmost_app()
        text = get_selected_text()

        if not text or not text.strip():
            return

        state = WindowState()

        def on_accept(result: str):
            self._active_window = None
            replace_selected(result, target_app)

        def on_cancel():
            self._active_window = None

        win = PreviewWindow(self._root, state, on_accept=on_accept, on_cancel=on_cancel)
        self._active_window = win

        def fetch():
            results = self._rewriter.rewrite_all(text)

            def apply():
                state.set_results(results)
                if win.winfo_exists():
                    win.update_state()

            self._root.after(0, apply)

        threading.Thread(target=fetch, daemon=True).start()

    def _start_hotkey_listener(self):
        hotkey_str = self._config.get("hotkey")  # e.g. "alt+space"
        parts = hotkey_str.split("+")
        modifiers = {f"<{p}>" for p in parts[:-1]}
        key_char = parts[-1]

        def on_activate():
            self._on_hotkey()

        h = keyboard.GlobalHotKeys({
            "<alt>+<space>": on_activate,
        })
        h.daemon = True
        h.start()

    def run(self):
        self._start_hotkey_listener()
        self._root.after(100, self._poll_queue)
        print("QuickPolish running. Press ⌥Space on selected text. Ctrl+C to quit.")
        self._root.mainloop()
```

- [ ] **Step 2: Commit**

```bash
git add quickpolish/app.py
git commit -m "feat: app orchestration — hotkey listener, pipeline, queue polling"
```

---

## Task 8: Entry Point and First Run

**Files:**
- Create: `main.py`

- [ ] **Step 1: Implement main.py**

```python
# main.py
from quickpolish.app import App

if __name__ == "__main__":
    App().run()
```

- [ ] **Step 2: Run the app manually to verify the full flow**

```bash
python main.py
```

Expected on first run: prompt for OpenAI API key. After entering it:
```
QuickPolish running. Press ⌥Space on selected text. Ctrl+C to quit.
```

Grant **Accessibility** permission when macOS prompts (System Settings → Privacy & Security → Accessibility → add Terminal or your Python binary).

- [ ] **Step 3: Manual integration test**

1. Open TextEdit or any app, type "i think this is good idea for the project"
2. Select the text
3. Press ⌥Space
4. Verify preview window appears with Natural result
5. Press Tab — verify mode switches to Professional
6. Press Tab again — verify Shorter
7. Press Tab again — verify back to Natural
8. Press Enter — verify text is replaced in TextEdit
9. Repeat with Esc — verify original text unchanged

- [ ] **Step 4: Manual test with Chinese/Chinglish input**

1. Type "我觉得这个方案很好，我们可以试试"
2. Select and press ⌥Space
3. Verify Natural result sounds like a real text message in English
4. Verify Professional result sounds like a professional email sentence

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 6: Final commit**

```bash
git add main.py
git commit -m "feat: entry point — QuickPolish MVP complete"
```

---

## Permissions Note

On first run, macOS will ask for **Accessibility** permission (needed for Cmd+C and Cmd+V simulation). Go to:

> System Settings → Privacy & Security → Accessibility → toggle on Terminal (or whichever app runs Python)

Without this, keystrokes will silently fail and clipboard won't be copied/pasted.
