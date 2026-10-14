"""Centralized gateway for configured Groq LLM calls."""

from groq import Groq

from app.core.config import load_application_config
from app.core.settings import settings


class LLMGateway:
    """Load niche-specific LLM settings and generate text with Groq."""

    def __init__(self, niche: str) -> None:
        if not settings.groq_api_key:
            raise RuntimeError(
                "GROQ_API_KEY is missing. Add it to your .env file."
            )

        self.config = load_application_config(niche)

        provider = self.config.llm.provider.lower()
        if provider != "groq":
            raise ValueError(
                f"Unsupported LLM provider: {provider}. "
                "Currently supported: groq."
            )

        if "default" not in self.config.llm.models:
            raise ValueError("LLM configuration must define models.default.")

        self.model = self.config.llm.models["default"]
        self.generation = self.config.llm.generation
        self.client = Groq(api_key=settings.groq_api_key)

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """Generate a text response from the configured model."""
        if not prompt.strip():
            raise ValueError("Prompt must not be empty.")

        messages: list[dict[str, str]] = []

        if system_prompt and system_prompt.strip():
            messages.append(
                {"role": "system", "content": system_prompt.strip()}
            )

        messages.append({"role": "user", "content": prompt.strip()})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.generation.temperature,
            max_tokens=self.generation.max_tokens,
        )

        content = response.choices[0].message.content

        if content is None:
            raise RuntimeError("The LLM returned an empty response.")

        return content.strip()
