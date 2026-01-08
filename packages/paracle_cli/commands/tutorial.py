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
        "[dim]You can exit anytime and resume with 'paracle tutorial resume'[/dim]",
        title="Welcome",
        border_style="cyan",
    )
    console.print(welcome)
    console.print()


def step_1_create_agent(progress: dict[str, Any]) -> bool:
    """Step 1: Create your first agent."""
    console.print(Panel(
        "[bold green]Step 1/6: Create Your First Agent[/bold green]\n\n"
        "Let's create an AI agent that can help you with tasks.",
        border_style="green"
    ))
    console.print()

    # Check if .parac exists
    parac_dir = Path.cwd() / ".parac"
    if not parac_dir.exists():
        console.print(
            "[yellow]Warning: No .parac/ directory found. Let's initialize one![/yellow]")
        if Confirm.ask("Initialize project with lite mode?", default=True):
            console.print("[dim]Running: paracle init --template lite[/dim]")
            import subprocess
            result = subprocess.run(
                ["paracle", "init", "--template", "lite"],
                cwd=Path.cwd(),
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                console.print(f"[red]❌ Error: {result.stderr}[/red]")
                return False
            console.print("[green]✅ Project initialized![/green]\n")

    # Create agent
    agent_name = Prompt.ask(
        "What would you like to name your agent?",
        default="my-assistant"
    )

    description = Prompt.ask(
        "What will this agent do? (brief description)",
        default="Help me with various tasks"
    )

    # Create agent spec directory
    agents_dir = parac_dir / "agents" / "specs"
    agents_dir.mkdir(parents=True, exist_ok=True)

    # Create agent spec file
    agent_file = agents_dir / f"{agent_name}.md"
    agent_content = f"""---
name: {agent_name}
description: {description}
model: gpt-4
temperature: 0.7
max_tokens: 2000
---

# {agent_name.replace('-', ' ').title()}

{description}

## Capabilities

- Understand natural language instructions
- Execute tasks step-by-step
- Provide clear explanations

## Usage

```bash
paracle agents run {agent_name} --task "Your task here"
```
"""

    agent_file.write_text(agent_content)

    console.print(f"\n[green]✅ Created agent spec at {agent_file}[/green]")
    console.print("\n[cyan]Let's review what was created:[/cyan]")
    console.print(Panel(
        f"[bold]name:[/bold] {agent_name}\n"
        f"[bold]description:[/bold] {description}\n"
        f"[bold]model:[/bold] gpt-4",
        title="Agent Configuration"
    ))

    # Update progress
    progress["checkpoints"]["step_1"] = "completed"
    progress["last_step"] = 1
    save_progress(progress)

    console.print()
    if not Confirm.ask("Ready for the next step?", default=True):
        console.print(
            "[yellow]💾 Progress saved. Run 'paracle tutorial resume' to continue.[/yellow]")
        return False

    return True


def step_2_add_tools(progress: dict[str, Any]) -> bool:
    """Step 2: Add tools to agent."""
    console.print(Panel(
        "[bold green]Step 2/6: Add Tools to Your Agent[/bold green]\n\n"
        "Tools give your agent capabilities like reading files, making HTTP requests, or running shell commands.",
        border_style="green"
    ))
    console.print()

    # Show available tools
    table = Table(title="Available Built-in Tools")
    table.add_column("Tool", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Use Case", style="dim")

    tools_info = [
        ("filesystem", "Read/write files and directories",
         "File operations, data processing"),
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
    selected = Prompt.ask(
        "Tools",
        default="filesystem,http"
    )

    tools = [t.strip() for t in selected.split(",")]

    # Find agent file
    parac_dir = Path.cwd() / ".parac"
    agents_dir = parac_dir / "agents" / "specs"
    agent_files = list(agents_dir.glob("*.md"))

    if not agent_files:
        console.print(
            "[red]❌ No agent found. Please complete step 1 first.[/red]")
        return False

    agent_file = agent_files[0]  # Use first agent

    # Read existing content
    content = agent_file.read_text()

    # Add tools section
    tools_section = "\n\n## Tools\n\n"
    for tool in tools:
        tools_section += f"- `{tool}`: Enabled\n"

    tools_section += "\n### Tool Configuration\n\n```yaml\ntools:\n"
    for tool in tools:
        tools_section += f"  - type: {tool}\n"
        tools_section += "    enabled: true\n"
    tools_section += "```\n"

    # Insert before Usage section or append
    if "## Usage" in content:
        content = content.replace("## Usage", tools_section + "\n## Usage")
    else:
        content += tools_section

    agent_file.write_text(content)

    console.print(
        f"\n[green]✅ Added {len(tools)} tools to your agent![/green]")
    console.print(f"\n[cyan]Tools added:[/cyan] {', '.join(tools)}")

    # Explain permissions
    console.print("\n[yellow]Warning: Tool Permissions:[/yellow]")
    console.print("  • Tools run with your user permissions")
    console.print("  • Always review tool actions before approval")
    console.print("  • Use [bold]--mode safe[/bold] for manual approval gates")

    # Update progress
    progress["checkpoints"]["step_2"] = "completed"
    progress["last_step"] = 2
    save_progress(progress)

    console.print()
    if not Confirm.ask("Ready for the next step?", default=True):
        console.print(
            "[yellow]💾 Progress saved. Run 'paracle tutorial resume' to continue.[/yellow]")
        return False

    return True


def step_3_add_skills(progress: dict[str, Any]) -> bool:
    """Step 3: Add skills for specialized capabilities."""
    console.print(Panel(
        "[bold green]Step 3/6: Add Skills to Your Agent[/bold green]\n\n"
        "Skills are reusable knowledge modules that give your agent specialized expertise.",
        border_style="green"
    ))
    console.print()

    # Show available skills
    console.print("[cyan]Checking available skills...[/cyan]")

    parac_dir = Path.cwd() / ".parac"
    skills_dir = parac_dir / "agents" / "skills"

    if not skills_dir.exists():
        console.print(
            "[yellow]⚠️  No skills directory found. Let's check built-in skills.[/yellow]\n")

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
            skill_desc = Prompt.ask(
                "Skill description", default="Custom expertise")

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

            # Assign skill to agent
            agents_dir = parac_dir / "agents" / "specs"
            agent_files = list(agents_dir.glob("*.md"))

            if agent_files:
                agent_file = agent_files[0]
                content = agent_file.read_text()

                # Add skills section
                skills_section = f"\n\n## Skills\n\n- `{skill_name}`: {skill_desc}\n"

                if "## Tools" in content:
                    content = content.replace(
                        "## Tools", skills_section + "\n## Tools")
                else:
                    content += skills_section

                agent_file.write_text(content)
                console.print("[green]✅ Assigned skill to your agent![/green]")
    else:
        # List existing skills
        existing_skills = [d.name for d in skills_dir.iterdir() if d.is_dir()]
        if existing_skills:
            console.print(
                f"[green]Found {len(existing_skills)} skills:[/green]")
            for skill in existing_skills:
                console.print(f"  • {skill}")
        else:
            console.print(
                "[yellow]No skills found. Create one using the prompts above.[/yellow]")

    console.print(
        "\n[cyan]💡 Tip:[/cyan] Skills can be shared across agents and provide specialized knowledge!")

    # Update progress
    progress["checkpoints"]["step_3"] = "completed"
    progress["last_step"] = 3
    save_progress(progress)

    console.print()
    if not Confirm.ask("Ready for the next step?", default=True):
        console.print(
            "[yellow]💾 Progress saved. Run 'paracle tutorial resume' to continue.[/yellow]")
        return False

    return True


def step_4_create_template(progress: dict[str, Any]) -> bool:
    """Step 4: Create project templates."""
    console.print(Panel(
        "[bold green]📍 Step 4/6: Create Project Templates[/bold green]\n\n"
        "Templates are reusable project configurations that you can share with your team.",
        border_style="green"
    ))
    console.print()

    console.print("[cyan]Template types:[/cyan]")
    console.print(
        "  • [bold]lite[/bold]: Minimal setup (5 files) - Quick prototyping")
    console.print(
        "  • [bold]standard[/bold]: Full setup (30+ files) - Production ready")
    console.print("  • [bold]custom[/bold]: Your own template")
    console.print()

    if Confirm.ask("Would you like to create a custom template?", default=False):
        template_name = Prompt.ask("Template name", default="my-template")
        template_desc = Prompt.ask(
            "Template description", default="Custom project template")

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
        console.print(
            f"\n[cyan]Usage:[/cyan] paracle init --template {template_name}")
    else:
        console.print("\n[dim]You can create templates later using:[/dim]")
        console.print("[dim]  paracle init --template custom[/dim]")

    console.print(
        "\n[cyan]💡 Tip:[/cyan] Templates are great for standardizing projects across your team!")

    # Update progress
    progress["checkpoints"]["step_4"] = "completed"
    progress["last_step"] = 4
    save_progress(progress)

    console.print()
    if not Confirm.ask("Ready for the next step?", default=True):
        console.print(
            "[yellow]💾 Progress saved. Run 'paracle tutorial resume' to continue.[/yellow]")
        return False

    return True


def step_5_test_agent(progress: dict[str, Any]) -> bool:
    """Step 5: Test agent locally."""
    console.print(Panel(
        "[bold green]📍 Step 5/6: Test Your Agent Locally[/bold green]\n\n"
        "Let's test your agent with a simple task.",
        border_style="green"
    ))
    console.print()

    # Find agent
    parac_dir = Path.cwd() / ".parac"
    agents_dir = parac_dir / "agents" / "specs"
    agent_files = list(agents_dir.glob("*.md"))

    if not agent_files:
        console.print(
            "[red]❌ No agent found. Please complete step 1 first.[/red]")
        return False

    agent_file = agent_files[0]
    agent_name = agent_file.stem

    console.print(f"[cyan]Testing agent:[/cyan] {agent_name}")
    console.print()

    # Check for API key
    env_file = Path.cwd() / ".env"
    if not env_file.exists():
        console.print(
            "[yellow]⚠️  No .env file found. You'll need an API key to test the agent.[/yellow]")
        console.print("\n[cyan]Supported providers:[/cyan]")
        console.print("  • OpenAI (OPENAI_API_KEY)")
        console.print("  • Anthropic (ANTHROPIC_API_KEY)")
        console.print("  • Google (GOOGLE_API_KEY)")
        console.print()

        if Confirm.ask("Would you like to configure an API key now?", default=True):
            provider = Prompt.ask(
                "Provider",
                choices=["openai", "anthropic", "google"],
                default="openai"
            )

            key_name = f"{provider.upper()}_API_KEY"
            api_key = Prompt.ask(f"{key_name} (input hidden)", password=True)

            env_file.write_text(f"{key_name}={api_key}\n")
            console.print("[green]✅ Saved API key to .env[/green]")
            console.print(
                "[yellow]⚠️  Make sure .env is in .gitignore![/yellow]")
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
                    "[yellow]💾 Progress saved. Run 'paracle tutorial resume' to continue.[/yellow]")
                return False
            return True

    # Generate test prompt
    test_prompt = Prompt.ask(
        "What task would you like to test?",
        default="Explain what you can do"
    )

    console.print(
        f"\n[dim]Running: paracle agents run {agent_name} --task \"{test_prompt}\"[/dim]")
    console.print(
        "[dim]This is a dry run - showing what would happen...[/dim]\n")

    # Simulate execution
    console.print("[cyan]🤖 Agent Execution Plan:[/cyan]")
    console.print(f"  1. Load agent: {agent_name}")
    console.print("  2. Initialize LLM provider")
    console.print(f"  3. Send prompt: \"{test_prompt}\"")
    console.print("  4. Process response")
    console.print("  5. Return result")

    console.print("\n[green]✅ Agent test plan validated![/green]")
    console.print("\n[cyan]💡 To actually run the agent:[/cyan]")
    console.print(
        f"[dim]  paracle agents run {agent_name} --task \"your task\"[/dim]")

    # Update progress
    progress["checkpoints"]["step_5"] = "completed"
    progress["last_step"] = 5
    save_progress(progress)

    console.print()
    if not Confirm.ask("Ready for the final step?", default=True):
        console.print(
            "[yellow]💾 Progress saved. Run 'paracle tutorial resume' to continue.[/yellow]")
        return False

    return True


def step_6_workflow(progress: dict[str, Any]) -> bool:
    """Step 6: Create and run workflow."""
    console.print(Panel(
        "[bold green]📍 Step 6/6: Create Your First Workflow[/bold green]\n\n"
        "Workflows orchestrate multiple agents to accomplish complex tasks.",
        border_style="green"
    ))
    console.print()

    # Create workflow
    workflow_name = Prompt.ask("Workflow name", default="my-workflow")
    workflow_desc = Prompt.ask(
        "Workflow description", default="My first workflow")

    parac_dir = Path.cwd() / ".parac"
    workflows_dir = parac_dir / "workflows"
    workflows_dir.mkdir(exist_ok=True)

    workflow_file = workflows_dir / f"{workflow_name}.yaml"

    # Find agent
    agents_dir = parac_dir / "agents" / "specs"
    agent_files = list(agents_dir.glob("*.md"))
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
    console.print(Panel(
        f"[bold]name:[/bold] {workflow_name}\n"
        f"[bold]agent:[/bold] {agent_name}\n"
        f"[bold]steps:[/bold] 1 step",
        title="Workflow Configuration"
    ))

    console.print("\n[cyan]💡 To run this workflow:[/cyan]")
    console.print(
        f"[dim]  paracle workflow run {workflow_name} --input task=\"your task\"[/dim]")

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
        "  📚 Read docs: docs/getting-started.md\n"
        "  🎯 Try examples: examples/ directory\n"
        "  💬 Join Discord: (Phase 7 deliverable)\n"
        "  📦 Browse templates: (Phase 7 deliverable)\n\n"
        "[dim]Run 'paracle --help' to see all available commands[/dim]",
        title="🎉 Congratulations!",
        border_style="green"
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
            f"[yellow]You have progress saved at step {progress['last_step']}[/yellow]")
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
                "[yellow]Run 'paracle tutorial start' when you're ready![/yellow]")
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
        console.print(
            "[yellow]No progress found. Starting from beginning...[/yellow]")
        console.print("[dim]Run: paracle tutorial start[/dim]")
        return

    if progress["last_step"] >= 6:
        console.print("[green]✅ Tutorial already completed![/green]")
        console.print("[dim]Run 'paracle tutorial start' to start over[/dim]")
        return

    console.print(
        f"[cyan]Resuming from step {progress['last_step'] + 1}...[/cyan]\n")

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
            f"[cyan]Run 'paracle tutorial resume' to continue from step {progress['last_step'] + 1}[/cyan]")
    else:
        console.print("[green]Tutorial completed! Great job![/green]")


@tutorial.command()
def reset() -> None:
    """Reset tutorial progress."""
    if Confirm.ask("Are you sure you want to reset tutorial progress?", default=False):
        get_progress_file().unlink(missing_ok=True)
        console.print("[green]✅ Tutorial progress reset[/green]")
        console.print("[dim]Run 'paracle tutorial start' to begin again[/dim]")
    else:
        console.print("[yellow]Reset cancelled[/yellow]")
