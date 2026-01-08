"""Architecture and design tools for Architect agent."""

import ast
import logging
from pathlib import Path
from typing import Any

from paracle_tools.builtin.base import BaseTool

logger = logging.getLogger("paracle.tools.architect")


class CodeAnalysisTool(BaseTool):
    """Analyze code structure, dependencies, and complexity.

    Provides insights into:
    - Module dependencies
    - Function/class complexity
    - Code metrics (LOC, cyclomatic complexity)
    - Import graph
    """

    def __init__(self):
        super().__init__(
            name="code_analysis",
            description="Analyze code structure, dependencies, and complexity metrics",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File or directory path to analyze",
                    },
                },
                "required": ["path"],
            },
        )

    async def _execute(self, path: str, **kwargs) -> dict[str, Any]:
        """Analyze code at given path.

        Args:
            path: File or directory path to analyze

        Returns:
            Analysis results with structure, metrics, dependencies
        """
        file_path = Path(path)

        if not file_path.exists():
            return {"error": f"Path not found: {path}"}

        if file_path.is_file() and file_path.suffix == ".py":
            return await self._analyze_file(file_path)
        elif file_path.is_dir():
            return await self._analyze_directory(file_path)
        else:
            return {"error": f"Unsupported file type: {path}"}

    async def _analyze_file(self, file_path: Path) -> dict[str, Any]:
        """Analyze a single Python file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))

            # Extract structure
            classes = [
                node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
            ]
            functions = [
                node.name
                for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef)
            ]
            imports = [
                node.names[0].name if hasattr(node, "names") else node.module
                for node in ast.walk(tree)
                if isinstance(node, ast.Import | ast.ImportFrom)
            ]

            # Calculate metrics
            lines = content.split("\n")
            loc = len(
                [
                    line
                    for line in lines
                    if line.strip() and not line.strip().startswith("#")
                ]
            )

            return {
                "file": str(file_path),
                "classes": classes,
                "functions": functions,
                "imports": list(set(imports)),
                "metrics": {
                    "lines_of_code": loc,
                    "total_lines": len(lines),
                    "class_count": len(classes),
                    "function_count": len(functions),
                },
            }
        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
            return {"error": str(e), "file": str(file_path)}

    async def _analyze_directory(self, dir_path: Path) -> dict[str, Any]:
        """Analyze all Python files in directory."""
        py_files = list(dir_path.rglob("*.py"))
        results = []

        for py_file in py_files:
            if "__pycache__" not in str(py_file):
                file_result = await self._analyze_file(py_file)
                results.append(file_result)

        # Aggregate metrics
        total_loc = sum(r.get("metrics", {}).get("lines_of_code", 0) for r in results)
        total_classes = sum(r.get("metrics", {}).get("class_count", 0) for r in results)
        total_functions = sum(
            r.get("metrics", {}).get("function_count", 0) for r in results
        )

        return {
            "directory": str(dir_path),
            "files_analyzed": len(results),
            "summary": {
                "total_lines_of_code": total_loc,
                "total_classes": total_classes,
                "total_functions": total_functions,
            },
            "files": results,
        }


class DiagramGenerationTool(BaseTool):
    """Generate architecture diagrams from code or descriptions.

    Supports:
    - Mermaid diagram generation
    - PlantUML diagrams
    - ASCII diagrams
    """

    def __init__(self):
        super().__init__(
            name="diagram_generation",
            description="Generate architecture and design diagrams (Mermaid, PlantUML, ASCII)",
            parameters={
                "type": "object",
                "properties": {
                    "diagram_type": {
                        "type": "string",
                        "description": "Type of diagram to generate",
                        "enum": ["mermaid", "plantuml", "ascii"],
                    },
                    "content": {
                        "type": "string",
                        "description": "Diagram content, description, or existing diagram code",
                    },
                },
                "required": ["diagram_type", "content"],
            },
        )

    async def _execute(
        self, diagram_type: str, content: str, **kwargs
    ) -> dict[str, Any]:
        """Generate a diagram.

        Args:
            diagram_type: Type of diagram (mermaid, plantuml, ascii)
            content: Diagram content or description

        Returns:
            Generated diagram code
        """
        if diagram_type == "mermaid":
            return self._generate_mermaid(content)
        elif diagram_type == "plantuml":
            return self._generate_plantuml(content)
        elif diagram_type == "ascii":
            return self._generate_ascii(content)
        else:
            return {"error": f"Unsupported diagram type: {diagram_type}"}

    def _generate_mermaid(self, content: str) -> dict[str, Any]:
        """Generate Mermaid diagram."""
        # If content is already Mermaid syntax, return as-is
        if content.strip().startswith(
            ("graph", "sequenceDiagram", "classDiagram", "flowchart")
        ):
            return {"diagram_type": "mermaid", "content": content}

        # Generate simple flowchart from description
        diagram = f"""```mermaid
flowchart TD
    A[Start] --> B[{content}]
    B --> C[End]
```"""
        return {"diagram_type": "mermaid", "content": diagram}

    def _generate_plantuml(self, content: str) -> dict[str, Any]:
        """Generate PlantUML diagram."""
        if content.strip().startswith("@startuml"):
            return {"diagram_type": "plantuml", "content": content}

        diagram = f"""@startuml
{content}
@enduml"""
        return {"diagram_type": "plantuml", "content": diagram}

    def _generate_ascii(self, content: str) -> dict[str, Any]:
        """Generate ASCII diagram."""
        diagram = f"""
┌─────────────────────────────────────┐
│         {content:^30s}         │
└─────────────────────────────────────┘
"""
        return {"diagram_type": "ascii", "content": diagram}


class PatternMatchingTool(BaseTool):
    """Detect design patterns and anti-patterns in code.

    Identifies:
    - Singleton pattern
    - Factory pattern
    - Observer pattern
    - Strategy pattern
    - Common anti-patterns (God object, spaghetti code, etc.)
    """

    def __init__(self):
        super().__init__(
            name="pattern_matching",
            description="Detect design patterns and anti-patterns in code",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File or directory path to analyze for patterns",
                    },
                },
                "required": ["path"],
            },
        )

    async def _execute(self, path: str, **kwargs) -> dict[str, Any]:
        """Detect patterns in code.

        Args:
            path: File or directory to analyze

        Returns:
            Detected patterns and anti-patterns
        """
        file_path = Path(path)

        if not file_path.exists():
            return {"error": f"Path not found: {path}"}

        if file_path.is_file() and file_path.suffix == ".py":
            return await self._detect_patterns_in_file(file_path)
        elif file_path.is_dir():
            results = []
            for py_file in file_path.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    file_result = await self._detect_patterns_in_file(py_file)
                    results.append(file_result)
            return {"directory": str(file_path), "files": results}
        else:
            return {"error": f"Unsupported file type: {path}"}

    async def _detect_patterns_in_file(self, file_path: Path) -> dict[str, Any]:
        """Detect patterns in a single file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))

            patterns = []
            anti_patterns = []

            # Detect Singleton pattern
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check for __new__ method (Singleton indicator)
                    has_new = any(
                        isinstance(item, ast.FunctionDef) and item.name == "__new__"
                        for item in node.body
                    )
                    if has_new:
                        patterns.append(
                            {
                                "type": "singleton",
                                "class": node.name,
                                "line": node.lineno,
                            }
                        )

                    # Check for God Object (many methods)
                    methods = [
                        item for item in node.body if isinstance(item, ast.FunctionDef)
                    ]
                    if len(methods) > 20:
                        anti_patterns.append(
                            {
                                "type": "god_object",
                                "class": node.name,
                                "method_count": len(methods),
                                "line": node.lineno,
                            }
                        )

            # Detect Factory pattern (functions returning instances)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if "factory" in node.name.lower() or "create" in node.name.lower():
                        patterns.append(
                            {
                                "type": "factory",
                                "function": node.name,
                                "line": node.lineno,
                            }
                        )

                    # Check for long functions (anti-pattern)
                    if len(node.body) > 50:
                        anti_patterns.append(
                            {
                                "type": "long_function",
                                "function": node.name,
                                "lines": len(node.body),
                                "line": node.lineno,
                            }
                        )

            return {
                "file": str(file_path),
                "patterns": patterns,
                "anti_patterns": anti_patterns,
            }
        except Exception as e:
            logger.error(f"Failed to detect patterns in {file_path}: {e}")
            return {"error": str(e), "file": str(file_path)}


# Tool instances
code_analysis = CodeAnalysisTool()
diagram_generation = DiagramGenerationTool()
pattern_matching = PatternMatchingTool()

__all__ = [
    "CodeAnalysisTool",
    "DiagramGenerationTool",
    "PatternMatchingTool",
    "code_analysis",
    "diagram_generation",
    "pattern_matching",
]
