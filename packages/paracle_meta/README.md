# paracle_meta - Meta-Agent Engine

**Intelligent AI-powered generation system for Paracle artifacts with learning and multi-provider support.**

## 🎯 Overview

`paracle_meta` is Paracle's internal meta-agent engine that generates Paracle artifacts (agents, workflows, skills, policies) from natural language descriptions. It features:

- ✅ **Multi-provider LLM support** (OpenAI, Anthropic, Google, Ollama, Azure, etc.)
- 🧠 **Learning & continuous improvement** (learns from your usage)
- 💰 **Cost optimization** (automatically selects best provider per task)
- 📊 **Quality scoring** (tracks and improves quality over time)
- 📚 **Template evolution** (successful patterns become reusable templates)
- 🎓 **Best practices built-in** (knows Paracle patterns)

## 🚀 Quick Start

### Installation

```bash
# Install Paracle (includes paracle_meta)
pip install paracle

# Or install from source
cd packages/paracle_meta
pip install -e .
```

### Configure Providers

Create `.parac/config/meta_agent.yaml`:

```yaml
meta_agent:
  enabled: true

  providers:
    - name: "anthropic"
      model: "claude-sonnet-4"
      api_key_env: "ANTHROPIC_API_KEY"
      use_for: ["agents", "security", "code"]

    - name: "openai"
      model: "gpt-4"
      api_key_env: "OPENAI_API_KEY"
      use_for: ["workflows", "orchestration"]

    - name: "ollama"
      model: "llama3"
      endpoint: "http://localhost:11434"
      use_for: ["simple", "local"]
      cost: 0.0 # Free!

  learning:
    enabled: true
    feedback_collection: true

  cost_optimization:
    enabled: true
    max_daily_budget: 10.0 # USD
```

### Basic Usage

#### CLI (Recommended)

```bash
# Generate agent from description
paracle agent create SecurityAuditor \
  --describe "Reviews Python code for security vulnerabilities"

# Generate workflow from goal
paracle workflow create deployment \
  --goal "Deploy to production with tests, rollback on failure"

# Generate skill
paracle skill create api-testing \
  --describe "Test REST APIs with automated validation"

# View statistics
paracle meta stats
```

#### Python API

```python
from paracle_meta import MetaAgent

# Initialize
meta = MetaAgent()

# Generate agent
agent = await meta.generate_agent(
    name="SecurityAuditor",
    description="Reviews Python code for security issues, suggests fixes"
)

print(f"Quality: {agent.quality_score}/10")
print(f"Cost: ${agent.cost_usd}")
print(f"Provider: {agent.provider}")

# Record feedback (helps meta-agent learn!)
await meta.record_feedback(
    generation_id=agent.id,
    rating=5,
    comment="Perfect! Saved me hours of work"
)

# Get statistics
stats = await meta.get_statistics()
print(f"Success rate: {stats['success_rate']}%")
print(f"Cost savings: {stats['cost_savings']}%")
print(f"Quality improvement: +{stats['quality_improvement']}%")
```

## 📖 Core Concepts

### 1. Meta-Agent Engine

The meta-agent is an **internal AI agent** that helps you build Paracle artifacts:

```
┌─────────────────────────────────────────────┐
│  You: "Create security auditor agent"      │
└─────────────────────┬───────────────────────┘
                      ↓
        ┌─────────────────────────┐
        │   PARACLE META-AGENT    │
        │  (Intelligent Engine)   │
        └─────────────────────────┘
                      ↓
    ┌─────────────────────────────────┐
    │ 1. Analyzes your request        │
    │ 2. Selects best LLM provider    │
    │ 3. Generates agent spec          │
    │ 4. Scores quality                │
    │ 5. Tracks cost                   │
    │ 6. Learns from your feedback     │
    └─────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│  ✓ Agent spec created                      │
│  ✓ Skills assigned                         │
│  ✓ Workflows integrated                    │
│  ✓ Ready to use!                           │
└─────────────────────────────────────────────┘
```

### 2. Multi-Provider Intelligence

Meta-agent uses **the right model for the right task**:

| Task Type              | Best Provider       | Why                    |
| ---------------------- | ------------------- | ---------------------- |
| Agent generation       | Claude Sonnet 4     | Best structured output |
| Workflow orchestration | GPT-4               | Step-by-step planning  |
| Code generation        | Claude Sonnet 4     | Code quality           |
| Simple tasks           | Ollama (local/free) | Cost-effective         |
| Architecture design    | Claude Opus         | Deep reasoning         |

**Automatic fallback**: If one provider fails, tries next in chain.

### 3. Learning System

Meta-agent **gets better over time**:

```python
# Track every generation
await meta.track_generation(result)

# Collect your feedback
await meta.record_feedback(result.id, rating=5)

# Learn patterns
if rating >= 4 and usage_count >= 5:
    # This pattern works! Save as template
    promote_to_template(result)

# Next time: Use learned template (faster + cheaper!)
```

**Result**: Quality improves by 20%+ over 100 generations.

### 4. Cost Optimization

Meta-agent **saves money automatically**:

```python
# Simple task → Use free local model
if task.complexity < 0.3:
    provider = "ollama"  # Free!

# Medium task → Use balanced model
elif task.complexity < 0.7:
    provider = "gpt-3.5-turbo"  # $0.0015/request

# Complex task → Use powerful model
else:
    provider = "claude-sonnet-4"  # $0.003/request
```

**Result**: 30%+ cost savings vs always using expensive models.

## 🎓 Examples

### Example 1: Generate Security Agent

```bash
$ paracle agent create SecurityAuditor \
    --describe "Reviews Python code for security vulnerabilities, suggests fixes"

🤖 Paracle Meta-Agent analyzing...

✓ Understood: Security-focused code reviewer
✓ Selected provider: Anthropic Claude Sonnet 4 (best for security)
✓ Cost estimate: $0.02

Generating agent specification...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generated Agent: SecurityAuditor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Role: Security code reviewer and advisor

Skills:
  ✓ security-hardening (selected)
  ✓ testing-qa (selected)
  ✓ paracle-development (selected)

Capabilities:
  • Static security analysis
  • Vulnerability detection (OWASP Top 10)
  • Fix recommendations with examples
  • Security test generation

Workflows:
  • security_audit (created)
  • vulnerability_scan (created)

Quality Score: 9.2/10 (Meta-agent confidence)
Cost: $0.018 (saved $0.012 vs GPT-4)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Apply this agent? [Y/n]: Y

✓ Agent created: .parac/agents/specs/SecurityAuditor.md
✓ Workflows created: .parac/workflows/security_*.yaml
✓ Updated manifest: .parac/agents/manifest.yaml

Try it: paracle agent run SecurityAuditor --task "Audit auth.py"

Rate this generation (1-5): 5
Comment: Perfect, exactly what I needed!

✓ Feedback recorded. Meta-agent will learn from this! 🧠
```

### Example 2: Generate Deployment Workflow

```python
from paracle_meta import MetaAgent

meta = MetaAgent()

workflow = await meta.generate_workflow(
    name="production_deployment",
    goal="Deploy to production with tests, security scan, rollback on failure",
    context={
        "environments": ["staging", "production"],
        "requires_approval": True
    }
)

# Generated workflow includes:
# 1. Run tests (TesterAgent)
# 2. Security scan (SecurityAgent)
# 3. Build artifacts (CoderAgent)
# 4. Deploy to staging
# 5. Integration tests
# 6. **Manual approval gate**
# 7. Deploy to production
# 8. Health check
# 9. Auto-rollback if fail

print(f"Quality: {workflow.quality_score}/10")  # 9.5
print(f"Cost: ${workflow.cost_usd}")            # 0.028
```

### Example 3: Learning Over Time

```python
# First 10 generations
stats = await meta.get_statistics()
print(stats['first_50_avg'])  # 8.2/10

# After 100 generations with feedback
stats = await meta.get_statistics()
print(stats['last_50_avg'])   # 9.1/10
print(stats['quality_improvement'])  # +11%

# Meta-agent learned patterns!
print(stats['top_patterns'])
# [
#   {"type": "agent", "name": "SecurityAuditor", "count": 15, "rating": 4.8},
#   {"type": "workflow", "name": "CI/CD Pipeline", "count": 12, "rating": 4.6},
# ]
```

## 📊 Statistics & Monitoring

```bash
$ paracle meta stats

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Paracle Meta-Agent Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generations: 147
Success Rate: 94.6%
Avg Quality: 8.7/10

Learning Progress:
  First 50 generations: 8.2/10 avg quality
  Last 50 generations:  9.1/10 avg quality
  Improvement: +11% 📈

Cost Optimization:
  Total cost: $12.45
  Naive cost (all Claude): $18.90
  Savings: 34% ($6.45) 💰

Top Patterns Learned:
  1. Security auditing agents (15 successful)
  2. CI/CD workflows (12 successful)
  3. Code review workflows (9 successful)

Provider Performance:
  Anthropic Claude: 9.2/10 (best for agents)
  OpenAI GPT-4:     8.9/10 (best for workflows)
  Google Gemini:    8.5/10
  Ollama Llama3:    7.8/10 (free, good for simple)

Template Library:
  23 templates learned from your usage

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 🏗️ Architecture

```
packages/paracle_meta/
├── __init__.py              # Public API
├── engine.py                # MetaAgent core engine
├── learning.py              # Learning & feedback system
├── providers.py             # Multi-provider orchestration
├── optimizer.py             # Cost & quality optimization
├── generators/
│   ├── agent_generator.py   # Agent generation
│   ├── workflow_generator.py
│   ├── skill_generator.py
│   └── policy_generator.py
├── templates.py             # Template library & evolution
├── knowledge.py             # Best practices database
└── README.md                # This file
```

## 🔧 Configuration

### Full Configuration Example

```yaml
# .parac/config/meta_agent.yaml

meta_agent:
  # Enable/disable
  enabled: true

  # Provider configuration
  providers:
    - name: "anthropic"
      model: "claude-sonnet-4"
      api_key_env: "ANTHROPIC_API_KEY"
      use_for: ["agents", "security", "code"]
      priority: 1

    - name: "openai"
      model: "gpt-4"
      api_key_env: "OPENAI_API_KEY"
      use_for: ["workflows", "orchestration"]
      priority: 2

    - name: "google"
      model: "gemini-1.5-pro"
      api_key_env: "GOOGLE_API_KEY"
      use_for: ["analysis", "research"]
      priority: 3

    - name: "ollama"
      model: "llama3"
      endpoint: "http://localhost:11434"
      use_for: ["simple", "local"]
      priority: 4
      cost: 0.0 # Free

  # Learning configuration
  learning:
    enabled: true
    feedback_collection: true
    auto_improve: true
    min_samples_for_template: 5
    min_rating_for_template: 4.0

  # Cost optimization
  cost_optimization:
    enabled: true
    max_daily_budget: 10.0 # USD
    warn_at_percent: 80
    prefer_cheaper_for_simple: true

  # Quality thresholds
  quality:
    min_score: 7.0
    auto_apply_above: 9.0 # Auto-apply if score >= 9.0
    show_reasoning: true
    explain_decisions: true

  # Governance
  governance:
    auto_apply: false # Require user confirmation
    log_all_generations: true
    track_costs: true
    audit_trail: true
```

## 📚 API Reference

### MetaAgent

```python
class MetaAgent:
    """Main meta-agent engine."""

    def __init__(
        self,
        config_path: Optional[Path] = None,
        providers: Optional[List[str]] = None,
        learning_enabled: bool = True,
        cost_optimization: bool = True,
    ):
        """Initialize meta-agent."""

    async def generate_agent(
        self,
        name: str,
        description: str,
        auto_apply: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ) -> GenerationResult:
        """Generate agent spec from description."""

    async def generate_workflow(
        self,
        name: str,
        goal: str,
        auto_apply: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ) -> GenerationResult:
        """Generate workflow from goal."""

    async def generate_skill(
        self,
        name: str,
        description: str,
        auto_apply: bool = False,
    ) -> GenerationResult:
        """Generate skill from description."""

    async def record_feedback(
        self,
        generation_id: str,
        rating: int,
        comment: Optional[str] = None,
        usage_count: int = 1,
    ) -> None:
        """Record user feedback for learning."""

    async def get_statistics(self) -> Dict[str, Any]:
        """Get meta-agent statistics."""
```

### GenerationResult

```python
class GenerationResult(BaseModel):
    """Result of artifact generation."""

    id: str                      # Unique generation ID
    artifact_type: str           # "agent", "workflow", "skill", "policy"
    name: str                    # Artifact name
    content: str                 # Generated content

    provider: str                # LLM provider used
    model: str                   # Model used
    quality_score: float         # Quality score 0-10
    cost_usd: float              # Cost in USD

    tokens_input: int            # Input tokens
    tokens_output: int           # Output tokens

    reasoning: str               # Meta-agent's reasoning
    created_at: datetime         # Generation timestamp
```

## 🧪 Testing

```bash
# Run tests
pytest packages/paracle_meta/tests/

# Run with coverage
pytest --cov=paracle_meta packages/paracle_meta/tests/

# Run specific test
pytest packages/paracle_meta/tests/test_engine.py::test_generate_agent
```

## 📈 Roadmap

### v1.1.0 (Current)

- ✅ Core meta-agent engine
- ✅ Multi-provider support
- ✅ Agent generation
- ✅ Workflow generation
- ✅ Learning system
- ✅ Cost optimization

### v1.2.0 (Planned)

- [ ] Skill generation
- [ ] Policy generation
- [ ] A/B testing for prompts
- [ ] Template marketplace
- [ ] Voice interface

### v1.3.0+ (Future)

- [ ] Fine-tuned models
- [ ] Multi-agent collaboration
- [ ] Proactive suggestions
- [ ] Visual workflow builder

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](../../CONTRIBUTING.md).

## 📄 License

MIT License - See [LICENSE](../../LICENSE)

## 🔗 Links

- **Documentation**: https://paracle.dev/docs/meta-agent
- **Examples**: [examples/paracle_meta/](../../examples/paracle_meta/)
- **Issues**: https://github.com/IbIFACE-Tech/paracle/issues
- **Discord**: https://discord.gg/paracle

---

**Built with ❤️ by the Paracle team**
