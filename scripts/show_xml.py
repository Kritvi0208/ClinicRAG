from pathlib import Path

ROOT = Path("data/extracted")

xml = next(ROOT.rglob("*.xml"))

with open(xml, "r", encoding="utf-8", errors="ignore") as inp, \
     open("sample_xml.txt", "w", encoding="utf-8") as out:

    for i in range(500):
        line = inp.readline()
        if not line:
            break
        out.write(line)

print("Saved sample_xml.txt")