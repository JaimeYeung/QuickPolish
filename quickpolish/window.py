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
HEIGHT = 220


class PreviewWindow(tk.Toplevel):
    def __init__(self, root: tk.Tk, state: WindowState, on_accept, on_cancel):
        super().__init__(root)
        self._state = state
        self._on_accept = on_accept
        self._on_cancel = on_cancel
        self._setup_window()
        self._build_ui()
        self._render()
        # Toplevel-level bindings are the fallback while the Text widget is
        # disabled (loading / error state) and can't receive focus.
        self.bind("<Tab>", self._on_tab)
        self.bind("<Return>", self._on_enter)
        self.bind("<Escape>", self._on_esc)
        self.focus_force()

    def _setup_window(self):
        self.title("QuickPolish")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{WIDTH}x{HEIGHT}+{(sw - WIDTH) // 2}+{(sh - HEIGHT) // 2}")

    def _build_ui(self):
        title_bar = tk.Frame(self, bg="#2a2a2a", padx=14, pady=10)
        title_bar.pack(fill="x")
        tk.Label(title_bar, text="✦ QuickPolish", bg="#2a2a2a", fg=FG,
                 font=FONT_TITLE).pack(side="left")

        self._text_frame = tk.Frame(self, bg=BG, padx=14, pady=14)
        self._text_frame.pack(fill="both", expand=True)
        self._text = tk.Text(
            self._text_frame,
            bg=BG, fg=FG, insertbackground=FG,
            font=FONT_MAIN, wrap="word",
            relief="flat", borderwidth=0, highlightthickness=0,
            height=5,
        )
        self._text.pack(fill="both", expand=True)

        # Widget-level bindings override the Text widget's default Tab/Return
        # behavior while the user is editing. Each returns "break" to stop the
        # default class binding from also firing.
        self._text.bind("<Tab>", self._on_tab)
        self._text.bind("<Return>", self._on_enter)
        self._text.bind("<Shift-Return>", self._on_shift_enter)
        self._text.bind("<Escape>", self._on_esc)

        mode_bar = tk.Frame(self, bg="#2a2a2a", padx=14, pady=8)
        mode_bar.pack(fill="x")
        self._mode_labels = {}
        for mode in MODES:
            lbl = tk.Label(mode_bar, text=mode.capitalize(), bg="#2a2a2a",
                           fg=MUTED, font=FONT_SMALL)
            lbl.pack(side="left", padx=6)
            self._mode_labels[mode] = lbl

        footer = tk.Frame(self, bg="#2a2a2a", padx=14, pady=6)
        footer.pack(fill="x")
        tk.Label(
            footer,
            text="↩ Replace    ⇧↩ Newline    Tab Switch    Esc Cancel",
            bg="#2a2a2a", fg=MUTED, font=FONT_SMALL,
        ).pack(side="left")

    def _set_text_widget(self, content: str, *, editable: bool, fg: str):
        # Must switch to "normal" to modify, even if we'll end up disabled.
        self._text.config(state="normal")
        self._text.delete("1.0", "end")
        self._text.insert("1.0", content)
        self._text.config(fg=fg, state="normal" if editable else "disabled")

    def _current_widget_text(self) -> str:
        # Text always appends a trailing newline; strip it via end-1c.
        return self._text.get("1.0", "end-1c")

    def _render(self):
        if self._state.is_loading:
            self._set_text_widget("Rewriting…", editable=False, fg=MUTED)
            for lbl in self._mode_labels.values():
                lbl.config(fg=MUTED, font=FONT_SMALL)
        else:
            if self._state.has_error:
                self._set_text_widget(
                    self._state.current_text, editable=False, fg="#ff6b6b",
                )
            else:
                self._set_text_widget(
                    self._state.current_text, editable=True, fg=FG,
                )
                # Let the user start typing immediately; cursor at end.
                self._text.mark_set("insert", "end")
                self._text.focus_set()
            for mode, lbl in self._mode_labels.items():
                if mode == self._state.current_mode:
                    lbl.config(fg=ACCENT, font=(*FONT_SMALL[:2], "bold"))
                else:
                    lbl.config(fg=MUTED, font=FONT_SMALL)

    def update_state(self):
        self._render()

    def _save_edits_to_state(self):
        """Persist the widget's current content into state for the active mode."""
        if not self._state.is_loading and not self._state.has_error:
            self._state.update_current_text(self._current_widget_text())

    def _on_tab(self, _event):
        if not self._state.is_loading:
            self._save_edits_to_state()
            self._state.cycle_mode()
            self._render()
        return "break"

    def _on_enter(self, _event):
        if not self._state.is_loading and not self._state.has_error:
            text = self._current_widget_text()
            self._state.update_current_text(text)
            self._on_accept(text)
        return "break"

    def _on_shift_enter(self, _event):
        if not self._state.is_loading and not self._state.has_error:
            self._text.insert("insert", "\n")
        return "break"

    def _on_esc(self, _event):
        self.destroy()
        self._on_cancel()
        return "break"
