"""Agent inheritance resolution.

This module implements the inheritance resolution algorithm for agents.
Agents can inherit from parent agents, forming an inheritance chain.

Key features:
- Merges spec fields from parent to child
- Supports max depth limit (default: 5, warning at 3+)
- Detects circular dependencies
- Tools and metadata are merged additively
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from paracle_domain.models import AgentSpec

if TYPE_CHECKING:
    from collections.abc import Callable

# Configuration
MAX_INHERITANCE_DEPTH = 5
WARN_DEPTH = 3


class InheritanceError(Exception):
    """Base exception for inheritance errors."""

    pass


class CircularInheritanceError(InheritanceError):
    """Raised when circular inheritance is detected."""

    def __init__(self, chain: list[str]) -> None:
        self.chain = chain
        cycle = " -> ".join(chain)
        super().__init__(f"Circular inheritance detected: {cycle}")


class MaxDepthExceededError(InheritanceError):
    """Raised when inheritance depth exceeds maximum."""

    def __init__(self, depth: int, max_depth: int, chain: list[str]) -> None:
        self.depth = depth
        self.max_depth = max_depth
        self.chain = chain
        super().__init__(
            f"Inheritance depth {depth} exceeds maximum {max_depth}. "
            f"Chain: {' -> '.join(chain)}"
        )


class ParentNotFoundError(InheritanceError):
    """Raised when a parent agent is not found."""

    def __init__(self, child: str, parent: str) -> None:
        self.child = child
        self.parent = parent
        super().__init__(f"Parent agent '{parent}' not found for agent '{child}'")


class InheritanceResult:
    """Result of inheritance resolution."""

    def __init__(
        self,
        resolved_spec: AgentSpec,
        chain: list[str],
        depth: int,
        warnings: list[str] | None = None,
    ) -> None:
        self.resolved_spec = resolved_spec
        self.chain = chain
        self.depth = depth
        self.warnings = warnings or []

    @property
    def has_warnings(self) -> bool:
        """Check if there are warnings."""
        return len(self.warnings) > 0


def resolve_inheritance(
    spec: AgentSpec,
    get_parent: Callable[[str], AgentSpec | None],
    max_depth: int = MAX_INHERITANCE_DEPTH,
    warn_depth: int = WARN_DEPTH,
) -> InheritanceResult:
    """Resolve agent inheritance chain.

    Args:
        spec: The agent spec to resolve
        get_parent: Function to retrieve parent spec by name
        max_depth: Maximum inheritance depth allowed
        warn_depth: Depth at which to generate warnings

    Returns:
        InheritanceResult with resolved spec and metadata

    Raises:
        CircularInheritanceError: If circular inheritance is detected
        MaxDepthExceededError: If max depth is exceeded
        ParentNotFoundError: If a parent agent is not found
    """
    if not spec.has_parent():
        return InheritanceResult(
            resolved_spec=spec,
            chain=[spec.name],
            depth=0,
        )

    # Build inheritance chain
    chain: list[str] = [spec.name]
    specs: list[AgentSpec] = [spec]
    current = spec

    while current.has_parent():
        parent_name = current.parent
        assert parent_name is not None  # Type narrowing

        # Check for circular inheritance
        if parent_name in chain:
            raise CircularInheritanceError(chain + [parent_name])

        # Check depth limit
        if len(chain) >= max_depth:
            raise MaxDepthExceededError(len(chain), max_depth, chain + [parent_name])

        # Get parent spec
        parent_spec = get_parent(parent_name)
        if parent_spec is None:
            raise ParentNotFoundError(current.name, parent_name)

        chain.append(parent_name)
        specs.append(parent_spec)
        current = parent_spec

    # Merge specs from root to leaf
    # Start from the last (root) and merge down to first (leaf)
    specs.reverse()
    resolved = _merge_specs(specs)

    # Generate warnings
    warnings: list[str] = []
    depth = len(chain) - 1
    if depth >= warn_depth:
        warnings.append(
            f"Inheritance depth {depth} is at or above warning threshold {warn_depth}. "
            "Consider flattening the hierarchy."
        )

    return InheritanceResult(
        resolved_spec=resolved,
        chain=chain,
        depth=depth,
        warnings=warnings,
    )


def _merge_specs(specs: list[AgentSpec]) -> AgentSpec:
    """Merge a list of specs from root to leaf.

    Later specs override earlier specs, except for:
    - tools: merged additively (child adds to parent's tools)
    - metadata: merged additively (child overrides parent's keys)
    - config: merged additively (child overrides parent's keys)
    """
    if not specs:
        raise ValueError("Cannot merge empty specs list")

    if len(specs) == 1:
        return specs[0].model_copy(deep=True)

    # Start with root spec
    base = specs[0]
    merged_tools = list(base.tools)
    merged_metadata = dict(base.metadata)
    merged_config = dict(base.config)

    # Apply each child spec
    for child in specs[1:]:
        # Merge tools (additive, avoid duplicates)
        for tool in child.tools:
            if tool not in merged_tools:
                merged_tools.append(tool)

        # Merge metadata (child overrides)
        merged_metadata.update(child.metadata)

        # Merge config (child overrides)
        merged_config.update(child.config)

    # Final spec uses leaf's explicit values, with merged collections
    leaf = specs[-1]

    return AgentSpec(
        name=leaf.name,
        description=leaf.description if leaf.description else base.description,
        provider=leaf.provider,
        model=leaf.model,
        temperature=leaf.temperature,
        max_tokens=leaf.max_tokens if leaf.max_tokens else base.max_tokens,
        system_prompt=leaf.system_prompt if leaf.system_prompt else base.system_prompt,
        parent=leaf.parent,
        tools=merged_tools,
        config=merged_config,
        metadata=merged_metadata,
    )


def validate_inheritance_chain(
    specs: dict[str, AgentSpec],
    max_depth: int = MAX_INHERITANCE_DEPTH,
) -> list[InheritanceError]:
    """Validate all inheritance chains in a collection of specs.

    Args:
        specs: Dictionary of agent name to spec
        max_depth: Maximum allowed inheritance depth

    Returns:
        List of inheritance errors found
    """
    errors: list[InheritanceError] = []

    def get_parent(name: str) -> AgentSpec | None:
        return specs.get(name)

    for name, spec in specs.items():
        try:
            resolve_inheritance(spec, get_parent, max_depth)
        except InheritanceError as e:
            errors.append(e)

    return errors
