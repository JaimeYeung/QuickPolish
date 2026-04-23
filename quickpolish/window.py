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
        # self.overrideredirect(True)
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{WIDTH}x200+{(sw - WIDTH) // 2}+{(sh - 200) // 2}")

    def _build_ui(self):
        title_bar = tk.Frame(self, bg="#2a2a2a", padx=14, pady=10)
        title_bar.pack(fill="x")
        tk.Label(title_bar, text="✦ QuickPolish", bg="#2a2a2a", fg=FG,
                 font=FONT_TITLE).pack(side="left")

        self._text_frame = tk.Frame(self, bg=BG, padx=14, pady=14)
        self._text_frame.pack(fill="both", expand=True)
        self._text_label = tk.Label(
            self._text_frame, text="", bg=BG, fg=FG,
            font=FONT_MAIN, wraplength=WIDTH - 28, justify="left", anchor="nw",
        )
        self._text_label.pack(fill="both", expand=True)

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
        tk.Label(footer, text="↩ Replace    Tab Switch    Esc Cancel",
                 bg="#2a2a2a", fg=MUTED, font=FONT_SMALL).pack(side="left")

    def _render(self):
        if self._state.is_loading:
            self._text_label.config(text="Rewriting…", fg=MUTED)
            for lbl in self._mode_labels.values():
                lbl.config(fg=MUTED, font=FONT_SMALL)
        else:
            self._text_label.config(
                text=self._state.current_text,
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
            self._on_accept(text)  # on_accept destroys window at the right time
        return "break"

    def _on_esc(self, _event):
        self.destroy()
        self._on_cancel()
        return "break"
