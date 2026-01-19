with open('tests/unit/test_workflow_execution_api.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the TestWorkflowExecution class and add a repository reset fixture
for i, line in enumerate(lines):
    if 'class TestWorkflowExecution:' in line:
        # Find the next line (should be docstring or first method)
        for j in range(i+1, min(i+10, len(lines))):
            if '\"\"\"' in lines[j]:
                # Insert after docstring
                docstring_end = j + 1
                while docstring_end < len(lines) and '\"\"\"' not in lines[docstring_end]:
                    docstring_end += 1
                docstring_end += 1
                
                # Insert the fixture
                lines.insert(docstring_end, '\n')
                lines.insert(docstring_end + 1, '    @pytest.fixture(autouse=True)\n')
                lines.insert(docstring_end + 2, '    def reset_repositories(self) -> None:\n')
                lines.insert(docstring_end + 3, '        \"\"\"Reset workflow repositories before each test.\"\"\"\n')
                lines.insert(docstring_end + 4, '        workflow_crud._repository.clear()\n')
                lines.insert(docstring_end + 5, '        workflow_execution._repository.clear()\n')
                break
        break

with open('tests/unit/test_workflow_execution_api.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Added reset_repositories fixture')
