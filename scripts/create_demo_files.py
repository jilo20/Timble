import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from apps.bulk_import.schema import FILES, SCHEMAS

rows = {k: [] for k in SCHEMAS}
rows["programs"] = [["DEMO-CS", "Demonstration Computer Science", 4, True]]
rows["subjects"] = [
    ["DEMO-FOUND", "Programming foundations", True],
    ["DEMO-ALG", "Algorithms", True],
]
rows["program-subjects"] = [
    ["DEMO-CS", "DEMO-FOUND", 1, 3, 1, 0, 1, 0, "LECTURE", "LAB", False, True],
    ["DEMO-CS", "DEMO-ALG", 2, 3, 2, 3, 1, 1, "LECTURE", "LAB", False, True],
]
rows["prerequisites"] = [["DEMO-CS", "DEMO-ALG", "DEMO-FOUND"]]
rows["block-sections"] = [
    ["DEMO-CS", year, letter, 30, True] for year in [1, 2] for letter in "ABCD"
]
rows["faculty"] = [
    ["DEMO-F1", "Alex", "", "Reyes", "FULL_TIME", 30, True],
    ["DEMO-F2", "Sam", "", "Cruz", "FULL_TIME", 30, True],
]
rows["faculty-teaching-rules"] = [
    ["DEMO-F1", "DEMO-FOUND", "MUST_TEACH"],
    ["DEMO-F2", "DEMO-FOUND", "CANNOT"],
    ["DEMO-F1", "DEMO-ALG", "CAN"],
    ["DEMO-F2", "DEMO-ALG", "MUST_TEACH"],
]
rows["rooms"] = [
    ["DEMO-L30", "LECTURE", 30, True],
    ["DEMO-L40", "LECTURE", 40, True],
    ["DEMO-C30", "LAB", 30, True],
]
rows["subject-aliases"] = [["DEMO PROGRAMMING", "DEMO-FOUND"]]
rows["historical-enrollment"] = [["2025-2026", "DEMO-CS", "DEMO PROGRAMMING", 100]]
folder = ROOT / "datasets" / "demo"
folder.mkdir(parents=True, exist_ok=True)
for kind, data in rows.items():
    with (folder / (FILES.get(kind, kind) + ".csv")).open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(SCHEMAS[kind].split(","))
        writer.writerows(data)
(folder / "README.md").write_text(
    "# Synthetic defense dataset\nNot real institutional data. Forecast 2026-2027 with capacity 30 and a user-entered 0.05 failure assumption. Foundations: 100 students, four sections. Algorithms: 100 Ã— (1 âˆ’ 0.05) = 95, four sections. All data are prefixed DEMO. Import with `manage.py load_demo`.\n",
    encoding="utf-8",
)

import runpy

runpy.run_path(str(ROOT / "scripts/package_demo.py"))
