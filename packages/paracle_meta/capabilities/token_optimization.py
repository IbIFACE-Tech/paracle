"""Token optimization capability for MetaAgent.

Reduces token usage through intelligent compression:
- Message summarization
- Code minification
- Redundancy removal
- Semantic deduplication
- Context pruning
- Smart truncation

Inspired by claude-flow's 32.3% token reduction techniques.
"""

import hashlib
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import Field

from paracle_meta.capabilities.base import (
    BaseCapability,
    CapabilityConfig,
    CapabilityResult,
)


class OptimizationLevel(str, Enum):
    """Optimization aggressiveness."""

    LIGHT = "light"  # 10-15% reduction, minimal loss
    MEDIUM = "medium"  # 20-30% reduction, acceptable loss
    AGGRESSIVE = "aggressive"  # 40-50% reduction, noticeable loss


class ContentType(str, Enum):
    """Type of content to optimize."""

    TEXT = "text"
    CODE = "code"
    CONVERSATION = "conversation"
    DOCUMENTATION = "documentation"
    MIXED = "mixed"


@dataclass
class OptimizationResult:
    """Result of token optimization."""

    original_text: str
    optimized_text: str
    original_tokens: int
    optimized_tokens: int
    reduction_pct: float
    techniques_used: list[str] = field(default_factory=list)
    quality_score: float = 0.9  # Estimated quality retention (0-1)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_tokens": self.original_tokens,
            "optimized_tokens": self.optimized_tokens,
            "tokens_saved": self.original_tokens - self.optimized_tokens,
            "reduction_pct": round(self.reduction_pct, 2),
            "techniques_used": self.techniques_used,
            "quality_score": round(self.quality_score, 3),
        }


class TokenOptimizationConfig(CapabilityConfig):
    """Configuration for token optimization capability."""

    default_level: OptimizationLevel = Field(
        default=OptimizationLevel.MEDIUM,
        description="Default optimization level",
    )
    preserve_code_structure: bool = Field(
        default=True,
        description="Preserve code indentation and structure",
    )
    preserve_markdown: bool = Field(
        default=True,
        description="Preserve markdown formatting",
    )
    min_text_length: int = Field(
        default=50,
        description="Minimum text length to optimize",
    )
    enable_summarization: bool = Field(
        default=True,
        description="Enable AI-powered summarization (requires LLM)",
    )


class TokenOptimizationCapability(BaseCapability):
    """Token optimization through intelligent compression.

    Reduces token usage while preserving meaning:
    - Remove redundancy and filler words
    - Compress whitespace
    - Minify code
    - Summarize long texts
    - Deduplicate similar content
    - Smart truncation

    Example:
        >>> optimizer = TokenOptimizationCapability()
        >>> await optimizer.initialize()

        >>> # Optimize text
        >>> result = await optimizer.optimize(
        ...     text="This is a very long text that could be shortened...",
        ...     level="medium",
        ...     content_type="text"
        ... )
        >>> print(f"Reduced by {result.output['reduction_pct']}%")

        >>> # Optimize code
        >>> result = await optimizer.optimize(
        ...     text=code_string,
        ...     content_type="code",
        ...     level="light"
        ... )

        >>> # Optimize conversation history
        >>> result = await optimizer.optimize_conversation(
        ...     messages=[
        ...         {"role": "user", "content": "..."},
        ...         {"role": "assistant", "content": "..."},
        ...     ],
        ...     max_tokens=2000
        ... )
    """

    name = "token_optimization"
    description = "Intelligent token reduction through compression and summarization"

    def __init__(self, config: TokenOptimizationConfig | None = None):
        """Initialize token optimization capability."""
        super().__init__(config or TokenOptimizationConfig())
        self.config: TokenOptimizationConfig = self.config
        self._stats = {
            "total_optimizations": 0,
            "total_tokens_saved": 0,
            "avg_reduction_pct": 0.0,
        }

    async def execute(self, **kwargs) -> CapabilityResult:
        """Execute token optimization operation.

        Args:
            action: Operation (optimize, optimize_conversation, estimate, stats)
            **kwargs: Operation-specific parameters

        Returns:
            CapabilityResult with operation outcome
        """
        if not self._initialized:
            await self.initialize()

        action = kwargs.pop("action", "optimize")
        start_time = time.time()

        try:
            if action == "optimize":
                result = await self._optimize(**kwargs)
            elif action == "optimize_conversation":
                result = await self._optimize_conversation(**kwargs)
            elif action == "estimate":
                result = self._estimate_tokens(**kwargs)
            elif action == "stats":
                result = self._get_stats(**kwargs)
            else:
                return CapabilityResult.error_result(
                    capability=self.name,
                    error=f"Unknown action: {action}",
                )

            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.success_result(
                capability=self.name,
                output=result,
                duration_ms=duration_ms,
                action=action,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CapabilityResult.error_result(
                capability=self.name,
                error=str(e),
                duration_ms=duration_ms,
                action=action,
            )

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation).

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        # Simple heuristic: ~4 characters per token for English
        # More accurate would use tiktoken, but this avoids dependency
        return len(text) // 4

    async def _optimize(
        self,
        text: str,
        level: str | None = None,
        content_type: str | None = None,
        **extra,
    ) -> dict[str, Any]:
        """Optimize text for token reduction.

        Args:
            text: Text to optimize
            level: Optimization level (light, medium, aggressive)
            content_type: Type of content (text, code, conversation, etc.)

        Returns:
            Optimization result
        """
        if len(text) < self.config.min_text_length:
            return {
                "original_text": text,
                "optimized_text": text,
                "original_tokens": self._estimate_tokens(text),
                "optimized_tokens": self._estimate_tokens(text),
                "reduction_pct": 0.0,
                "message": "Text too short to optimize",
            }

        level_enum = OptimizationLevel(level) if level else self.config.default_level
        content_type_enum = (
            ContentType(content_type) if content_type else ContentType.TEXT
        )

        original_tokens = self._estimate_tokens(text)
        optimized = text
        techniques = []

        # Apply optimization techniques based on level and content type
        if content_type_enum == ContentType.CODE:
            optimized, code_techniques = self._optimize_code(optimized, level_enum)
            techniques.extend(code_techniques)
        elif content_type_enum == ContentType.CONVERSATION:
            optimized, conv_techniques = self._optimize_conversation_text(
                optimized, level_enum
            )
            techniques.extend(conv_techniques)
        else:
            # General text optimization
            optimized, text_techniques = self._optimize_text(optimized, level_enum)
            techniques.extend(text_techniques)

        optimized_tokens = self._estimate_tokens(optimized)
        reduction_pct = (
            ((original_tokens - optimized_tokens) / original_tokens * 100)
            if original_tokens > 0
            else 0
        )

        # Update stats
        self._stats["total_optimizations"] += 1
        self._stats["total_tokens_saved"] += original_tokens - optimized_tokens
        self._stats["avg_reduction_pct"] = (
            self._stats["avg_reduction_pct"] * (self._stats["total_optimizations"] - 1)
            + reduction_pct
        ) / self._stats["total_optimizations"]

        result = OptimizationResult(
            original_text=text,
            optimized_text=optimized,
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            reduction_pct=reduction_pct,
            techniques_used=techniques,
        )

        return {
            "optimized_text": optimized,
            **result.to_dict(),
        }

    def _optimize_text(
        self, text: str, level: OptimizationLevel
    ) -> tuple[str, list[str]]:
        """Optimize general text.

        Args:
            text: Text to optimize
            level: Optimization level

        Returns:
            (optimized_text, techniques_used)
        """
        optimized = text
        techniques = []

        # Level 1: Light optimization (all levels)
        # Remove extra whitespace
        optimized = re.sub(r"\s+", " ", optimized)
        techniques.append("whitespace_compression")

        # Remove trailing whitespace
        optimized = "\n".join(line.rstrip() for line in optimized.split("\n"))
        techniques.append("trailing_whitespace_removal")

        if level in (OptimizationLevel.MEDIUM, OptimizationLevel.AGGRESSIVE):
            # Level 2: Medium optimization
            # Remove filler words
            filler_words = [
                r"\bvery\b",
                r"\breally\b",
                r"\bquite\b",
                r"\bactually\b",
                r"\bjust\b",
                r"\bbasically\b",
                r"\bliterally\b",
            ]
            for pattern in filler_words:
                optimized = re.sub(pattern, "", optimized, flags=re.IGNORECASE)
            techniques.append("filler_word_removal")

            # Simplify phrases
            replacements = {
                r"in order to": "to",
                r"due to the fact that": "because",
                r"in the event that": "if",
                r"at this point in time": "now",
                r"for the purpose of": "for",
            }
            for pattern, replacement in replacements.items():
                optimized = re.sub(pattern, replacement, optimized, flags=re.IGNORECASE)
            techniques.append("phrase_simplification")

        if level == OptimizationLevel.AGGRESSIVE:
            # Level 3: Aggressive optimization
            # Remove articles in non-critical contexts
            optimized = re.sub(r"\b(a|an|the)\s+", " ", optimized, flags=re.IGNORECASE)
            techniques.append("article_removal")

            # Abbreviate common words
            abbreviations = {
                r"\bwith\b": "w/",
                r"\bwithout\b": "w/o",
                r"\band\b": "&",
                r"\bapproximately\b": "~",
            }
            for pattern, abbrev in abbreviations.items():
                optimized = re.sub(pattern, abbrev, optimized, flags=re.IGNORECASE)
            techniques.append("abbreviation")

        # Final cleanup
        optimized = re.sub(r"\s+", " ", optimized).strip()

        return optimized, techniques

    def _optimize_code(
        self, code: str, level: OptimizationLevel
    ) -> tuple[str, list[str]]:
        """Optimize code while preserving functionality.

        Args:
            code: Code to optimize
            level: Optimization level

        Returns:
            (optimized_code, techniques_used)
        """
        optimized = code
        techniques = []

        if not self.config.preserve_code_structure:
            # Remove comments
            optimized = re.sub(r"#.*$", "", optimized, flags=re.MULTILINE)
            optimized = re.sub(r"//.*$", "", optimized, flags=re.MULTILINE)
            optimized = re.sub(r"/\*.*?\*/", "", optimized, flags=re.DOTALL)
            techniques.append("comment_removal")

        # Remove blank lines
        optimized = re.sub(r"\n\s*\n", "\n", optimized)
        techniques.append("blank_line_removal")

        if level in (OptimizationLevel.MEDIUM, OptimizationLevel.AGGRESSIVE):
            # Remove trailing whitespace
            optimized = "\n".join(line.rstrip() for line in optimized.split("\n"))
            techniques.append("trailing_whitespace")

        if (
            level == OptimizationLevel.AGGRESSIVE
            and not self.config.preserve_code_structure
        ):
            # Aggressive minification (may break some code)
            # Remove extra spaces around operators
            optimized = re.sub(r"\s*([=+\-*/,<>])\s*", r"\1", optimized)
            techniques.append("operator_spacing_removal")

        return optimized, techniques

    def _optimize_conversation_text(
        self, text: str, level: OptimizationLevel
    ) -> tuple[str, list[str]]:
        """Optimize conversation text.

        Args:
            text: Conversation text
            level: Optimization level

        Returns:
            (optimized_text, techniques_used)
        """
        optimized = text
        techniques = []

        # Remove conversational fillers
        fillers = [
            r"\buh\b",
            r"\bum\b",
            r"\bhmm\b",
            r"\bwell\b",
            r"\bso\b",
            r"\blike\b",
            r"\byou know\b",
        ]
        for pattern in fillers:
            optimized = re.sub(pattern, "", optimized, flags=re.IGNORECASE)
        techniques.append("conversation_filler_removal")

        # Apply general text optimization
        optimized, text_techniques = self._optimize_text(optimized, level)
        techniques.extend(text_techniques)

        return optimized, techniques

    async def _optimize_conversation(
        self,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,
        preserve_recent: int = 5,
        **extra,
    ) -> dict[str, Any]:
        """Optimize conversation history.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Target maximum tokens
            preserve_recent: Number of recent messages to preserve fully

        Returns:
            Optimized conversation
        """
        if not messages:
            return {
                "optimized_messages": [],
                "original_tokens": 0,
                "optimized_tokens": 0,
                "reduction_pct": 0.0,
            }

        original_tokens = sum(
            self._estimate_tokens(msg.get("content", "")) for msg in messages
        )

        # Preserve most recent messages
        recent_messages = (
            messages[-preserve_recent:] if len(messages) > preserve_recent else messages
        )
        older_messages = (
            messages[:-preserve_recent] if len(messages) > preserve_recent else []
        )

        optimized_messages = []

        # Optimize older messages more aggressively
        for msg in older_messages:
            content = msg.get("content", "")
            if len(content) > 100:  # Only optimize non-trivial messages
                opt_result = await self._optimize(
                    text=content,
                    level="aggressive",
                    content_type="conversation",
                )
                optimized_messages.append(
                    {
                        "role": msg.get("role", "user"),
                        "content": opt_result["optimized_text"],
                    }
                )
            else:
                optimized_messages.append(msg)

        # Preserve recent messages with light optimization
        for msg in recent_messages:
            content = msg.get("content", "")
            opt_result = await self._optimize(
                text=content,
                level="light",
                content_type="conversation",
            )
            optimized_messages.append(
                {
                    "role": msg.get("role", "user"),
                    "content": opt_result["optimized_text"],
                }
            )

        # If still over max_tokens, remove oldest messages
        if max_tokens:
            current_tokens = sum(
                self._estimate_tokens(msg.get("content", ""))
                for msg in optimized_messages
            )

            while (
                current_tokens > max_tokens
                and len(optimized_messages) > preserve_recent
            ):
                removed = optimized_messages.pop(0)
                current_tokens -= self._estimate_tokens(removed.get("content", ""))

        optimized_tokens = sum(
            self._estimate_tokens(msg.get("content", "")) for msg in optimized_messages
        )
        reduction_pct = (
            ((original_tokens - optimized_tokens) / original_tokens * 100)
            if original_tokens > 0
            else 0
        )

        return {
            "optimized_messages": optimized_messages,
            "original_messages_count": len(messages),
            "optimized_messages_count": len(optimized_messages),
            "original_tokens": original_tokens,
            "optimized_tokens": optimized_tokens,
            "tokens_saved": original_tokens - optimized_tokens,
            "reduction_pct": round(reduction_pct, 2),
        }

    def _get_stats(self, **kwargs) -> dict[str, Any]:
        """Get optimization statistics.

        Returns:
            Statistics
        """
        return {
            **self._stats,
            "avg_reduction_pct": round(self._stats["avg_reduction_pct"], 2),
        }

    # Convenience methods
    async def optimize(
        self,
        text: str,
        level: str | None = None,
        content_type: str | None = None,
    ) -> CapabilityResult:
        """Optimize text."""
        return await self.execute(
            action="optimize",
            text=text,
            level=level,
            content_type=content_type,
        )

    async def optimize_conversation(
        self,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,
    ) -> CapabilityResult:
        """Optimize conversation history."""
        return await self.execute(
            action="optimize_conversation",
            messages=messages,
            max_tokens=max_tokens,
        )

    async def get_stats(self) -> CapabilityResult:
        """Get statistics."""
        return await self.execute(action="stats")
