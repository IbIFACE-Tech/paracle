"""Example: Agent using built-in tools together.

This example demonstrates how to create an agent that uses multiple
built-in tools to accomplish complex tasks.

Scenario: A code analysis agent that:
1. Lists files in a directory
2. Reads source files
3. Runs tests
4. Fetches documentation from APIs
5. Generates a report

Run: uv run python examples/04_agent_with_tools.py
"""

import asyncio
from pathlib import Path

from paracle_tools import http_get, list_directory, read_file, run_command, write_file


class CodeAnalysisAgent:
    """An agent that analyzes code using built-in tools."""

    def __init__(self, project_path: str):
        """Initialize agent with project path.

        Args:
            project_path: Path to the project to analyze.
        """
        self.project_path = Path(project_path)
        self.analysis_results = {
            "files": [],
            "test_results": None,
            "file_contents": {},
            "external_data": {},
        }

    async def analyze_project(self) -> dict:
        """Run full project analysis.

        Returns:
            Analysis results dictionary.
        """
        print("🔍 Starting code analysis...")

        # Step 1: Discover files
        await self._discover_files()

        # Step 2: Read and analyze source files
        await self._analyze_source_files()

        # Step 3: Run tests
        await self._run_tests()

        # Step 4: Fetch external documentation
        await self._fetch_external_docs()

        # Step 5: Generate report
        await self._generate_report()

        print("\n✅ Analysis complete!")
        return self.analysis_results

    async def _discover_files(self):
        """Discover all Python files in the project."""
        print("\n📁 Step 1: Discovering files...")

        result = await list_directory.execute(
            path=str(self.project_path), recursive=True
        )

        if result.success:
            python_files = [
                entry
                for entry in result.output["entries"]
                if entry["type"] == "file" and entry["name"].endswith(".py")
            ]
            self.analysis_results["files"] = python_files
            print(f"   Found {len(python_files)} Python files")
        else:
            print(f"   ❌ Error: {result.error}")

    async def _analyze_source_files(self):
        """Read and analyze source files."""
        print("\n📖 Step 2: Reading source files...")

        # Read first 3 files as examples
        files_to_read = self.analysis_results["files"][:3]

        for file_entry in files_to_read:
            file_path = self.project_path / file_entry["name"]

            result = await read_file.execute(path=str(file_path))

            if result.success:
                self.analysis_results["file_contents"][file_entry["name"]] = {
                    "lines": result.output["lines"],
                    "size": result.output["size"],
                    "content_preview": result.output["content"][:200] + "...",
                }
                print(f"   ✓ {file_entry['name']}: {result.output['lines']} lines")
            else:
                print(f"   ❌ {file_entry['name']}: {result.error}")

    async def _run_tests(self):
        """Run project tests."""
        print("\n🧪 Step 3: Running tests...")

        # Run pytest on built-in tools tests
        result = await run_command.execute(
            command="pytest tests/unit/test_builtin_tools_filesystem.py -v --tb=short -q"
        )

        if result.success:
            self.analysis_results["test_results"] = {
                "return_code": result.output["return_code"],
                "passed": result.output["success"],
                "output": result.output["stdout"],
            }

            if result.output["success"]:
                print("   ✅ Tests passed")
            else:
                print(f"   ⚠️ Tests failed (exit code: {result.output['return_code']})")

            # Show summary
            output_lines = result.output["stdout"].strip().split("\n")
            for line in output_lines[-3:]:
                if line.strip():
                    print(f"      {line}")
        else:
            print(f"   ❌ Error running tests: {result.error}")

    async def _fetch_external_docs(self):
        """Fetch documentation from external APIs."""
        print("\n🌐 Step 4: Fetching external documentation...")

        # Fetch Python package info from PyPI
        result = await http_get.execute(url="https://pypi.org/pypi/pydantic/json")

        if result.success and result.output["json"]:
            package_info = result.output["json"]["info"]
            self.analysis_results["external_data"]["pydantic"] = {
                "name": package_info["name"],
                "version": package_info["version"],
                "summary": package_info["summary"],
            }
            print(f"   ✓ Pydantic: v{package_info['version']}")
            print(f"      {package_info['summary']}")

        # Fetch another package
        result = await http_get.execute(url="https://pypi.org/pypi/fastapi/json")

        if result.success and result.output["json"]:
            package_info = result.output["json"]["info"]
            self.analysis_results["external_data"]["fastapi"] = {
                "name": package_info["name"],
                "version": package_info["version"],
                "summary": package_info["summary"],
            }
            print(f"   ✓ FastAPI: v{package_info['version']}")

    async def _generate_report(self):
        """Generate analysis report."""
        print("\n📝 Step 5: Generating report...")

        report_lines = [
            "=" * 70,
            "CODE ANALYSIS REPORT",
            "=" * 70,
            "",
            f"Project: {self.project_path}",
            "",
            "## FILES",
            f"Total Python files: {len(self.analysis_results['files'])}",
            "",
        ]

        # Add file details
        report_lines.append("Analyzed files:")
        for name, details in self.analysis_results["file_contents"].items():
            report_lines.append(f"  - {name}")
            report_lines.append(
                f"    Lines: {details['lines']}, Size: {details['size']} bytes"
            )

        # Add test results
        if self.analysis_results["test_results"]:
            report_lines.append("")
            report_lines.append("## TESTS")
            test_status = (
                "PASSED"
                if self.analysis_results["test_results"]["passed"]
                else "FAILED"
            )
            report_lines.append(f"Status: {test_status}")

        # Add external data
        if self.analysis_results["external_data"]:
            report_lines.append("")
            report_lines.append("## DEPENDENCIES")
            for pkg_name, pkg_info in self.analysis_results["external_data"].items():
                report_lines.append(f"  - {pkg_info['name']} v{pkg_info['version']}")
                report_lines.append(f"    {pkg_info['summary']}")

        report_lines.append("")
        report_lines.append("=" * 70)

        report_content = "\n".join(report_lines)

        # Write report to file
        report_path = self.project_path / "analysis_report.txt"
        result = await write_file.execute(path=str(report_path), content=report_content)

        if result.success:
            print(f"   ✅ Report written to: {result.output['path']}")
            print("\n" + report_content)
        else:
            print(f"   ❌ Error writing report: {result.error}")


async def main():
    """Run the code analysis agent example."""
    print("=" * 70)
    print("AGENT WITH BUILT-IN TOOLS EXAMPLE")
    print("=" * 70)
    print("\nThis example demonstrates an agent using multiple tools:")
    print("- list_directory: Discover files")
    print("- read_file: Read source code")
    print("- run_command: Execute tests")
    print("- http_get: Fetch external data")
    print("- write_file: Generate report")

    # Create agent for the tests directory
    agent = CodeAnalysisAgent(project_path="tests/unit")

    # Run analysis
    results = await agent.analyze_project()

    # Show summary
    print("\n" + "=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)
    print(f"Files analyzed: {len(results['file_contents'])}")
    print(f"Tests run: {'Yes' if results['test_results'] else 'No'}")
    print(f"External data fetched: {len(results['external_data'])} sources")
    print("=" * 70)


async def registry_example():
    """Demonstrate using BuiltinToolRegistry for tool management."""
    print("\n" + "=" * 70)
    print("BONUS: Using BuiltinToolRegistry")
    print("=" * 70)

    from paracle_tools import BuiltinToolRegistry

    # Create registry with configuration
    registry = BuiltinToolRegistry(
        filesystem_paths=[".", "./tests", "./packages"],
        allowed_commands=["git", "pytest", "python", "ls", "dir"],
        http_timeout=10.0,
        command_timeout=30.0,
    )

    # List available tools
    print("\n📦 Available tools:")
    tools_by_category = registry.get_tools_by_category()
    for category, tool_names in tools_by_category.items():
        print(f"\n  {category}:")
        for name in tool_names:
            tool = registry.get_tool(name)
            print(f"    - {name}: {tool.description}")

    # Execute tools through registry
    print("\n🔧 Executing tools through registry:")

    # Filesystem tool
    result = await registry.execute_tool("list_directory", path="examples")
    if result.success:
        print(f"\n  ✓ list_directory: found {result.output['count']} items")

    # Shell tool
    result = await registry.execute_tool("run_command", command="git log -1 --oneline")
    if result.success:
        print(f"  ✓ run_command: {result.output['stdout'].strip()}")

    # HTTP tool
    result = await registry.execute_tool(
        "http_get", url="https://api.github.com/repos/python/cpython"
    )
    if result.success and result.output["json"]:
        repo = result.output["json"]
        print(f"  ✓ http_get: {repo['full_name']} ({repo['stargazers_count']:,} stars)")


if __name__ == "__main__":
    # Run main example
    asyncio.run(main())

    # Run registry example
    asyncio.run(registry_example())
