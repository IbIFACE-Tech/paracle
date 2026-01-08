"""Dynamic tutorial system for Paracle CLI.

This module provides automatic tutorial generation for any CLI command
by introspecting Click command metadata.
"""

from paracle_cli.tutorial.generator import TutorialGenerator
from paracle_cli.tutorial.introspector import CLIIntrospector
from paracle_cli.tutorial.runner import InteractiveTutorialRunner

__all__ = [
    "CLIIntrospector",
    "TutorialGenerator",
    "InteractiveTutorialRunner",
]
