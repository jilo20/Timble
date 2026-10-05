import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
with zipfile.ZipFile(root / "datasets/demo-datasets.zip", "w", zipfile.ZIP_DEFLATED) as archive:
    for path in sorted((root / "datasets/demo").glob("*.csv")):
        archive.write(path, path.name)
print("Created datasets/demo-datasets.zip")
