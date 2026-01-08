# Agent Execution Model

## 🎯 Critical Distinction: Agents Are Executed, Not Personas

### ❌ WRONG: "Adopting Agent Persona"

**DON'T think of it this way:**
```
AI Assistant: "I will now adopt the CoderAgent persona and implement the feature..."
```

This implies the AI assistant **becomes** the agent, which is incorrect.

### ✅ CORRECT: "Running/Executing Agents"

**DO think of it this way:**
```
AI Assistant: "I'll run the CoderAgent to implement this feature..."
User: paracle agent run coder --task "Implement authentication"
```

Agents are **executable programs**, not personas to roleplay.

---

## 🔧 What Are Paracle Agents?

### Agents Are Executable Entities

Agents are **specifications** that define:
- **Role**: What the agent is responsible for (e.g., "code implementation")
- **Capabilities**: What the agent can do (e.g., "write production-quality code")
- **Instructions**: How the agent should approach tasks
- **Skills**: Specialized knowledge the agent has access to
- **Model Configuration**: LLM provider, model, temperature, etc.

### Agents Are Run, Not Adopted

When you need an agent's capabilities, you **execute** it:

```bash
# Execute the CoderAgent
paracle agent run coder --task "Implement user authentication"

# Execute the ReviewerAgent
paracle agent run reviewer --task "Review authentication PR"

# Execute the TesterAgent
paracle agent run tester --task "Create test suite for auth"
```

---

## 🤖 Role of AI Assistants (GitHub Copilot, Claude, etc.)

### What AI Assistants Do

1. **Help Select the Right Agent**
   - Analyze the task
   - Recommend which agent to run
   - Explain why that agent is appropriate

2. **Prepare Agent Execution**
   - Gather necessary context
   - Check prerequisites (current phase, roadmap, policies)
   - Formulate clear task descriptions

3. **Interpret Agent Output**
   - Explain what the agent did
   - Summarize results
   - Suggest next steps

4. **Assist Manual Implementation** (when agents aren't run)
   - Follow agent standards from specs
   - Apply agent's assigned skills
   - Implement according to agent's guidelines

### What AI Assistants DON'T Do

❌ **DON'T "become" the agent**
❌ **DON'T claim to "adopt a persona"**
❌ **DON'T pretend to execute with agent's authority**

The AI assistant is a **helper**, not the agent itself.

---

## 📋 Correct Workflow

### Scenario: Implement a New Feature

**Step 1: Task Analysis**
```
User: "I need to implement user authentication"

AI Assistant:
"Based on this task, I recommend running the CoderAgent because:
- It's a code implementation task
- CoderAgent specializes in writing production-quality code
- It has the 'paracle-development' skill for framework patterns

Let me check the project state first..."
[Reads .parac/memory/context/current_state.yaml]
[Reads .parac/roadmap/roadmap.yaml]

"The project is in Phase 4 (API Server & CLI), and authentication
is a valid feature for this phase. Ready to proceed."
```

**Step 2: Agent Selection**
```
AI Assistant:
"I recommend: paracle agent run coder --task 'Implement user authentication with JWT tokens'

Alternatively, if you want me to implement manually, I'll follow:
- CoderAgent standards from .parac/agents/specs/coder.md
- Code style from .parac/policies/CODE_STYLE.md
- Testing policy from .parac/policies/TESTING.md"
```

**Step 3A: Agent Execution (Preferred)**
```
User: paracle agent run coder --task "Implement user authentication with JWT tokens" --mode safe

[CoderAgent executes]
- Analyzes requirements
- Designs solution
- Implements code
- Creates tests
- Updates documentation
```

**Step 3B: Manual Implementation (Alternative)**
```
User: "Implement it manually following CoderAgent standards"

AI Assistant:
[Reads .parac/agents/specs/coder.md]
[Implements following agent's guidelines]
[Applies agent's assigned skills]
[Logs action to .parac/memory/logs/agent_actions.log]
```

**Step 4: After Execution**
```
AI Assistant:
"The implementation is complete. Here's what was done:
- Created packages/paracle_api/auth.py (JWT authentication)
- Added tests/unit/test_auth.py (100% coverage)
- Updated docs/api-reference.md (authentication endpoints)

Logged to .parac/memory/logs/agent_actions.log:
[2026-01-06 10:30:00] [CoderAgent] [IMPLEMENTATION] Implemented JWT authentication in packages/paracle_api/auth.py"
```

---

## 🎭 Analogy: Agents Are Like Programs

Think of agents like command-line programs:

### ❌ WRONG Analogy
```
"I will become the 'ls' command and list files..."
```

### ✅ CORRECT Analogy
```
"I'll run the 'ls' command to list files:
$ ls -la"
```

Similarly for agents:

### ❌ WRONG
```
"I will adopt the CoderAgent persona and write code..."
```

### ✅ CORRECT
```
"I'll run the CoderAgent to write this code:
$ paracle agent run coder --task 'Write authentication module'"
```

---

## 🔗 Integration with External AI Applications

### MCP Server Integration

External AI applications (Claude Desktop, Cline, Continue.dev) interact with Paracle agents through the MCP server:

```json
{
  "tool": "paracle_run_agent",
  "params": {
    "agent_id": "coder",
    "task": "Implement user authentication",
    "inputs": {
      "language": "python",
      "framework": "FastAPI"
    }
  }
}
```

The AI application **calls the tool** to **execute the agent** - it doesn't "become" the agent.

### Example: Claude Desktop

```
User: "Implement user authentication in the Paracle project"

Claude: "I'll execute the CoderAgent for this task..."
[Uses paracle_run_agent MCP tool]
[Agent executes in Paracle]
[Returns results to Claude]

Claude: "The CoderAgent has implemented authentication.
Here's what was created:
- packages/paracle_api/auth.py
- tests/unit/test_auth.py
- Endpoint: POST /api/auth/login"
```

Claude didn't "become" CoderAgent - it **orchestrated** CoderAgent's execution.

---

## 📊 Agent Execution vs. Manual Implementation

### When to Execute Agents

✅ **Use `paracle agent run`** when:
- Complex, multi-step tasks
- Need agent's specialized skills
- Want consistent agent behavior
- Automated workflows (CI/CD)
- MCP integration (external AI apps)

### When to Implement Manually (Following Agent Standards)

✅ **Manual implementation** when:
- Simple, straightforward tasks
- Agent execution not available
- Learning/teaching purposes
- Rapid prototyping
- AI assistant helping in real-time

**Key**: Even when implementing manually, **follow agent standards** from `.parac/agents/specs/{agent}.md`

---

## 🎓 Key Takeaways

### For AI Application Developers

1. **Agents are executable entities** with specifications
2. **Run agents via CLI** or **MCP tools**, don't roleplay
3. **AI assistants orchestrate**, they don't "become" agents
4. **Agent specs define behavior**, not the AI's identity

### For Paracle Users

1. **Use `paracle agent run`** to execute agents
2. **AI assistants help select** the right agent
3. **Agent specs document** what each agent does
4. **Manual implementation** should follow agent standards

### For AI Assistants (GitHub Copilot, Claude, etc.)

1. **DON'T say**: "I will adopt the CoderAgent persona..."
2. **DO say**: "I'll run the CoderAgent..." or "Following CoderAgent standards..."
3. **Help users**: Select agent, prepare execution, interpret results
4. **When implementing manually**: Follow agent specs, apply skills, log actions

---

## 📚 Related Documentation

- **[Agent Discovery](agent-discovery.md)** - How agents are discovered
- **[Agent Execution Quick Reference](agent-execution-quickref.md)** - Command reference
- **[Agent Run Command](agent-run-quickref.md)** - Complete guide
- **[MCP Integration](mcp-integration.md)** - External AI integration
- **[MCP Capability Coverage](mcp-capability-coverage.md)** - MCP server tools

---

## ✅ Terminology Summary

| ❌ AVOID                    | ✅ USE INSTEAD                       |
| -------------------------- | ----------------------------------- |
| "Adopt CoderAgent persona" | "Run CoderAgent"                    |
| "Become the agent"         | "Execute the agent"                 |
| "Agent persona"            | "Agent specification"               |
| "Take on agent role"       | "Follow agent standards"            |
| "I am CoderAgent"          | "I'll run CoderAgent"               |
| "Switch to PM persona"     | "Run PM agent" or "Follow PM specs" |

---

**Last Updated**: 2026-01-06
**Version**: 1.0
**Status**: Specification
**Purpose**: Clarify agent execution model for all AI/IDE integrations
