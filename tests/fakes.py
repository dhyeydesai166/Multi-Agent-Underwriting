"""A model stand-in. Unit tests never call Ollama."""

from underwriting.schemas import LlmResponse


class FakeClient:
    def __init__(
        self,
        text: str,
        input_tokens: int = 10,
        output_tokens: int = 5,
    ) -> None:
        self.text = text
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.calls = 0

    def complete(
        self,
        *,
        system: str,
        user: str,
        applicant_id: str,
    ) -> LlmResponse:
        self.calls += 1
        return LlmResponse(
            text=self.text,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
        )
