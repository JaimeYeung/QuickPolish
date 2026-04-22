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
