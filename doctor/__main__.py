import json
import sys
from pathlib import Path

filename = f'health-{sys.argv[1]}.json'

if Path(filename).exists():
    with open(filename, 'r') as f:
        content: dict = json.load(f)
else:
    sys.exit(1)

heathy_overall = True

for module, props in content.items():
    date_string, healthy = props
    print(module, date_string, healthy)
    if not healthy:
        healthy_overall = False

if healthy_overall:
    sys.exit(0)
else:
    sys.exit(0)
