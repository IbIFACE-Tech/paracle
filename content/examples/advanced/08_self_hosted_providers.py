"""
Example: Using self-hosted and open-source LLM providers.

Demonstrates:
1. LM Studio (local models)
2. vLLM (self-hosted inference)
3. llama.cpp (local inference)
4. text-generation-webui (oobabooga)
5. LocalAI (self-hosted)
6. Jan (desktop app)
"""


from paracle_providers import (
    ChatMessage,
    LLMConfig,
    create_jan_provider,
    create_llamacpp_provider,
    create_lmstudio_provider,
    create_localai_provider,
    create_text_generation_webui_provider,
    create_vllm_provider,
)


async def test_lmstudio():
    """Test LM Studio local model."""
    print("\n=== Testing LM Studio ===")

    # LM Studio runs on http://localhost:1234 by default
    provider = create_lmstudio_provider(port=1234)

    try:
        response = await provider.chat_completion(
            messages=[
                ChatMessage(
                    role="user", content="What is the capital of France?"
                )
            ],
            config=LLMConfig(temperature=0.7, max_tokens=100),
            model="local-model",  # Use whatever model is loaded
        )
        print(f"Response: {response.content}")
        print(f"Model: {response.model}")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure LM Studio is running on port 1234")
    finally:
        await provider.__aexit__(None, None, None)


async def test_vllm():
    """Test vLLM self-hosted server."""
    print("\n=== Testing vLLM ===")

    # vLLM typically runs on http://localhost:8000
    provider = create_vllm_provider(base_url="http://localhost:8000/v1")

    try:
        response = await provider.chat_completion(
            messages=[
                ChatMessage(
                    role="user", content="Write a haiku about programming."
                )
            ],
            config=LLMConfig(temperature=0.9, max_tokens=100),
            model="meta-llama/Llama-3-8b-hf",  # Model loaded in vLLM
        )
        print(f"Response: {response.content}")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure vLLM is running on port 8000")
        print("Start with: vllm serve meta-llama/Llama-3-8b-hf")
    finally:
        await provider.__aexit__(None, None, None)


async def test_llamacpp():
    """Test llama.cpp server."""
    print("\n=== Testing llama.cpp ===")

    # llama.cpp server typically runs on http://localhost:8080
    provider = create_llamacpp_provider(
        base_url="http://localhost:8080/v1"
    )

    try:
        response = await provider.chat_completion(
            messages=[
                ChatMessage(
                    role="user",
                    content="Explain quantum computing in simple terms.",
                )
            ],
            config=LLMConfig(temperature=0.7, max_tokens=200),
            model="llama-3-8b",  # Model loaded in llama.cpp
        )
        print(f"Response: {response.content}")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure llama.cpp server is running")
        print(
            "Start with: ./llama-server -m models/llama-3-8b.gguf "
            "--port 8080"
        )
    finally:
        await provider.__aexit__(None, None, None)


async def test_text_generation_webui():
    """Test text-generation-webui (oobabooga)."""
    print("\n=== Testing text-generation-webui ===")

    # oobabooga typically runs on http://localhost:5000
    provider = create_text_generation_webui_provider(
        base_url="http://localhost:5000/v1"
    )

    try:
        response = await provider.chat_completion(
            messages=[
                ChatMessage(
                    role="user",
                    content="What are the benefits of open-source AI?",
                )
            ],
            config=LLMConfig(temperature=0.8, max_tokens=150),
            model="TheBloke/Llama-2-7B-Chat-GGUF",
        )
        print(f"Response: {response.content}")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure text-generation-webui is running")
        print("Enable API mode with --api flag")
    finally:
        await provider.__aexit__(None, None, None)


async def test_localai():
    """Test LocalAI."""
    print("\n=== Testing LocalAI ===")

    # LocalAI typically runs on http://localhost:8080
    provider = create_localai_provider(
        base_url="http://localhost:8080/v1"
    )

    try:
        response = await provider.chat_completion(
            messages=[
                ChatMessage(
                    role="user",
                    content="Why is privacy important in AI?",
                )
            ],
            config=LLMConfig(temperature=0.7, max_tokens=150),
            model="gpt-3.5-turbo",  # LocalAI model alias
        )
        print(f"Response: {response.content}")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure LocalAI is running")
        print("Docker: docker run -p 8080:8080 localai/localai:latest")
    finally:
        await provider.__aexit__(None, None, None)


async def test_jan():
    """Test Jan (desktop app)."""
    print("\n=== Testing Jan ===")

    # Jan desktop app runs on http://localhost:1337
    provider = create_jan_provider(base_url="http://localhost:1337/v1")

    try:
        response = await provider.chat_completion(
            messages=[
                ChatMessage(
                    role="user",
                    content="What makes a good programming language?",
                )
            ],
            config=LLMConfig(temperature=0.7, max_tokens=150),
            model="tinyllama-1.1b",  # Model installed in Jan
        )
        print(f"Response: {response.content}")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Jan app is running")
        print("Download from: https://jan.ai")
    finally:
        await provider.__aexit__(None, None, None)


async def compare_self_hosted():
    """Compare multiple self-hosted providers."""
    print("\n=== Comparing Self-Hosted Providers ===")

    prompt = "What is 2+2?"
    message = [ChatMessage(role="user", content=prompt)]
    config = LLMConfig(temperature=0.1, max_tokens=50)

    providers = [
        ("LM Studio", create_lmstudio_provider(), "local-model"),
        ("vLLM", create_vllm_provider(), "meta-llama/Llama-3-8b-hf"),
        ("llama.cpp", create_llamacpp_provider(), "llama-3-8b"),
        (
            "text-gen-webui",
            create_text_generation_webui_provider(),
            "model",
        ),
        ("LocalAI", create_localai_provider(), "gpt-3.5-turbo"),
        ("Jan", create_jan_provider(), "tinyllama-1.1b"),
    ]

    for name, provider, model in providers:
        try:
            import time

            start = time.time()
            response = await provider.chat_completion(
                messages=message, config=config, model=model
            )
            duration = time.time() - start

            print(f"\n{name}:")
            print(f"  Response: {response.content[:100]}...")
            print(f"  Duration: {duration:.2f}s")
            print(
                f"  Tokens: {response.usage.total_tokens if response.usage else 'N/A'}"
            )
        except Exception as e:
            print(f"\n{name}: ❌ {str(e)[:50]}")
        finally:
            await provider.__aexit__(None, None, None)


async def streaming_example():
    """Demonstrate streaming with self-hosted provider."""
    print("\n=== Streaming from Self-Hosted ===")

    provider = create_lmstudio_provider()

    try:
        print("Prompt: Write a short story about AI")
        print("Response: ", end="", flush=True)

        async for chunk in provider.stream_completion(
            messages=[
                ChatMessage(
                    role="user", content="Write a short story about AI."
                )
            ],
            config=LLMConfig(temperature=0.9, max_tokens=200),
            model="local-model",
        ):
            print(chunk.content, end="", flush=True)

        print("\n")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        await provider.__aexit__(None, None, None)


if __name__ == "__main__":
    print("Self-Hosted Provider Examples")
    print("=" * 50)
    print("\nNote: These examples require running servers.")
    print("Uncomment the tests you want to run.\n")

    # Uncomment the tests you want to run:
    # asyncio.run(test_lmstudio())
    # asyncio.run(test_vllm())
    # asyncio.run(test_llamacpp())
    # asyncio.run(test_text_generation_webui())
    # asyncio.run(test_localai())
    # asyncio.run(test_jan())
    # asyncio.run(compare_self_hosted())
    # asyncio.run(streaming_example())

    print("\nSelf-Hosted Options Summary:")
    print("=" * 50)
    print("1. LM Studio - Easy GUI for local models")
    print("   Website: https://lmstudio.ai")
    print(
        "   Best for: Beginners, Windows/Mac users, "
        "one-click local AI"
    )
    print()
    print("2. vLLM - High-performance inference")
    print("   Website: https://vllm.ai")
    print("   Best for: Production, high throughput, GPU optimization")
    print()
    print("3. llama.cpp - Efficient CPU inference")
    print("   Website: https://github.com/ggerganov/llama.cpp")
    print("   Best for: CPU-only, quantized models, low memory")
    print()
    print("4. text-generation-webui - Feature-rich UI")
    print("   Website: https://github.com/oobabooga/text-generation-webui")
    print("   Best for: Experimentation, many features, extensions")
    print()
    print("5. LocalAI - Drop-in OpenAI replacement")
    print("   Website: https://localai.io")
    print(
        "   Best for: OpenAI API compatibility, Docker deployment"
    )
    print()
    print("6. Jan - Modern desktop app")
    print("   Website: https://jan.ai")
    print("   Best for: Privacy-focused, easy desktop deployment")
