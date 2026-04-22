import pytest
from unittest.mock import MagicMock
from quickpolish.rewriter import Rewriter, MODES


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
