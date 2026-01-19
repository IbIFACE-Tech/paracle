with open('packages/paracle_api/routers/agents.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix the problematic lines
fixed_lines = []
for line in lines:
    if 'try:\
' in line:
        fixed_lines.append(line.replace('try:\
        ', 'try:\n        '))
    elif '\
    except' in line:
        fixed_lines.append(line.replace('\
    except', '\n    except'))
    elif '\
        raise' in line:
        fixed_lines.append(line.replace('\
        raise', '\n        raise'))
    elif '\
            status_code' in line:
        fixed_lines.append(line.replace('\
            status_code', '\n            status_code'))
    elif '\
            detail' in line:
        fixed_lines.append(line.replace('\
            detail', '\n            detail'))
    elif '\
        )' in line:
        fixed_lines.append(line.replace('\
        )', '\n        )'))
    else:
        fixed_lines.append(line)

with open('packages/paracle_api/routers/agents.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print('Fixed agents.py')
