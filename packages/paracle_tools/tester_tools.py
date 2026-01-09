"""Testing tools for Tester agent."""

from paracle_tools.builtin.base import BaseTool
import logging
import subprocess
from typing import Any

logger = logging.getLogger("paracle.tools.tester")

try:
    # SECURITY: Use defusedxml to prevent XML external entity attacks
    import defusedxml.ElementTree as ET  # type: ignore

    _using_defusedxml = True
except ImportError:
    # Fallback to standard library with debug log only
    import xml.etree.ElementTree as ET

    _using_defusedxml = False
    # Log at debug level - only visible when debugging is enabled
    logger.debug(
        "defusedxml not installed. Using xml.etree.ElementTree. "
        "Install defusedxml for production: pip install defusedxml"
    )


class TestGenerationTool(BaseTool):
    """Generate test cases from code or specifications.

    Generates:
    - Unit test scaffolds
    - Integration test templates
    - Property-based tests
    - Parameterized tests
    """

    def __init__(self):
        super().__init__(
            name="test_generation",
            description="Generate test cases for code",
            parameters={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Module, function, or class to generate tests for",
                    },
                    "test_type": {
                        "type": "string",
                        "description": "Type of test to generate",
                        "enum": ["unit", "integration", "property", "parametrized"],
                        "default": "unit",
                    },
                    "class_name": {
                        "type": "string",
                        "description": "Custom class name for the test class",
                    },
                },
                "required": ["target"],
            },
        )

    async def _execute(
        self, target: str, test_type: str = "unit", **kwargs
    ) -> dict[str, Any]:
        """Generate tests for target.

        Args:
            target: Module/function/class to test
            test_type: Type of test (unit, integration, property, parametrized)

        Returns:
            Generated test code
        """
        if test_type == "unit":
            return self._generate_unit_test(target, **kwargs)
        elif test_type == "integration":
            return self._generate_integration_test(target, **kwargs)
        elif test_type == "property":
            return self._generate_property_test(target, **kwargs)
        elif test_type == "parametrized":
            return self._generate_parametrized_test(target, **kwargs)
        else:
            return {"error": f"Unsupported test type: {test_type}"}

    def _generate_unit_test(self, target: str, **kwargs) -> dict[str, Any]:
        """Generate unit test scaffold."""
        class_name = kwargs.get(
            "class_name", "".join(x.title() for x in target.split("_"))
        )

        code = f'''"""Unit tests for {target}."""

import pytest

from {target} import *


class Test{class_name}:
    """Test suite for {target}."""

    @pytest.fixture
    def setup(self):
        """Setup test fixtures."""
        # Arrange
        pass

    def test_basic_functionality(self, setup):
        """Test basic functionality."""
        # Act

        # Assert
        pass

    def test_edge_cases(self, setup):
        """Test edge cases."""
        # Test empty input

        # Test None input

        # Test invalid input
        pass

    def test_error_handling(self, setup):
        """Test error handling."""
        with pytest.raises(Exception):
            # Trigger expected exception
            pass

    def test_state_changes(self, setup):
        """Test state changes."""
        # Verify state before

        # Perform action

        # Verify state after
        pass
'''

        return {
            "test_type": "unit",
            "target": target,
            "code": code,
        }

    def _generate_integration_test(self, target: str, **kwargs) -> dict[str, Any]:
        """Generate integration test template."""
        code = f'''"""Integration tests for {target}."""

import pytest

from {target} import *


@pytest.mark.integration
class TestIntegration{target.title().replace("_", "")}:
    """Integration test suite for {target}."""

    @pytest.fixture(scope="module")
    def setup_module(self):
        """Setup module-level fixtures."""
        # Initialize resources
        yield
        # Cleanup resources

    def test_end_to_end_flow(self, setup_module):
        """Test end-to-end flow."""
        # Step 1: Setup

        # Step 2: Execute workflow

        # Step 3: Verify results

        # Step 4: Cleanup
        pass

    def test_integration_with_dependencies(self, setup_module):
        """Test integration with external dependencies."""
        # Test database integration

        # Test API integration

        # Test file system integration
        pass
'''

        return {
            "test_type": "integration",
            "target": target,
            "code": code,
        }

    def _generate_property_test(self, target: str, **kwargs) -> dict[str, Any]:
        """Generate property-based test."""
        code = f'''"""Property-based tests for {target}."""

from hypothesis import given, strategies as st
import pytest

from {target} import *


class TestProperties{target.title().replace("_", "")}:
    """Property-based tests for {target}."""

    @given(st.integers())
    def test_integer_property(self, value):
        """Test property holds for all integers."""
        # Define property that should always hold
        assert True  # Replace with actual property

    @given(st.text())
    def test_string_property(self, text):
        """Test property holds for all strings."""
        assert True  # Replace with actual property

    @given(st.lists(st.integers()))
    def test_list_property(self, items):
        """Test property holds for all lists."""
        assert True  # Replace with actual property
'''

        return {
            "test_type": "property",
            "target": target,
            "code": code,
        }

    def _generate_parametrized_test(
        self, target: str, cases: list = None, **kwargs
    ) -> dict[str, Any]:
        """Generate parametrized test."""
        cases_str = cases or [
            "('input1', 'expected1')",
            "('input2', 'expected2')",
            "('input3', 'expected3')",
        ]

        code = f'''"""Parametrized tests for {target}."""

import pytest

from {target} import *


class TestParametrized{target.title().replace("_", "")}:
    """Parametrized tests for {target}."""

    @pytest.mark.parametrize("input_val,expected", [
        {",        ".join(cases_str)}
    ])
    def test_with_parameters(self, input_val, expected):
        """Test with multiple parameter sets."""
        # Execute
        result = None  # Call function with input_val

        # Verify
        assert result == expected
'''

        return {
            "test_type": "parametrized",
            "target": target,
            "code": code,
        }


class TestExecutionTool(BaseTool):
    """Execute tests and collect detailed results.

    Features:
    - Run specific tests or suites
    - Parallel execution
    - Result collection
    - Failure analysis
    """

    def __init__(self):
        super().__init__(
            name="test_execution",
            description="Execute pytest tests with options",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to test file or directory (optional)",
                    },
                    "markers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Test markers to filter (e.g., unit, integration)",
                    },
                    "parallel": {
                        "type": "boolean",
                        "description": "Run tests in parallel with pytest-xdist",
                        "default": False,
                    },
                },
            },
        )

    async def _execute(
        self, path: str = None, markers: list = None, parallel: bool = False, **kwargs
    ) -> dict[str, Any]:
        """Execute tests.

        Args:
            path: Optional path to test file/directory
            markers: Optional test markers to filter (e.g., ['unit', 'integration'])
            parallel: Run tests in parallel

        Returns:
            Test execution results
        """
        cmd = ["pytest"]

        if path:
            cmd.append(path)

        if markers:
            cmd.extend(["-m", " or ".join(markers)])

        if parallel:
            cmd.extend(["-n", "auto"])

        cmd.extend(
            [
                "-v",
                "--tb=short",
                "--junit-xml=test-results.xml",
            ]
        )

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
            )

            # Parse JUnit XML for detailed results
            junit_results = self._parse_junit_xml("test-results.xml")

            return {
                "path": path or "all tests",
                "markers": markers,
                "parallel": parallel,
                "return_code": result.returncode,
                "passed": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr,
                "junit_results": junit_results,
            }
        except subprocess.TimeoutExpired:
            return {"error": "Tests timed out after 10 minutes"}
        except FileNotFoundError:
            return {"error": "pytest not installed"}
        except Exception as e:
            return {"error": str(e)}

    def _parse_junit_xml(self, xml_path: str) -> dict[str, Any]:
        """Parse JUnit XML results."""
        # Warn once if using unsafe XML parser in production
        if not _using_defusedxml and not hasattr(self, "_xml_warning_shown"):
            logger.warning(
                "Using xml.etree.ElementTree for XML parsing. "
                "Install defusedxml for production: pip install defusedxml"
            )
            self._xml_warning_shown = True

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            testsuite = root if root.tag == "testsuite" else root.find(
                "testsuite")
            if testsuite is None:
                return {"error": "Invalid JUnit XML format"}

            return {
                "tests": int(testsuite.get("tests", 0)),
                "failures": int(testsuite.get("failures", 0)),
                "errors": int(testsuite.get("errors", 0)),
                "skipped": int(testsuite.get("skipped", 0)),
                "time": float(testsuite.get("time", 0)),
            }
        except FileNotFoundError:
            return {"error": f"JUnit XML not found: {xml_path}"}
        except Exception as e:
            return {"error": f"Failed to parse JUnit XML: {e}"}


class CoverageAnalysisTool(BaseTool):
    """Analyze test coverage and generate reports.

    Provides:
    - Line coverage
    - Branch coverage
    - Function coverage
    - Coverage reports (HTML, JSON, terminal)
    """

    def __init__(self):
        super().__init__(
            name="coverage_analysis",
            description="Analyze test coverage with pytest-cov",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to test file or directory (optional)",
                    },
                    "report_type": {
                        "type": "string",
                        "description": "Coverage report format",
                        "enum": ["terminal", "html", "json", "xml"],
                        "default": "terminal",
                    },
                },
            },
        )

    async def _execute(
        self, path: str = None, report_type: str = "terminal", **kwargs
    ) -> dict[str, Any]:
        """Analyze test coverage.

        Args:
            path: Optional path to test
            report_type: Report format (terminal, html, json, xml)

        Returns:
            Coverage analysis results
        """
        cmd = ["pytest", "--cov=packages"]

        if path:
            cmd.append(path)

        if report_type == "html":
            cmd.append("--cov-report=html")
        elif report_type == "json":
            cmd.append("--cov-report=json")
        elif report_type == "xml":
            cmd.append("--cov-report=xml")
        else:
            cmd.append("--cov-report=term")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
            )

            coverage_data = self._parse_coverage_output(result.stdout)

            return {
                "path": path or "all packages",
                "report_type": report_type,
                "coverage": coverage_data,
                "output": result.stdout,
            }
        except subprocess.TimeoutExpired:
            return {"error": "Coverage analysis timed out"}
        except FileNotFoundError:
            return {"error": "pytest or pytest-cov not installed"}
        except Exception as e:
            return {"error": str(e)}

    def _parse_coverage_output(self, output: str) -> dict[str, Any]:
        """Parse coverage percentage from output."""
        lines = output.split("\n")

        for line in lines:
            if "TOTAL" in line:
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        coverage_pct = parts[-1].rstrip("%")
                        return {
                            "total_coverage": float(coverage_pct),
                            "status": (
                                "good"
                                if float(coverage_pct) >= 80
                                else "needs_improvement"
                            ),
                        }
                    except ValueError:
                        pass

        return {"error": "Could not parse coverage percentage"}


# Tool instances
test_generation = TestGenerationTool()
test_execution = TestExecutionTool()
coverage_analysis = CoverageAnalysisTool()

__all__ = [
    "TestGenerationTool",
    "TestExecutionTool",
    "CoverageAnalysisTool",
    "test_generation",
    "test_execution",
    "coverage_analysis",
]
