"""Integration tests for multi-agent scenarios across multiple adapters.

These tests verify that Paracle can orchestrate multiple agents
using different framework adapters simultaneously.
Requires API keys in .env file.
"""

import asyncio
import os

import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from paracle_adapters import list_available_adapters
from paracle_domain.models import AgentSpec

# Skip all tests if no API key
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set"
)


class TestMultiAdapterSimultaneous:
    """Test multiple adapters running simultaneously."""

    @pytest.mark.asyncio
    async def test_parallel_execution_all_adapters(self):
        """Test running agents on all available adapters in parallel."""
        available = list_available_adapters()
        question = "What is 5 + 3? Just the number."
        expected = "8"

        adapters_to_test = []

        # Setup LangChain
        if available.get("langchain"):
            from langchain_openai import ChatOpenAI
            from paracle_adapters.langchain_adapter import LangChainAdapter

            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
            adapter = LangChainAdapter(llm=llm)
            spec = AgentSpec(
                name="langchain-calculator",
                model="gpt-4o-mini",
                provider="openai",
                system_prompt="You are a calculator. Only respond with numbers.",
            )
            adapters_to_test.append(("langchain", adapter, spec))

        # Setup LlamaIndex
        if available.get("llamaindex"):
            from llama_index.llms.openai import OpenAI as LlamaOpenAI
            from paracle_adapters.llamaindex_adapter import LlamaIndexAdapter

            llm = LlamaOpenAI(model="gpt-4o-mini", temperature=0)
            adapter = LlamaIndexAdapter(llm=llm)
            spec = AgentSpec(
                name="llamaindex-calculator",
                model="gpt-4o-mini",
                provider="openai",
                system_prompt="You are a calculator. Only respond with numbers.",
            )
            adapters_to_test.append(("llamaindex", adapter, spec))

        # Setup AutoGen
        if available.get("autogen"):
            from paracle_adapters.autogen_adapter import AutoGenAdapter

            llm_config = {
                "model": "gpt-4o-mini",
                "api_key": os.getenv("OPENAI_API_KEY"),
                "temperature": 0,
            }
            adapter = AutoGenAdapter(llm_config=llm_config)
            spec = AgentSpec(
                name="autogen-calculator",
                model="gpt-4o-mini",
                provider="openai",
                system_prompt="You are a calculator. Only respond with numbers.",
            )
            adapters_to_test.append(("autogen", adapter, spec))

        # Setup MSAF
        if available.get("msaf"):
            from agent_framework.openai import OpenAIResponsesClient
            from paracle_adapters.msaf_adapter import MSAFAdapter

            client = OpenAIResponsesClient(
                api_key=os.getenv("OPENAI_API_KEY"),
                model_id="gpt-4o-mini",
            )
            adapter = MSAFAdapter(client=client)
            spec = AgentSpec(
                name="msaf-calculator",
                model="gpt-4o-mini",
                provider="openai",
                system_prompt="You are a calculator. Only respond with numbers.",
            )
            adapters_to_test.append(("msaf", adapter, spec))

        assert len(adapters_to_test) >= 2, "Need at least 2 adapters for this test"

        # Create all agents
        agents = {}
        for name, adapter, spec in adapters_to_test:
            agent = await adapter.create_agent(spec)
            agents[name] = (adapter, agent)

        # Execute all agents in parallel
        async def execute_agent(name, adapter, agent):
            result = await adapter.execute_agent(agent, {"input": question})
            return name, result

        tasks = [
            execute_agent(name, adapter, agent)
            for name, (adapter, agent) in agents.items()
        ]

        results = await asyncio.gather(*tasks)

        print("\n" + "=" * 60)
        print("PARALLEL MULTI-ADAPTER EXECUTION")
        print("=" * 60)
        print(f"Question: {question}")
        print("-" * 60)

        for name, result in results:
            response = result["response"]
            contains_answer = expected in str(response)
            status = "OK" if contains_answer else "FAIL"
            print(f"[{name}] {status}: {str(response)[:100]}")
            assert contains_answer, f"{name} should return {expected}"

        print(f"\nAll {len(results)} adapters returned correct answer simultaneously!")


class TestMultiAgentCollaboration:
    """Test multiple agents collaborating on a task."""

    @pytest.mark.asyncio
    async def test_agent_pipeline_different_adapters(self):
        """Test a pipeline where output from one adapter feeds into another."""
        available = list_available_adapters()

        # Need at least 2 different adapters
        if (
            sum(
                [
                    available.get("langchain", False),
                    available.get("llamaindex", False),
                    available.get("autogen", False),
                    available.get("msaf", False),
                ]
            )
            < 2
        ):
            pytest.skip("Need at least 2 adapters for pipeline test")

        # Step 1: Use first available adapter to generate a math problem
        # Step 2: Use second available adapter to solve it

        adapters = []

        if available.get("langchain"):
            from langchain_openai import ChatOpenAI
            from paracle_adapters.langchain_adapter import LangChainAdapter

            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
            adapters.append(("langchain", LangChainAdapter(llm=llm)))

        if available.get("msaf") and len(adapters) < 2:
            from agent_framework.openai import OpenAIResponsesClient
            from paracle_adapters.msaf_adapter import MSAFAdapter

            client = OpenAIResponsesClient(
                api_key=os.getenv("OPENAI_API_KEY"),
                model_id="gpt-4o-mini",
            )
            adapters.append(("msaf", MSAFAdapter(client=client)))

        if available.get("autogen") and len(adapters) < 2:
            from paracle_adapters.autogen_adapter import AutoGenAdapter

            llm_config = {
                "model": "gpt-4o-mini",
                "api_key": os.getenv("OPENAI_API_KEY"),
                "temperature": 0,
            }
            adapters.append(("autogen", AutoGenAdapter(llm_config=llm_config)))

        if available.get("llamaindex") and len(adapters) < 2:
            from llama_index.llms.openai import OpenAI as LlamaOpenAI
            from paracle_adapters.llamaindex_adapter import LlamaIndexAdapter

            llm = LlamaOpenAI(model="gpt-4o-mini", temperature=0)
            adapters.append(("llamaindex", LlamaIndexAdapter(llm=llm)))

        generator_name, generator_adapter = adapters[0]
        solver_name, solver_adapter = adapters[1]

        # Create generator agent
        generator_spec = AgentSpec(
            name="problem-generator",
            model="gpt-4o-mini",
            provider="openai",
            system_prompt=(
                "You are a math problem generator. Generate a simple addition "
                "problem with two single-digit numbers. Format: 'X + Y = ?'"
            ),
        )
        generator = await generator_adapter.create_agent(generator_spec)

        # Create solver agent
        solver_spec = AgentSpec(
            name="problem-solver",
            model="gpt-4o-mini",
            provider="openai",
            system_prompt=(
                "You are a math solver. Given a math problem, solve it and "
                "respond with just the answer number."
            ),
        )
        solver = await solver_adapter.create_agent(solver_spec)

        # Execute pipeline
        print("\n" + "=" * 60)
        print("AGENT PIPELINE: CROSS-ADAPTER COLLABORATION")
        print("=" * 60)

        # Step 1: Generate problem
        gen_result = await generator_adapter.execute_agent(
            generator, {"input": "Generate a simple addition problem."}
        )
        problem = gen_result["response"]
        print(f"[{generator_name}] Generated: {problem}")

        # Step 2: Solve problem
        solve_result = await solver_adapter.execute_agent(
            solver, {"input": f"Solve this: {problem}"}
        )
        solution = solve_result["response"]
        print(f"[{solver_name}] Solution: {solution}")

        print("-" * 60)
        print(f"Pipeline completed: {generator_name} -> {solver_name}")

        # Verify we got responses
        assert problem, "Generator should produce a problem"
        assert solution, "Solver should produce a solution"


class TestMultiAgentRoles:
    """Test multiple agents with different roles working together."""

    @pytest.mark.asyncio
    async def test_researcher_writer_reviewer_pipeline(self):
        """Test a 3-agent pipeline: researcher -> writer -> reviewer."""
        available = list_available_adapters()

        # Use different adapters for each role
        adapters = {}

        if available.get("langchain"):
            from langchain_openai import ChatOpenAI
            from paracle_adapters.langchain_adapter import LangChainAdapter

            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
            adapters["researcher"] = ("langchain", LangChainAdapter(llm=llm))

        if available.get("msaf"):
            from agent_framework.openai import OpenAIResponsesClient
            from paracle_adapters.msaf_adapter import MSAFAdapter

            client = OpenAIResponsesClient(
                api_key=os.getenv("OPENAI_API_KEY"),
                model_id="gpt-4o-mini",
            )
            adapters["writer"] = ("msaf", MSAFAdapter(client=client))

        if available.get("autogen"):
            from paracle_adapters.autogen_adapter import AutoGenAdapter

            llm_config = {
                "model": "gpt-4o-mini",
                "api_key": os.getenv("OPENAI_API_KEY"),
                "temperature": 0.2,
            }
            adapters["reviewer"] = ("autogen", AutoGenAdapter(llm_config=llm_config))

        if len(adapters) < 2:
            pytest.skip("Need at least 2 different adapters for role test")

        # Define agent specs for each role
        specs = {
            "researcher": AgentSpec(
                name="researcher",
                model="gpt-4o-mini",
                provider="openai",
                system_prompt=(
                    "You are a researcher. When asked about a topic, provide "
                    "3 key facts in a numbered list. Be concise."
                ),
                config={"role": "Researcher", "goal": "Find key facts"},
            ),
            "writer": AgentSpec(
                name="writer",
                model="gpt-4o-mini",
                provider="openai",
                system_prompt=(
                    "You are a writer. Take research notes and write a single "
                    "paragraph summary. Be engaging but factual."
                ),
                config={"role": "Writer", "goal": "Create content"},
            ),
            "reviewer": AgentSpec(
                name="reviewer",
                model="gpt-4o-mini",
                provider="openai",
                system_prompt=(
                    "You are a reviewer. Review the content and provide brief "
                    "feedback: what's good and what could be improved."
                ),
                config={"role": "Reviewer", "goal": "Quality check"},
            ),
        }

        print("\n" + "=" * 60)
        print("MULTI-ROLE AGENT PIPELINE")
        print("=" * 60)

        topic = "the planet Mars"
        content = {}

        # Execute each available role
        for role in ["researcher", "writer", "reviewer"]:
            if role not in adapters:
                # Use first available adapter as fallback
                fallback_role = list(adapters.keys())[0]
                adapter_name, adapter = adapters[fallback_role]
                print(f"[{role}] Using {adapter_name} (fallback)")
            else:
                adapter_name, adapter = adapters[role]
                print(f"[{role}] Using {adapter_name}")

            agent = await adapter.create_agent(specs[role])

            if role == "researcher":
                prompt = f"Research key facts about {topic}"
            elif role == "writer":
                prompt = f"Write a summary based on: {content.get('researcher', topic)}"
            else:
                prompt = f"Review this content: {content.get('writer', 'No content')}"

            result = await adapter.execute_agent(agent, {"input": prompt})
            content[role] = str(result["response"])[:500]
            print(f"  Output: {content[role][:100]}...")

        print("-" * 60)
        print("Pipeline completed successfully!")

        # Verify all roles produced output
        for role in ["researcher", "writer", "reviewer"]:
            assert content.get(role), f"{role} should produce output"


class TestConcurrentMultipleAgentsSameAdapter:
    """Test multiple agents on same adapter concurrently."""

    @pytest.mark.asyncio
    async def test_concurrent_agents_langchain(self):
        """Test multiple LangChain agents running concurrently."""
        available = list_available_adapters()
        if not available.get("langchain"):
            pytest.skip("LangChain not installed")

        from langchain_openai import ChatOpenAI
        from paracle_adapters.langchain_adapter import LangChainAdapter

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        adapter = LangChainAdapter(llm=llm)

        # Create 3 different specialized agents
        agents_specs = [
            AgentSpec(
                name="translator-spanish",
                model="gpt-4o-mini",
                provider="openai",
                system_prompt="You translate to Spanish. Just give the translation.",
            ),
            AgentSpec(
                name="translator-french",
                model="gpt-4o-mini",
                provider="openai",
                system_prompt="You translate to French. Just give the translation.",
            ),
            AgentSpec(
                name="translator-german",
                model="gpt-4o-mini",
                provider="openai",
                system_prompt="You translate to German. Just give the translation.",
            ),
        ]

        # Create all agents
        agents = []
        for spec in agents_specs:
            agent = await adapter.create_agent(spec)
            agents.append((spec.name, agent))

        # Execute all concurrently
        word = "hello"

        async def translate(name, agent):
            result = await adapter.execute_agent(agent, {"input": f"Translate: {word}"})
            return name, result["response"]

        tasks = [translate(name, agent) for name, agent in agents]
        results = await asyncio.gather(*tasks)

        print("\n" + "=" * 60)
        print("CONCURRENT TRANSLATION AGENTS (LangChain)")
        print("=" * 60)
        print(f"Word: {word}")
        print("-" * 60)

        expected_translations = {
            "translator-spanish": "hola",
            "translator-french": "bonjour",
            "translator-german": "hallo",
        }

        for name, response in results:
            response_lower = str(response).lower()
            expected = expected_translations.get(name, "")
            status = "OK" if expected in response_lower else "PARTIAL"
            print(f"[{name}] {status}: {response}")

        assert len(results) == 3, "All 3 translators should respond"


class TestAdapterInteroperability:
    """Test that agents from different adapters can share data."""

    @pytest.mark.asyncio
    async def test_data_handoff_between_adapters(self):
        """Test passing structured data between different adapter agents."""
        available = list_available_adapters()

        if not (available.get("langchain") and available.get("msaf")):
            pytest.skip("Need both LangChain and MSAF for this test")

        from agent_framework.openai import OpenAIResponsesClient
        from langchain_openai import ChatOpenAI
        from paracle_adapters.langchain_adapter import LangChainAdapter
        from paracle_adapters.msaf_adapter import MSAFAdapter

        # Setup LangChain adapter
        lc_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        lc_adapter = LangChainAdapter(llm=lc_llm)

        # Setup MSAF adapter
        msaf_client = OpenAIResponsesClient(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_id="gpt-4o-mini",
        )
        msaf_adapter = MSAFAdapter(client=msaf_client)

        # LangChain agent: Extract structured data
        extractor_spec = AgentSpec(
            name="data-extractor",
            model="gpt-4o-mini",
            provider="openai",
            system_prompt=(
                "Extract the name and age from the text. " "Format: Name: X, Age: Y"
            ),
        )
        extractor = await lc_adapter.create_agent(extractor_spec)

        # MSAF agent: Process structured data
        processor_spec = AgentSpec(
            name="data-processor",
            model="gpt-4o-mini",
            provider="openai",
            system_prompt=(
                "You receive data about a person. "
                "Calculate birth year (current year 2026) and respond with just the year."
            ),
        )
        processor = await msaf_adapter.create_agent(processor_spec)

        print("\n" + "=" * 60)
        print("DATA HANDOFF: LANGCHAIN -> MSAF")
        print("=" * 60)

        # Step 1: Extract data with LangChain
        text = "John is a 30 year old developer from New York."
        extract_result = await lc_adapter.execute_agent(extractor, {"input": text})
        extracted = extract_result["response"]
        print(f"[LangChain Extractor] Input: {text}")
        print(f"[LangChain Extractor] Output: {extracted}")

        # Step 2: Process with MSAF
        process_result = await msaf_adapter.execute_agent(
            processor, {"input": f"Person data: {extracted}"}
        )
        processed = process_result["response"]
        print(f"[MSAF Processor] Output: {processed}")

        print("-" * 60)
        print("Data handoff completed successfully!")

        # Verify data flowed through
        assert "30" in extracted or "John" in extracted, "Should extract data"
        assert "1996" in str(processed) or "1995" in str(
            processed
        ), f"Birth year should be ~1996, got: {processed}"


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])
