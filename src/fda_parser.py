import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from src.logger import logger

INDEX_PATH = Path("data/processed/drugs_index.json")
NS = {'ns': 'urn:hl7-org:v3'}

def extract_text(element) -> str:
    """Recursively extracts and formats text from HL7 XML elements into Markdown."""
    if element is None:
        return ""
    
    parts = []
    if element.text:
        parts.append(element.text)
        
    for child in element:
        tag_local = child.tag.split("}")[-1].lower() if "}" in child.tag else child.tag.lower()
        
        if tag_local == "paragraph":
            parts.append("\n" + extract_text(child) + "\n")
        elif tag_local == "list":
            parts.append("\n" + extract_text(child) + "\n")
        elif tag_local == "item":
            parts.append("* " + extract_text(child) + "\n")
        elif tag_local == "br":
            parts.append("\n")
        elif tag_local == "tr":
            parts.append("\n| " + extract_text(child) + " |")
        elif tag_local in ["td", "th"]:
            parts.append(extract_text(child) + " | ")
        else:
            parts.append(extract_text(child))
            
        if child.tail:
            parts.append(child.tail)
            
    text = "".join(parts)
    # Clean up spacing
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text.strip()

def get_fda_drug_info(medicine_name: str) -> dict:
    """Searches the local FDA XML database index and parses the drug label details if found."""
    if not INDEX_PATH.exists():
        logger.warning(f"FDA drugs index does not exist at {INDEX_PATH}.")
        return None
        
    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            index = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load drugs index: {e}")
        return None
        
    med_key = medicine_name.strip().lower()
    
    # Try direct match
    drug_meta = index.get(med_key)
    
    # Try partial matching if direct match fails
    if not drug_meta:
        for key, value in index.items():
            if med_key in key or key in med_key:
                drug_meta = value
                break
                
    if not drug_meta:
        return None
        
    xml_path = Path(drug_meta["file"])
    if not xml_path.exists():
        logger.warning(f"Indexed XML file {xml_path} does not exist on disk.")
        return None
        
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Initialize sections
        extracted = {
            "name": drug_meta["name"],
            "generic": drug_meta["generic"],
            "category": drug_meta["category"],
            "uses": "",
            "side_effects": "",
            "warnings": "",
            "storage": "",
            "interactions": ""
        }
        
        # Scan for sections
        sections_found = root.findall(".//ns:section", NS)
        
        for section in sections_found:
            # Check display name from code element
            code_el = section.find("ns:code", NS)
            display_name = ""
            if code_el is not None:
                display_name = (code_el.attrib.get("displayName") or "").lower()
                
            # Check section title
            title_el = section.find("ns:title", NS)
            title_text = (title_el.text or "").lower() if title_el is not None else ""
            
            # Combine for search match
            match_str = f"{display_name} {title_text}"
            
            # Find the text element
            text_el = section.find("ns:text", NS)
            if text_el is None:
                continue
                
            text_content = extract_text(text_el)
            if not text_content:
                continue
                
            # Map sections
            if "indications" in match_str or "usage" in match_str or "purpose" in match_str:
                extracted["uses"] += "\n\n" + text_content
            elif "adverse reactions" in match_str or "side effects" in match_str or "adverse events" in match_str:
                extracted["side_effects"] += "\n\n" + text_content
            elif "warning" in match_str or "precautions" in match_str or "contraindications" in match_str:
                extracted["warnings"] += "\n\n" + text_content
            elif "dosage" in match_str or "administration" in match_str or "how supplied" in match_str or "storage" in match_str:
                extracted["storage"] += "\n\n" + text_content
            elif "drug interactions" in match_str:
                extracted["interactions"] += "\n\n" + text_content
                
        # Clean up any leading/trailing newlines
        for key in ["uses", "side_effects", "warnings", "storage", "interactions"]:
            extracted[key] = extracted[key].strip()
            if not extracted[key]:
                extracted[key] = "Refer to professional clinical consultation."
                
        return extracted
    except Exception as e:
        logger.error(f"Error parsing FDA XML file {xml_path}: {e}")
        return None
