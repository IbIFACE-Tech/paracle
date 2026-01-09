"""
Example: Using multiple providers with Paracle.

This example demonstrates how to use different LLM providers
and compare their responses.
"""

import asyncio
import os

from paracle_providers import (
    ChatMessage,
    LLMConfig,
    ModelCapability,
    ProviderRegistry,
    get_model_catalog,
)


async def test_provider(provider_name: str, model: str, prompt: str):
    """Test a provider with a prompt."""
    try:
        # Create provider
        provider = ProviderRegistry.create_provider(provider_name)

        # Prepare messages
        messages = [
            ChatMessage(
                role="system",
                content="You are a helpful AI assistant. Keep responses concise.",
            ),
            ChatMessage(role="user", content=prompt),
        ]

        # Configure
        config = LLMConfig(temperature=0.7, max_tokens=100)

        print(f"\n{'='*60}")
        print(f"Provider: {provider_name}")
        print(f"Model: {model}")
        print(f"{'='*60}")

        # Generate completion
        response = await provider.chat_completion(
            messages=messages, config=config, model=model
        )

        print(f"Response: {response.content}")
        print(
            f"Tokens: {response.usage.total_tokens} "
            f"(prompt: {response.usage.prompt_tokens}, "
            f"completion: {response.usage.completion_tokens})"
        )
        print(f"Finish reason: {response.finish_reason}")

        return response

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"Provider: {provider_name} - FAILED")
        print(f"{'='*60}")
        print(f"Error: {e}")
        return None


async def test_streaming(provider_name: str, model: str, prompt: str):
    """Test streaming with a provider."""
    try:
        provider = ProviderRegistry.create_provider(provider_name)

        messages = [
            ChatMessage(
                role="system",
                content="You are a helpful AI assistant.",
            ),
            ChatMessage(role="user", content=prompt),
        ]

        config = LLMConfig(temperature=0.7, max_tokens=100)

        print(f"\n{'='*60}")
        print(f"Streaming from {provider_name}/{model}")
        print(f"{'='*60}")
        print("Response: ", end="", flush=True)

        async for chunk in provider.stream_completion(
            messages=messages, config=config, model=model
        ):
            print(chunk.content, end="", flush=True)

        print("\n")

    except Exception as e:
        print(f"Streaming error: {e}")


async def discover_models():
    """Discover available models using the catalog."""
    print("\n" + "=" * 60)
    print("MODEL DISCOVERY")
    print("=" * 60)

    catalog = get_model_catalog()

    # List all providers
    print("\nAvailable Providers:")
    for provider in catalog.list_providers():
        print(f"  - {provider.display_name} ({provider.provider_id})")
        print(f"    Models: {len(provider.models)}")
        print(f"    Streaming: {'✅' if provider.supports_streaming else '❌'}")

    # Find models with tool calling
    print("\n\nModels with Tool Calling:")
    results = catalog.search_models(capability=ModelCapability.TOOL_CALLING)
    for provider, model in results[:5]:  # Show first 5
        print(f"  - {provider.display_name}/{model.model_id}")
        if model.context_window:
            print(f"    Context: {model.context_window:,} tokens")

    # Find cost-effective models
    print("\n\nCost-Effective Models (< $1/M tokens):")
    results = catalog.search_models(max_cost=1.0)
    for provider, model in results[:5]:
        if model.input_cost_per_million:
            print(
                f"  - {provider.display_name}/{model.model_id}: "
                f"${model.input_cost_per_million}/M"
            )

    # Find models with vision
    print("\n\nModels with Vision Support:")
    results = catalog.search_models(capability=ModelCapability.IMAGE_INPUT)
    for provider, model in results[:5]:
        print(f"  - {provider.display_name}/{model.model_id}")


async def compare_providers():
    """Compare responses from different providers."""
    prompt = "Explain what makes Python a great programming language in 50 words."

    # Test configurations
    tests = [
        ("openai", "gpt-3.5-turbo"),
        ("anthropic", "claude-3-haiku-20240307"),
        ("google", "gemini-1.5-flash"),
        ("xai", "grok-beta"),
        ("deepseek", "deepseek-chat"),
        ("groq", "llama-3.1-8b-instant"),
    ]

    print("\n" + "=" * 60)
    print("PROVIDER COMPARISON")
    print("=" * 60)
    print(f"Prompt: {prompt}\n")

    # Test each provider
    results = []
    for provider_name, model in tests:
        # Check if API key is set
        key_env_vars = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
            "xai": "XAI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "groq": "GROQ_API_KEY",
        }

        env_var = key_env_vars.get(provider_name)
        if env_var and not os.getenv(env_var):
            print(f"\nSkipping {provider_name}: {env_var} not set")
            continue

        result = await test_provider(provider_name, model, prompt)
        if result:
            results.append((provider_name, model, result))

    # Summary
    if results:
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        for provider_name, model, result in results:
            print(f"\n{provider_name}/{model}:")
            print(f"  Tokens: {result.usage.total_tokens}")
            print(f"  Length: {len(result.content)} chars")


async def test_streaming_providers():
    """Test streaming with different providers."""
    prompt = "Count from 1 to 10 slowly."

    tests = [
        ("openai", "gpt-3.5-turbo"),
        ("groq", "llama-3.1-8b-instant"),
        ("deepseek", "deepseek-chat"),
    ]

    print("\n" + "=" * 60)
    print("STREAMING TEST")
    print("=" * 60)

    for provider_name, model in tests:
        # Check API key
        key_env_vars = {
            "openai": "OPENAI_API_KEY",
            "groq": "GROQ_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
        }

        env_var = key_env_vars.get(provider_name)
        if env_var and not os.getenv(env_var):
            print(f"\nSkipping {provider_name}: {env_var} not set")
            continue

        await test_streaming(provider_name, model, prompt)
        await asyncio.sleep(0.5)  # Brief pause between tests


async def test_openai_compatible():
    """Test OpenAI-compatible providers."""
    from paracle_providers.openai_compatible import (
        create_lmstudio_provider,
    )

    print("\n" + "=" * 60)
    print("OPENAI-COMPATIBLE PROVIDERS")
    print("=" * 60)

    # Example with LM Studio (if running locally)
    try:
        provider = create_lmstudio_provider(port=1234)
        messages = [ChatMessage(role="user", content="Hello from Paracle!")]
        config = LLMConfig(temperature=0.7, max_tokens=50)

        print("\nTesting LM Studio (localhost:1234)...")
        response = await provider.chat_completion(
            messages=messages, config=config, model="local-model"
        )
        print(f"Response: {response.content}")

    except Exception as e:
        print(f"LM Studio not available: {e}")
        print("To use LM Studio:")
        print("1. Download from https://lmstudio.ai")
        print("2. Load a model")
        print("3. Start the local server")


async def main():
    """Run all examples."""
    print("=" * 60)
    print("PARACLE MULTI-PROVIDER EXAMPLE")
    print("=" * 60)

    # Model discovery
    await discover_models()

    # Compare providers
    await compare_providers()

    # Test streaming
    await test_streaming_providers()

    # Test OpenAI-compatible
    await test_openai_compatible()

    print("\n" + "=" * 60)
    print("EXAMPLES COMPLETE")
    print("=" * 60)
    print("\nTips:")
    print("- Set API keys as environment variables")
    print("- Use Groq for fastest inference")
    print("- Use DeepSeek for cost-effectiveness")
    print("- Use Ollama for local/private deployments")


if __name__ == "__main__":
    asyncio.run(main())
