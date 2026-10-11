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
        agent_name: str = "",
    ) -> LlmResponse:
        self.calls += 1
        return LlmResponse(
            text=self.text,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
        )


class ScriptedClient:
    """Returns a different JSON body on each call, in order."""

    def __init__(
        self,
        texts: list[str],
        input_tokens: int = 10,
        output_tokens: int = 5,
    ) -> None:
        self.texts = texts
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.calls = 0

    def complete(
        self,
        *,
        system: str,
        user: str,
        applicant_id: str,
        agent_name: str = "",
    ) -> LlmResponse:
        text = self.texts[self.calls]
        self.calls += 1
        return LlmResponse(
            text=text,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
        )
