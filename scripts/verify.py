"""Run backend verification without modifying the configured application database."""

import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
env = os.environ.copy()
env["SQLITE_PATH"] = str(root / ".work/verification.sqlite3")
for args in [
    ["test", "tests", "--verbosity", "1"],
    ["check"],
    ["makemigrations", "--check", "--dry-run"],
]:
    subprocess.run([sys.executable, str(root / "backend/manage.py"), *args], env=env, check=True)
