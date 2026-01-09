"""Fix security agent tests to use agent.get_effective_spec()."""

import re
from pathlib import Path

test_file = Path("tests/integration/test_security_agent.py")
content = test_file.read_text(encoding="utf-8")

# Patterns to replace
patterns = [
    # agent.name -> effective.name
    (r"assert agent\.name ==", "assert effective.name =="),
    # agent.tools -> effective.tools
    (r'assert "([^"]+)" in agent\.tools', r'assert "\1" in effective.tools'),
    (r"assert len\(agent\.tools\)", "assert len(effective.tools)"),
    # agent.skills -> effective.skills
    (r'assert "([^"]+)" in agent\.skills', r'assert "\1" in effective.skills'),
    (r"assert len\(agent\.skills\)", "assert len(effective.skills)"),
    # agent.temperature -> effective.temperature
    (r"assert agent\.temperature", "assert effective.temperature"),
    # agent.parent -> effective.parent
    (r"assert agent\.parent", "assert effective.parent"),
    # agent.metadata -> effective.metadata
    (r"agent\.metadata", "effective.metadata"),
]

# Apply replacements
for pattern, replacement in patterns:
    content = re.sub(pattern, replacement, content)

# Add effective = agent.get_effective_spec() after agent creation
# Find patterns like: agent = agent_factory.create(...)


def add_effective_spec(match):
    indent = match.group(1)
    line = match.group(0)
    # Check if next line already has effective =
    return f"{line}\n{indent}effective = agent.get_effective_spec()"


# Only add if not already present
lines = content.split("\n")
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    new_lines.append(line)

    # Check if this is an agent creation line
    if re.search(r"(\s+)agent = agent_factory\.create\(", line):
        # Check if next line already has effective =
        if (
            i + 1 < len(lines)
            and "effective = agent.get_effective_spec()" not in lines[i + 1]
        ):
            indent = re.match(r"(\s+)", line).group(1)
            new_lines.append(f"{indent}effective = agent.get_effective_spec()")

    i += 1

content = "\n".join(new_lines)

# Write back
test_file.write_text(content, encoding="utf-8")
print(f"✅ Fixed {test_file}")
