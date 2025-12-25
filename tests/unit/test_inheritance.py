"""Tests for agent inheritance resolution."""

import pytest

from paracle_domain import (
    AgentSpec,
    CircularInheritanceError,
    InheritanceResult,
    MaxDepthExceededError,
    ParentNotFoundError,
    resolve_inheritance,
    validate_inheritance_chain,
)


class TestResolveInheritance:
    """Tests for resolve_inheritance function."""

    def test_no_parent(self) -> None:
        """Test spec without parent returns unchanged."""
        spec = AgentSpec(name="test", provider="openai", model="gpt-4")

        result = resolve_inheritance(spec, lambda _: None)

        assert result.resolved_spec.name == "test"
        assert result.chain == ["test"]
        assert result.depth == 0
        assert not result.has_warnings

    def test_single_parent(self) -> None:
        """Test single level inheritance."""
        base = AgentSpec(
            name="base",
            provider="openai",
            model="gpt-4",
            system_prompt="Base prompt",
            tools=["tool1"],
        )
        child = AgentSpec(
            name="child",
            provider="openai",
            model="gpt-4-turbo",
            parent="base",
            tools=["tool2"],
        )

        def get_parent(name: str) -> AgentSpec | None:
            return base if name == "base" else None

        result = resolve_inheritance(child, get_parent)

        assert result.resolved_spec.name == "child"
        assert result.resolved_spec.model == "gpt-4-turbo"  # Child overrides
        assert result.resolved_spec.system_prompt == "Base prompt"  # Inherited
        assert "tool1" in result.resolved_spec.tools  # Merged
        assert "tool2" in result.resolved_spec.tools  # Merged
        assert result.chain == ["child", "base"]
        assert result.depth == 1

    def test_multi_level_inheritance(self) -> None:
        """Test multi-level inheritance."""
        grandparent = AgentSpec(
            name="grandparent",
            provider="openai",
            model="gpt-3.5",
            tools=["base_tool"],
            metadata={"level": "0"},
        )
        parent = AgentSpec(
            name="parent",
            provider="openai",
            model="gpt-4",
            parent="grandparent",
            tools=["parent_tool"],
            metadata={"level": "1"},
        )
        child = AgentSpec(
            name="child",
            provider="openai",
            model="gpt-4-turbo",
            parent="parent",
            tools=["child_tool"],
            metadata={"level": "2"},
        )

        specs = {"grandparent": grandparent, "parent": parent}

        def get_parent(name: str) -> AgentSpec | None:
            return specs.get(name)

        result = resolve_inheritance(child, get_parent)

        assert result.resolved_spec.name == "child"
        assert result.resolved_spec.model == "gpt-4-turbo"
        # All tools should be merged
        assert "base_tool" in result.resolved_spec.tools
        assert "parent_tool" in result.resolved_spec.tools
        assert "child_tool" in result.resolved_spec.tools
        # Metadata is merged with child overriding
        assert result.resolved_spec.metadata["level"] == "2"
        assert result.chain == ["child", "parent", "grandparent"]
        assert result.depth == 2

    def test_circular_inheritance_error(self) -> None:
        """Test circular inheritance is detected."""
        a = AgentSpec(name="a", provider="openai", model="gpt-4", parent="b")
        b = AgentSpec(name="b", provider="openai", model="gpt-4", parent="a")

        specs = {"a": a, "b": b}

        def get_parent(name: str) -> AgentSpec | None:
            return specs.get(name)

        with pytest.raises(CircularInheritanceError) as exc_info:
            resolve_inheritance(a, get_parent)

        assert "a" in exc_info.value.chain
        assert "b" in exc_info.value.chain

    def test_max_depth_exceeded_error(self) -> None:
        """Test max depth is enforced."""
        # Create a chain of 6 levels
        specs = {}
        for i in range(6):
            parent = f"level{i-1}" if i > 0 else None
            specs[f"level{i}"] = AgentSpec(
                name=f"level{i}",
                provider="openai",
                model="gpt-4",
                parent=parent,
            )

        def get_parent(name: str) -> AgentSpec | None:
            return specs.get(name)

        # With max_depth=5, level5 (which has 5 ancestors) should fail
        with pytest.raises(MaxDepthExceededError) as exc_info:
            resolve_inheritance(specs["level5"], get_parent, max_depth=5)

        assert exc_info.value.depth >= exc_info.value.max_depth

    def test_parent_not_found_error(self) -> None:
        """Test parent not found raises error."""
        spec = AgentSpec(
            name="child",
            provider="openai",
            model="gpt-4",
            parent="nonexistent",
        )

        with pytest.raises(ParentNotFoundError) as exc_info:
            resolve_inheritance(spec, lambda _: None)

        assert exc_info.value.child == "child"
        assert exc_info.value.parent == "nonexistent"

    def test_warning_at_depth(self) -> None:
        """Test warning is generated at warn_depth."""
        specs = {}
        for i in range(4):
            parent = f"level{i-1}" if i > 0 else None
            specs[f"level{i}"] = AgentSpec(
                name=f"level{i}",
                provider="openai",
                model="gpt-4",
                parent=parent,
            )

        def get_parent(name: str) -> AgentSpec | None:
            return specs.get(name)

        result = resolve_inheritance(specs["level3"], get_parent, warn_depth=3)

        assert result.has_warnings
        assert any("warning" in w.lower() for w in result.warnings)

    def test_tools_not_duplicated(self) -> None:
        """Test tools are not duplicated during merge."""
        base = AgentSpec(
            name="base",
            provider="openai",
            model="gpt-4",
            tools=["shared_tool", "base_tool"],
        )
        child = AgentSpec(
            name="child",
            provider="openai",
            model="gpt-4",
            parent="base",
            tools=["shared_tool", "child_tool"],  # shared_tool appears in both
        )

        def get_parent(name: str) -> AgentSpec | None:
            return base if name == "base" else None

        result = resolve_inheritance(child, get_parent)

        # shared_tool should appear only once
        assert result.resolved_spec.tools.count("shared_tool") == 1
        assert len(result.resolved_spec.tools) == 3


class TestValidateInheritanceChain:
    """Tests for validate_inheritance_chain function."""

    def test_valid_chains(self) -> None:
        """Test validation passes for valid chains."""
        specs = {
            "base": AgentSpec(name="base", provider="openai", model="gpt-4"),
            "child": AgentSpec(
                name="child",
                provider="openai",
                model="gpt-4",
                parent="base",
            ),
        }

        errors = validate_inheritance_chain(specs)

        assert len(errors) == 0

    def test_detects_all_errors(self) -> None:
        """Test validation detects multiple errors."""
        specs = {
            "orphan": AgentSpec(
                name="orphan",
                provider="openai",
                model="gpt-4",
                parent="nonexistent",
            ),
            "a": AgentSpec(name="a", provider="openai", model="gpt-4", parent="b"),
            "b": AgentSpec(name="b", provider="openai", model="gpt-4", parent="a"),
        }

        errors = validate_inheritance_chain(specs)

        assert len(errors) == 3  # orphan + circular (a and b both error)
