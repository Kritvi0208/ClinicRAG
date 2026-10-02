import os
import re
import html
import xml.etree.ElementTree as ET
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.logger import logger

def clean_html_to_markdown(html_content: str) -> str:
    """Converts MedlinePlus HTML content into clean GitHub-flavored markdown."""
    if not html_content:
        return ""
    
    text = html.unescape(html_content)
    
    # Replace bold and italics
    text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<b>(.*?)</b>', r'**\1**', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<em>(.*?)</em>', r'*\1*', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<i>(.*?)</i>', r'*\1*', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Replace links
    text = re.sub(r'<a\s+[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Replace list items
    text = re.sub(r'<li>\s*(.*?)\s*</li>', r'- \1\n', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Replace block level elements with newlines
    text = re.sub(r'</?(?:ul|ol|p|div|span|h[1-6]|table|tr|td|th)[^>]*>', '\n\n', text, flags=re.IGNORECASE)
    
    # Clean up excess whitespace and blank lines
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def sanitize_filename(name: str) -> str:
    """Converts a topic title into a safe filesystem filename."""
    name = name.lower().strip()
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[\s_-]+', '_', name)
    return name

def build_medlineplus_dataset(xml_path: Path, output_base_dir: Path):
    """Parses official MedlinePlus XML and generates structured Markdown files."""
    if not xml_path.exists():
        logger.error(f"MedlinePlus XML file not found at {xml_path}")
        return
        
    logger.info(f"Parsing MedlinePlus XML from {xml_path}...")
    tree = ET.parse(str(xml_path))
    root = tree.getroot()
    
    topics = root.findall('health-topic')
    logger.info(f"Found {len(topics)} total health topics in XML.")
    
    generated_count = 0
    skipped_count = 0
    
    for topic in topics:
        url = topic.get('url', '')
        # Filter for English topics (exclude Spanish mirror URLs)
        if '/spanish/' in url:
            skipped_count += 1
            continue
            
        title = topic.get('title', '').strip()
        if not title:
            continue
            
        # Extract metadata
        topic_id = topic.get('id', '')
        date_created = topic.get('date-created', '')
        
        # Also called (synonyms)
        also_called = [child.text.strip() for child in topic.findall('also-called') if child.text]
        
        # Primary category groups
        groups = [child.text.strip() for child in topic.findall('group') if child.text]
        primary_group = groups[0] if groups else "General_Health"
        primary_group_folder = sanitize_filename(primary_group).title()
        
        # Mesh headings
        mesh_headings = [child.findtext('descriptor', '').strip() or child.text.strip() for child in topic.findall('mesh-heading') if child is not None]
        mesh_headings = [m for m in mesh_headings if m]
        
        # Related topics
        related_topics = [child.text.strip() for child in topic.findall('related-topic') if child.text]
        
        # Full summary
        summary_elem = topic.find('full-summary')
        summary_html = summary_elem.text if summary_elem is not None and summary_elem.text else ""
        clean_summary = clean_html_to_markdown(summary_html)
        
        if not clean_summary:
            continue
            
        # NIH Reference Sites
        sites = []
        for site in topic.findall('site'):
            s_title = site.get('title', '').strip()
            s_url = site.get('url', '').strip()
            if s_title and s_url:
                sites.append(f"- [{s_title}]({s_url})")
                
        # Build comprehensive markdown content
        target_dir = output_base_dir / primary_group_folder
        target_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{sanitize_filename(title)}.md"
        target_file = target_dir / filename
        
        md_lines = [
            f"# {title}",
            "",
            f"**Source**: MedlinePlus / National Library of Medicine (NIH)",
            f"**Official URL**: {url}",
            f"**Category**: {', '.join(groups) if groups else primary_group}",
        ]
        
        if also_called:
            md_lines.append(f"**Also Known As**: {', '.join(also_called)}")
            
        md_lines.extend([
            "",
            "## Summary and Clinical Guidance",
            clean_summary,
            "",
        ])
        
        if related_topics or mesh_headings:
            md_lines.append("## Related Medical Topics and Terminology")
            if mesh_headings:
                md_lines.append(f"- **Medical Subject Headings (MeSH)**: {', '.join(mesh_headings[:8])}")
            if related_topics:
                md_lines.append(f"- **Related Conditions**: {', '.join(related_topics[:8])}")
            md_lines.append("")
            
        if sites:
            md_lines.append("## Official Health Organization References")
            md_lines.extend(sites[:6])
            md_lines.append("")
            
        target_file.write_text("\n".join(md_lines), encoding="utf-8")
        generated_count += 1

    logger.info(f"Successfully generated {generated_count} verified MedlinePlus medical documents across {output_base_dir} (Skipped {skipped_count} non-English topics).")
    print(f"Extraction Complete! Generated {generated_count} rich MedlinePlus documents.")

if __name__ == "__main__":
    raw_xml = Path("data/raw/mplus_topics_2026-07-15.xml")
    output_dir = Path("data/knowledge_base/medlineplus")
    build_medlineplus_dataset(raw_xml, output_dir)
