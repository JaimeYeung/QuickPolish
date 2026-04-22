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
