"""MCP tool for governance compliance validation.

This module exposes .parac/ structure validation as an MCP tool that
AI assistants (Claude, Cursor, etc.) can call to validate file paths
before creating files.

The tool prevents AI assistants from violating .parac/ governance structure
by validating file paths and suggesting correct locations.

Usage (from AI assistant):
    # Validate file path before creating
    result = await validate_parac_file_path(".parac/costs.db")

    if not result["is_valid"]:
        # Use suggested path instead
        correct_path = result["suggested_path"]
"""

from typing import Any

from paracle_core.governance.ai_compliance import get_compliance_engine


class GovernanceValidationTool:
    """MCP tool for validating .parac/ file paths.

    This tool is exposed via MCP server so AI assistants can validate
    file paths before creating them.
    """

    def __init__(self):
        """Initialize governance validation tool."""
        self.engine = get_compliance_engine()

    def get_tool_definition(self) -> dict[str, Any]:
        """Get MCP tool definition.

        Returns:
            Tool definition dictionary for MCP registration
        """
        return {
            "name": "validate_parac_file_path",
            "description": """
            Validate a file path against .parac/ governance structure rules.

            Use this tool BEFORE creating any file in the .parac/ directory
            to ensure correct placement according to governance standards.

            The tool will:
            - Validate the proposed file path
            - Return error if path violates structure rules
            - Suggest correct location if path is wrong
            - Provide documentation on correct placement

            Example usage:
                Before: Creating .parac/costs.db
                Action: Call validate_parac_file_path(".parac/costs.db")
                Result: Error + suggestion to use .parac/memory/data/costs.db
            """.strip(),
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to validate (relative or absolute)",
                    },
                },
                "required": ["file_path"],
            },
        }

    async def execute(self, file_path: str) -> dict[str, Any]:
        """Execute validation.

        Args:
            file_path: Path to validate

        Returns:
            Validation result with suggestions
        """
        result = self.engine.validate_file_path(file_path)

        response = {
            "is_valid": result.is_valid,
            "path": str(result.path),
        }

        if not result.is_valid:
            response.update(
                {
                    "error": result.error,
                    "suggested_path": str(result.suggested_path),
                    "rule_violated": result.rule_violated,
                    "auto_fix_available": result.auto_fix_available,
                    "category": result.category.value if result.category else None,
                    "documentation": (
                        self.engine.get_structure_documentation(result.category)
                        if result.category
                        else None
                    ),
                }
            )

        return response


class BatchValidationTool:
    """MCP tool for validating multiple file paths at once."""

    def __init__(self):
        """Initialize batch validation tool."""
        self.engine = get_compliance_engine()

    def get_tool_definition(self) -> dict[str, Any]:
        """Get MCP tool definition."""
        return {
            "name": "validate_parac_file_paths_batch",
            "description": """
            Validate multiple file paths against .parac/ governance structure.

            Use this when creating multiple files to validate all paths at once.
            Returns list of violations with suggestions for each.
            """.strip(),
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of paths to validate",
                    },
                },
                "required": ["file_paths"],
            },
        }

    async def execute(self, file_paths: list[str]) -> dict[str, Any]:
        """Execute batch validation.

        Args:
            file_paths: List of paths to validate

        Returns:
            Batch validation results
        """
        violations = self.engine.get_violations(file_paths)

        return {
            "total_files": len(file_paths),
            "violations_count": len(violations),
            "all_valid": len(violations) == 0,
            "violations": [
                {
                    "path": str(v.path),
                    "error": v.error,
                    "suggested_path": str(v.suggested_path),
                    "rule_violated": v.rule_violated,
                }
                for v in violations
            ],
        }


class StructureDocumentationTool:
    """MCP tool for getting .parac/ structure documentation."""

    def __init__(self):
        """Initialize documentation tool."""
        self.engine = get_compliance_engine()

    def get_tool_definition(self) -> dict[str, Any]:
        """Get MCP tool definition."""
        return {
            "name": "get_parac_structure_docs",
            "description": """
            Get documentation on .parac/ structure rules for a file category.

            Use this to learn correct file placement rules before creating files.

            Available categories:
            - operational_data: Databases, metrics, cache files
            - logs: Log files
            - knowledge: Knowledge base markdown files
            - decisions: Architecture Decision Records
            - agent_specs: Agent specification files
            - user_docs: User-facing documentation
            - source_code: Python source code
            """.strip(),
            "input_schema": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": [
                            "operational_data",
                            "logs",
                            "knowledge",
                            "decisions",
                            "agent_specs",
                            "user_docs",
                            "source_code",
                        ],
                        "description": "File category to get documentation for",
                    },
                },
                "required": ["category"],
            },
        }

    async def execute(self, category: str) -> dict[str, Any]:
        """Execute documentation retrieval.

        Args:
            category: File category

        Returns:
            Documentation for the category
        """
        from paracle_core.governance.ai_compliance import FileCategory

        try:
            file_category = FileCategory(category)
            documentation = self.engine.get_structure_documentation(file_category)

            return {
                "category": category,
                "documentation": documentation,
            }
        except ValueError:
            return {
                "error": f"Unknown category: {category}",
                "available_categories": [c.value for c in FileCategory],
            }


# Tool instances for MCP registration
governance_validation_tool = GovernanceValidationTool()
batch_validation_tool = BatchValidationTool()
structure_documentation_tool = StructureDocumentationTool()
