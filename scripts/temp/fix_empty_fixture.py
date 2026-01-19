with open('tests/unit/test_workflow_execution_api.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the empty reset_repositories fixture and fill it
for i, line in enumerate(lines):
    if 'def reset_repositories(self) -> None:' in line and i+1 < len(lines):
        # Check if next line is docstring
        if '\"\"\"' in lines[i+1]:
            # Find end of docstring
            j = i + 2
            while j < len(lines) and '\"\"\"' not in lines[j]:
                j += 1
            # Insert the implementation after docstring
            if j < len(lines):
                lines.insert(j + 1, '        workflow_crud._repository.clear()\n')
                lines.insert(j + 2, '        workflow_execution._repository.clear()\n')
        break

with open('tests/unit/test_workflow_execution_api.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Fixed empty reset_repositories fixture')
