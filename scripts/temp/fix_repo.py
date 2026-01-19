with open('tests/unit/test_workflow_execution_api.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the import section and add workflow_execution import
for i, line in enumerate(lines):
    if 'from paracle_api.routers import workflow_crud' in line:
        # Add workflow_execution import
        lines.insert(i + 1, 'from paracle_api.routers import workflow_execution\n')
        break

# Find sample_workflow fixture and make it add to both repositories
for i, line in enumerate(lines):
    if 'return workflow_crud._repository.add(workflow)' in line:
        # Replace with adding to both repositories
        lines[i] = '        workflow = workflow_crud._repository.add(workflow)\n'
        lines.insert(i + 1, '        workflow_execution._repository.add(workflow)\n')
        lines.insert(i + 2, '        return workflow\n')
        break

with open('tests/unit/test_workflow_execution_api.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Fixed workflow repository sharing')
