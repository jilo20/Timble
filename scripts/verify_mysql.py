"""Run the suite on a uniquely named disposable MySQL database, never the application schema."""

import os
import subprocess
import sys
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
env = os.environ.copy()
env.pop("SQLITE_PATH", None)
env["TIMBLE_TEST_DATABASE"] = "timble_v2_test_" + uuid.uuid4().hex[:12]
subprocess.run(
    [sys.executable, str(root / "backend/manage.py"), "test", "tests", "--verbosity", "1"],
    env=env,
    check=True,
)
