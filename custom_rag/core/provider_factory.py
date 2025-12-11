from custom_rag.core.llm_provider import LLMProvider
from custom_rag.core.openai_provider import OpenAIProvider


class ProviderFactory:
    """Factory for creating LLM provider instances."""

    @staticmethod
    def create_provider(
        provider_name: str,
        model: str,
        reasoning_effort: str | None = None,
    ) -> LLMProvider:
        """
        Create an LLM provider instance.

        Args:
            provider_name: Provider name ('openai', 'anthropic', etc.)
            model: Model name to use
            reasoning_effort: Optional reasoning effort level for reasoning models

        Returns:
            LLM provider instance

        Raises:
            ValueError: If provider is not supported
        """
        provider_name = provider_name.lower()

        if provider_name == "openai":
            return OpenAIProvider(model=model, reasoning_effort=reasoning_effort)

        raise ValueError(
            f"Unsupported LLM provider: {provider_name}. "
            f"Supported providers: openai"
        )
