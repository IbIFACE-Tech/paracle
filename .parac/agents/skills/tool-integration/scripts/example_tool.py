#!/usr/bin/env python3
"""Example custom tool implementation.

This demonstrates how to create a custom tool for Paracle agents.
"""

from typing import Any

from pydantic import BaseModel, Field


class ToolInput(BaseModel):
    """Input schema for the tool."""
    query: str = Field(..., description="The search query")
    limit: int = Field(default=10, ge=1, le=100, description="Max results")
    filters: dict[str, str] | None = Field(
        default=None, description="Optional filters")


class ToolResult(BaseModel):
    """Result schema for the tool."""
    success: bool
    output: str
    metadata: dict[str, Any] | None = None
    error: str | None = None


class ExampleTool:
    """Example tool for searching data.

    This tool demonstrates:
    - Input validation with Pydantic
    - Error handling
    - Structured output
    - Metadata tracking
    """

    name = "example-search"
    description = "Search for data with optional filtering"
    input_schema = ToolInput

    async def execute(self, input_data: ToolInput) -> ToolResult:
        """Execute the tool.

        Args:
            input_data: Validated input data

        Returns:
            Tool execution result
        """
        try:
            # Simulate search operation
            results = await self._search(
                query=input_data.query,
                limit=input_data.limit,
                filters=input_data.filters,
            )

            return ToolResult(
                success=True,
                output=f"Found {len(results)} results for '{input_data.query}'",
                metadata={
                    "count": len(results),
                    "query": input_data.query,
                    "results": results,
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e),
            )

    async def _search(
        self,
        query: str,
        limit: int,
        filters: dict[str, str] | None,
    ) -> list:
        """Perform search operation."""
        # This is where you'd integrate with external APIs,
        # databases, or other data sources

        # Example mock results
        results = [
            {"id": i, "title": f"Result {i}", "score": 0.9 - (i * 0.1)}
            for i in range(min(limit, 5))
        ]

        return results


# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        tool = ExampleTool()

        # Test the tool
        input_data = ToolInput(
            query="test query",
            limit=5,
        )

        result = await tool.execute(input_data)

        if result.success:
            print(f"✅ {result.output}")
            print(f"📊 Metadata: {result.metadata}")
        else:
            print(f"❌ Error: {result.error}")

    asyncio.run(main())
