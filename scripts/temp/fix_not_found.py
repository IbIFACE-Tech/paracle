with open('tests/unit/test_workflow_execution_api.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix test_execute_workflow_not_found
for i, line in enumerate(lines):
    if 'def test_execute_workflow_not_found(self, client: TestClient) -> None:' in line:
        # Look for the POST line in this test
        for j in range(i, min(i+15, len(lines))):
            if 'f"/api/workflows/{sample_workflow.id}/execute"' in lines[j]:
                lines[j] = lines[j].replace(
                    'f"/api/workflows/{sample_workflow.id}/execute"',
                    '"/api/workflows/non-existent-workflow/execute"'
                )
                break
        break

with open('tests/unit/test_workflow_execution_api.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Fixed test_execute_workflow_not_found')
