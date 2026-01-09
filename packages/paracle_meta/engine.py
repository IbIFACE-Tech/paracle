"""Paracle Meta-Agent Engine - Core Implementation.

The meta-agent orchestrates intelligent generation of Paracle artifacts
using multi-provider LLMs, learning, and optimization.

Hybrid Architecture combining:
- Native lightweight capabilities (filesystem, shell, web, memory)
- Anthropic Claude SDK for intelligent AI-powered operations
- MCP integration for external tools
- Task/workflow management with DAG execution
- Autonomous agent spawning for high load

Enhanced with powerful capabilities:
- Web search and crawling
- Code execution and testing
- MCP integration for external tools
- Task/workflow management
- Autonomous agent spawning for high load
- Anthropic Claude SDK (tool use, code generation, analysis)
- FileSystem operations
- LLM-powered code creation
- Persistent memory and context
- Shell command execution
"""

from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path
from typing import Any

from paracle_core.logging import get_logger

# Import capabilities
from paracle_meta.capabilities import (  # Original capabilities; New hybrid capabilities
    AgentSpawner,
    AnthropicCapability,
    CodeCreationCapability,
    CodeExecutionCapability,
    FileSystemCapability,
    MCPCapability,
    MemoryCapability,
    ShellCapability,
    TaskManagementCapability,
    ToolDefinition,
    WebCapability,
)
from paracle_meta.capabilities.base import CapabilityResult
from paracle_meta.generators import (
    AgentGenerator,
    PolicyGenerator,
    SkillGenerator,
    WorkflowGenerator,
)
from paracle_meta.generators.base import GenerationRequest, GenerationResult
from paracle_meta.knowledge import BestPracticesDatabase
from paracle_meta.learning import LearningEngine
from paracle_meta.optimizer import CostOptimizer, QualityScorer
from paracle_meta.providers import ProviderOrchestrator
from paracle_meta.templates import TemplateLibrary

logger = get_logger(__name__)


class MetaAgent:
    """Paracle Meta-Agent Engine.

    Intelligent AI-powered system that generates Paracle artifacts
    from natural language descriptions with learning and optimization.

    Enhanced capabilities (Hybrid Architecture):

    Native Capabilities:
    - Web search and crawling for research
    - Code execution and testing
    - FileSystem operations with sandboxing
    - Shell command execution
    - Persistent memory and context
    - Task/workflow management
    - Autonomous agent spawning

    Anthropic-Powered Capabilities:
    - Intelligent code generation
    - Code analysis and refactoring
    - Multi-turn conversations with tool use
    - Task decomposition
    - Natural language to code

    Example:
        >>> async with MetaAgent() as meta:
        ...     # Generate agent
        ...     agent = await meta.generate_agent(
        ...         name="SecurityAuditor",
        ...         description="Reviews Python code for security issues"
        ...     )
        ...
        ...     # Use native capabilities
        ...     files = await meta.list_files("src/", pattern="*.py")
        ...     result = await meta.run_shell("pytest tests/")
        ...
        ...     # Use Anthropic-powered capabilities
        ...     code = await meta.generate_code("Create a FastAPI user endpoint")
        ...     analysis = await meta.analyze_code_with_claude(existing_code)
        ...
        ...     # Store context for later
        ...     await meta.remember("last_analysis", analysis.output)
        ...
        ...     # Spawn specialized agent for heavy work
        ...     spawned = await meta.spawn_agent("Researcher", agent_type="researcher")
    """

    def __init__(
        self,
        config_path: Path | None = None,
        providers: list[str] | None = None,
        learning_enabled: bool = True,
        cost_optimization: bool = True,
        capabilities_enabled: bool = True,
    ):
        """Initialize meta-agent.

        Args:
            config_path: Path to meta_agent.yaml config file
            providers: List of provider names to use
            learning_enabled: Enable learning from feedback
            cost_optimization: Enable cost optimization
            capabilities_enabled: Enable enhanced capabilities
        """
        self.config_path = config_path or self._find_config()
        self._capabilities_enabled = capabilities_enabled
        self._initialized = False

        # Core components
        self.orchestrator = ProviderOrchestrator(providers=providers)
        self.learning_engine = LearningEngine(enabled=learning_enabled)
        self.cost_optimizer = CostOptimizer(enabled=cost_optimization)
        self.quality_scorer = QualityScorer()

        # Generators
        self.agent_generator = AgentGenerator(self.orchestrator)
        self.workflow_generator = WorkflowGenerator(self.orchestrator)
        self.skill_generator = SkillGenerator(self.orchestrator)
        self.policy_generator = PolicyGenerator(self.orchestrator)

        # Knowledge
        self.templates = TemplateLibrary()
        self.best_practices = BestPracticesDatabase()

        # Original capabilities (initialized lazily)
        self._web: WebCapability | None = None
        self._code: CodeExecutionCapability | None = None
        self._mcp: MCPCapability | None = None
        self._tasks: TaskManagementCapability | None = None
        self._spawner: AgentSpawner | None = None

        # New hybrid capabilities (initialized lazily)
        self._anthropic: AnthropicCapability | None = None
        self._filesystem: FileSystemCapability | None = None
        self._code_creation: CodeCreationCapability | None = None
        self._memory: MemoryCapability | None = None
        self._shell: ShellCapability | None = None

        logger.info(
            "MetaAgent initialized",
            extra={
                "providers": self.orchestrator.available_providers,
                "learning": learning_enabled,
                "cost_optimization": cost_optimization,
                "capabilities": capabilities_enabled,
                "hybrid_mode": True,
            },
        )

    async def generate_agent(
        self,
        name: str,
        description: str,
        auto_apply: bool = False,
        context: dict[str, Any] | None = None,
    ) -> GenerationResult:
        """Generate agent spec from natural language description.

        Args:
            name: Agent name
            description: Natural language description of agent's purpose
            auto_apply: If True, apply without user review
            context: Additional context (e.g., existing skills, project info)

        Returns:
            GenerationResult with agent spec and metadata

        Example:
            >>> result = await meta.generate_agent(
            ...     name="SecurityAuditor",
            ...     description="Reviews Python for security issues, suggests fixes"
            ... )
            >>> print(result.quality_score)  # 9.2
            >>> print(result.cost_usd)       # 0.018
        """
        request = GenerationRequest(
            artifact_type="agent",
            name=name,
            description=description,
            context=context or {},
            auto_apply=auto_apply,
        )

        return await self._generate(request)

    async def generate_workflow(
        self,
        name: str,
        goal: str,
        auto_apply: bool = False,
        context: dict[str, Any] | None = None,
    ) -> GenerationResult:
        """Generate workflow from goal description.

        Args:
            name: Workflow name
            goal: Natural language goal description
            auto_apply: If True, apply without user review
            context: Additional context

        Returns:
            GenerationResult with workflow spec

        Example:
            >>> result = await meta.generate_workflow(
            ...     name="deployment",
            ...     goal="Deploy to production with tests, rollback on failure"
            ... )
        """
        request = GenerationRequest(
            artifact_type="workflow",
            name=name,
            description=goal,
            context=context or {},
            auto_apply=auto_apply,
        )

        return await self._generate(request)

    async def generate_skill(
        self,
        name: str,
        description: str,
        auto_apply: bool = False,
    ) -> GenerationResult:
        """Generate skill from description.

        Args:
            name: Skill name
            description: Skill description
            auto_apply: If True, apply without review

        Returns:
            GenerationResult with skill spec
        """
        request = GenerationRequest(
            artifact_type="skill",
            name=name,
            description=description,
            auto_apply=auto_apply,
        )

        return await self._generate(request)

    async def generate_policy(
        self,
        name: str,
        requirements: str,
        policy_type: str = "custom",
        auto_apply: bool = False,
    ) -> GenerationResult:
        """Generate policy from requirements.

        Args:
            name: Policy name
            requirements: Policy requirements
            policy_type: Type of policy (security, testing, code_style, custom)
            auto_apply: If True, apply without review

        Returns:
            GenerationResult with policy spec
        """
        request = GenerationRequest(
            artifact_type="policy",
            name=name,
            description=requirements,
            context={"policy_type": policy_type},
            auto_apply=auto_apply,
        )

        return await self._generate(request)

    async def _generate(self, request: GenerationRequest) -> GenerationResult:
        """Internal: Orchestrate generation with learning and optimization.

        Flow:
        1. Check templates (learned patterns)
        2. Select optimal provider
        3. Generate with LLM
        4. Score quality
        5. Track cost
        6. Return result
        """
        logger.info(f"Generating {request.artifact_type}: {request.name}")

        # 1. Check for existing template
        template = await self.templates.find_similar(
            artifact_type=request.artifact_type, description=request.description
        )

        if template and template.quality_score > 9.0:
            logger.info(f"Using high-quality template: {template.id}")
            # Use template directly (fast + cheap)
            result = await self._generate_from_template(request, template)
        else:
            # 2. Select optimal provider
            provider_info = self.cost_optimizer.select_provider(
                task_type=request.artifact_type,
                complexity=self._estimate_complexity(request),
            )

            # 3. Generate with LLM
            generator = self._get_generator(request.artifact_type)

            # provider_info is a dict from CostOptimizer
            result = await generator.generate(
                request=request,
                provider=provider_info["provider"],
                model=provider_info["model"],
                best_practices=await self.best_practices.get_for(request.artifact_type),
            )

        # 4. Score quality
        result.quality_score = await self.quality_scorer.score(result)

        # 5. Track for learning
        await self.learning_engine.track_generation(result)

        # 6. Log cost
        await self.cost_optimizer.track_cost(result)

        logger.info(
            f"Generated {request.artifact_type}",
            extra={
                "name": request.name,
                "provider": result.provider,
                "quality": result.quality_score,
                "cost": result.cost_usd,
            },
        )

        return result

    async def record_feedback(
        self,
        generation_id: str,
        rating: int,
        comment: str | None = None,
        usage_count: int = 1,
    ) -> None:
        """Record user feedback for learning.

        Args:
            generation_id: ID of the generation
            rating: User rating 1-5 stars
            comment: Optional feedback comment
            usage_count: How many times artifact was used

        Example:
            >>> await meta.record_feedback(
            ...     generation_id=result.id,
            ...     rating=5,
            ...     comment="Perfect! Saved me hours of work"
            ... )
        """
        await self.learning_engine.record_feedback(
            generation_id=generation_id,
            rating=rating,
            comment=comment,
            usage_count=usage_count,
        )

        logger.info(f"Feedback recorded: {generation_id} ({rating}/5)")

    async def get_statistics(self) -> dict[str, Any]:
        """Get meta-agent statistics.

        Returns:
            Dictionary with statistics:
            - total_generations: Total number of generations
            - success_rate: Success rate (%)
            - avg_quality: Average quality score
            - total_cost: Total cost in USD
            - cost_savings: Savings vs naive approach (%)
            - learning_progress: Quality improvement over time
            - top_patterns: Most successful patterns

        Example:
            >>> stats = await meta.get_statistics()
            >>> print(f"Success rate: {stats['success_rate']}%")
            >>> print(f"Cost savings: {stats['cost_savings']}%")
            >>> print(f"Quality improvement: +{stats['learning_progress']}%")
        """
        learning_stats = await self.learning_engine.get_statistics()
        cost_stats = await self.cost_optimizer.get_statistics()

        return {
            **learning_stats,
            **cost_stats,
            "provider_performance": await self.orchestrator.get_performance_stats(),
            "templates_learned": await self.templates.count(),
            "best_practices_count": await self.best_practices.count(),
        }

    def _get_generator(self, artifact_type: str):
        """Get appropriate generator for artifact type."""
        generators = {
            "agent": self.agent_generator,
            "workflow": self.workflow_generator,
            "skill": self.skill_generator,
            "policy": self.policy_generator,
        }
        return generators[artifact_type]

    def _estimate_complexity(self, request: GenerationRequest) -> float:
        """Estimate generation complexity (0.0-1.0).

        Used for provider selection and cost optimization.
        """
        # Simple heuristic - can be improved with ML
        desc_length = len(request.description)
        has_context = bool(request.context)

        base_complexity = min(desc_length / 500, 0.5)
        context_bonus = 0.2 if has_context else 0

        return min(base_complexity + context_bonus, 1.0)

    async def _generate_from_template(
        self, request: GenerationRequest, template: Any
    ) -> GenerationResult:
        """Generate from existing template (fast + cheap)."""
        # Customize template for this request
        content = template.customize(
            name=request.name, description=request.description, context=request.context
        )

        return GenerationResult(
            id=f"gen_{datetime.now().timestamp()}",
            artifact_type=request.artifact_type,
            name=request.name,
            content=content,
            provider="template",
            model=template.id,
            quality_score=template.quality_score,
            cost_usd=0.0,  # Free!
            tokens_input=0,
            tokens_output=0,
            reasoning=f"Used high-quality template {template.id} (score: {template.quality_score})",
        )

    def _find_config(self) -> Path:
        """Find meta_agent.yaml config file."""
        # Search in .parac/config/
        parac_dir = Path.cwd() / ".parac"
        config_path = parac_dir / "config" / "meta_agent.yaml"

        if not config_path.exists():
            logger.warning(f"Config not found: {config_path}, using defaults")

        return config_path

    # =========================================================================
    # Capability Management
    # =========================================================================

    async def initialize(self) -> None:
        """Initialize all capabilities.

        Call this after creating the MetaAgent to enable enhanced capabilities.
        Initializes both native and Anthropic-powered capabilities.
        """
        if self._initialized:
            return

        if self._capabilities_enabled:
            logger.info("Initializing MetaAgent hybrid capabilities...")

            # Initialize original capabilities
            self._web = WebCapability()
            self._code = CodeExecutionCapability()
            self._mcp = MCPCapability()
            self._tasks = TaskManagementCapability()
            self._spawner = AgentSpawner()

            await self._web.initialize()
            await self._code.initialize()
            await self._mcp.initialize()
            await self._tasks.initialize()
            await self._spawner.initialize()

            # Initialize new hybrid capabilities
            self._anthropic = AnthropicCapability()
            self._filesystem = FileSystemCapability()
            self._code_creation = CodeCreationCapability()
            self._memory = MemoryCapability()
            self._shell = ShellCapability()

            await self._anthropic.initialize()
            await self._filesystem.initialize()
            await self._code_creation.initialize()
            await self._memory.initialize()
            await self._shell.initialize()

            logger.info(
                "All hybrid capabilities initialized",
                extra={
                    "anthropic_available": self._anthropic.is_available,
                },
            )

        self._initialized = True

    async def shutdown(self) -> None:
        """Shutdown all capabilities and cleanup resources."""
        # Original capabilities
        if self._web:
            await self._web.shutdown()
        if self._code:
            await self._code.shutdown()
        if self._mcp:
            await self._mcp.shutdown()
        if self._tasks:
            await self._tasks.shutdown()
        if self._spawner:
            await self._spawner.shutdown()

        # New hybrid capabilities
        if self._anthropic:
            await self._anthropic.shutdown()
        if self._filesystem:
            await self._filesystem.shutdown()
        if self._code_creation:
            await self._code_creation.shutdown()
        if self._memory:
            await self._memory.shutdown()
        if self._shell:
            await self._shell.shutdown()

        self._initialized = False
        logger.info("MetaAgent shutdown complete")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()

    # =========================================================================
    # Web Capabilities
    # =========================================================================

    async def web_search(
        self,
        query: str,
        num_results: int = 10,
    ) -> CapabilityResult:
        """Search the web for information.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            CapabilityResult with search results

        Example:
            >>> result = await meta.web_search("Python best practices")
            >>> for item in result.output:
            ...     print(item['title'], item['url'])
        """
        if not self._web:
            await self.initialize()
        return await self._web.search(query, num_results)

    async def web_fetch(self, url: str) -> CapabilityResult:
        """Fetch and parse a web page.

        Args:
            url: URL to fetch

        Returns:
            CapabilityResult with page content

        Example:
            >>> result = await meta.web_fetch("https://docs.python.org")
            >>> print(result.output['title'])
            >>> print(result.output['content'][:500])
        """
        if not self._web:
            await self.initialize()
        return await self._web.fetch(url)

    async def web_crawl(
        self,
        start_url: str,
        max_pages: int = 5,
    ) -> CapabilityResult:
        """Crawl multiple pages starting from a URL.

        Args:
            start_url: Starting URL
            max_pages: Maximum pages to crawl

        Returns:
            CapabilityResult with crawl results
        """
        if not self._web:
            await self.initialize()
        return await self._web.crawl(start_url, max_pages)

    # =========================================================================
    # Code Execution Capabilities
    # =========================================================================

    async def run_code(
        self,
        code: str,
        language: str = "python",
    ) -> CapabilityResult:
        """Execute code in specified language.

        Args:
            code: Code to execute
            language: Programming language

        Returns:
            CapabilityResult with execution output

        Example:
            >>> result = await meta.run_code("print(2 + 2)")
            >>> print(result.output['stdout'])  # "4\\n"
        """
        if not self._code:
            await self.initialize()
        return await self._code.run_python(code)

    async def run_tests(
        self,
        test_path: str = "tests/",
        coverage: bool = False,
    ) -> CapabilityResult:
        """Run tests with pytest.

        Args:
            test_path: Path to tests
            coverage: Enable coverage reporting

        Returns:
            CapabilityResult with test results
        """
        if not self._code:
            await self.initialize()
        return await self._code.run_tests(test_path, coverage)

    async def analyze_code(
        self,
        code: str,
        checks: list[str] | None = None,
    ) -> CapabilityResult:
        """Analyze code quality.

        Args:
            code: Code to analyze
            checks: Checks to run (lint, type)

        Returns:
            CapabilityResult with analysis results
        """
        if not self._code:
            await self.initialize()
        return await self._code.analyze(code, checks)

    # =========================================================================
    # MCP Capabilities
    # =========================================================================

    async def mcp_list_tools(self) -> CapabilityResult:
        """List available MCP tools.

        Returns:
            CapabilityResult with list of tools
        """
        if not self._mcp:
            await self.initialize()
        return await self._mcp.list_tools()

    async def mcp_call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> CapabilityResult:
        """Call an MCP tool.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            CapabilityResult with tool output
        """
        if not self._mcp:
            await self.initialize()
        return await self._mcp.call_tool(tool_name, arguments)

    # =========================================================================
    # Task Management Capabilities
    # =========================================================================

    async def create_task(
        self,
        name: str,
        description: str = "",
        priority: str = "normal",
    ) -> CapabilityResult:
        """Create a new task.

        Args:
            name: Task name
            description: Task description
            priority: Task priority (low, normal, high, critical)

        Returns:
            CapabilityResult with task data
        """
        if not self._tasks:
            await self.initialize()
        return await self._tasks.create_task(
            name, description=description, priority=priority
        )

    async def run_task(self, task_id: str) -> CapabilityResult:
        """Run a task by ID.

        Args:
            task_id: Task ID

        Returns:
            CapabilityResult with task result
        """
        if not self._tasks:
            await self.initialize()
        return await self._tasks.run_task(task_id)

    async def create_workflow(
        self,
        name: str,
        tasks: list[dict[str, Any]],
    ) -> CapabilityResult:
        """Create a workflow from task definitions.

        Args:
            name: Workflow name
            tasks: List of task definitions

        Returns:
            CapabilityResult with workflow data
        """
        if not self._tasks:
            await self.initialize()
        return await self._tasks.create_workflow(name, tasks)

    async def run_workflow(self, workflow_id: str) -> CapabilityResult:
        """Run a workflow by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            CapabilityResult with workflow result
        """
        if not self._tasks:
            await self.initialize()
        return await self._tasks.run_workflow(workflow_id)

    # =========================================================================
    # Agent Spawning Capabilities
    # =========================================================================

    async def spawn_agent(
        self,
        name: str,
        agent_type: str = "general",
        capabilities: list[str] | None = None,
    ) -> CapabilityResult:
        """Spawn a specialized agent.

        Useful for delegating specific tasks or handling high load.

        Args:
            name: Agent name
            agent_type: Type of agent (researcher, coder, reviewer, tester, etc.)
            capabilities: List of capabilities for the agent

        Returns:
            CapabilityResult with spawned agent data

        Example:
            >>> result = await meta.spawn_agent("CodeReviewer", agent_type="reviewer")
            >>> agent_id = result.output['id']
            >>> await meta.assign_to_agent(agent_id, "Review PR #123")
        """
        if not self._spawner:
            await self.initialize()
        return await self._spawner.spawn(name, agent_type, capabilities=capabilities)

    async def terminate_agent(self, agent_id: str) -> CapabilityResult:
        """Terminate a spawned agent.

        Args:
            agent_id: ID of agent to terminate

        Returns:
            CapabilityResult with termination result
        """
        if not self._spawner:
            await self.initialize()
        return await self._spawner.terminate(agent_id)

    async def assign_to_agent(
        self,
        agent_id: str,
        task: str,
    ) -> CapabilityResult:
        """Assign a task to a spawned agent.

        Args:
            agent_id: Agent ID
            task: Task description

        Returns:
            CapabilityResult with assignment result
        """
        if not self._spawner:
            await self.initialize()
        return await self._spawner.assign(agent_id, task)

    async def get_pool_status(self) -> CapabilityResult:
        """Get status of the agent pool.

        Returns:
            CapabilityResult with pool status including:
            - total_agents: Total spawned agents
            - available_agents: Agents available for tasks
            - busy_agents: Agents currently working
            - load: Current load ratio (0-1)
        """
        if not self._spawner:
            await self.initialize()
        return await self._spawner.get_pool_status()

    # =========================================================================
    # High-Level Autonomous Operations
    # =========================================================================

    async def research(
        self,
        topic: str,
        depth: str = "normal",
    ) -> dict[str, Any]:
        """Perform autonomous research on a topic.

        Combines web search, page crawling, and content analysis
        to gather comprehensive information on a topic.

        Args:
            topic: Research topic
            depth: Research depth (quick, normal, thorough)

        Returns:
            Research results with sources and summary

        Example:
            >>> results = await meta.research("Python async best practices")
            >>> print(results['summary'])
            >>> print(results['sources'])
        """
        if not self._initialized:
            await self.initialize()

        # Determine search count based on depth
        search_counts = {"quick": 3, "normal": 5, "thorough": 10}
        num_results = search_counts.get(depth, 5)

        # Search for information
        search_result = await self.web_search(topic, num_results)

        if not search_result.success:
            return {
                "topic": topic,
                "error": search_result.error,
                "sources": [],
                "summary": "",
            }

        # Gather sources
        sources = []
        contents = []

        for item in search_result.output[:3]:  # Fetch top 3 results
            try:
                page_result = await self.web_fetch(item.get("url", ""))
                if page_result.success:
                    sources.append(
                        {
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "snippet": item.get("snippet", ""),
                        }
                    )
                    contents.append(page_result.output.get("content", "")[:2000])
            except Exception:
                pass

        # Combine results
        return {
            "topic": topic,
            "depth": depth,
            "sources": sources,
            "content_summary": "\n---\n".join(contents[:3]),
            "search_results": search_result.output,
        }

    async def auto_scale_if_needed(self) -> bool:
        """Check load and spawn additional agents if needed.

        Returns:
            True if agents were spawned

        Example:
            >>> if await meta.auto_scale_if_needed():
            ...     print("Spawned additional agents due to high load")
        """
        if not self._spawner:
            await self.initialize()

        status = await self.get_pool_status()
        if status.success:
            load = status.output.get("load", 0)
            if load > 0.8:  # High load
                result = await self.spawn_agent(
                    f"AutoScaled_{datetime.now().timestamp():.0f}", agent_type="general"
                )
                return result.success
        return False

    @property
    def capabilities_status(self) -> dict[str, bool]:
        """Get status of all capabilities."""
        return {
            # Original
            "web": self._web is not None and self._web.is_initialized,
            "code": self._code is not None and self._code.is_initialized,
            "mcp": self._mcp is not None and self._mcp.is_initialized,
            "tasks": self._tasks is not None and self._tasks.is_initialized,
            "spawner": self._spawner is not None and self._spawner.is_initialized,
            # Hybrid
            "anthropic": self._anthropic is not None and self._anthropic.is_initialized,
            "anthropic_available": self._anthropic is not None
            and self._anthropic.is_available,
            "filesystem": self._filesystem is not None
            and self._filesystem.is_initialized,
            "code_creation": self._code_creation is not None
            and self._code_creation.is_initialized,
            "memory": self._memory is not None and self._memory.is_initialized,
            "shell": self._shell is not None and self._shell.is_initialized,
        }

    # =========================================================================
    # Anthropic-Powered Capabilities
    # =========================================================================

    async def claude_complete(
        self,
        prompt: str,
        system: str | None = None,
        **kwargs,
    ) -> CapabilityResult:
        """Complete a prompt using Claude.

        Args:
            prompt: The prompt to complete
            system: Optional system prompt
            **kwargs: Additional parameters (model, temperature, etc.)

        Returns:
            CapabilityResult with completion

        Example:
            >>> result = await meta.claude_complete("Explain Python decorators")
            >>> print(result.output["content"])
        """
        if not self._anthropic:
            await self.initialize()
        return await self._anthropic.complete(prompt, system, **kwargs)

    async def claude_with_tools(
        self,
        prompt: str,
        tools: list[ToolDefinition | dict[str, Any]],
        **kwargs,
    ) -> CapabilityResult:
        """Complete with Claude tool use.

        Args:
            prompt: The prompt
            tools: List of tool definitions
            **kwargs: Additional parameters

        Returns:
            CapabilityResult with completion and tool calls

        Example:
            >>> tools = [AnthropicCapability.get_builtin_tools()["search_web"]]
            >>> result = await meta.claude_with_tools("Find Python tutorials", tools)
            >>> for call in result.output.get("tool_calls", []):
            ...     print(f"Tool: {call['name']}, Input: {call['input']}")
        """
        if not self._anthropic:
            await self.initialize()
        return await self._anthropic.complete_with_tools(prompt, tools, **kwargs)

    async def generate_code(
        self,
        description: str,
        language: str = "python",
        context: str | None = None,
    ) -> CapabilityResult:
        """Generate code using Claude.

        Args:
            description: Natural language description of what to generate
            language: Programming language (default: python)
            context: Additional context about the codebase

        Returns:
            CapabilityResult with generated code

        Example:
            >>> result = await meta.generate_code(
            ...     "Create a FastAPI endpoint for user registration",
            ...     language="python"
            ... )
            >>> print(result.output["code"])
        """
        if not self._code_creation:
            await self.initialize()
        return await self._code_creation.create_function(
            name="generated",
            description=description,
        )

    async def analyze_code_with_claude(
        self,
        code: str,
        analysis_type: str = "general",
    ) -> CapabilityResult:
        """Analyze code using Claude.

        Args:
            code: Code to analyze
            analysis_type: Type of analysis (general, security, performance, refactoring)

        Returns:
            CapabilityResult with analysis

        Example:
            >>> result = await meta.analyze_code_with_claude(my_code, "security")
            >>> print(result.output["analysis"])
        """
        if not self._anthropic:
            await self.initialize()
        return await self._anthropic.analyze_code(code, analysis_type)

    async def decompose_task(
        self,
        task: str,
        context: str | None = None,
    ) -> CapabilityResult:
        """Decompose a complex task into subtasks using Claude.

        Args:
            task: Task description
            context: Additional context

        Returns:
            CapabilityResult with subtasks

        Example:
            >>> result = await meta.decompose_task("Build a REST API")
            >>> for subtask in result.output["subtasks"]:
            ...     print(f"- {subtask['name']}")
        """
        if not self._anthropic:
            await self.initialize()
        return await self._anthropic.decompose_task(task, context)

    async def stream_claude(
        self,
        prompt: str,
        system: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream a completion from Claude.

        Args:
            prompt: The prompt
            system: Optional system prompt

        Yields:
            Text chunks as they arrive

        Example:
            >>> async for chunk in meta.stream_claude("Write a poem"):
            ...     print(chunk, end="", flush=True)
        """
        if not self._anthropic:
            await self.initialize()
        async for chunk in self._anthropic.stream_completion(prompt, system):
            yield chunk

    # =========================================================================
    # FileSystem Capabilities
    # =========================================================================

    async def read_file(self, path: str) -> CapabilityResult:
        """Read a file.

        Args:
            path: File path

        Returns:
            CapabilityResult with file content
        """
        if not self._filesystem:
            await self.initialize()
        return await self._filesystem.read_file(path)

    async def write_file(
        self,
        path: str,
        content: str,
        create_dirs: bool = True,
    ) -> CapabilityResult:
        """Write content to a file.

        Args:
            path: File path
            content: Content to write
            create_dirs: Create parent directories if needed

        Returns:
            CapabilityResult with write result
        """
        if not self._filesystem:
            await self.initialize()
        return await self._filesystem.write_file(path, content, create_dirs)

    async def list_files(
        self,
        path: str = ".",
        pattern: str | None = None,
        recursive: bool = False,
    ) -> CapabilityResult:
        """List files in a directory.

        Args:
            path: Directory path
            pattern: Glob pattern to filter files
            recursive: Include subdirectories

        Returns:
            CapabilityResult with file list
        """
        if not self._filesystem:
            await self.initialize()
        if pattern:
            return await self._filesystem.glob_files(pattern, path)
        return await self._filesystem.list_directory(path, recursive)

    async def search_in_files(
        self,
        pattern: str,
        path: str = ".",
        file_pattern: str = "**/*.py",
    ) -> CapabilityResult:
        """Search for pattern in files.

        Args:
            pattern: Search pattern (regex)
            path: Base directory
            file_pattern: Glob pattern for files to search

        Returns:
            CapabilityResult with matches
        """
        if not self._filesystem:
            await self.initialize()
        return await self._filesystem.search_content(pattern, path, file_pattern)

    async def git_status(self) -> CapabilityResult:
        """Get git status of the workspace.

        Returns:
            CapabilityResult with git status
        """
        if not self._filesystem:
            await self.initialize()
        return await self._filesystem.git_status()

    # =========================================================================
    # Shell Capabilities
    # =========================================================================

    async def run_shell(
        self,
        command: str,
        timeout: float = 60.0,
    ) -> CapabilityResult:
        """Run a shell command.

        Args:
            command: Command to run
            timeout: Timeout in seconds

        Returns:
            CapabilityResult with command output
        """
        if not self._shell:
            await self.initialize()
        return await self._shell.run(command, timeout)

    async def run_python_script(
        self,
        script_path: str,
        args: list[str] = None,
        timeout: float = 60.0,
    ) -> CapabilityResult:
        """Run a Python script.

        Args:
            script_path: Path to script
            args: Command line arguments
            timeout: Timeout in seconds

        Returns:
            CapabilityResult with script output
        """
        if not self._shell:
            await self.initialize()
        return await self._shell.run_python_script(script_path, args, timeout)

    async def system_info(self) -> CapabilityResult:
        """Get system information.

        Returns:
            CapabilityResult with system info
        """
        if not self._shell:
            await self.initialize()
        return await self._shell.system_info()

    # =========================================================================
    # Memory Capabilities
    # =========================================================================

    async def remember(
        self,
        key: str,
        value: Any,
        ttl_hours: int | None = None,
    ) -> CapabilityResult:
        """Store a value in memory.

        Args:
            key: Storage key
            value: Value to store
            ttl_hours: Optional time-to-live in hours

        Returns:
            CapabilityResult with store result
        """
        if not self._memory:
            await self.initialize()
        return await self._memory.store(key, value, ttl_hours=ttl_hours)

    async def recall(self, key: str) -> CapabilityResult:
        """Retrieve a value from memory.

        Args:
            key: Storage key

        Returns:
            CapabilityResult with retrieved value
        """
        if not self._memory:
            await self.initialize()
        return await self._memory.retrieve(key)

    async def search_memory(
        self,
        query: str,
        limit: int = 10,
    ) -> CapabilityResult:
        """Search memory for matching items.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            CapabilityResult with matching items
        """
        if not self._memory:
            await self.initialize()
        return await self._memory.search(query, limit)

    async def add_to_context(
        self,
        role: str,
        content: str,
    ) -> CapabilityResult:
        """Add a message to conversation context.

        Args:
            role: Message role (user, assistant, system)
            content: Message content

        Returns:
            CapabilityResult with add result
        """
        if not self._memory:
            await self.initialize()
        return await self._memory.add_context(role, content)

    async def get_conversation_context(
        self,
        max_tokens: int = 100000,
    ) -> CapabilityResult:
        """Get conversation context within token limit.

        Args:
            max_tokens: Maximum tokens to return

        Returns:
            CapabilityResult with context messages
        """
        if not self._memory:
            await self.initialize()
        return await self._memory.get_context(max_tokens)

    # =========================================================================
    # Code Creation Capabilities
    # =========================================================================

    async def create_module(
        self,
        name: str,
        description: str,
        save_path: str | None = None,
    ) -> CapabilityResult:
        """Create a complete Python module.

        Args:
            name: Module name
            description: Module description
            save_path: Optional path to save the module

        Returns:
            CapabilityResult with generated module code
        """
        if not self._code_creation:
            await self.initialize()
        return await self._code_creation.create_module(name, description, save_path)

    async def create_class(
        self,
        name: str,
        description: str,
        **kwargs,
    ) -> CapabilityResult:
        """Create a Python class.

        Args:
            name: Class name
            description: Class description
            **kwargs: Additional parameters (base_classes, attributes, methods)

        Returns:
            CapabilityResult with generated class code
        """
        if not self._code_creation:
            await self.initialize()
        return await self._code_creation.create_class(name, description, **kwargs)

    async def create_function(
        self,
        name: str,
        description: str,
        **kwargs,
    ) -> CapabilityResult:
        """Create a Python function.

        Args:
            name: Function name
            description: Function description
            **kwargs: Additional parameters (parameters, return_type)

        Returns:
            CapabilityResult with generated function code
        """
        if not self._code_creation:
            await self.initialize()
        return await self._code_creation.create_function(name, description, **kwargs)

    async def create_tests(
        self,
        code: str,
        test_framework: str = "pytest",
    ) -> CapabilityResult:
        """Generate tests for code.

        Args:
            code: Code to generate tests for
            test_framework: Test framework (pytest, unittest)

        Returns:
            CapabilityResult with generated test code
        """
        if not self._code_creation:
            await self.initialize()
        return await self._code_creation.create_tests(code, test_framework)

    async def refactor_code(
        self,
        code: str,
        instructions: str,
    ) -> CapabilityResult:
        """Refactor code according to instructions.

        Args:
            code: Code to refactor
            instructions: Refactoring instructions

        Returns:
            CapabilityResult with refactored code
        """
        if not self._code_creation:
            await self.initialize()
        return await self._code_creation.refactor(code, instructions)

    async def create_api_endpoint(
        self,
        name: str,
        description: str,
        method: str = "GET",
        framework: str = "fastapi",
    ) -> CapabilityResult:
        """Create an API endpoint.

        Args:
            name: Endpoint name
            description: Endpoint description
            method: HTTP method
            framework: API framework (fastapi, flask)

        Returns:
            CapabilityResult with generated endpoint code
        """
        if not self._code_creation:
            await self.initialize()
        return await self._code_creation.create_api_endpoint(
            name, description, method, framework
        )
