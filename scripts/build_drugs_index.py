import os
import sys
import json
import time
import xml.etree.ElementTree as ET
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.logger import logger

EXTRACTED_DIR = Path("data/extracted")
INDEX_PATH = Path("data/processed/drugs_index.json")
INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)

# HL7 v3 XML Namespace
NS = {'ns': 'urn:hl7-org:v3'}

def parse_xml_file(filepath: Path) -> dict:
    """Parses product name and generic name from SPL XML file."""
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        # Extract product name
        prod_name_el = root.find(".//ns:manufacturedProduct/ns:manufacturedProduct/ns:name", NS)
        prod_name = prod_name_el.text.strip() if prod_name_el is not None and prod_name_el.text else None
        
        # Fallback to document title if product name is missing
        if not prod_name:
            title_el = root.find("ns:title", NS)
            prod_name = title_el.text.strip() if title_el is not None and title_el.text else None
            
        # Extract generic name
        generic_name_el = root.find(".//ns:genericMedicine/ns:name", NS)
        generic_name = generic_name_el.text.strip() if generic_name_el is not None and generic_name_el.text else None
        
        if prod_name:
            rel_path = os.path.relpath(str(filepath), os.getcwd())
            return {
                "name": prod_name,
                "generic": generic_name or "N/A",
                "file": rel_path.replace("\\", "/") # Normalize to forward slashes
            }
    except Exception as e:
        logger.warning(f"Error parsing {filepath.name}: {e}")
    return {}

def main():
    print("Building local index of official FDA drug labels...")
    start_time = time.time()
    
    if not EXTRACTED_DIR.exists():
        print(f"Error: Directory {EXTRACTED_DIR} does not exist.")
        sys.exit(1)
        
    index = {}
    total_processed = 0
    unique_drugs = set()
    
    categories = ["animal", "homeopathic", "otc", "other", "prescription"]
    
    for cat in categories:
        cat_dir = EXTRACTED_DIR / cat
        if not cat_dir.exists():
            continue
            
        print(f"Indexing category '{cat}'...")
        xml_files = list(cat_dir.glob("**/*.xml"))
        print(f"  Found {len(xml_files)} XML files.")
        
        for filepath in xml_files:
            total_processed += 1
            drug_data = parse_xml_file(filepath)
            
            if drug_data:
                drug_data["category"] = cat
                
                # We want to index by lowercase product name
                name_key = drug_data["name"].lower().strip()
                index[name_key] = drug_data
                unique_drugs.add(drug_data["name"])
                
                # Index by generic name as well if present
                if drug_data["generic"] != "N/A":
                    generic_key = drug_data["generic"].lower().strip()
                    if generic_key not in index:
                        index[generic_key] = drug_data
                        
    # Save the index to file
    try:
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=4, ensure_ascii=False)
        duration = time.time() - start_time
        print(f"\nSuccess! Built drugs index in {duration:.2f} seconds.")
        print(f"Total XML files parsed: {total_processed}")
        print(f"Total unique drug names: {len(unique_drugs)}")
        print(f"Total unique index keys (names + generics): {len(index)}")
        print(f"Index file saved at: {INDEX_PATH}")
        logger.info(f"Built drugs index containing {len(index)} keys.")
    except Exception as e:
        print(f"Error saving index file: {e}")
        logger.error(f"Failed to save drugs index: {e}")

if __name__ == "__main__":
    main()
