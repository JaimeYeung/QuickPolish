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
