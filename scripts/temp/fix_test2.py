with open('tests/unit/test_workflow_crud_api.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find test_list_workflows and update it
in_test = False
for i, line in enumerate(lines):
    if 'def test_list_workflows(' in line:
        in_test = True
    elif in_test and 'client.post("/api/workflows", json={"spec": spec})' in line:
        lines[i] = '            create_response = client.post("/api/workflows", json={"spec": spec})\n'
        lines.insert(i + 1, '            assert create_response.status_code == 201, f"Failed to create workflow {i}: {create_response.json()}"\n')
        break

with open('tests/unit/test_workflow_crud_api.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Updated test_list_workflows')
