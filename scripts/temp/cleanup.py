with open('tests/unit/test_workflow_execution_api.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove duplicate fixture definitions and fix the class
new_lines = []
in_reset_fixture = False
fixture_count = 0
skip_until_next_method = False

for i, line in enumerate(lines):
    # Skip duplicate workflow_execution imports
    if 'from paracle_api.routers import workflow_execution' in line:
        if 'workflow_crud' not in line:
            # This is a standalone duplicate, skip it
            continue
    
    # Track reset_repositories fixtures
    if '@pytest.fixture(autouse=True)' in line:
        # Check if next line is reset_repositories
        if i+1 < len(lines) and 'def reset_repositories' in lines[i+1]:
            fixture_count += 1
            if fixture_count > 1:
                # Skip duplicate fixture
                skip_until_next_method = True
                continue
    
    if skip_until_next_method:
        # Skip lines until we find the next method or fixture
        if (line.strip().startswith('def ') or line.strip().startswith('@pytest')) and 'reset_repositories' not in line:
            skip_until_next_method = False
        else:
            continue
    
    new_lines.append(line)

with open('tests/unit/test_workflow_execution_api.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Cleaned up duplicate fixtures')
