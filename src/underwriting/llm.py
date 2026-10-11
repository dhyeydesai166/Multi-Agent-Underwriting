"""Model call. Tests use a fake. Live runs use Ollama."""

import json
import urllib.error
import urllib.request
from typing import Protocol

from underwriting.config import (
    MODEL_NAME,
    OLLAMA_HOST,
    TEMPERATURE,
    TIMEOUT_APPLICANT_ID,
    TIMEOUT_SECONDS,
)
from underwriting.schemas import LlmResponse


class LlmClient(Protocol):
    def complete(
        self,
        *,
        system: str,
        user: str,
        applicant_id: str,
        agent_name: str = "",
    ) -> LlmResponse:
        """Return the model text and the provider token counts."""


class OllamaClient:
    """One chat call to a local Ollama model. JSON mode is required."""

    def __init__(
        self,
        model: str = MODEL_NAME,
        base_url: str = OLLAMA_HOST,
        timeout_s: float = TIMEOUT_SECONDS,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def complete(
        self,
        *,
        system: str,
        user: str,
        applicant_id: str,
        agent_name: str = "",
    ) -> LlmResponse:
        if (
            applicant_id == TIMEOUT_APPLICANT_ID
            and agent_name == "risk_scoring_agent"
        ):
            raise TimeoutError(
                f"{applicant_id} risk scoring timed out before the model call"
            )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": TEMPERATURE},
        }
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise TimeoutError("Ollama did not respond") from exc
        text = body.get("message", {}).get("content", "")
        if not text:
            raise ValueError("Model returned empty content")
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("Model returned invalid JSON") from exc
        return LlmResponse(
            text=text,
            input_tokens=int(body.get("prompt_eval_count", 0)),
            output_tokens=int(body.get("eval_count", 0)),
        )


class FailureDemoClient(OllamaClient):
    """Earlier steps stay local. Risk scoring uses OllamaClient and times out."""

    def complete(
        self,
        *,
        system: str,
        user: str,
        applicant_id: str,
        agent_name: str = "",
    ) -> LlmResponse:
        if agent_name == "risk_scoring_agent":
            return super().complete(
                system=system,
                user=user,
                applicant_id=applicant_id,
                agent_name=agent_name,
            )
        if agent_name == "intake_agent":
            body = {
                "applicant_id": applicant_id,
                "full_name": "Timeout Case",
                "age": 40,
                "coverage_amount": 10000,
                "missing_fields": [],
            }
        else:
            body = {"extra_facts": []}
        return LlmResponse(
            text=json.dumps(body),
            input_tokens=1,
            output_tokens=1,
        )
