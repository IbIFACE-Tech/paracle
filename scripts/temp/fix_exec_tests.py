with open('tests/unit/test_workflow_execution_api.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace execution endpoints to match actual API
replacements = [
    # Execute endpoint - should use workflow_id
    ('"/api/workflows/execute"', 'f"/api/workflows/{sample_workflow.id}/execute"'),
    # Get execution status - needs /v1 prefix
    ('"/api/workflows/executions/', '"/v1/api/workflows/executions/'),
    # Cancel execution - needs /v1 prefix  
    # Note: already starts with /api/workflows/executions so just add v1
]

# Do replacements
for old, new in replacements:
    content = content.replace(old, new)

# Fix the specific lines that build URLs dynamically
content = content.replace(
    'response = client.get(f\"/api/workflows/executions/{execution_id}\")',
    'response = client.get(f\"/v1/api/workflows/executions/{execution_id}\")'
)
content = content.replace(
    'response = client.post(f\"/api/workflows/executions/{execution_id}/cancel\")',
    'response = client.post(f\"/v1/api/workflows/executions/{execution_id}/cancel\")'
)
content = content.replace(
    'response = client.get(\"/api/workflows/executions/non-existent-exec\")',
    'response = client.get(\"/v1/api/workflows/executions/non-existent-exec\")'
)
content = content.replace(
    'response = client.post(\"/api/workflows/executions/non-existent-exec/cancel\")',
    'response = client.post(\"/v1/api/workflows/executions/non-existent-exec/cancel\")'
)

with open('tests/unit/test_workflow_execution_api.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated workflow execution test endpoints')
