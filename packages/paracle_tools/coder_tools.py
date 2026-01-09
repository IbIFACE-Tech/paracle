"""Development tools for Coder agent."""

import logging
import subprocess
from pathlib import Path
from typing import Any

from paracle_tools.builtin.base import BaseTool

logger = logging.getLogger("paracle.tools.coder")


class CodeGenerationTool(BaseTool):
    """Generate code from templates or specifications.

    Supports:
    - Python class/function generation
    - Test boilerplate generation
    - Configuration file generation
    """

    def __init__(self):
        super().__init__(
            name="code_generation",
            description="Generate code from templates or specifications",
            parameters={
                "type": "object",
                "properties": {
                    "template_type": {
                        "type": "string",
                        "description": "Type of code to generate",
                        "enum": ["class", "function", "test", "config"],
                    },
                    "name": {
                        "type": "string",
                        "description": "Name of the class/function to generate",
                    },
                    "base": {
                        "type": "string",
                        "description": "Base class name (for class template)",
                    },
                    "methods": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of method names (for class template)",
                    },
                    "params": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Function parameters (for function template)",
                    },
                    "return_type": {
                        "type": "string",
                        "description": "Return type annotation (for function template)",
                    },
                    "target": {
                        "type": "string",
                        "description": "Target module to test (for test template)",
                    },
                    "format": {
                        "type": "string",
                        "description": "Config format (for config template)",
                        "enum": ["yaml", "toml", "json"],
                    },
                },
                "required": ["template_type"],
            },
        )

    async def _execute(self, template_type: str, **kwargs) -> dict[str, Any]:
        """Generate code based on template type.

        Args:
            template_type: Type of code to generate (class, function, test, config)
            **kwargs: Template parameters

        Returns:
            Generated code
        """
        if template_type == "class":
            return self._generate_class(**kwargs)
        elif template_type == "function":
            return self._generate_function(**kwargs)
        elif template_type == "test":
            return self._generate_test(**kwargs)
        elif template_type == "config":
            return self._generate_config(**kwargs)
        else:
            return {"error": f"Unsupported template type: {template_type}"}

    def _generate_class(
        self, name: str, base: str = None, methods: list = None, **kwargs
    ) -> dict[str, Any]:
        """Generate a Python class."""
        base_str = f"({base})" if base else ""
        methods_str = methods or ["__init__"]

        code = f'''"""Generated class."""


class {name}{base_str}:
    """TODO: Add docstring."""

'''

        for method in methods_str:
            if method == "__init__":
                code += '''    def __init__(self):
        """Initialize instance."""
        pass

'''
            else:
                code += f'''    def {method}(self):
        """TODO: Add docstring."""
        pass

'''

        return {"code": code, "type": "class", "name": name}

    def _generate_function(
        self, name: str, params: list = None, return_type: str = None, **kwargs
    ) -> dict[str, Any]:
        """Generate a Python function."""
        params_str = ", ".join(params or [""])
        return_annotation = f" -> {return_type}" if return_type else ""

        code = f'''def {name}({params_str}){return_annotation}:
    """TODO: Add docstring.

    Args:
        {chr(10).join(f"{p}: TODO" for p in (params or []))}

    Returns:
        TODO
    """
    pass
'''

        return {"code": code, "type": "function", "name": name}

    def _generate_test(self, target: str, **kwargs) -> dict[str, Any]:
        """Generate test boilerplate."""
        code = f'''"""Tests for {target}."""

import pytest

from {target} import TODO


class Test{target.title().replace("_", "")}:
    """Test suite for {target}."""

    def test_basic(self):
        """Test basic functionality."""
        # Arrange

        # Act

        # Assert
        pass

    def test_edge_case(self):
        """Test edge cases."""
        pass

    def test_error_handling(self):
        """Test error handling."""
        with pytest.raises(Exception):
            pass
'''

        return {"code": code, "type": "test", "target": target}

    def _generate_config(self, format: str, **kwargs) -> dict[str, Any]:
        """Generate configuration file."""
        if format == "yaml":
            code = """# Configuration
version: "1.0"

settings:
  debug: false
  timeout: 30
"""
        elif format == "toml":
            code = """[settings]
debug = false
timeout = 30
"""
        elif format == "json":
            code = """{
  "settings": {
    "debug": false,
    "timeout": 30
  }
}
"""
        else:
            return {"error": f"Unsupported config format: {format}"}

        return {"code": code, "type": "config", "format": format}


class RefactoringTool(BaseTool):
    """Refactor code for better quality and maintainability.

    Operations:
    - Extract method
    - Rename symbol
    - Move code
    - Simplify conditionals
    """

    def __init__(self):
        super().__init__(
            name="refactoring",
            description="Refactor code with extract method, rename, and formatting",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "Refactoring operation to perform",
                        "enum": ["extract_method", "rename", "format"],
                    },
                    "path": {
                        "type": "string",
                        "description": "File path to refactor",
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Start line for extract_method operation",
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "End line for extract_method operation",
                    },
                    "old_name": {
                        "type": "string",
                        "description": "Current symbol name for rename operation",
                    },
                    "new_name": {
                        "type": "string",
                        "description": "New name for extract_method or rename operation",
                    },
                },
                "required": ["operation", "path"],
            },
        )

    async def _execute(self, operation: str, path: str, **kwargs) -> dict[str, Any]:
        """Perform refactoring operation.

        Args:
            operation: Refactoring operation (extract_method, rename, move, simplify)
            path: File path to refactor
            **kwargs: Operation-specific parameters

        Returns:
            Refactoring results
        """
        file_path = Path(path)

        if not file_path.exists():
            return {"error": f"File not found: {path}"}

        if operation == "extract_method":
            return await self._extract_method(file_path, **kwargs)
        elif operation == "rename":
            return await self._rename_symbol(file_path, **kwargs)
        elif operation == "format":
            return await self._format_code(file_path)
        else:
            return {"error": f"Unsupported operation: {operation}"}

    async def _extract_method(
        self, file_path: Path, start_line: int, end_line: int, new_name: str, **kwargs
    ) -> dict[str, Any]:
        """Extract lines into a new method."""
        return {
            "operation": "extract_method",
            "file": str(file_path),
            "new_method": new_name,
            "lines_extracted": f"{start_line}-{end_line}",
            "status": "simulated",
            "message": "Extract method operation would be performed",
        }

    async def _rename_symbol(
        self, file_path: Path, old_name: str, new_name: str, **kwargs
    ) -> dict[str, Any]:
        """Rename a symbol throughout the file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            occurrences = content.count(old_name)
            # Note: In a real implementation, we would write the new content
            _ = content.replace(old_name, new_name)  # Simulated only

            return {
                "operation": "rename",
                "file": str(file_path),
                "old_name": old_name,
                "new_name": new_name,
                "occurrences": occurrences,
                "status": "simulated",
            }
        except Exception as e:
            return {"error": str(e)}

    async def _format_code(self, file_path: Path) -> dict[str, Any]:
        """Format code with black."""
        try:
            result = subprocess.run(
                ["black", "--check", str(file_path)],
                capture_output=True,
                text=True,
            )

            needs_formatting = result.returncode != 0

            return {
                "operation": "format",
                "file": str(file_path),
                "needs_formatting": needs_formatting,
                "status": "checked",
            }
        except FileNotFoundError:
            return {"error": "black not installed"}
        except Exception as e:
            return {"error": str(e)}


class TestingTool(BaseTool):
    """Run tests and collect results.

    Supports:
    - pytest execution
    - Coverage analysis
    - Test result parsing
    """

    def __init__(self):
        super().__init__(
            name="testing",
            description="Run pytest tests and analyze coverage",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Test action to perform",
                        "enum": ["run", "coverage", "check"],
                    },
                    "path": {
                        "type": "string",
                        "description": "Path to test file or directory (optional)",
                    },
                },
                "required": ["action"],
            },
        )

    async def _execute(self, action: str, path: str = None, **kwargs) -> dict[str, Any]:
        """Execute testing action.

        Args:
            action: Test action (run, coverage, check)
            path: Optional path to test file/directory
            **kwargs: Additional test parameters

        Returns:
            Test results
        """
        if action == "run":
            return await self._run_tests(path, **kwargs)
        elif action == "coverage":
            return await self._run_coverage(path, **kwargs)
        elif action == "check":
            return await self._check_tests_exist(path)
        else:
            return {"error": f"Unsupported action: {action}"}

    async def _run_tests(self, path: str = None, **kwargs) -> dict[str, Any]:
        """Run pytest."""
        cmd = ["pytest"]
        if path:
            cmd.append(path)
        cmd.extend(["-v", "--tb=short"])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            return {
                "action": "run_tests",
                "path": path or "all tests",
                "return_code": result.returncode,
                "output": result.stdout,
                "errors": result.stderr,
                "passed": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {"error": "Tests timed out after 5 minutes"}
        except FileNotFoundError:
            return {"error": "pytest not installed"}
        except Exception as e:
            return {"error": str(e)}

    async def _run_coverage(self, path: str = None, **kwargs) -> dict[str, Any]:
        """Run tests with coverage."""
        cmd = ["pytest", "--cov=packages"]
        if path:
            cmd.append(path)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            return {
                "action": "coverage",
                "path": path or "all tests",
                "return_code": result.returncode,
                "output": result.stdout,
                "errors": result.stderr,
            }
        except FileNotFoundError:
            return {"error": "pytest or pytest-cov not installed"}
        except Exception as e:
            return {"error": str(e)}

    async def _check_tests_exist(self, path: str) -> dict[str, Any]:
        """Check if tests exist for path."""
        target_path = Path(path)

        if not target_path.exists():
            return {"error": f"Path not found: {path}"}

        if target_path.is_file():
            # Look for corresponding test file
            test_file = target_path.parent / f"test_{target_path.name}"
            tests_dir = Path("tests")
            alt_test_file = (
                tests_dir / target_path.parent.name / f"test_{target_path.name}"
            )

            return {
                "action": "check_tests",
                "file": str(target_path),
                "test_file_exists": test_file.exists() or alt_test_file.exists(),
                "test_file": (
                    str(test_file) if test_file.exists() else str(alt_test_file)
                ),
            }

        return {"error": "Path must be a file"}


# Tool instances
code_generation = CodeGenerationTool()
refactoring = RefactoringTool()
testing = TestingTool()

__all__ = [
    "CodeGenerationTool",
    "RefactoringTool",
    "TestingTool",
    "code_generation",
    "refactoring",
    "testing",
]
