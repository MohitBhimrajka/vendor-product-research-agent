import os
from pathlib import Path
import markdown
from markdown.extensions import fenced_code, tables, toc, attr_list, def_list, footnotes
from markdown.extensions.codehilite import CodeHiliteExtension
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime
import yaml
from bs4 import BeautifulSoup, Comment
import re
from typing import Optional, Dict, List, Tuple, Any
from config import SECTION_ORDER, PDF_CONFIG
from pydantic import BaseModel

class PDFSection(BaseModel):
    """Model for a section in the PDF."""
    id: str
    title: str
    content: str # Raw Markdown content
    html_content: str = "" # Processed HTML content
    intro: str = ""
    key_topics: List[str] = []
    metadata: Dict = {} # YAML frontmatter metadata
    reading_time: int = 0 # Estimated reading time in minutes
    subsections: List[Any] = [] # Subsections of this section

class EnhancedPDFGenerator:
    """Enhanced PDF Generator with better markdown support and styling."""
    
    def __init__(self, template_path: Optional[str] = None):
        """Initialize the PDF generator with an optional custom template path."""
        if template_path:
            self.template_dir = str(Path(template_path).parent)
            self.template_name = Path(template_path).name
        else:
            self.template_dir = str(Path(__file__).parent / 'templates')
            self.template_name = 'enhanced_report_template.html'
        
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        self.template = self.env.get_template(self.template_name)
        
        # Initialize markdown with an expanded set of extensions
        self.md = markdown.Markdown(extensions=[
            'extra',  # Includes tables, fenced_code, footnotes, etc.
            'meta',
            'codehilite',
            'admonition',
            'attr_list',
            'toc',
            'def_list',  # Definition lists
            'footnotes',  # Footnotes support
            'abbr',  # Abbreviation support
            'md_in_html',  # Markdown inside HTML
            'sane_lists',  # Better list handling
            'nl2br',  # Convert newlines to <br> tags for proper line breaks
        ], extension_configs={
            'codehilite': {'css_class': 'highlight', 'guess_lang': False},
            'toc': {'permalink': False},  # Disable permalinks to remove ¶
            'footnotes': {'BACKLINK_TEXT': '↩'}
        })

    def _extract_section_metadata(self, content: str) -> Tuple[Dict, str]:
        """Extract YAML frontmatter and content from a markdown section."""
        metadata = {}
        content = content.lstrip()  # Remove leading whitespace
        if content.startswith('---'):
            try:
                # Split carefully, expecting '---', yaml block, '---', content
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    markdown_content = parts[2]
                    loaded_meta = yaml.safe_load(frontmatter)
                    # Ensure it's a dict, handle empty frontmatter gracefully
                    metadata = loaded_meta if isinstance(loaded_meta, dict) else {}
                    return metadata, markdown_content.strip()
            except (yaml.YAMLError, IndexError, ValueError) as e:
                # If debugging needed: print(f"Failed to parse YAML frontmatter: {e}")
                pass
        return metadata, content.strip()

    def _estimate_reading_time(self, content: str) -> int:
        """Estimate reading time in minutes based on word count."""
        words = len(content.split())
        # Assuming faster reading speed (300 words per minute) and capping at 5 minutes
        estimated_time = min(5, max(1, round(words / 300)))
        return estimated_time

    def _extract_key_topics(self, content: str, max_topics: int = None) -> List[str]:
        """Extract key topics from the content based on headings.
        
        This extracts the subsection headings (h2, h3) from the content to build
        a table of contents.
        
        Args:
            content: The markdown content to extract topics from
            max_topics: Optional maximum number of topics to extract
            
        Returns:
            List of topic strings
        """
        # First convert the markdown to HTML to get proper heading structure
        temp_html = self._convert_markdown_to_html(content)
        soup = BeautifulSoup(temp_html, 'html.parser')
        
        # Only consider h2 and h3 headings for key topics
        headings = soup.find_all(['h2', 'h3'])
        topics = []
        
        # Skip the first h2 if it exists and looks like a title
        starting_index = 0
        if headings and headings[0].name == 'h2':
            # Check if it's the section title (usually matches the section.title)
            starting_index = 1
        
        for heading in headings[starting_index:]:
            # Get the clean text without numbers
            text = heading.get_text().strip()
            
            # Remove any leading numbers like "1. " or "1.1. " that might be present
            clean_text = re.sub(r'^\d+(\.\d+)*\.\s+', '', text)
            
            topics.append(clean_text)
            
            # Only limit if max_topics is specified
            if max_topics and len(topics) >= max_topics:
                break
        
        return topics

    def _create_markdown_processor(self):
        """Create a markdown processor with all necessary extensions."""
        md = markdown.Markdown(extensions=[
            'extra',  # Includes tables, fenced_code, footnotes, etc.
            'meta',
            'codehilite',
            'admonition',
            'attr_list',
            'toc',
            'def_list',  # Definition lists
            'footnotes',  # Footnotes support
            'abbr',  # Abbreviation support
            'md_in_html',  # Markdown inside HTML
            'sane_lists',  # Better list handling
            'nl2br',  # Convert newlines to <br> tags for proper line breaks
        ], extension_configs={
            'codehilite': {'css_class': 'highlight', 'guess_lang': False},
            'toc': {'permalink': False},  # Disable permalinks to remove ¶
            'footnotes': {'BACKLINK_TEXT': '↩'}
        })
        return md
        
    def _process_headings(self, soup):
        """Add classes and IDs to headings for better navigation without visible permalinks."""
        # Process all headings for better styling and navigation
        for h_tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            # Add classes based on heading level
            h_tag['class'] = h_tag.get('class', []) + [f'heading-{h_tag.name}']
            
            # Generate an ID from the heading text if it doesn't have one
            if not h_tag.get('id'):
                heading_text = h_tag.get_text().strip()
                heading_id = re.sub(r'[^\w\s-]', '', heading_text.lower())
                heading_id = re.sub(r'[\s-]+', '-', heading_id)
                h_tag['id'] = heading_id
            
            # We no longer add the visible paragraph symbol anchor
            # Just ensure the heading has an ID for internal linking

    def _cleanup_raw_markdown(self, content: str) -> str:
        """Clean up common LLM formatting issues like literal '\n'."""
        # Replace literal '\n' with actual newlines
        content = content.replace('\\n', '\n')
        # Remove any trailing whitespace
        content = content.strip()
        # Normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        # Ensure consistent spacing around headers
        content = re.sub(r'(\n#{1,6}.*?)(?:\n(?!\n))', r'\1\n\n', content)
        
        # Fix table formatting issues
        # 1. Find potential table patterns (lines with multiple |)
        lines = content.split('\n')
        in_table = False
        table_start_index = -1
        for i, line in enumerate(lines):
            pipe_count = line.count('|')
            
            # Check if this line looks like a table row (has 2+ pipes)
            if pipe_count >= 2:
                # If we weren't in a table before, mark this as the start
                if not in_table:
                    in_table = True
                    table_start_index = i
            # If we were in a table but current line doesn't look like one
            elif in_table:
                # We've reached the end of a table
                in_table = False
                # Process the table we just found
                table_lines = lines[table_start_index:i]
                
                # Check if we have a header row and separator row
                if len(table_lines) >= 2:
                    header_row = table_lines[0]
                    separator_row = table_lines[1]
                    
                    # Fix separator row if needed (it should contain only |, -, and :)
                    if not all(c in '|:-' for c in separator_row.strip()):
                        # Create a proper separator row based on the header
                        cols = header_row.strip('|').split('|')
                        separator_row = '|' + '|'.join(['-' * len(col.strip()) for col in cols]) + '|'
                        table_lines[1] = separator_row
                
                # Update the original lines with fixed table
                lines[table_start_index:i] = table_lines
                
        # Ensure proper spacing around tables
        content = '\n'.join(lines)
        content = re.sub(r'(\n\|.*\|\n)(?!\n)', r'\1\n', content)  # Add newline after table
        content = re.sub(r'\n\n(\|.*\|)', r'\n\1', content)  # Remove extra newline before table
        
        return content

    def _convert_markdown_to_html(self, markdown_content):
        """
        Convert markdown content to HTML with enhanced styling.
        """
        # Pre-process raw table-like structures to ensure proper table rendering
        lines = markdown_content.split('\n')
        processed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            # If line has 2+ pipe characters, it might be part of a table
            if line.count('|') >= 2:
                # This might be the start of a table
                table_lines = [line]
                j = i + 1
                
                # Collect all consecutive table-like lines
                while j < len(lines) and lines[j].count('|') >= 2:
                    table_lines.append(lines[j])
                    j += 1
                    
                # Check if we have at least 2 rows (header + separator)
                if len(table_lines) >= 2:
                    # Ensure we have a proper separator row
                    if not all(c in '|:-' for c in table_lines[1].strip() if c not in ' '):
                        # Create a proper separator row based on header
                        cols = table_lines[0].count('|') - 1
                        table_lines.insert(1, '|' + '|'.join(['---' for _ in range(cols)]) + '|')
                
                # Add table with proper line breaks before and after
                if processed_lines and processed_lines[-1]:
                    processed_lines.append('')  # Empty line before table
                processed_lines.extend(table_lines)
                processed_lines.append('')  # Empty line after table
                i = j
            else:
                processed_lines.append(line)
                i += 1
                
        # Use the pre-processed markdown
        markdown_content = '\n'.join(processed_lines)
        
        # Create the markdown object with all extensions
        md = self._create_markdown_processor()
        
        # Convert markdown to HTML
        html = md.convert(markdown_content)
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check for raw table text that wasn't converted
        # This is a fallback for tables that weren't properly parsed
        for p in soup.find_all('p'):
            text = p.get_text()
            # If paragraph contains multiple | characters in a row-like pattern
            if '|' in text and len(re.findall(r'\|.*\|', text)) > 0:
                table_lines = text.split('\n')
                # Only process if we have at least 2 lines with pipes
                if sum(1 for line in table_lines if '|' in line) >= 2:
                    # This might be a table that wasn't parsed correctly
                    # Create HTML table manually
                    table = soup.new_tag('table')
                    table['class'] = ['enhanced-table', 'zebra-stripe']
                    
                    in_header = True
                    for line in table_lines:
                        if not line.strip() or not '|' in line:
                            continue
                        # Skip separator row (contains only |, -, and :)
                        if all(c in '|:-' for c in line.strip()):
                            in_header = False
                            continue
                            
                        # Process as a table row
                        tr = soup.new_tag('tr')
                        cells = line.strip().split('|')
                        # Skip empty first/last cell if line starts/ends with |
                        if line.startswith('|'):
                            cells = cells[1:]
                        if line.endswith('|'):
                            cells = cells[:-1]
                            
                        for cell in cells:
                            if in_header:
                                td = soup.new_tag('th')
                            else:
                                td = soup.new_tag('td')
                            td.string = cell.strip()
                            tr.append(td)
                        
                        if in_header:
                            thead = soup.new_tag('thead')
                            thead.append(tr)
                            table.append(thead)
                            in_header = False
                        else:
                            if not table.find('tbody'):
                                tbody = soup.new_tag('tbody')
                                table.append(tbody)
                            table.tbody.append(tr)
                    
                    # If we created a valid table, replace the paragraph
                    if table.find('tr'):
                        # Wrap in responsive div
                        table_div = soup.new_tag('div')
                        table_div['class'] = ['table-responsive']
                        table_div.append(table)
                        p.replace_with(table_div)
        
        # Process headings to add anchors for TOC
        self._process_headings(soup)
        
        # Process lists - first-level lists
        for ul in soup.find_all(['ul', 'ol'], recursive=False):
            self._process_list(ul, level=1, soup=soup)
        
        # Find any lists that may be inside other elements (not directly under body)
        for container in soup.find_all(['div', 'blockquote', 'td']):
            for ul in container.find_all(['ul', 'ol'], recursive=False):
                self._process_list(ul, level=1, soup=soup)
        
        # Process tables
        for table in soup.find_all('table'):
            # Wrap table in a responsive div if not already wrapped
            if table.parent.get('class') != ['table-responsive']:
                table_div = soup.new_tag('div')
                table_div['class'] = ['table-responsive']
                table.wrap(table_div)
            
            # Add enhanced styling to table
            table['class'] = table.get('class', []) + ['enhanced-table']
            
            # Add zebra striping and header styling
            if table.find('thead'):
                table['class'] = table['class'] + ['has-header']
            table['class'] = table['class'] + ['zebra-stripe']
            
            # Align number cells to the right
            for td in table.find_all('td'):
                if td.string and td.string.strip().replace('.', '', 1).isdigit():
                    td['class'] = td.get('class', []) + ['text-right']
        
        # Process definition lists
        for dl in soup.find_all('dl'):
            dl['class'] = dl.get('class', []) + ['definition-list']
            for dt in dl.find_all('dt'):
                dt['class'] = dt.get('class', []) + ['term']
            for dd in dl.find_all('dd'):
                dd['class'] = dd.get('class', []) + ['definition']
        
        # Process footnotes
        footnotes_div = soup.find('div', class_='footnote')
        if footnotes_div:
            footnotes_div['class'] = ['enhanced-footnotes']
            for ol in footnotes_div.find_all('ol'):
                ol['class'] = ol.get('class', []) + ['footnote-list']
                for li in ol.find_all('li'):
                    li['class'] = li.get('class', []) + ['footnote-item']
        
        return str(soup)

    def _process_list(self, list_tag, level=1, soup=None):
        """
        Process a list and its nested lists recursively.
        
        Args:
            list_tag: The list tag (ul or ol) to process
            level: The current nesting level
            soup: The BeautifulSoup object for creating new tags
        """
        # Add appropriate classes based on level
        if level == 1:
            list_tag['class'] = list_tag.get('class', []) + ['enhanced-list']
        else:
            list_tag['class'] = list_tag.get('class', []) + ['nested-list']
            
            # For deep nesting (3+), add a level indicator class
            if level > 2:
                list_tag['class'] = list_tag['class'] + [f'level-{level}']
        
        # Process all list items at this level
        for li in list_tag.find_all('li', recursive=False):
            if level == 1:
                li['class'] = li.get('class', []) + ['enhanced-list-item']
            else:
                li['class'] = li.get('class', []) + ['nested-list-item']
                
                # For deep nesting (3+), add a level indicator class
                if level > 2:
                    li['class'] = li['class'] + [f'item-level-{level}']
            
            # Process nested lists recursively
            for nested_list in li.find_all(['ul', 'ol'], recursive=False):
                self._process_list(nested_list, level=level+1, soup=soup)

    def _generate_toc(self, sections):
        """Generate a properly formatted and hyperlinked table of contents."""
        if not sections:
            return ""
            
        toc_html = '<div class="toc-container">\n'
        toc_html += '<h2 class="toc-title">Table of Contents</h2>\n'
        toc_html += '<div class="toc-entries">\n'
        
        for idx, section in enumerate(sections, 1):
            # Create section entry with proper hyperlink
            # Use section-{idx} as the anchor, which matches the IDs in the template
            section_id = f"section-{section.id}"
            section_title = section.title.strip()
            
            toc_html += f'<div class="toc-entry">\n'
            toc_html += f'  <a href="#{section_id}" class="toc-link">{section_title}</a>\n'
            
            # Handle subsections if they exist (using hasattr to check)
            if hasattr(section, 'subsections') and section.subsections:
                toc_html += '  <div class="toc-subsections">\n'
                
                for sub_idx, subsection in enumerate(section.subsections, 1):
                    subsection_id = f"{section_id}-sub-{sub_idx}"
                    subsection_title = subsection.title.strip()
                    
                    toc_html += f'    <div class="toc-subsection">\n'
                    toc_html += f'      <a href="#{subsection_id}" class="toc-sublink">{subsection_title}</a>\n'
                    toc_html += f'    </div>\n'
                
                toc_html += '  </div>\n'
            
            toc_html += '</div>\n'
        
        toc_html += '</div>\n</div>\n'
        
        return toc_html
        
    def _process_sections(self, sections):
        """
        Process sections for the report, adding IDs and processing markdown into HTML.
        """
        processed_sections = []
        section_counter = 0
        
        for section in sections:
            section_counter += 1
            # Ensure the section ID is consistent with what the template expects
            if not hasattr(section, "id") or not section.id:
                section.id = f"section-{section_counter}"
            
            # Extract metadata, main content and sources separately
            metadata, main_content, _ = self._extract_metadata_and_split_sources(section.content)
            
            # Update section with extracted metadata
            section.metadata.update(metadata)
            
            # Process the main content of the section
            if main_content:
                # Extract key topics for the section cover
                section.key_topics = self._extract_key_topics(main_content, max_topics=5)
                
                # Estimate reading time
                section.reading_time = self._estimate_reading_time(main_content)
                
                # Extract introduction paragraph
                section.intro = self._extract_intro(main_content)
                
                # Convert main content to HTML - this now includes sources
                full_html = self._convert_markdown_to_html(main_content)
                
                # Set the HTML content for the section
                section.html_content = full_html
            
            processed_sections.append(section)
        
        return processed_sections

    def _extract_intro(self, content: str) -> str:
        """Extract the introduction paragraph from the content."""
        # Split content into lines
        lines = content.strip().split('\n')
        intro_lines = []
        
        # Skip metadata and empty lines at the start
        i = 0
        while i < len(lines) and (not lines[i].strip() or ':' in lines[i]):
            i += 1
            
        # Skip headers
        while i < len(lines) and lines[i].strip().startswith('#'):
            i += 1
            
        # Collect lines until we hit a header or end of content
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('#') or not line:
                break
            intro_lines.append(line)
            i += 1
            
        if not intro_lines:
            return "<p>This section provides detailed analysis and insights.</p>"
            
        # Convert the intro lines to HTML with full markdown processing
        intro_content = '\n\n'.join(intro_lines)  # Use double newlines for paragraphs
        
        # Use the full markdown processor with all extensions
        self.md.reset()
        intro_html = self.md.convert(intro_content)
        
        return intro_html

    def generate_pdf(self, sections_data: List[PDFSection], output_path: str, metadata: Dict) -> Path:
        """Generate a PDF report from the provided section data and metadata."""
        processed_sections = self._process_sections(sections_data)

        # Get paths for logo and favicon
        template_dir = Path(self.template_dir)
        assets_dir = template_dir / 'assets'
        os.makedirs(assets_dir, exist_ok=True)
        
        # Directly use the assets in templates/assets
        logo_path = assets_dir / 'supervity_logo.png'
        favicon_path = assets_dir / 'supervity_favicon.png'
        
        # Use proper URLs for WeasyPrint
        logo_url = f"templates/assets/supervity_logo.png"
        favicon_url = f"templates/assets/supervity_favicon.png"
        
        print(f"Using logo URL: {logo_url}")
        print(f"Using favicon URL: {favicon_url}")

        # Prepare template context
        context = {
            'company_name': metadata.get('company', 'Company'),
            'language': metadata.get('language', 'English'),
            'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sections': processed_sections,
            'toc': self._generate_toc(processed_sections),
            'metadata': metadata,
            'logo_path': logo_url,
            'favicon_path': favicon_url
        }

        # Render template and generate PDF
        final_html_content = self.template.render(**context)

        try:
            # Get the base directory for proper resource resolution
            base_url = os.path.dirname(os.path.abspath(__file__))
            print(f"Using base URL: {base_url}")
            
            html = HTML(string=final_html_content, base_url=base_url)
            # Define font config (consider making this configurable)
            font_config = FontConfiguration()
            css = CSS(string='''
                @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&family=Noto+Sans:wght@400;700&display=swap');
                
                /* Base styles */
                body { 
                    font-family: 'Noto Sans', 'Noto Sans JP', sans-serif;
                    line-height: 1.6;
                }
                
                /* Table of contents styles */
                .toc-container {
                    margin: 1em 0 2em 0;
                }
                
                .toc-title {
                    font-size: 18pt;
                    color: #000b37;
                    margin-bottom: 1.5em;
                    text-align: center;
                    font-weight: bold;
                    letter-spacing: 0.05em;
                    border-bottom: none;
                }
                
                .toc-entries {
                    padding: 0 1em;
                }
                
                .toc-entry {
                    margin: 0.8em 0;
                    position: relative;
                    display: flex;
                    align-items: baseline;
                    justify-content: space-between;
                }
                
                .toc-entry::after {
                    content: "";
                    position: absolute;
                    bottom: 0.5em;
                    left: 0;
                    right: 0;
                    border-bottom: 1px dotted #c7c7c7;
                    z-index: 1;
                }
                
                .toc-link {
                    font-weight: bold;
                    font-size: 12pt;
                    color: #000b37;
                    text-decoration: none;
                    background: white;
                    padding-right: 0.5em;
                    position: relative;
                    z-index: 2;
                    display: inline-block;
                    width: auto;
                    max-width: calc(100% - 4em);
                }
                
                .toc-link::after {
                    content: target-counter(attr(href), page);
                    position: absolute;
                    right: -4em;
                    background: white;
                    padding: 0 0.5em;
                    color: #474747;
                    z-index: 2;
                    font-weight: normal;
                }
                
                .toc-subsections {
                    margin-left: 2em;
                    margin-top: 0.5em;
                    width: 100%;
                }
                
                .toc-subsection {
                    margin: 0.4em 0;
                    position: relative;
                    display: flex;
                    align-items: baseline;
                    justify-content: space-between;
                }
                
                .toc-subsection::after {
                    content: "";
                    position: absolute;
                    bottom: 0.3em;
                    left: 0;
                    right: 0;
                    border-bottom: 1px dotted #c7c7c7;
                    z-index: 1;
                }
                
                .toc-sublink {
                    font-size: 10pt;
                    color: #474747;
                    text-decoration: none;
                    background: white;
                    padding-right: 0.5em;
                    position: relative;
                    z-index: 2;
                    display: inline-block;
                    width: auto;
                    max-width: calc(100% - 3em);
                }
                
                .toc-sublink::after {
                    content: target-counter(attr(href), page);
                    position: absolute;
                    right: -3em;
                    background: white;
                    padding: 0 0.5em;
                    color: #474747;
                    z-index: 2;
                    font-weight: normal;
                }
                
                /* Enhanced list styles */
                .enhanced-list {
                    list-style-type: disc;
                    margin: 0.8em 0;
                    padding-left: 1.5em;
                    line-height: 1.4;
                }
                
                .enhanced-list-item {
                    margin-bottom: 0.4em;
                    position: relative;
                    padding-left: 0.2em;
                }
                
                .nested-list {
                    list-style-type: circle;
                    margin: 0.4em 0 0.4em 0.5em;
                    padding-left: 1.5em;
                }
                
                .nested-list-item {
                    margin-bottom: 0.3em;
                }
                
                /* Force proper bullet rendering */
                ul.enhanced-list > li::marker {
                    color: #474747;
                    font-size: 0.9em;
                }
                
                ul.nested-list > li::marker {
                    color: #7f8c8d;
                    font-size: 0.85em;
                }
                
                /* Additional styling for ordered lists */
                ol.enhanced-list {
                    list-style-type: decimal;
                }
                
                ol.nested-list {
                    list-style-type: lower-alpha;
                }
                
                ol.nested-list ol.nested-list {
                    list-style-type: lower-roman;
                }
                
                /* Handle mixed nested list types */
                ul.enhanced-list ol.nested-list {
                    list-style-type: decimal;
                }
                
                ol.enhanced-list ul.nested-list {
                    list-style-type: disc;
                }
                
                /* Deeply nested list styles (3+ levels) */
                .level-3 {
                    margin-left: 0.3em !important;
                    padding-left: 1.2em !important;
                }
                
                ul.level-3 {
                    list-style-type: square;
                }
                
                ol.level-3 {
                    list-style-type: lower-roman;
                }
                
                .level-4 {
                    margin-left: 0.2em !important;
                    padding-left: 1em !important;
                }
                
                ul.level-4 {
                    list-style-type: none;
                }
                
                ul.level-4 > li:before {
                    content: "–";
                    position: absolute;
                    left: -0.8em;
                }
                
                ol.level-4 {
                    list-style-type: decimal;
                }
                
                /* Enhanced table styles */
                .table-responsive {
                    margin: 0.75em 0;
                    width: 100%;
                }
                
                .enhanced-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 1em;
                }
                
                .enhanced-table.has-header thead {
                    background-color: #f5f5f5;
                }
                
                .enhanced-table.zebra-stripe tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
                
                .enhanced-table th,
                .enhanced-table td {
                    padding: 0.75em;
                    border: 1px solid #ddd;
                }
                
                .enhanced-table .text-right {
                    text-align: right;
                }
                
                .enhanced-table .text-center {
                    text-align: center;
                }
                
                /* Table figure and caption styles */
                .table-figure {
                    margin: 2em 0;
                }
                
                .table-figure figcaption {
                    font-style: italic;
                    text-align: center;
                    margin-top: 0.5em;
                    color: #666;
                }
                
                /* Definition list styles */
                .definition-list {
                    margin: 1em 0;
                    padding: 0;
                }
                
                .definition-list .term {
                    font-weight: bold;
                    margin-top: 1em;
                }
                
                .definition-list .definition {
                    margin-left: 2em;
                    margin-bottom: 1em;
                }
                
                /* Footnote styles */
                .enhanced-footnotes {
                    margin-top: 2em;
                    padding-top: 1em;
                    border-top: 1px solid #ddd;
                }
                
                .enhanced-footnotes::before {
                    content: "Footnotes";
                    font-weight: bold;
                    display: block;
                    margin-bottom: 1em;
                }
                
                .footnote-item {
                    font-size: 0.9em;
                    color: #666;
                    margin-bottom: 0.5em;
                }
                
                .footnote-item a {
                    color: #0066cc;
                    text-decoration: none;
                }
                
                .footnote-item a:hover {
                    text-decoration: underline;
                }
                
                /* Utility classes */
                .text-right { text-align: right; }
                .text-center { text-align: center; }
                
                /* Long URL display */
                a.long-url {
                    word-wrap: break-word;
                    font-size: 0.9em;
                    color: #7f8c8d;
                    font-family: monospace;
                }
            ''', font_config=font_config)

            html.write_pdf(
                output_path,
                stylesheets=[css],  # Apply CSS
                presentational_hints=True,  # Allow HTML styling attributes
                font_config=font_config
            )
            print(f"PDF generated successfully: {output_path}")
            return Path(output_path)
        except Exception as e:
            print(f"Error during WeasyPrint PDF generation: {e}")
            # Optionally write the final HTML to a file for debugging
            debug_html_path = Path(output_path).with_suffix('.debug.html')
            with open(debug_html_path, 'w', encoding='utf-8') as f_debug:
                f_debug.write(final_html_content)
            print(f"Debug HTML saved to: {debug_html_path}")
            raise  # Re-raise the exception

    def _extract_metadata_and_split_sources(self, raw_content: str) -> Tuple[Dict, str, str]:
        """Extract YAML frontmatter only, keeping content intact.
        
        This function:
        1. Extracts any YAML frontmatter at the beginning of the content
        2. Returns the metadata and the full content
        3. No longer splits sources from main content
        """
        metadata = {}
        main_content = ""
        sources_content = "" # This will always remain empty now

        cleaned_content = self._cleanup_raw_markdown(raw_content)

        # 1. Extract YAML frontmatter (if present)
        content_to_process = cleaned_content
        if cleaned_content.strip().startswith('---'):
            parts = cleaned_content.split('---', 2)
            if len(parts) >= 3:
                try:
                    frontmatter = parts[1]
                    loaded_meta = yaml.safe_load(frontmatter)
                    metadata = loaded_meta if isinstance(loaded_meta, dict) else {}
                    content_to_process = parts[2].strip()
                except yaml.YAMLError:
                    print(f"Could not parse YAML frontmatter. Treating as content.")
                    content_to_process = cleaned_content # Process everything if YAML fails

        # 2. NO LONGER SPLITTING SOURCES - All remaining content is main_content
        main_content = content_to_process
        sources_content = "" # Explicitly set to empty

        return metadata, main_content, sources_content

def process_markdown_files(base_dir: Path, company_name: str, language: str, template_path: Optional[str] = None) -> Optional[Path]:
    """Process all markdown files in the markdown directory and generate a PDF."""
    markdown_dir = base_dir / 'markdown'
    pdf_dir = base_dir / 'pdf'
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Collect sections from markdown files
    sections = []
    
    # Use SECTION_ORDER to determine the correct order of sections
    for section_id, section_title in SECTION_ORDER:
        file_path = markdown_dir / f"{section_id}.md"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if content.strip():  # Only include non-empty sections
                section = PDFSection(
                    id=section_id,
                    title=section_title,
                    content=content
                )
                sections.append(section)
    
    if not sections:
        print("No markdown files found or all files were empty.")
        return None
    
    # Generate PDF
    pdf_generator = EnhancedPDFGenerator(template_path)
    output_path = pdf_dir / f"{company_name}_{language}_Report.pdf"
    
    return pdf_generator.generate_pdf(
        sections, 
        str(output_path), 
        {
            'title': f"{company_name} {language} Report",
            'company': company_name,
            'language': language
        }
    ) 