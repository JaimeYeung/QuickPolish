import pytest
from unittest.mock import MagicMock
from quickpolish.rewriter import Rewriter, MODES, strip_ai_dashes


def make_mock_response(text: str):
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


def test_strip_ai_dashes_replaces_em_dash():
    assert strip_ai_dashes("I think this works — let me know") == "I think this works, let me know"


def test_strip_ai_dashes_replaces_en_dash():
    assert strip_ai_dashes("pages 10–20 are key") == "pages 10, 20 are key"


def test_strip_ai_dashes_keeps_regular_hyphen_in_compound_words():
    assert strip_ai_dashes("This is a well-known issue") == "This is a well-known issue"


def test_strip_ai_dashes_handles_no_spaces_around_em_dash():
    assert strip_ai_dashes("fast—but fragile") == "fast, but fragile"


def test_strip_ai_dashes_collapses_doubles():
    # Dash right next to existing punctuation shouldn't leave ", ,"
    assert strip_ai_dashes("good, — really") == "good, really"


def test_rewrite_all_strips_em_dashes_from_model_output(mocker):
    client = MagicMock()
    client.chat.completions.create.return_value = make_mock_response(
        "It's fine — honestly, it works"
    )
    rewriter = Rewriter(client=client, model="gpt-4o")

    results = rewriter.rewrite_all("whatever")

    for mode in MODES:
        assert "—" not in results[mode]
        assert "–" not in results[mode]
