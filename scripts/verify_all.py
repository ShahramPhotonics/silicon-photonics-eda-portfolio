#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
projects = sorted(p for p in root.iterdir() if p.is_dir() and p.name[:2].isdigit())
failed = []
runner = "import runpy; ns=runpy.run_path('tests/test_geometry.py'); [fn() for name, fn in ns.items() if name.startswith('test_') and callable(fn)]"
for project in projects:
    print(f'\n== {project.name} ==', flush=True)
    result = subprocess.run([sys.executable, '-c', runner], cwd=project)
    if result.returncode:
        failed.append(project.name)
if failed:
    raise SystemExit('failed: ' + ', '.join(failed))
print(f'\nVerified {len(projects)} projects.')
