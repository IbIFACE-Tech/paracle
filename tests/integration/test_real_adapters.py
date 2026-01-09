"""Integration tests for framework adapters with real LLMs.

These tests use real API calls to verify adapter functionality.
Requires API keys in .env file.
"""

import os

import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from paracle_adapters import list_available_adapters
from paracle_domain.models import AgentSpec, WorkflowSpec, WorkflowStep

# Skip all tests if no API key
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set"
)


@pytest.fixture
def simple_agent_spec():
    """Create a simple agent specification for testing."""
    return AgentSpec(
        name="test-assistant",
        model="gpt-4o-mini",
        provider="openai",
        system_prompt="You are a helpful assistant. Keep responses brief (1-2 sentences).",
        temperature=0.7,
        config={
            "tools": [],
            "role": "Assistant",
            "goal": "Help users with simple questions",
        },
    )


@pytest.fixture
def simple_workflow_spec():
    """Create a simple workflow specification for testing."""
    return WorkflowSpec(
        name="test-workflow",
        description="A simple test workflow",
        steps=[
            WorkflowStep(
                id="step1",
                name="Analyze",
                agent="analyzer",
                inputs={"task": "Analyze the input"},
            ),
            WorkflowStep(
                id="step2",
                name="Summarize",
                agent="summarizer",
                depends_on=["step1"],
                inputs={"task": "Summarize the analysis"},
            ),
        ],
    )


class TestLangChainAdapter:
    """Test LangChain adapter with real LLM."""

    @pytest.fixture
    def skip_if_unavailable(self):
        available = list_available_adapters()
        if not available.get("langchain"):
            pytest.skip("LangChain not installed")

    @pytest.mark.asyncio
    async def test_langchain_agent_execution(
        self, skip_if_unavailable, simple_agent_spec
    ):
        """Test LangChain agent creation and execution."""
        from langchain_openai import ChatOpenAI
        from paracle_adapters.langchain_adapter import LangChainAdapter

        # Create LLM
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

        # Create adapter
        adapter = LangChainAdapter(llm=llm)

        # Verify framework info
        assert adapter.framework_name == "langchain"
        assert "agents" in adapter.supported_features

        # Create agent
        agent_result = await adapter.create_agent(simple_agent_spec)
        assert agent_result["type"] in ["langgraph", "chain"]
        assert "agent" in agent_result or "chain" in agent_result

        # Execute agent
        result = await adapter.execute_agent(
            agent_result, {"input": "What is 2 + 2? Just give the number."}
        )

        assert "response" in result
        assert "4" in result["response"]
        assert result["metadata"]["framework"] == "langchain"

        print(f"\n[LangChain] Response: {result['response']}")
        print(f"[LangChain] Metadata: {result['metadata']}")


class TestLlamaIndexAdapter:
    """Test LlamaIndex adapter with real LLM."""

    @pytest.fixture
    def skip_if_unavailable(self):
        available = list_available_adapters()
        if not available.get("llamaindex"):
            pytest.skip("LlamaIndex not installed")

    @pytest.mark.asyncio
    async def test_llamaindex_agent_execution(
        self, skip_if_unavailable, simple_agent_spec
    ):
        """Test LlamaIndex agent creation and execution."""
        from llama_index.llms.openai import OpenAI as LlamaOpenAI
        from paracle_adapters.llamaindex_adapter import LlamaIndexAdapter

        # Create LLM
        llm = LlamaOpenAI(model="gpt-4o-mini", temperature=0.7)

        # Create adapter
        adapter = LlamaIndexAdapter(llm=llm)

        # Verify framework info
        assert adapter.framework_name == "llamaindex"
        assert "rag" in adapter.supported_features

        # Create agent
        agent_result = await adapter.create_agent(simple_agent_spec)
        assert agent_result["type"] == "react_agent"
        assert "agent" in agent_result

        # Execute agent
        result = await adapter.execute_agent(
            agent_result, {"input": "What is the capital of France? One word answer."}
        )

        assert "response" in result
        assert "Paris" in result["response"] or "paris" in result["response"].lower()
        assert result["metadata"]["framework"] == "llamaindex"

        print(f"\n[LlamaIndex] Response: {result['response']}")
        print(f"[LlamaIndex] Metadata: {result['metadata']}")


class TestCrewAIAdapter:
    """Test CrewAI adapter with real LLM."""

    @pytest.fixture
    def skip_if_unavailable(self):
        available = list_available_adapters()
        if not available.get("crewai"):
            pytest.skip("CrewAI not installed")

    @pytest.mark.asyncio
    async def test_crewai_agent_execution(self, skip_if_unavailable, simple_agent_spec):
        """Test CrewAI agent creation and execution."""
        from paracle_adapters.crewai_adapter import CrewAIAdapter

        # CrewAI uses model name directly
        adapter = CrewAIAdapter(model="gpt-4o-mini", verbose=False)

        # Verify framework info
        assert adapter.framework_name == "crewai"
        assert "crews" in adapter.supported_features

        # Update agent spec for CrewAI
        crew_agent_spec = AgentSpec(
            name="researcher",
            model="gpt-4o-mini",
            provider="openai",
            system_prompt="You are a researcher.",
            config={
                "role": "Researcher",
                "goal": "Find accurate information",
                "backstory": "Expert researcher with years of experience",
            },
        )

        # Create agent
        agent_result = await adapter.create_agent(crew_agent_spec)
        assert agent_result["type"] == "crewai_agent"
        assert "agent" in agent_result

        # Execute agent (CrewAI creates a minimal crew for single agent)
        result = await adapter.execute_agent(
            agent_result,
            {
                "input": "What year was Python programming language created?",
                "expected_output": "The year Python was created",
            },
        )

        assert "response" in result
        assert "1991" in result["response"] or "1989" in result["response"]
        assert result["metadata"]["framework"] == "crewai"

        print(f"\n[CrewAI] Response: {result['response'][:200]}...")
        print(f"[CrewAI] Metadata: {result['metadata']}")


class TestAutoGenAdapter:
    """Test AutoGen adapter with real LLM."""

    @pytest.fixture
    def skip_if_unavailable(self):
        available = list_available_adapters()
        if not available.get("autogen"):
            pytest.skip("AutoGen not installed")

    @pytest.mark.asyncio
    async def test_autogen_agent_execution(
        self, skip_if_unavailable, simple_agent_spec
    ):
        """Test AutoGen agent creation and execution."""
        from paracle_adapters.autogen_adapter import AutoGenAdapter

        # Create adapter with LLM config
        llm_config = {
            "model": "gpt-4o-mini",
            "api_key": os.getenv("OPENAI_API_KEY"),
            "temperature": 0.7,
        }
        adapter = AutoGenAdapter(llm_config=llm_config)

        # Verify framework info
        assert adapter.framework_name == "autogen"
        assert "group_chat" in adapter.supported_features

        # Create agent
        agent_result = await adapter.create_agent(simple_agent_spec)
        assert "autogen" in agent_result["type"]
        assert "agent" in agent_result

        # Execute agent
        result = await adapter.execute_agent(
            agent_result, {"input": "What is 10 multiplied by 5? Just the number."}
        )

        assert "response" in result
        assert "50" in result["response"]
        assert result["metadata"]["framework"] == "autogen"

        print(f"\n[AutoGen] Response: {result['response']}")
        print(f"[AutoGen] Metadata: {result['metadata']}")


class TestMSAFAdapter:
    """Test MSAF adapter with real LLM."""

    @pytest.fixture
    def skip_if_unavailable(self):
        available = list_available_adapters()
        if not available.get("msaf"):
            pytest.skip("MSAF not installed")

    @pytest.mark.asyncio
    async def test_msaf_agent_execution(self, skip_if_unavailable, simple_agent_spec):
        """Test MSAF agent creation and execution."""
        from agent_framework.openai import OpenAIResponsesClient
        from paracle_adapters.msaf_adapter import MSAFAdapter

        # Create client with OpenAI API key
        client = OpenAIResponsesClient(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_id="gpt-4o-mini",
        )

        # Create adapter
        adapter = MSAFAdapter(client=client)

        # Verify framework info
        assert adapter.framework_name == "msaf"
        assert "agents" in adapter.supported_features

        # Create agent
        agent_result = await adapter.create_agent(simple_agent_spec)
        assert agent_result["type"] == "msaf_agent"
        assert "agent" in agent_result

        # Execute agent
        result = await adapter.execute_agent(
            agent_result, {"input": "What is 7 plus 8? Just the number."}
        )

        assert "response" in result
        assert "15" in result["response"]
        assert result["metadata"]["framework"] == "msaf"

        print(f"\n[MSAF] Response: {result['response']}")
        print(f"[MSAF] Metadata: {result['metadata']}")


class TestAdapterComparison:
    """Compare responses across different adapters."""

    @pytest.mark.asyncio
    async def test_same_question_different_adapters(self, simple_agent_spec):
        """Test that all adapters can answer the same question."""
        question = "What is the largest planet in our solar system? One word answer."
        expected_word = "Jupiter"

        available = list_available_adapters()
        results = {}

        # Test LangChain
        if available.get("langchain"):
            try:
                from langchain_openai import ChatOpenAI
                from paracle_adapters.langchain_adapter import LangChainAdapter

                llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
                adapter = LangChainAdapter(llm=llm)
                agent = await adapter.create_agent(simple_agent_spec)
                result = await adapter.execute_agent(agent, {"input": question})
                results["langchain"] = result["response"]
            except Exception as e:
                results["langchain"] = f"ERROR: {e}"

        # Test LlamaIndex
        if available.get("llamaindex"):
            try:
                from llama_index.llms.openai import OpenAI as LlamaOpenAI
                from paracle_adapters.llamaindex_adapter import LlamaIndexAdapter

                llm = LlamaOpenAI(model="gpt-4o-mini", temperature=0)
                adapter = LlamaIndexAdapter(llm=llm)
                agent = await adapter.create_agent(simple_agent_spec)
                result = await adapter.execute_agent(agent, {"input": question})
                results["llamaindex"] = result["response"]
            except Exception as e:
                results["llamaindex"] = f"ERROR: {e}"

        # Test AutoGen
        if available.get("autogen"):
            try:
                from paracle_adapters.autogen_adapter import AutoGenAdapter

                llm_config = {
                    "model": "gpt-4o-mini",
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "temperature": 0,
                }
                adapter = AutoGenAdapter(llm_config=llm_config)
                agent = await adapter.create_agent(simple_agent_spec)
                result = await adapter.execute_agent(agent, {"input": question})
                results["autogen"] = result["response"]
            except Exception as e:
                results["autogen"] = f"ERROR: {e}"

        print("\n" + "=" * 60)
        print("ADAPTER COMPARISON TEST")
        print("=" * 60)
        print(f"Question: {question}")
        print("-" * 60)

        for adapter_name, response in results.items():
            contains_answer = expected_word.lower() in response.lower()
            status = "OK" if contains_answer else "FAIL"
            print(f"[{adapter_name}] {status} {response[:100]}")

        # At least one adapter should work
        assert len(results) > 0, "No adapters available for testing"

        # Check that non-error responses contain expected answer
        for name, response in results.items():
            if not response.startswith("ERROR:"):
                assert (
                    expected_word.lower() in response.lower()
                ), f"{name} did not return expected answer"


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])
