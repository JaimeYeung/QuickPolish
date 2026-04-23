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
        self._root.withdraw()
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
            return

        target_app = get_frontmost_app()
        text = get_selected_text()

        if not text or not text.strip():
            return

        state = WindowState()

        def on_accept(result: str):
            # Runs on the Tk main thread (from the window's <Return> handler).
            self._active_window = None
            if win.winfo_exists():
                win.destroy()
            # Paste in a background thread so we don't block the Tk main loop
            # while osascript activates the target app.
            threading.Thread(
                target=replace_selected,
                args=(result, target_app),
                daemon=True,
            ).start()

        def on_cancel():
            self._active_window = None
            if win.winfo_exists():
                win.destroy()

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
        # Avoid pynput.keyboard.GlobalHotKeys on macOS: in some pynput versions
        # its internal _on_press signature doesn't match what the darwin backend
        # calls, which raises
        #   TypeError: GlobalHotKeys._on_press() missing 1 required positional argument: 'injected'
        # Use HotKey + Listener instead — this is pynput's recommended pattern
        # and it doesn't hit that buggy class at all.
        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse("<ctrl>+g"),
            self._on_hotkey,
        )

        def _for_canonical(f):
            def wrapped(k):
                try:
                    f(listener.canonical(k))
                except Exception:
                    # Never let a stray event kill the listener thread.
                    pass
            return wrapped

        listener = keyboard.Listener(
            on_press=_for_canonical(hotkey.press),
            on_release=_for_canonical(hotkey.release),
        )
        listener.daemon = True
        listener.start()

    def run(self):
        self._start_hotkey_listener()
        self._root.after(100, self._poll_queue)
        print("QuickPolish running. Press ⌃G on selected text. Ctrl+C to quit.")
        self._root.mainloop()
