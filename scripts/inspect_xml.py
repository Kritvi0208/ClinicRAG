from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path("data/extracted")

xml_files = list(ROOT.rglob("*.xml"))

print(f"Found {len(xml_files)} XML files")

xml_file = xml_files[0]

print(f"\nInspecting:\n{xml_file}\n")

tree = ET.parse(xml_file)
root = tree.getroot()

print("=" * 80)
print("ROOT TAG")
print("=" * 80)
print(root.tag)

print("\n" + "=" * 80)
print("FIRST 100 UNIQUE TAGS")
print("=" * 80)

tags = sorted(set(elem.tag for elem in root.iter()))

for tag in tags[:100]:
    print(tag)

print("\nTotal unique tags:", len(tags))