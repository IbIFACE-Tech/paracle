# Paracle Meta Improvement Plan

## Overview

This plan addresses three key improvements to paracle_meta v1.3.0:
1. Provider abstraction layer for LLM operations
2. Real fallback strategies (not just mocks)
3. Capability composition to reduce engine bloat
4. Chat mode and plan mode additions

---

## Phase 1: Provider Abstraction Layer

### Problem
Capabilities are tightly coupled to Anthropic. Each capability (CodeCreation, etc.) directly uses AnthropicCapability.

### Solution
Create a `CapabilityProvider` protocol that abstracts LLM operations.

### Implementation

**1.1 Create provider protocol** (`packages/paracle_meta/capabilities/provider_protocol.py`):
```python
from typing import Protocol, AsyncIterator
from dataclasses import dataclass

@dataclass
class LLMRequest:
    prompt: str
    system_prompt: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
    tools: list[dict] | None = None

@dataclass
class LLMResponse:
    content: str
    tool_calls: list[dict] | None = None
    usage: dict | None = None
    provider: str = ""

class CapabilityProvider(Protocol):
    """Abstract provider for LLM operations in capabilities."""

    @property
    def name(self) -> str: ...

    @property
    def is_available(self) -> bool: ...

    async def complete(self, request: LLMRequest) -> LLMResponse: ...

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]: ...
```

**1.2 Implement providers**:
- `AnthropicProvider` - wraps existing Anthropic SDK
- `OpenAIProvider` - new OpenAI implementation
- `OllamaProvider` - local model support
- `MockProvider` - for testing (current mock behavior)

**1.3 Update capabilities to use protocol**:
- CodeCreationCapability receives `CapabilityProvider` in config
- FileSystemCapability already provider-agnostic (no LLM)
- ShellCapability already provider-agnostic

---

## Phase 2: Real Fallback Strategies

### Problem
Current "mock mode" returns placeholder responses. No real fallback when primary provider fails.

### Solution
Implement fallback chains using existing ProviderOrchestrator patterns.

### Implementation

**2.1 Create CapabilityProviderChain** (`packages/paracle_meta/capabilities/provider_chain.py`):
```python
class CapabilityProviderChain:
    """Chain of providers with automatic fallback."""

    def __init__(self, providers: list[CapabilityProvider]):
        self.providers = providers
        self._failures: dict[str, int] = {}

    async def complete(self, request: LLMRequest) -> LLMResponse:
        last_error = None
        for provider in self.providers:
            if not provider.is_available:
                continue
            if self._is_circuit_open(provider.name):
                continue
            try:
                return await provider.complete(request)
            except Exception as e:
                self._record_failure(provider.name)
                last_error = e
        raise ProviderChainExhaustedError(last_error)
```

**2.2 Fallback strategies**:
- `PrimaryWithFallback`: Try primary, fall to secondary on failure
- `RoundRobin`: Distribute load across providers
- `CostOptimized`: Use cheapest available provider
- `QualityFirst`: Use best model, fallback to cheaper

**2.3 Configuration**:
```yaml
# .parac/project.yaml
meta:
  providers:
    primary: anthropic
    fallback:
      - openai
      - ollama
    strategy: primary_with_fallback
```

---

## Phase 3: Capability Composition (Engine Refactoring)

### Problem
MetaAgent has 55 methods, ~30-35 are pure passthrough wrappers. "God object" anti-pattern.

### Solution
Replace passthrough methods with capability facades and direct access.

### Implementation

**3.1 Create capability registry**:
```python
class CapabilityRegistry:
    """Lazy-loading capability registry."""

    def __init__(self, config: MetaAgentConfig):
        self._config = config
        self._capabilities: dict[str, BaseCapability] = {}

    async def get(self, name: str) -> BaseCapability:
        if name not in self._capabilities:
            self._capabilities[name] = await self._create(name)
        return self._capabilities[name]
```

**3.2 Simplify MetaAgent interface**:

Keep core methods (~15-20):
```python
class MetaAgent:
    # Generation (core purpose)
    async def generate_agent(...)
    async def generate_workflow(...)
    async def generate_skill(...)
    async def generate_policy(...)

    # Capability access
    @property
    def capabilities(self) -> CapabilityRegistry

    # Sessions (new)
    async def start_session(self, mode: str) -> Session

    # Learning
    async def record_feedback(...)
```

**3.3 Access pattern change**:
```python
# Before (55 passthrough methods)
await meta.read_file("path")
await meta.write_file("path", "content")
await meta.git_status()

# After (direct capability access)
fs = await meta.capabilities.get("filesystem")
await fs.read_file("path")
await fs.write_file("path", "content")
await fs.git_status()
```

---

## Phase 4: Chat Mode

### Problem
No interactive chat interface despite conversation support existing.

### Solution
Add session-based chat mode with tool use.

### Implementation

**4.1 Create ChatSession** (`packages/paracle_meta/sessions/chat.py`):
```python
@dataclass
class ChatMessage:
    role: str  # user, assistant, tool
    content: str
    tool_calls: list[dict] | None = None
    tool_results: list[dict] | None = None

class ChatSession:
    """Interactive chat session with tool use."""

    def __init__(
        self,
        provider: CapabilityProvider,
        capabilities: CapabilityRegistry,
        memory: MemoryCapability | None = None
    ):
        self.provider = provider
        self.capabilities = capabilities
        self.memory = memory
        self.messages: list[ChatMessage] = []
        self.tools = self._build_tool_definitions()

    async def send(self, message: str) -> ChatMessage:
        """Send message, handle tool calls, return response."""
        self.messages.append(ChatMessage(role="user", content=message))

        response = await self.provider.complete(LLMRequest(
            prompt=self._format_messages(),
            tools=self.tools
        ))

        # Handle tool calls if present
        if response.tool_calls:
            tool_results = await self._execute_tools(response.tool_calls)
            # Continue conversation with tool results
            ...

        return ChatMessage(role="assistant", content=response.content)
```

**4.2 CLI integration**:
```bash
# Start chat mode
paracle meta chat

# With specific capabilities
paracle meta chat --capabilities filesystem,code_creation

# Resume session
paracle meta chat --session <session_id>
```

**4.3 Built-in tools for chat**:
- `read_file`, `write_file`, `list_directory`
- `create_function`, `create_class`, `refactor`
- `run_shell` (with approval)
- `search_web`, `fetch_url`

---

## Phase 5: Plan Mode

### Problem
No structured planning interface for complex tasks.

### Solution
Add plan mode that decomposes tasks and tracks execution.

### Implementation

**5.1 Create PlanSession** (`packages/paracle_meta/sessions/plan.py`):
```python
@dataclass
class PlanStep:
    id: str
    description: str
    status: str = "pending"  # pending, in_progress, completed, failed
    result: str | None = None
    substeps: list["PlanStep"] | None = None

class PlanSession:
    """Structured planning and execution session."""

    async def create_plan(self, goal: str) -> list[PlanStep]:
        """Decompose goal into executable steps."""
        result = await self.provider.complete(LLMRequest(
            prompt=f"Decompose this goal into steps: {goal}",
            system_prompt=PLANNING_PROMPT
        ))
        return self._parse_steps(result.content)

    async def execute_step(self, step: PlanStep) -> PlanStep:
        """Execute a single step with appropriate capability."""
        ...

    async def execute_plan(self, steps: list[PlanStep]) -> list[PlanStep]:
        """Execute all steps, handling dependencies."""
        ...
```

**5.2 CLI integration**:
```bash
# Start plan mode
paracle meta plan "Implement user authentication"

# Review plan before execution
paracle meta plan "..." --review

# Execute existing plan
paracle meta plan --execute <plan_id>
```

---

## Migration Path

### Backward Compatibility
- Keep existing methods as deprecated wrappers for 1 release
- Add deprecation warnings pointing to new patterns
- Document migration in CHANGELOG

### Deprecation Timeline
- v1.4.0: Add new patterns, deprecate old methods
- v1.5.0: Remove deprecated methods

---

## File Structure

```
packages/paracle_meta/
├── capabilities/
│   ├── provider_protocol.py    # NEW: CapabilityProvider protocol
│   ├── provider_chain.py       # NEW: Fallback chain
│   ├── providers/              # NEW: Provider implementations
│   │   ├── __init__.py
│   │   ├── anthropic.py
│   │   ├── openai.py
│   │   ├── ollama.py
│   │   └── mock.py
│   └── ... (existing capabilities)
├── sessions/                   # NEW: Interactive sessions
│   ├── __init__.py
│   ├── base.py
│   ├── chat.py
│   └── plan.py
├── registry.py                 # NEW: CapabilityRegistry
├── engine.py                   # REFACTOR: Simplified MetaAgent
└── ... (existing files)
```

---

## Success Metrics

1. **Provider Abstraction**: 3+ providers implemented and tested
2. **Fallback**: Provider failures handled gracefully with fallback
3. **Engine Size**: Reduced from 55 to ~15-20 public methods
4. **Chat Mode**: Interactive chat with tool use working
5. **Plan Mode**: Task decomposition and execution working
6. **Test Coverage**: Maintain 80%+ coverage

---

## Implementation Order

1. Provider protocol and chain (foundation)
2. Registry and engine refactoring (cleanup)
3. Chat mode (high user value)
4. Plan mode (builds on chat)
5. Additional providers (OpenAI, Ollama)

Estimated: 5 implementation phases
