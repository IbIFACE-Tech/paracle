"""Documentation tools for Documenter agent."""

import logging
import subprocess
from typing import Any

from paracle_tools.builtin.base import BaseTool

logger = logging.getLogger("paracle.tools.documenter")


class MarkdownGenerationTool(BaseTool):
    """Generate markdown documentation.

    Creates:
    - README files
    - User guides
    - Tutorials
    - Change logs
    """

    def __init__(self):
        super().__init__(
            name="markdown_generation",
            description="Generate markdown documentation",
            parameters={
                "type": "object",
                "properties": {
                    "doc_type": {
                        "type": "string",
                        "description": "Type of documentation to generate",
                        "enum": ["readme", "guide", "tutorial", "changelog"],
                    },
                    "project_name": {
                        "type": "string",
                        "description": "Project name (for readme)",
                    },
                    "description": {
                        "type": "string",
                        "description": "Project description (for readme)",
                    },
                    "title": {
                        "type": "string",
                        "description": "Document title (for guide/tutorial)",
                    },
                    "sections": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Section titles (for guide)",
                    },
                    "steps": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Step titles (for tutorial)",
                    },
                    "version": {
                        "type": "string",
                        "description": "Version number (for changelog)",
                    },
                    "date": {
                        "type": "string",
                        "description": "Release date (for changelog)",
                    },
                },
                "required": ["doc_type"],
            },
        )

    async def _execute(self, doc_type: str, **kwargs) -> dict[str, Any]:
        """Generate markdown documentation.

        Args:
            doc_type: Type of document (readme, guide, tutorial, changelog)
            **kwargs: Document-specific parameters

        Returns:
            Generated markdown content
        """
        if doc_type == "readme":
            return self._generate_readme(**kwargs)
        elif doc_type == "guide":
            return self._generate_guide(**kwargs)
        elif doc_type == "tutorial":
            return self._generate_tutorial(**kwargs)
        elif doc_type == "changelog":
            return self._generate_changelog(**kwargs)
        else:
            return {"error": f"Unsupported doc type: {doc_type}"}

    def _generate_readme(
        self, project_name: str, description: str = "", **kwargs
    ) -> dict[str, Any]:
        """Generate README.md."""
        content = f"""# {project_name}

{description}

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

```bash
pip install {project_name.lower().replace(" ", "-")}
```

## Quick Start

```python
from {project_name.lower().replace(" ", "_")} import *

# Your code here
```

## Documentation

See [docs](./docs) for complete documentation.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
"""

        return {
            "doc_type": "readme",
            "content": content,
            "file": "README.md",
        }

    def _generate_guide(
        self, title: str, sections: list = None, **kwargs
    ) -> dict[str, Any]:
        """Generate user guide."""
        sections_list = sections or [
            "Introduction",
            "Getting Started",
            "Advanced Usage",
        ]

        content = f"# {title}\n\n"

        for section in sections_list:
            content += f"## {section}\n\n"
            content += "TODO: Add content for this section.\n\n"

        return {
            "doc_type": "guide",
            "title": title,
            "content": content,
        }

    def _generate_tutorial(
        self, title: str, steps: list = None, **kwargs
    ) -> dict[str, Any]:
        """Generate tutorial."""
        steps_list = steps or ["Step 1", "Step 2", "Step 3"]

        content = f"# {title}\n\n"
        content += "In this tutorial, you'll learn how to...\n\n"

        for i, step in enumerate(steps_list, 1):
            content += f"## Step {i}: {step}\n\n"
            content += "```python\n# Code example\n```\n\n"

        content += "## Conclusion\n\nYou've successfully...\n"

        return {
            "doc_type": "tutorial",
            "title": title,
            "content": content,
        }

    def _generate_changelog(
        self, version: str, changes: list = None, **kwargs
    ) -> dict[str, Any]:
        """Generate changelog entry."""
        changes_list = changes or []

        content = f"## [{version}] - {kwargs.get('date', 'YYYY-MM-DD')}\n\n"

        if changes_list:
            for category in ["Added", "Changed", "Fixed", "Removed"]:
                category_changes = [
                    c for c in changes_list if c.get("type") == category.lower()
                ]
                if category_changes:
                    content += f"### {category}\n\n"
                    for change in category_changes:
                        content += f"- {change.get('description', '')}\n"
                    content += "\n"
        else:
            content += "### Added\n\n- New feature\n\n"
            content += "### Changed\n\n- Updated behavior\n\n"
            content += "### Fixed\n\n- Bug fix\n\n"

        return {
            "doc_type": "changelog",
            "version": version,
            "content": content,
        }


class ApiDocGenerationTool(BaseTool):
    """Generate API documentation from code.

    Supports:
    - OpenAPI/Swagger specs
    - Function/class documentation
    - Parameter descriptions
    - Example code
    """

    def __init__(self):
        super().__init__(
            name="api_doc_generation",
            description="Generate API documentation",
            parameters={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Source code path to document",
                    },
                    "output_format": {
                        "type": "string",
                        "description": "Output documentation format",
                        "enum": ["markdown", "html", "openapi"],
                        "default": "markdown",
                    },
                },
                "required": ["source"],
            },
        )

    async def _execute(
        self, source: str, output_format: str = "markdown", **kwargs
    ) -> dict[str, Any]:
        """Generate API documentation.

        Args:
            source: Source code path
            output_format: Output format (markdown, html, json, openapi)

        Returns:
            Generated API documentation
        """
        if output_format == "markdown":
            return await self._generate_markdown_docs(source)
        elif output_format == "html":
            return await self._generate_html_docs(source)
        elif output_format == "openapi":
            return await self._generate_openapi_spec(source)
        else:
            return {"error": f"Unsupported format: {output_format}"}

    async def _generate_markdown_docs(self, source: str) -> dict[str, Any]:
        """Generate markdown API docs."""
        try:
            # Use pydoc or sphinx
            result = subprocess.run(
                ["python", "-m", "pydoc", source],
                capture_output=True,
                text=True,
                timeout=30,
            )

            return {
                "format": "markdown",
                "source": source,
                "content": result.stdout,
            }
        except Exception as e:
            return {"error": str(e)}

    async def _generate_html_docs(self, source: str) -> dict[str, Any]:
        """Generate HTML API docs with Sphinx."""
        return {
            "format": "html",
            "source": source,
            "message": "Use 'make docs' to build HTML documentation with Sphinx",
        }

    async def _generate_openapi_spec(self, source: str) -> dict[str, Any]:
        """Generate OpenAPI specification."""
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "API",
                "version": "1.0.0",
            },
            "paths": {},
        }

        return {
            "format": "openapi",
            "source": source,
            "spec": spec,
        }


class DiagramCreationTool(BaseTool):
    """Create diagrams for documentation.

    Creates:
    - Architecture diagrams (Mermaid, PlantUML)
    - Flowcharts
    - Sequence diagrams
    - Class diagrams
    """

    def __init__(self):
        super().__init__(
            name="diagram_creation",
            description="Create diagrams for documentation",
            parameters={
                "type": "object",
                "properties": {
                    "diagram_type": {
                        "type": "string",
                        "description": "Type of diagram to create",
                        "enum": ["flowchart", "sequence", "class", "architecture"],
                    },
                    "title": {
                        "type": "string",
                        "description": "Diagram title",
                    },
                    "participants": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Participants (for sequence diagrams)",
                    },
                },
                "required": ["diagram_type"],
            },
        )

    async def _execute(self, diagram_type: str, **kwargs) -> dict[str, Any]:
        """Create a diagram.

        Args:
            diagram_type: Type of diagram (flowchart, sequence, class, architecture)
            **kwargs: Diagram-specific parameters

        Returns:
            Diagram definition
        """
        if diagram_type == "flowchart":
            return self._create_flowchart(**kwargs)
        elif diagram_type == "sequence":
            return self._create_sequence_diagram(**kwargs)
        elif diagram_type == "class":
            return self._create_class_diagram(**kwargs)
        elif diagram_type == "architecture":
            return self._create_architecture_diagram(**kwargs)
        else:
            return {"error": f"Unsupported diagram type: {diagram_type}"}

    def _create_flowchart(self, title: str = "Flowchart", **kwargs) -> dict[str, Any]:
        """Create flowchart diagram."""
        diagram = """```mermaid
flowchart TD
    A[Start] --> B{Decision?}
    B -->|Yes| C[Process A]
    B -->|No| D[Process B]
    C --> E[End]
    D --> E
```"""

        return {
            "diagram_type": "flowchart",
            "title": title,
            "content": diagram,
        }

    def _create_sequence_diagram(
        self, title: str = "Sequence", participants: list = None, **kwargs
    ) -> dict[str, Any]:
        """Create sequence diagram."""
        parts = participants or ["User", "System", "Database"]

        diagram = "```mermaid\nsequenceDiagram\n"
        for part in parts:
            diagram += f"    participant {part}\n"
        diagram += "    User->>System: Request\n"
        diagram += "    System->>Database: Query\n"
        diagram += "    Database-->>System: Result\n"
        diagram += "    System-->>User: Response\n"
        diagram += "```"

        return {
            "diagram_type": "sequence",
            "title": title,
            "content": diagram,
        }

    def _create_class_diagram(
        self, title: str = "Class Diagram", **kwargs
    ) -> dict[str, Any]:
        """Create class diagram."""
        diagram = """```mermaid
classDiagram
    class BaseClass {
        +attribute: str
        +method()
    }
    class ChildClass {
        +specific_method()
    }
    BaseClass <|-- ChildClass
```"""

        return {
            "diagram_type": "class",
            "title": title,
            "content": diagram,
        }

    def _create_architecture_diagram(
        self, title: str = "Architecture", **kwargs
    ) -> dict[str, Any]:
        """Create architecture diagram."""
        diagram = """```mermaid
graph TB
    subgraph "Presentation Layer"
        UI[User Interface]
    end
    subgraph "Application Layer"
        API[API]
        BL[Business Logic]
    end
    subgraph "Data Layer"
        DB[(Database)]
    end
    UI --> API
    API --> BL
    BL --> DB
```"""

        return {
            "diagram_type": "architecture",
            "title": title,
            "content": diagram,
        }


# Tool instances
markdown_generation = MarkdownGenerationTool()
api_doc_generation = ApiDocGenerationTool()
diagram_creation = DiagramCreationTool()

__all__ = [
    "MarkdownGenerationTool",
    "ApiDocGenerationTool",
    "DiagramCreationTool",
    "markdown_generation",
    "api_doc_generation",
    "diagram_creation",
]
