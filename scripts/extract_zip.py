# scripts/extract_dailymed_zips.py

from pathlib import Path
import zipfile
import shutil

RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/extracted")

if OUT_DIR.exists():
    shutil.rmtree(OUT_DIR)

OUT_DIR.mkdir(parents=True, exist_ok=True)

zip_count = 0
xml_count = 0
failed = 0

for zip_path in RAW_DIR.rglob("*.zip"):

    relative = zip_path.relative_to(RAW_DIR)
    destination = OUT_DIR / relative.with_suffix("")

    destination.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(destination)

        zip_count += 1

        xml_count += len(list(destination.rglob("*.xml")))

        if zip_count % 100 == 0:
            print(f"Extracted {zip_count} ZIPs...")

    except Exception as e:
        failed += 1
        print(f"Failed: {zip_path.name}")
        print(e)

print("\n===========================")
print(f"ZIPs Extracted : {zip_count}")
print(f"XML Files      : {xml_count}")
print(f"Failed         : {failed}")
print(f"Saved To       : {OUT_DIR}")
print("===========================")