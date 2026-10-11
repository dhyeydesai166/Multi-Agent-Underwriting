"""The Ollama client, with the network replaced by a fake."""

import json
import urllib.error
from unittest.mock import patch

import pytest

from underwriting.llm import OllamaClient


class _Response:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *args: object) -> bool:
        return False


def _complete(client: OllamaClient) -> object:
    return client.complete(
        system="system",
        user="user",
        applicant_id="APP-1001",
        agent_name="intake_agent",
    )


def test_timeout_applicant_never_calls_the_network() -> None:
    client = OllamaClient()
    with patch("urllib.request.urlopen") as urlopen:
        with pytest.raises(TimeoutError, match="APP-TIMEOUT"):
            client.complete(
                system="system",
                user="user",
                applicant_id="APP-TIMEOUT",
                agent_name="risk_scoring_agent",
            )
    urlopen.assert_not_called()


def test_ollama_returns_text_and_token_counts() -> None:
    payload = {
        "message": {"content": '{"ok": true}'},
        "prompt_eval_count": 4,
        "eval_count": 2,
    }
    with patch("urllib.request.urlopen", return_value=_Response(payload)):
        result = _complete(OllamaClient())
    assert result.text == '{"ok": true}'
    assert result.input_tokens == 4
    assert result.output_tokens == 2


def test_empty_model_content_raises() -> None:
    payload = {"message": {"content": ""}}
    with patch("urllib.request.urlopen", return_value=_Response(payload)):
        with pytest.raises(ValueError, match="empty content"):
            _complete(OllamaClient())


def test_model_text_that_is_not_json_raises() -> None:
    payload = {"message": {"content": "not json"}}
    with patch("urllib.request.urlopen", return_value=_Response(payload)):
        with pytest.raises(ValueError, match="invalid JSON"):
            _complete(OllamaClient())


def test_network_error_is_a_timeout() -> None:
    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("down"),
    ):
        with pytest.raises(TimeoutError, match="Ollama did not respond"):
            _complete(OllamaClient())
