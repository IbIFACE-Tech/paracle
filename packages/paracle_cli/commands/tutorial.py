"""Interactive tutorial command for Paracle onboarding."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()


def get_progress_file() -> Path:
    """Get tutorial progress file path."""
    parac_dir = Path.cwd() / ".parac"
    if not parac_dir.exists():
        parac_dir = Path.cwd()

    progress_dir = parac_dir / "memory"
    progress_dir.mkdir(parents=True, exist_ok=True)
    return progress_dir / ".tutorial_progress.json"


def load_progress() -> dict[str, Any]:
    """Load tutorial progress."""
    progress_file = get_progress_file()
    if progress_file.exists():
        return json.loads(progress_file.read_text())

    return {
        "version": 1,
        "started": datetime.now().isoformat(),
        "last_step": 0,
        "checkpoints": {
            "step_1": "not_started",
            "step_2": "not_started",
            "step_3": "not_started",
            "step_4": "not_started",
            "step_5": "not_started",
            "step_6": "not_started",
        },
    }


def save_progress(progress: dict[str, Any]) -> None:
    """Save tutorial progress."""
    progress_file = get_progress_file()
    progress_file.write_text(json.dumps(progress, indent=2))


def show_welcome() -> None:
    """Show welcome message."""
    welcome = Panel(
        "[bold cyan]Welcome to Paracle Interactive Tutorial[/bold cyan]\n\n"
        "This tutorial will guide you through:\n"
        "  1.  Creating your first agent\n"
        "  2.  Adding tools to your agent\n"
        "  3.  Adding skills for specialized capabilities\n"
        "  4.  Creating project templates\n"
        "  5.  Testing your agent locally\n"
        "  6.  Running your first workflow\n\n"
        "[dim]Estimated time: 30 minutes[/dim]\n"
        "[dim]You can exit anytime and resume with "
        "'paracle tutorial resume'[/dim]",
        title="Welcome",
        border_style="cyan",
    )
    console.print(welcome)
    console.print()


def step_1_create_agent(progress: dict[str, Any]) -> bool:
    """Step 1: Create your first agent."""
    console.print(
        Panel(
            "[bold green]Step 1/6: Create Your First Agent[/bold green]\n\n"
            "Let's create an AI agent with proper .parac/ governance integration.",
            border_style="green",
        )
    )
    console.print()

    # Check if .parac exists
    parac_dir = Path.cwd() / ".parac"
    if not parac_dir.exists():
        console.print(
            "[yellow]Warning: No .parac/ directory found. Let's initialize one![/yellow]"
        )
        if Confirm.ask("Initialize project with lite mode?", default=True):
            console.print("[dim]Running: paracle init --template lite[/dim]")
            import subprocess

            result = subprocess.run(
                ["paracle", "init", "--template", "lite"],
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                console.print(f"[red]Error: {result.stderr}[/red]")
                return False
            console.print("[green]Project initialized![/green]\n")

    # Create agent
    agent_name = Prompt.ask(
        "What would you like to name your agent?", default="my-assistant"
    )

    # Validate agent name format
    import re

    if not re.match(r"^[a-z][a-z0-9-]*$", agent_name):
        console.print(
            "[yellow]Agent name should be lowercase with hyphens (e.g., my-assistant)[/yellow]"
        )
        agent_name = agent_name.lower().replace(" ", "-").replace("_", "-")
        console.print(f"[dim]Using: {agent_name}[/dim]")

    description = Prompt.ask(
        "What will this agent do? (brief description)",
        default="Help me with various tasks",
    )

    # Create agent spec directory
    agents_dir = parac_dir / "agents" / "specs"
    agents_dir.mkdir(parents=True, exist_ok=True)

    # Create agent spec file with new format (governance integration)
    agent_file = agents_dir / f"{agent_name}.md"
    agent_title = agent_name.replace("-", " ").title() + " Agent"
    agent_content = f"""# {agent_title}

## Role

{description}

## Governance Integration

### Before Starting Any Task

1. Read `.parac/memory/context/current_state.yaml` - Current phase & status
2. Check `.parac/roadmap/roadmap.yaml` - Priorities for current phase
3. Review `.parac/memory/context/open_questions.md` - Check for blockers

### After Completing Work

Log action to `.parac/memory/logs/agent_actions.log`:

```
[TIMESTAMP] [{agent_name.upper().replace('-', '_')}] [ACTION_TYPE] Description
```

**Action Types**: IMPLEMENTATION, TEST, BUGFIX, REFACTORING, REVIEW, DOCUMENTATION

## Skills

- paracle-development

## Responsibilities

### Primary Tasks

- Understand natural language instructions
- Execute tasks step-by-step
- Provide clear explanations

### Quality Standards

- Follow project coding standards
- Document work in agent_actions.log

## Tools & Capabilities

- Task execution
- Code generation
- Problem solving

## Usage

```bash
paracle agents run {agent_name} --task "Your task here"
```
"""

    agent_file.write_text(agent_content)

    console.print(f"\n[green]Created agent spec at {agent_file}[/green]")

    # Validate the created agent
    console.print("\n[cyan]Validating agent spec...[/cyan]")
    import subprocess

    result = subprocess.run(
        ["paracle", "agents", "validate", agent_name],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        console.print("[green]Agent spec is valid![/green]")
    else:
        console.print("[yellow]Warning: Agent spec has issues[/yellow]")
        console.print(f"[dim]{result.stdout}[/dim]")

    console.print("\n[cyan]Agent created with:[/cyan]")
    console.print(
        Panel(
            f"[bold]Name:[/bold] {agent_name}\n"
            f"[bold]Role:[/bold] {description}\n"
            f"[bold]Governance:[/bold] .parac/ integration included\n"
            f"[bold]Location:[/bold] .parac/agents/specs/{agent_name}.md",
            title="Agent Configuration",
        )
    )

    console.print("\n[cyan]Agent management commands:[/cyan]")
    console.print(f"  paracle agents validate {agent_name}  # Validate spec")
    console.print(f"  paracle agents format {agent_name}    # Auto-fix issues")
    console.print("  paracle agents list                  # List all agents")

    # Update progress
    progress["checkpoints"]["step_1"] = "completed"
    progress["last_step"] = 1
    save_progress(progress)

    console.print()
    if not Confirm.ask("Ready for the next step?", default=True):
        console.print(
            "[yellow]Progress saved. Run 'paracle tutorial resume' to continue.[/yellow]"
        )
        return False

    return True


def step_2_add_tools(progress: dict[str, Any]) -> bool:
    """Step 2: Add tools to agent."""
    console.print(
        Panel(
            "[bold green]Step 2/6: Add Tools to Your Agent[/bold green]\n\n"
            "Tools give your agent capabilities like reading files, making HTTP requests, or running shell commands.",
            border_style="green",
        )
    )
    console.print()

    # Show available tools
    table = Table(title="Available Built-in Tools")
    table.add_column("Tool", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Use Case", style="dim")

    tools_info = [
        (
            "filesystem",
            "Read/write files and directories",
            "File operations, data processing",
        ),
        ("http", "Make HTTP requests", "API calls, web scraping"),
        ("shell", "Execute shell commands", "System operations, git commands"),
        ("python", "Execute Python code", "Data analysis, calculations"),
        ("search", "Search the web", "Research, fact-checking"),
    ]

    for tool_name, desc, use_case in tools_info:
        table.add_row(tool_name, desc, use_case)

    console.print(table)
    console.print()

    # Let user select tools
    console.print("[cyan]Select tools to add (comma-separated):[/cyan]")
    selected = Prompt.ask("Tools", default="filesystem,http")

    tools = [t.strip() for t in selected.split(",")]

    # Find agent file (skip SCHEMA.md and TEMPLATE.md)
    parac_dir = Path.cwd() / ".parac"
    agents_dir = parac_dir / "agents" / "specs"
    agent_files = [
        f
        for f in agents_dir.glob("*.md")
        if f.stem.upper() not in ("SCHEMA", "TEMPLATE")
    ]

    if not agent_files:
        console.print("[red]No agent found. Please complete step 1 first.[/red]")
        return False

    agent_file = agent_files[0]  # Use first agent

    # Read existing content
    content = agent_file.read_text()

    # Update Tools & Capabilities section if it exists
    tools_list = "\n".join([f"- {tool}" for tool in tools])

    if "## Tools & Capabilities" in content:
        # Replace existing section
        import re

        content = re.sub(
            r"## Tools & Capabilities\n\n.*?(?=\n## |\Z)",
            f"## Tools & Capabilities\n\n{tools_list}\n\n",
            content,
            flags=re.DOTALL,
        )
    elif "## Usage" in content:
        # Insert before Usage
        content = content.replace(
            "## Usage", f"## Tools & Capabilities\n\n{tools_list}\n\n## Usage"
        )
    else:
        # Append
        content += f"\n\n## Tools & Capabilities\n\n{tools_list}\n"

    agent_file.write_text(content)

    console.print(f"\n[green]Added {len(tools)} tools to your agent![/green]")
    console.print(f"\n[cyan]Tools added:[/cyan] {', '.join(tools)}")

    # Explain permissions
    console.print("\n[yellow]Tool Permissions:[/yellow]")
    console.print("  - Tools run with your user permissions")
    console.print("  - Always review tool actions before approval")
    console.print("  - Use [bold]--mode safe[/bold] for manual approval gates")

    # Update progress
    progress["checkpoints"]["step_2"] = "completed"
    progress["last_step"] = 2
    save_progress(progress)

    console.print()
    if not Confirm.ask("Ready for the next step?", default=True):
        console.print(
            "[yellow]Progress saved. Run 'paracle tutorial resume' to continue.[/yellow]"
        )
        return False

    return True


def step_3_add_skills(progress: dict[str, Any]) -> bool:
    """Step 3: Add skills for specialized capabilities."""
    console.print(
        Panel(
            "[bold green]Step 3/6: Add Skills to Your Agent[/bold green]\n\n"
            "Skills are reusable knowledge modules that give your agent specialized expertise.",
            border_style="green",
        )
    )
    console.print()

    # Show available skills
    console.print("[cyan]Checking available skills...[/cyan]")

    parac_dir = Path.cwd() / ".parac"
    skills_dir = parac_dir / "agents" / "skills"

    if not skills_dir.exists():
        console.print(
            "[yellow]⚠️  No skills directory found. Let's check built-in skills.[/yellow]\n"
        )

        # Show example skills
        table = Table(title="Example Built-in Skills")
        table.add_column("Skill", style="cyan")
        table.add_column("Description", style="white")

        example_skills = [
            ("paracle-development", "Framework-specific development patterns"),
            ("api-development", "REST API design and implementation"),
            ("testing-qa", "Testing strategies and quality assurance"),
            ("security-hardening", "Security best practices"),
            ("performance-optimization", "Performance tuning and optimization"),
        ]

        for skill_name, desc in example_skills:
            table.add_row(skill_name, desc)

        console.print(table)
        console.print()

        if Confirm.ask("Would you like to create a custom skill?", default=True):
            skill_name = Prompt.ask("Skill name", default="custom-skill")
            skill_desc = Prompt.ask("Skill description", default="Custom expertise")

            # Create skills directory
            skills_dir.mkdir(parents=True, exist_ok=True)

            # Create skill files
            skill_dir = skills_dir / skill_name
            skill_dir.mkdir(exist_ok=True)

            # Create skill.yaml
            skill_yaml = skill_dir / f"{skill_name}.yaml"
            skill_yaml_content = f"""name: {skill_name}
description: {skill_desc}
version: "1.0.0"
priority: medium
capabilities:
  - capability_1
  - capability_2
"""
            skill_yaml.write_text(skill_yaml_content)

            # Create SKILL.md
            skill_md = skill_dir / "SKILL.md"
            skill_md_content = f"""# {skill_name.replace('-', ' ').title()}

{skill_desc}

## Expertise Areas

- Area 1
- Area 2

## Guidelines

When working with this skill, follow these guidelines:

1. Guideline 1
2. Guideline 2

## Examples

```bash
# Example usage
paracle agents run my-agent --skill {skill_name}
```
"""
            skill_md.write_text(skill_md_content)

            console.print(f"\n[green]✅ Created skill at {skill_dir}[/green]")

            # Assign skill to agent (skip SCHEMA.md and TEMPLATE.md)
            agents_dir = parac_dir / "agents" / "specs"
            agent_files = [
                f
                for f in agents_dir.glob("*.md")
                if f.stem.upper() not in ("SCHEMA", "TEMPLATE")
            ]

            if agent_files:
                agent_file = agent_files[0]
                content = agent_file.read_text()

                # Update Skills section if it exists, otherwise add it
                if "## Skills" in content:
                    # Add skill to existing section
                    import re

                    content = re.sub(
                        r"(## Skills\n\n)(.*?)(?=\n## |\Z)",
                        rf"\1\2- {skill_name}\n",
                        content,
                        flags=re.DOTALL,
                    )
                elif "## Responsibilities" in content:
                    # Insert before Responsibilities
                    content = content.replace(
                        "## Responsibilities",
                        f"## Skills\n\n- {skill_name}\n\n## Responsibilities",
                    )
                else:
                    content += f"\n\n## Skills\n\n- {skill_name}\n"

                agent_file.write_text(content)
                console.print("[green]✅ Assigned skill to your agent![/green]")
    else:
        # List existing skills
        existing_skills = [d.name for d in skills_dir.iterdir() if d.is_dir()]
        if existing_skills:
            console.print(f"[green]Found {len(existing_skills)} skills:[/green]")
            for skill in existing_skills:
                console.print(f"  • {skill}")
        else:
            console.print(
                "[yellow]No skills found. Create one using the prompts above.[/yellow]"
            )

    console.print(
        "\n[cyan]💡 Tip:[/cyan] Skills can be shared across agents and provide specialized knowledge!"
    )

    # Update progress
    progress["checkpoints"]["step_3"] = "completed"
    progress["last_step"] = 3
    save_progress(progress)

    console.print()
    if not Confirm.ask("Ready for the next step?", default=True):
        console.print(
            "[yellow]💾 Progress saved. Run 'paracle tutorial resume' to continue.[/yellow]"
        )
        return False

    return True


def step_4_create_template(progress: dict[str, Any]) -> bool:
    """Step 4: Create project templates."""
    console.print(
        Panel(
            "[bold green]📍 Step 4/6: Create Project Templates[/bold green]\n\n"
            "Templates are reusable project configurations that you can share with your team.",
            border_style="green",
        )
    )
    console.print()

    console.print("[cyan]Template types:[/cyan]")
    console.print("  • [bold]lite[/bold]: Minimal setup (5 files) - Quick prototyping")
    console.print(
        "  • [bold]standard[/bold]: Full setup (30+ files) - Production ready"
    )
    console.print("  • [bold]custom[/bold]: Your own template")
    console.print()

    if Confirm.ask("Would you like to create a custom template?", default=False):
        template_name = Prompt.ask("Template name", default="my-template")
        template_desc = Prompt.ask(
            "Template description", default="Custom project template"
        )

        parac_dir = Path.cwd() / ".parac"
        templates_dir = parac_dir / "templates"
        templates_dir.mkdir(exist_ok=True)

        template_dir = templates_dir / template_name
        template_dir.mkdir(exist_ok=True)

        # Create template.yaml
        template_yaml = template_dir / "template.yaml"
        template_yaml_content = f"""name: {template_name}
description: {template_desc}
version: "1.0.0"
author: "Your Name"
tags:
  - custom
  - template

structure:
  - .parac/project.yaml
  - .parac/agents/specs/
  - .parac/workflows/
  - .parac/memory/context/

variables:
  project_name: "{{{{ project_name }}}}"
  author: "{{{{ author }}}}"
"""
        template_yaml.write_text(template_yaml_content)

        # Create README
        readme = template_dir / "README.md"
        readme_content = f"""# {template_name.replace('-', ' ').title()}

{template_desc}

## Usage

```bash
paracle init --template {template_name}
```

## Structure

- `.parac/` - Project configuration
- `agents/` - Agent specifications
- `workflows/` - Workflow definitions

## Customization

Edit `template.yaml` to customize the template structure.
"""
        readme.write_text(readme_content)

        console.print(f"\n[green]✅ Created template at {template_dir}[/green]")
        console.print(f"\n[cyan]Usage:[/cyan] paracle init --template {template_name}")
    else:
        console.print("\n[dim]You can create templates later using:[/dim]")
        console.print("[dim]  paracle init --template custom[/dim]")

    console.print(
        "\n[cyan]💡 Tip:[/cyan] Templates are great for standardizing projects across your team!"
    )

    # Update progress
    progress["checkpoints"]["step_4"] = "completed"
    progress["last_step"] = 4
    save_progress(progress)

    console.print()
    if not Confirm.ask("Ready for the next step?", default=True):
        console.print(
            "[yellow]💾 Progress saved. Run 'paracle tutorial resume' to continue.[/yellow]"
        )
        return False

    return True


def step_5_test_agent(progress: dict[str, Any]) -> bool:
    """Step 5: Test agent locally."""
    console.print(
        Panel(
            "[bold green]📍 Step 5/6: Test Your Agent Locally[/bold green]\n\n"
            "Let's test your agent with a simple task.",
            border_style="green",
        )
    )
    console.print()

    # Find agent (skip SCHEMA.md and TEMPLATE.md)
    parac_dir = Path.cwd() / ".parac"
    agents_dir = parac_dir / "agents" / "specs"
    agent_files = [
        f
        for f in agents_dir.glob("*.md")
        if f.stem.upper() not in ("SCHEMA", "TEMPLATE")
    ]

    if not agent_files:
        console.print("[red]No agent found. Please complete step 1 first.[/red]")
        return False

    agent_file = agent_files[0]
    agent_name = agent_file.stem

    console.print(f"[cyan]Testing agent:[/cyan] {agent_name}")
    console.print()

    # Check for API key
    env_file = Path.cwd() / ".env"
    if not env_file.exists():
        console.print(
            "[yellow]⚠️  No .env file found. You'll need an API key to test the agent.[/yellow]"
        )
        console.print("\n[cyan]Supported providers:[/cyan]")
        console.print("  • OpenAI (OPENAI_API_KEY)")
        console.print("  • Anthropic (ANTHROPIC_API_KEY)")
        console.print("  • Google (GOOGLE_API_KEY)")
        console.print()

        if Confirm.ask("Would you like to configure an API key now?", default=True):
            provider = Prompt.ask(
                "Provider", choices=["openai", "anthropic", "google"], default="openai"
            )

            key_name = f"{provider.upper()}_API_KEY"
            api_key = Prompt.ask(f"{key_name} (input hidden)", password=True)

            env_file.write_text(f"{key_name}={api_key}\n")
            console.print("[green]✅ Saved API key to .env[/green]")
            console.print("[yellow]⚠️  Make sure .env is in .gitignore![/yellow]")
        else:
            console.print("[dim]You can add API keys later to .env file[/dim]")
            console.print("[dim]Skipping agent test for now.[/dim]")

            # Update progress
            progress["checkpoints"]["step_5"] = "completed"
            progress["last_step"] = 5
            save_progress(progress)

            console.print()
            if not Confirm.ask("Ready for the next step?", default=True):
                console.print(
                    "[yellow]💾 Progress saved. Run 'paracle tutorial resume' to continue.[/yellow]"
                )
                return False
            return True

    # Generate test prompt
    test_prompt = Prompt.ask(
        "What task would you like to test?", default="Explain what you can do"
    )

    console.print(
        f'\n[dim]Running: paracle agents run {agent_name} --task "{test_prompt}"[/dim]'
    )
    console.print("[dim]This is a dry run - showing what would happen...[/dim]\n")

    # Simulate execution
    console.print("[cyan]🤖 Agent Execution Plan:[/cyan]")
    console.print(f"  1. Load agent: {agent_name}")
    console.print("  2. Initialize LLM provider")
    console.print(f'  3. Send prompt: "{test_prompt}"')
    console.print("  4. Process response")
    console.print("  5. Return result")

    console.print("\n[green]✅ Agent test plan validated![/green]")
    console.print("\n[cyan]💡 To actually run the agent:[/cyan]")
    console.print(f'[dim]  paracle agents run {agent_name} --task "your task"[/dim]')

    # Update progress
    progress["checkpoints"]["step_5"] = "completed"
    progress["last_step"] = 5
    save_progress(progress)

    console.print()
    if not Confirm.ask("Ready for the final step?", default=True):
        console.print(
            "[yellow]💾 Progress saved. Run 'paracle tutorial resume' to continue.[/yellow]"
        )
        return False

    return True


def step_6_workflow(progress: dict[str, Any]) -> bool:
    """Step 6: Create and run workflow."""
    console.print(
        Panel(
            "[bold green]📍 Step 6/6: Create Your First Workflow[/bold green]\n\n"
            "Workflows orchestrate multiple agents to accomplish complex tasks.",
            border_style="green",
        )
    )
    console.print()

    # Create workflow
    workflow_name = Prompt.ask("Workflow name", default="my-workflow")
    workflow_desc = Prompt.ask("Workflow description", default="My first workflow")

    parac_dir = Path.cwd() / ".parac"
    workflows_dir = parac_dir / "workflows"
    workflows_dir.mkdir(exist_ok=True)

    workflow_file = workflows_dir / f"{workflow_name}.yaml"

    # Find agent (skip SCHEMA.md and TEMPLATE.md)
    agents_dir = parac_dir / "agents" / "specs"
    agent_files = [
        f
        for f in agents_dir.glob("*.md")
        if f.stem.upper() not in ("SCHEMA", "TEMPLATE")
    ]
    agent_name = agent_files[0].stem if agent_files else "my-agent"

    workflow_content = f"""name: {workflow_name}
description: {workflow_desc}
version: "1.0.0"

steps:
  - id: step1
    agent: {agent_name}
    task: "{{{{ input.task }}}}"
    inputs:
      task: "{{{{ input.task }}}}"

outputs:
  result: "{{{{ steps.step1.output }}}}"
"""

    workflow_file.write_text(workflow_content)

    console.print(f"\n[green]✅ Created workflow at {workflow_file}[/green]")

    # Show workflow
    console.print("\n[cyan]Workflow structure:[/cyan]")
    console.print(
        Panel(
            f"[bold]name:[/bold] {workflow_name}\n"
            f"[bold]agent:[/bold] {agent_name}\n"
            f"[bold]steps:[/bold] 1 step",
            title="Workflow Configuration",
        )
    )

    console.print("\n[cyan]💡 To run this workflow:[/cyan]")
    console.print(
        f'[dim]  paracle workflow run {workflow_name} --input task="your task"[/dim]'
    )

    # Update progress
    progress["checkpoints"]["step_6"] = "completed"
    progress["last_step"] = 6
    save_progress(progress)

    # Show completion
    console.print()
    completion = Panel(
        "[bold green]🎓 Tutorial Complete![/bold green]\n\n"
        "You've learned how to:\n"
        "  ✅ Create agents\n"
        "  ✅ Add tools\n"
        "  ✅ Add skills\n"
        "  ✅ Create templates\n"
        "  ✅ Test agents\n"
        "  ✅ Build workflows\n\n"
        "[bold cyan]Next Steps:[/bold cyan]\n"
        "  📚 Read docs: content/docs/getting-started.md\n"
        "  🎯 Try examples: content/examples/ directory\n"
        "  💬 Join Discord: (Phase 7 deliverable)\n"
        "  📦 Browse templates: (Phase 7 deliverable)\n\n"
        "[dim]Run 'paracle --help' to see all available commands[/dim]",
        title="🎉 Congratulations!",
        border_style="green",
    )
    console.print(completion)

    return True


@click.group()
def tutorial() -> None:
    """Interactive tutorial for learning Paracle.

    This step-by-step guide will help you:
    - Create your first agent
    - Add tools and skills
    - Create templates
    - Test and run workflows

    Progress is automatically saved, so you can resume anytime.
    """
    pass


@tutorial.command()
@click.option("--step", type=int, help="Start from specific step (1-6)")
def start(step: int | None) -> None:
    """Start the interactive tutorial."""
    progress = load_progress()

    # Determine starting step
    if step:
        start_step = step
    elif progress["last_step"] > 0:
        console.print(
            f"[yellow]You have progress saved at step {progress['last_step']}[/yellow]"
        )
        if Confirm.ask("Resume from where you left off?", default=True):
            start_step = progress["last_step"] + 1
        else:
            start_step = 1
    else:
        start_step = 1

    # Show welcome on first step
    if start_step == 1:
        show_welcome()
        if not Confirm.ask("Ready to start?", default=True):
            console.print(
                "[yellow]Run 'paracle tutorial start' when you're ready![/yellow]"
            )
            return
        console.print()

    # Run steps
    steps = [
        step_1_create_agent,
        step_2_add_tools,
        step_3_add_skills,
        step_4_create_template,
        step_5_test_agent,
        step_6_workflow,
    ]

    for i in range(start_step - 1, len(steps)):
        if not steps[i](progress):
            return
        console.print()

    # Clear progress on completion
    if progress["checkpoints"]["step_6"] == "completed":
        get_progress_file().unlink(missing_ok=True)


@tutorial.command()
def resume() -> None:
    """Resume tutorial from last checkpoint."""
    progress = load_progress()

    if progress["last_step"] == 0:
        console.print("[yellow]No progress found. Starting from beginning...[/yellow]")
        console.print("[dim]Run: paracle tutorial start[/dim]")
        return

    if progress["last_step"] >= 6:
        console.print("[green]✅ Tutorial already completed![/green]")
        console.print("[dim]Run 'paracle tutorial start' to start over[/dim]")
        return

    console.print(f"[cyan]Resuming from step {progress['last_step'] + 1}...[/cyan]\n")

    # Import click context to call start with step
    from click.testing import CliRunner

    runner = CliRunner()
    runner.invoke(start, ["--step", str(progress["last_step"] + 1)])


@tutorial.command()
def status() -> None:
    """Show tutorial progress."""
    progress = load_progress()

    table = Table(title="Tutorial Progress")
    table.add_column("Step", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Description", style="dim")

    steps_info = [
        ("1", "step_1", "Create your first agent"),
        ("2", "step_2", "Add tools to agent"),
        ("3", "step_3", "Add skills for expertise"),
        ("4", "step_4", "Create project templates"),
        ("5", "step_5", "Test agent locally"),
        ("6", "step_6", "Run first workflow"),
    ]

    for step_num, step_key, desc in steps_info:
        status = progress["checkpoints"][step_key]
        if status == "completed":
            status_text = "[green]OK Completed[/green]"
        elif status == "in_progress":
            status_text = "[yellow]>> In Progress[/yellow]"
        else:
            status_text = "[dim]-- Not Started[/dim]"

        table.add_row(step_num, status_text, desc)

    console.print(table)
    console.print()

    if progress["last_step"] == 0:
        console.print("[cyan]Run 'paracle tutorial start' to begin![/cyan]")
    elif progress["last_step"] < 6:
        console.print(
            f"[cyan]Run 'paracle tutorial resume' to continue from step {progress['last_step'] + 1}[/cyan]"
        )
    else:
        console.print("[green]Tutorial completed! Great job![/green]")


@tutorial.command()
def reset() -> None:
    """Reset tutorial progress."""
    if Confirm.ask("Are you sure you want to reset tutorial progress?", default=False):
        get_progress_file().unlink(missing_ok=True)
        console.print("[green]Tutorial progress reset[/green]")
        console.print("[dim]Run 'paracle tutorial start' to begin again[/dim]")
    else:
        console.print("[yellow]Reset cancelled[/yellow]")


# =============================================================================
# DYNAMIC TUTORIAL COMMANDS
# =============================================================================


def _get_cli_introspector():
    """Get CLI introspector with root command."""
    from paracle_cli.main import cli as root_cli
    from paracle_cli.tutorial.introspector import CLIIntrospector

    return CLIIntrospector(root_cli)


@tutorial.command("learn")
@click.argument("command_path", required=False)
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Run in interactive mode with parameter collection",
)
@click.option("--quick", "-q", is_flag=True, help="Show quick reference guide only")
@click.option(
    "--dry-run", is_flag=True, help="Don't execute commands, just show what would run"
)
def learn_command(
    command_path: str | None,
    interactive: bool,
    quick: bool,
    dry_run: bool,
) -> None:
    """Learn how to use any CLI command.

    Automatically generates tutorials for any Paracle command.

    Examples:
        paracle tutorial learn agents          # Learn agents group
        paracle tutorial learn agents/run      # Learn specific command
        paracle tutorial learn workflow -i     # Interactive mode
        paracle tutorial learn config -q       # Quick reference
    """
    from paracle_cli.tutorial.generator import TutorialGenerator
    from paracle_cli.tutorial.runner import InteractiveTutorialRunner

    introspector = _get_cli_introspector()

    # If no command specified, show available commands
    if not command_path:
        _show_available_commands(introspector)
        return

    # Normalize path (support both "agents run" and "agents/run")
    command_path = command_path.replace(" ", "/")

    # Find the command
    command = introspector.get_command(command_path)

    if not command:
        # Try to find partial matches
        matches = introspector.find_command(command_path)
        if matches:
            console.print(f"[yellow]Command '{command_path}' not found.[/yellow]")
            console.print("\n[cyan]Did you mean:[/cyan]")
            for match in matches[:5]:
                console.print(f"  • paracle tutorial learn {match.path}")
            return
        else:
            console.print(f"[red]Command '{command_path}' not found.[/red]")
            console.print(
                "\n[dim]Run 'paracle tutorial learn' to see all commands[/dim]"
            )
            return

    # Generate tutorial
    generator = TutorialGenerator()
    tutorial_content = generator.generate(command)

    # Run in appropriate mode
    runner = InteractiveTutorialRunner(dry_run=dry_run)

    if quick:
        runner.run_quick_guide(command)
    elif interactive:
        runner.run_tutorial(command, tutorial_content)
    else:
        # Default: show generated tutorial content
        _show_tutorial_content(command, tutorial_content, generator)


def _show_available_commands(introspector) -> None:
    """Show all available commands for tutorial."""
    console.print(
        Panel(
            "[bold cyan]Available Commands for Tutorial[/bold cyan]\n\n"
            "Use `paracle tutorial learn <command>` to learn any command.",
            border_style="cyan",
        )
    )
    console.print()

    # Get command tree
    tree = introspector.get_command_tree()

    # Show top-level groups
    table = Table(title="Command Groups")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Subcommands", style="dim")

    for sub in tree.subcommands:
        if sub.hidden:
            continue
        desc = sub.short_help or sub.help_text.split("\n")[0][:50]
        subcmd_count = len(sub.subcommands) if sub.is_group else 0
        subcmd_text = f"{subcmd_count} subcommands" if subcmd_count else "-"
        table.add_row(sub.name, desc, subcmd_text)

    console.print(table)
    console.print()

    # Show usage examples
    console.print("[bold]Usage examples:[/bold]")
    console.print("  paracle tutorial learn agents       # Learn agents group")
    console.print("  paracle tutorial learn agents/run   # Learn specific command")
    console.print("  paracle tutorial learn workflow -i  # Interactive mode")
    console.print("  paracle tutorial learn config -q    # Quick reference")


def _show_tutorial_content(command, tutorial_content, generator) -> None:
    """Show tutorial content in rich format."""

    # Title panel
    console.print(
        Panel(
            f"[bold green]Tutorial: {tutorial_content.title}[/bold green]",
            border_style="green",
        )
    )
    console.print()

    # Overview
    console.print("[bold]Overview[/bold]")
    console.print(tutorial_content.overview)
    console.print()

    # Prerequisites
    if tutorial_content.prerequisites:
        console.print("[bold]Prerequisites[/bold]")
        for prereq in tutorial_content.prerequisites:
            console.print(f"  • {prereq}")
        console.print()

    # Steps
    console.print("[bold]Steps[/bold]")
    for i, step in enumerate(tutorial_content.steps, 1):
        console.print(f"\n[cyan]{i}. {step.title}[/cyan]")
        # Truncate description if too long
        desc = step.description
        if len(desc) > 200:
            desc = desc[:200] + "..."
        console.print(f"   {desc}")
        if step.example:
            example_lines = step.example.split("\n")
            for line in example_lines[:3]:
                console.print(f"   [dim]$ {line}[/dim]")

    console.print()

    # Common patterns
    if tutorial_content.common_patterns:
        console.print("[bold]Common Patterns[/bold]")
        for pattern in tutorial_content.common_patterns:
            console.print(f"  • {pattern}")
        console.print()

    # Related commands
    if tutorial_content.related_commands:
        console.print("[bold]Related Commands[/bold]")
        for cmd in tutorial_content.related_commands:
            console.print(f"  • {cmd}")
        console.print()

    # Footer with more options
    console.print()
    console.print(
        "[dim]For interactive tutorial: paracle tutorial learn "
        + f"{command.path} -i[/dim]"
    )
    console.print(
        "[dim]For quick reference: paracle tutorial learn " + f"{command.path} -q[/dim]"
    )


@tutorial.command("list")
@click.option(
    "--all",
    "-a",
    "show_all",
    is_flag=True,
    help="Show all commands including hidden ones",
)
@click.option("--tree", "-t", is_flag=True, help="Show commands as a tree structure")
def list_commands(show_all: bool, tree: bool) -> None:
    """List all available CLI commands.

    Shows all commands that can be learned with `paracle tutorial learn`.

    Examples:
        paracle tutorial list           # List all command groups
        paracle tutorial list --all     # Include hidden commands
        paracle tutorial list --tree    # Show as tree structure
    """
    introspector = _get_cli_introspector()
    commands = introspector.get_all_commands()

    if tree:
        _show_command_tree(introspector, show_all)
    else:
        _show_command_list(commands, show_all)


def _show_command_list(commands: dict, show_all: bool) -> None:
    """Show commands as a flat list."""
    table = Table(title="All CLI Commands")
    table.add_column("Command", style="cyan")
    table.add_column("Type", style="dim")
    table.add_column("Description", style="white")

    for path in sorted(commands.keys()):
        cmd = commands[path]
        if cmd.hidden and not show_all:
            continue

        cmd_type = "group" if cmd.is_group else "command"
        desc = cmd.short_help or cmd.help_text.split("\n")[0][:50]
        if cmd.hidden:
            desc = f"[dim](hidden) {desc}[/dim]"

        table.add_row(f"paracle {path.replace('/', ' ')}", cmd_type, desc)

    console.print(table)
    console.print()
    console.print(f"[dim]Total: {len(commands)} commands[/dim]")
    console.print(
        "[dim]Use 'paracle tutorial learn <command>' to learn any command[/dim]"
    )


def _show_command_tree(introspector, show_all: bool) -> None:
    """Show commands as a tree structure."""
    from rich.tree import Tree

    root = introspector.get_command_tree()

    tree = Tree("[bold cyan]paracle[/bold cyan]")

    def add_to_tree(parent_tree, command_info, indent=0):
        for sub in command_info.subcommands:
            if sub.hidden and not show_all:
                continue

            label = f"[cyan]{sub.name}[/cyan]"
            if sub.is_group:
                label += " [dim](group)[/dim]"
            if sub.hidden:
                label += " [dim](hidden)[/dim]"

            branch = parent_tree.add(label)

            if sub.is_group:
                add_to_tree(branch, sub, indent + 1)

    add_to_tree(tree, root)
    console.print(tree)
    console.print()
    console.print(
        "[dim]Use 'paracle tutorial learn <command>' to learn any command[/dim]"
    )


@tutorial.command("search")
@click.argument("query")
def search_commands(query: str) -> None:
    """Search for commands by name or description.

    Examples:
        paracle tutorial search agent    # Find commands related to agents
        paracle tutorial search run      # Find run commands
        paracle tutorial search json     # Find commands with json option
    """
    introspector = _get_cli_introspector()
    matches = introspector.find_command(query)

    if not matches:
        console.print(f"[yellow]No commands found matching '{query}'[/yellow]")
        console.print(
            "\n[dim]Try a different search term or use 'paracle tutorial list'[/dim]"
        )
        return

    console.print(f"[cyan]Found {len(matches)} command(s) matching '{query}':[/cyan]")
    console.print()

    table = Table()
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="white")

    for cmd in matches[:15]:  # Limit to 15 results
        desc = cmd.short_help or cmd.help_text.split("\n")[0][:60]
        table.add_row(f"paracle {cmd.path.replace('/', ' ')}", desc)

    console.print(table)

    if len(matches) > 15:
        console.print(f"\n[dim]... and {len(matches) - 15} more[/dim]")

    console.print(
        "\n[dim]Use 'paracle tutorial learn <command>' to learn a command[/dim]"
    )
