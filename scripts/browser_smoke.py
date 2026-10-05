"""Run a real browser against a disposable database; leave the user's DB untouched."""

import os
import secrets
import subprocess
import sys
import time
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
work = ROOT / ".work"
work.mkdir(exist_ok=True)
os.environ["SQLITE_PATH"] = str(work / f"browser-{uuid.uuid4().hex}.sqlite3")
os.environ["TIMBLE_TEST_PASSWORD"] = secrets.token_urlsafe(24)
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
sys.path.insert(0, str(ROOT / "backend"))
import django

django.setup()
from django.contrib.auth import get_user_model
from django.core.management import call_command

call_command("migrate", verbosity=0)
get_user_model().objects.create_user(
    username="browser-test", password=os.environ["TIMBLE_TEST_PASSWORD"]
)
flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
processes = []
handles = []
try:
    for command, cwd, name in [
        (
            [sys.executable, "manage.py", "runserver", "127.0.0.1:8000", "--noreload"],
            ROOT / "backend",
            "backend",
        ),
        (
            [
                "node",
                str(ROOT / "frontend/node_modules/vite/bin/vite.js"),
                "--host",
                "127.0.0.1",
                "--port",
                "5173",
                "--strictPort",
            ],
            ROOT / "frontend",
            "frontend",
        ),
    ]:
        log = (work / f"browser-{name}.log").open("w")
        handles.append(log)
        processes.append(
            subprocess.Popen(command, cwd=cwd, stdout=log, stderr=log, creationflags=flags)
        )
    for url in ["http://127.0.0.1:8000/api/session/", "http://127.0.0.1:5173/"]:
        for retry in range(40):
            if any(p.poll() is not None for p in processes):
                raise RuntimeError(
                    "Test server failed to start. Check .work logs; ports must be free."
                )
            try:
                urllib.request.urlopen(url, timeout=1)
                break
            except Exception:
                time.sleep(0.25)
        else:
            raise RuntimeError("Server startup timeout")
    subprocess.run(["node", str(ROOT / "scripts/browser_smoke.mjs")], cwd=ROOT, check=True)
finally:
    for p in processes:
        p.terminate()
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()
    for log in handles:
        log.close()
