import re

with open("packages/paracle_api/routers/agents.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find the discover_agents() call and wrap it
pattern = r'(    discovery = AgentDiscovery\(parac_root\)\n\n)(    agents = discovery\.discover_agents\(\))'
replacement = r'\1    try:\n        agents = discovery.discover_agents()\n    except FileNotFoundError:\n        raise HTTPException(\n            status_code=404,\n            detail="No .parac/ directory found. Initialize with ''paracle init''.",\n        )'

content = re.sub(pattern, replacement, content)

with open("packages/paracle_api/routers/agents.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed")
