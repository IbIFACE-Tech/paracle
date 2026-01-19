import re

with open('tests/unit/test_workflow_crud_api.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the reset_repository fixture and add monkeypatch parameter
for i, line in enumerate(lines):
    if 'def reset_repository(self) -> None:' in line:
        lines[i] = '    def reset_repository(self, monkeypatch) -> None:\n'
    elif 'workflow_crud._repository.clear()' in line and i < len(lines) - 1:
        # Add mocking after clear()
        lines.insert(i + 1, '        # Mock the loader to return None so tests use the repository\n')
        lines.insert(i + 2, '        monkeypatch.setattr(\"paracle_api.routers.workflow_crud._loader\", None)\n')
        lines.insert(i + 3, '        monkeypatch.setattr(\"paracle_api.routers.workflow_crud._get_loader\", lambda: None)\n')
        break

with open('tests/unit/test_workflow_crud_api.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Updated test_workflow_crud_api.py')
