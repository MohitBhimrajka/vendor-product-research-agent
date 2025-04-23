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
from config import PDF_CONFIG
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
        """Generate a PDF report from processed markdown sections."""
        try:
            # Process all sections to extract metadata and convert to HTML
            processed_sections = self._process_sections(sections_data)
            
            # Render the HTML template with the processed sections
            rendered_html = self.template.render(
                title=metadata.get('title', 'Generated Report'),
                identifier=metadata.get('identifier', ''),
                language=metadata.get('language', 'English'),
                sections=processed_sections,
                report_type=metadata.get('report_type', 'Report'),
                generation_timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                toc=self._generate_toc(processed_sections),
                **metadata  # Pass along all other metadata
            )
            
            # Save the HTML to a file for debugging if needed
            output_html_path = Path(output_path).with_suffix('.html')
            with open(output_html_path, 'w', encoding='utf-8') as f:
                f.write(rendered_html)
            
            # Function to generate the PDF using WeasyPrint
            return self._generate_pdf_from_html(rendered_html, output_path, metadata)
            
        except Exception as e:
            print(f"Error generating PDF: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _generate_pdf_from_html(self, html_content: str, output_path: str, metadata: Dict) -> Path:
        """Generate a PDF from the rendered HTML content."""
        try:
            # Configure fonts
            font_config = FontConfiguration()
            
            # Create the HTML object for WeasyPrint
            html = HTML(string=html_content)
            
            # Create the PDF
            css_string = """
                @page {
                    margin: 1cm 1.5cm;
                    @top-center {
                        content: string(title);
                        font-size: 9pt;
                        color: #666;
                    }
                    @bottom-center {
                        content: "Page " counter(page) " of " counter(pages);
                        font-size: 9pt;
                        color: #666;
                    }
                }
                
                /* Title styling for running header */
                h1 {
                    string-set: title content();
                    page-break-before: always;
                    break-before: page;
                }
                
                /* Fix first page not having page break */
                section:first-of-type h1 {
                    page-break-before: avoid;
                    break-before: avoid;
                }
                
                /* Typography */
                body {
                    font-family: "Roboto", "Helvetica Neue", Helvetica, Arial, sans-serif;
                    line-height: 1.5;
                    color: #333;
                    font-size: 11pt;
                    margin: 0;
                    padding: 0;
                }
                
                /* Section styling */
                section {
                    margin-bottom: 1.5em;
                }
                
                /* Headings */
                h1, h2, h3, h4, h5, h6 {
                    font-family: "Roboto", "Helvetica Neue", Helvetica, Arial, sans-serif;
                    font-weight: 500;
                    line-height: 1.2;
                    margin-top: 1.5em;
                    margin-bottom: 0.75em;
                    color: #205493;
                }
                
                h1 {
                    font-size: 22pt;
                    color: #112e51;
                    border-bottom: 2px solid #112e51;
                    padding-bottom: 0.2em;
                }
                
                h2 {
                    font-size: 18pt;
                    border-bottom: 1px solid #205493;
                    padding-bottom: 0.1em;
                }
                
                h3 {
                    font-size: 15pt;
                    color: #323a45;
                }
                
                h4 {
                    font-size: 13pt;
                    color: #323a45;
                }
                
                h5, h6 {
                    font-size: 11pt;
                    color: #323a45;
                }
                
                /* Cover page styling */
                .cover-page {
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    height: 297mm; /* A4 height */
                    width: 210mm; /* A4 width */
                    text-align: center;
                    padding: 2cm;
                }
                
                .cover-page h1 {
                    font-size: 28pt;
                    text-align: center;
                    color: #112e51;
                    border-bottom: none;
                    margin-bottom: 0.5cm;
                }
                
                .cover-page .subtitle {
                    font-size: 16pt;
                    color: #205493;
                    margin-bottom: 2cm;
                    font-weight: 300;
                }
                
                .cover-page .report-meta {
                    margin-top: 2cm;
                    font-size: 12pt;
                    color: #5b616b;
                }
                
                /* Table of Contents */
                .toc {
                    margin: 2cm 0;
                    page-break-after: always;
                }
                
                .toc h2 {
                    font-size: 18pt;
                    text-align: center;
                    margin-bottom: 1cm;
                    border-bottom: none;
                }
                
                .toc ul {
                    list-style-type: none;
                    padding-left: 0;
                }
                
                .toc ul ul {
                    padding-left: 1.5em;
                }
                
                .toc li {
                    margin-bottom: 0.5em;
                    padding-bottom: 0.25em;
                    border-bottom: 1px dotted #aeb0b5;
                }
                
                .toc a {
                    text-decoration: none;
                    color: #205493;
                }
                
                /* Links */
                a {
                    color: #0071bc;
                    text-decoration: underline;
                }
                
                /* Lists */
                ul, ol {
                    margin-top: 0.5em;
                    margin-bottom: 1em;
                    padding-left: 2em;
                }
                
                li {
                    margin-bottom: 0.25em;
                }
                
                /* Tables */
                table {
                    width: 100%;
                    margin: 1em 0;
                    border-collapse: collapse;
                    font-size: 10pt;
                }
                
                th {
                    background-color: #f1f1f1;
                    font-weight: 600;
                    text-align: left;
                    vertical-align: middle;
                    padding: 0.5em;
                    border: 1px solid #5b616b;
                }
                
                td {
                    padding: 0.5em;
                    border: 1px solid #5b616b;
                    vertical-align: top;
                }
                
                /* Alternating row colors */
                tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
                
                /* Code blocks */
                pre {
                    background-color: #f1f1f1;
                    border: 1px solid #d6d7d9;
                    border-radius: 3px;
                    padding: 1em;
                    font-family: Monaco, Consolas, "Courier New", monospace;
                    font-size: 9pt;
                    line-height: 1.4;
                    overflow-x: auto;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }
                
                code {
                    font-family: Monaco, Consolas, "Courier New", monospace;
                    font-size: 90%;
                    padding: 0.2em 0.4em;
                    background-color: #f1f1f1;
                    border-radius: 3px;
                }
                
                /* Blockquotes */
                blockquote {
                    margin: 1em 0;
                    padding: 0.5em 1em;
                    border-left: 4px solid #205493;
                    background-color: #f1f1f1;
                    font-style: italic;
                }
                
                blockquote p:first-child {
                    margin-top: 0;
                }
                
                blockquote p:last-child {
                    margin-bottom: 0;
                }
                
                /* Horizontal rule */
                hr {
                    border: none;
                    height: 1px;
                    background-color: #aeb0b5;
                    margin: 2em 0;
                }
                
                /* Images */
                img {
                    max-width: 100%;
                    height: auto;
                    display: block;
                    margin: 1em auto;
                }
                
                /* Figure and captions */
                figure {
                    margin: 1.5em 0;
                    text-align: center;
                }
                
                figcaption {
                    font-size: 90%;
                    color: #5b616b;
                    margin-top: 0.5em;
                    font-style: italic;
                }
                
                /* Notes and warnings */
                .note, .warning, .info, .tip {
                    margin: 1em 0;
                    padding: 1em;
                    border-left: 4px solid;
                    background-color: #f9f9f9;
                }
                
                .note {
                    border-color: #02bfe7;
                }
                
                .warning {
                    border-color: #fdb81e;
                }
                
                .info {
                    border-color: #205493;
                }
                
                .tip {
                    border-color: #4aa564;
                }
                
                /* Key metrics */
                .key-metrics {
                    display: flex;
                    flex-wrap: wrap;
                    margin: 1em 0;
                    justify-content: space-between;
                }
                
                .metric-card {
                    width: 30%;
                    margin-bottom: 1em;
                    padding: 1em;
                    background-color: #f1f1f1;
                    border-left: 4px solid #205493;
                }
                
                .metric-title {
                    font-weight: 600;
                    margin-bottom: 0.5em;
                    color: #323a45;
                }
                
                .metric-value {
                    font-size: 18pt;
                    font-weight: 300;
                    color: #205493;
                }
                
                /* Category boxes */
                .category-box {
                    padding: 1em;
                    margin: 1em 0;
                    background-color: #f1f1f1;
                    border: 1px solid #d6d7d9;
                    border-radius: 4px;
                }
                
                .category-title {
                    font-size: 14pt;
                    font-weight: 500;
                    color: #205493;
                    margin-bottom: 0.5em;
                }
                
                /* Footnotes */
                .footnotes {
                    margin-top: 2em;
                    border-top: 1px solid #aeb0b5;
                    padding-top: 1em;
                }
                
                .footnote-item {
                    font-size: 9pt;
                    color: #5b616b;
                    margin-bottom: 0.5em;
                }
                
                .footnote-item a {
                    color: #0071bc;
                    text-decoration: none;
                }
                
                .footnote-item a:hover {
                    text-decoration: underline;
                }
                
                /* Utility classes */
                .text-center {
                    text-align: center;
                }
                
                .text-right {
                    text-align: right;
                }
                
                .text-small {
                    font-size: 90%;
                }
                
                .text-large {
                    font-size: 110%;
                }
                
                .font-light {
                    font-weight: 300;
                }
                
                .font-semibold {
                    font-weight: 600;
                }
                
                .font-bold {
                    font-weight: 700;
                }
                
                .bg-light {
                    background-color: #f9f9f9;
                }
                
                .bg-highlight {
                    background-color: #f1f1f1;
                }
                
                /* Page breaks */
                .page-break {
                    page-break-before: always;
                    break-before: page;
                }
                
                /* Avoid breaking these elements across pages */
                h1, h2, h3, h4, h5, h6, table, figure, .note, .warning, .info, .tip {
                    page-break-inside: avoid;
                }
                
                /* Avoid page breaks after headings */
                h1, h2, h3, h4, h5, h6 {
                    page-break-after: avoid;
                }
                
                /* Long URL display */
                .long-url {
                    word-wrap: break-word;
                    font-size: 9pt;
                    color: #5b616b;
                    font-family: Monaco, Consolas, "Courier New", monospace;
                }

                /* Special sections */
                .executive-summary {
                    background-color: #f1f1f1;
                    padding: 1em;
                    margin: 1em 0;
                    border-left: 4px solid #112e51;
                }
                
                /* Report sections */
                .section-intro {
                    font-style: italic;
                    color: #323a45;
                    margin-bottom: 1em;
                }
                
                /* Section metadata */
                .section-meta {
                    margin-bottom: 1em;
                    font-size: 9pt;
                    color: #5b616b;
                }
                
                /* Key topics list */
                .key-topics {
                    margin: 1em 0;
                    padding: 0.5em 1em;
                    background-color: #f1f1f1;
                    border-left: 2px solid #205493;
                }
                
                .key-topics h4 {
                    margin-top: 0;
                    margin-bottom: 0.5em;
                    color: #205493;
                }
                
                .key-topics ul {
                    margin: 0;
                    padding-left: 1.5em;
                }
            """
            
            # Apply CSS and generate the PDF
            css = CSS(string=css_string, font_config=font_config)
            
            html.write_pdf(
                output_path,
                stylesheets=[css],
                presentational_hints=True,
                font_config=font_config
            )
            print(f"PDF generated successfully: {output_path}")
            return Path(output_path)
            
        except Exception as e:
            print(f"Error during PDF generation: {e}")
            # Save the HTML for debugging
            debug_html_path = Path(output_path).with_suffix('.debug.html')
            with open(debug_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"Debug HTML saved to: {debug_html_path}")
            raise

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

def process_markdown_files(
    base_dir: Path, 
    identifier: str, 
    report_type_name: str, 
    section_order: Optional[List[Tuple[str, str]]] = None, 
    template_path: Optional[str] = None,
    stages: Optional[List[str]] = None,
    stage_dirs: Optional[Dict[str, Path]] = None,
    filtered_vendors: Optional[List[str]] = None,  # Added for product reports
    deep_dive_vendors: Optional[List[str]] = None,  # Added for final product reports
    deep_dive_dirs: Optional[Dict[str, str]] = None  # Mapping of vendor names to their deep dive base dirs
) -> Optional[Path]:
    """
    Process markdown files based on a given section order and generate a PDF.
    
    Args:
        base_dir: The base directory containing markdown and pdf folders
        identifier: The vendor name or product category
        report_type_name: Used for the PDF filename (e.g., "VendorReport", "ProductReport")
        section_order: The list of (id, title) tuples to determine order and titles
        template_path: Optional custom template path
        stages: List of stage names to process in order (e.g., ['research', 'analysis', 'final'])
        stage_dirs: Dictionary mapping stage names to directory paths, if stages are in different locations
        filtered_vendors: List of filtered vendors for product reports
        deep_dive_vendors: List of vendors for which deep dives were executed
        deep_dive_dirs: Mapping of vendor names to their deep dive base directories
        
    Returns:
        Path to the generated PDF or None if no sections were found
    """
    pdf_dir = base_dir / 'pdf'
    os.makedirs(pdf_dir, exist_ok=True)

    sections = []
    
    # Use section_order if provided, otherwise fall back to SECTION_ORDER from config
    if section_order is None:
        section_order = SECTION_ORDER
    
    print(f"Using section order: {[s[0] for s in section_order]}")

    if not section_order:
         print("Error: No section order provided or available in config.")
         return None
    
    # If no stages specified, use the default single-stage approach with markdown dir in base_dir
    if not stages:
        markdown_dirs = [base_dir / 'markdown']
        print(f"Looking for markdown files in: {markdown_dirs[0]}")
    else:
        # Handle multi-stage processing
        markdown_dirs = []
        for stage in stages:
            if stage_dirs and stage in stage_dirs:
                # Use the provided custom directory for this stage
                stage_path = stage_dirs[stage]
                if not stage_path.is_absolute():
                    stage_path = base_dir / stage_path
            else:
                # Default to base_dir/stage_name/markdown
                stage_path = base_dir / stage / 'markdown'
            
            markdown_dirs.append(stage_path)
            print(f"Looking for {stage} stage markdown files in: {stage_path}")

    # Special handling for vendor deep dives if specified
    deep_dive_sections = []
    if deep_dive_vendors and len(deep_dive_vendors) > 0:
        print(f"Processing deep dives for vendors: {deep_dive_vendors}")
        
        vendor_section_order = None
        # Try to import VENDOR_SECTION_ORDER from config for organizing deep dive content
        try:
            from config import VENDOR_SECTION_ORDER
            vendor_section_order = VENDOR_SECTION_ORDER
            print(f"Using VENDOR_SECTION_ORDER for deep dive content organization")
        except ImportError:
            print("Could not import VENDOR_SECTION_ORDER from config, will use alphabetical ordering")
        
        for vendor_name in deep_dive_vendors:
            # Clean the vendor name for use in directory names
            clean_vendor_name = re.sub(r'[\\/*?:"<>| ]', "_", vendor_name)
            deep_dive_dir = None
            
            # First try to get the path from the deep_dive_dirs mapping if available
            if deep_dive_dirs and vendor_name in deep_dive_dirs and deep_dive_dirs[vendor_name]:
                try:
                    deep_dive_dir_str = deep_dive_dirs[vendor_name]
                    deep_dive_dir = Path(deep_dive_dir_str)
                    if deep_dive_dir.exists() and deep_dive_dir.is_dir():
                        print(f"Found deep dive directory for {vendor_name} from mapping: {deep_dive_dir}")
                    else:
                        print(f"Deep dive directory from mapping does not exist: {deep_dive_dir}")
                        deep_dive_dir = None
                except Exception as e:
                    print(f"Error using deep dive directory from mapping for {vendor_name}: {e}")
                    deep_dive_dir = None
            
            # If no path from mapping or it doesn't exist, try alternative methods
            if not deep_dive_dir:
                # Attempt pattern-based discovery
                print(f"No valid deep dive directory found from mapping for {vendor_name}, trying pattern search...")
                
                # Search for a matching deep dive directory
                # Pattern: base_dir/vendor_VendorName_timestamp, or custom pattern
                
                # Check potential deep dive directory patterns
                potential_patterns = [
                    f"vendor_{clean_vendor_name}_*",        # Expected pattern
                    f"VendorResearch_{clean_vendor_name}_*",  # Alternative pattern
                    f"*_{clean_vendor_name}_*",               # Generalized pattern
                    f"*deep*dive*{clean_vendor_name}*",       # Deep dive keyword pattern
                    clean_vendor_name                         # Simple vendor name pattern
                ]
                
                # Find the first matching directory
                for pattern in potential_patterns:
                    matches = list(base_dir.glob(pattern))
                    if not matches:
                        # Try parent directory if available
                        parent_dir = base_dir.parent if base_dir.parent != base_dir else None
                        if parent_dir:
                            matches = list(parent_dir.glob(pattern))
                    
                    for match in matches:
                        if match.is_dir():
                            deep_dive_dir = match
                            print(f"Found deep dive directory for {vendor_name} using pattern '{pattern}': {deep_dive_dir}")
                            break
                    if deep_dive_dir:
                        break
                    
                # If no dedicated directory found, try subdirectories of base_dir
                if not deep_dive_dir:
                    print(f"No pattern match found for {vendor_name}, checking subdirectories...")
                    for subdir in base_dir.iterdir():
                        if subdir.is_dir() and any(keyword in subdir.name.lower() for keyword in ["deep", "dive", "vendor", clean_vendor_name.lower()]):
                            # Check if this might be a deep dive directory
                            potential_vendor_dir = subdir / clean_vendor_name
                            if potential_vendor_dir.exists() and potential_vendor_dir.is_dir():
                                deep_dive_dir = potential_vendor_dir
                                print(f"Found deep dive directory in subdirectory: {deep_dive_dir}")
                                break
                            elif clean_vendor_name.lower() in subdir.name.lower():
                                deep_dive_dir = subdir
                                print(f"Found potential deep dive directory by name match: {deep_dive_dir}")
                                break
            
            if deep_dive_dir:
                print(f"Processing deep dive content for {vendor_name} from {deep_dive_dir}")
                
                # Look for the markdown directory within the deep dive directory
                dd_markdown_dir = deep_dive_dir / "markdown"
                if dd_markdown_dir.exists() and dd_markdown_dir.is_dir():
                    # Create a section for this vendor's deep dive
                    dd_section_content = f"# Deep Dive: {vendor_name}\n\n"
                    
                    # Process files in order if vendor_section_order is available, otherwise alphabetically
                    if vendor_section_order:
                        # Use vendor section order for organized content
                        for section_id, section_title in vendor_section_order:
                            dd_file = dd_markdown_dir / f"{section_id}.md"
                            if dd_file.exists():
                                try:
                                    with open(dd_file, 'r', encoding='utf-8') as f:
                                        section_content = f.read().strip()
                                        if section_content:
                                            dd_section_content += f"## {section_title}\n\n{section_content}\n\n"
                                except Exception as e:
                                    print(f"Error reading deep dive file {dd_file}: {e}")
                    else:
                        # Fallback to alphabetical sorting
                        dd_files = sorted(list(dd_markdown_dir.glob("*.md")))
                        for dd_file in dd_files:
                            # Skip potential system or temporary files
                            if dd_file.name.startswith('.') or dd_file.name.startswith('~'):
                                continue
                                
                            try:
                                with open(dd_file, 'r', encoding='utf-8') as f:
                                    section_content = f.read().strip()
                                    if section_content:
                                        section_title = dd_file.stem.replace('_', ' ').title()
                                        dd_section_content += f"## {section_title}\n\n{section_content}\n\n"
                            except Exception as e:
                                print(f"Error reading deep dive file {dd_file}: {e}")
                    
                    # Create a deep dive section for this vendor
                    if dd_section_content.strip() != f"# Deep Dive: {vendor_name}":  # Check if we added content
                        deep_dive_sections.append(PDFSection(
                            id=f"deep_dive_{clean_vendor_name}",
                            title=f"Deep Dive: {vendor_name}",
                            content=dd_section_content
                        ))
                        print(f"Added deep dive section for {vendor_name}")
                    else:
                        print(f"No content found in deep dive markdown files for {vendor_name}")
                else:
                    print(f"No markdown directory found in deep dive directory for {vendor_name}: {deep_dive_dir}")
            else:
                print(f"Could not find deep dive directory for vendor: {vendor_name}")

    # Process each section from the main section order
    for section_id, section_title in section_order:
        # Special handling for vendor deep dives section
        if section_id == "vendor_deep_dives":
            if deep_dive_sections:
                # Add all deep dive sections in place of the placeholder
                sections.extend(deep_dive_sections)
                print(f"Added {len(deep_dive_sections)} deep dive sections")
            else:
                # Add a placeholder section if no deep dive content was found
                placeholder_content = "# Vendor Deep Dives\n\n"
                placeholder_content += "No vendor deep dive content was found or specified for this report.\n"
                
                sections.append(PDFSection(
                    id="vendor_deep_dives_placeholder",
                    title="Vendor Deep Dives",
                    content=placeholder_content
                ))
                print("Added placeholder for vendor deep dives (no content available)")
            continue
            
        section_content = None
        source_dir = None
        
        # Look for the section file in each directory, prioritizing later stages
        for markdown_dir in markdown_dirs:
            file_path = markdown_dir / f"{section_id}.md"
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if content.strip():
                        section_content = content
                        source_dir = markdown_dir
                        print(f"Found section {section_id} in {markdown_dir}")
                except Exception as e:
                    print(f"Error reading section file {file_path}: {e}")
        
        # Add the section if we found content for it
        if section_content:
            section = PDFSection(
                id=section_id,
                title=section_title,
                content=section_content
            )
            sections.append(section)
        else:
            print(f"Section file not found in any directory, skipping: {section_id}.md")

    if not sections:
        print("No non-empty markdown sections found to generate PDF.")
        return None

    pdf_generator = EnhancedPDFGenerator(template_path)
    # Sanitize identifier for filename
    safe_identifier = re.sub(r'[\\/*?:"<>| ]', "_", identifier)
    
    # Add stage information to filename if using stages
    if stages:
        stage_suffix = f"_{'-'.join(stages)}"
    else:
        stage_suffix = ""
        
    output_filename = f"{safe_identifier}{stage_suffix}_{report_type_name}.pdf"
    output_path = pdf_dir / output_filename

    # Pass necessary metadata for the template
    pdf_metadata = {
        'title': f"{identifier} - {report_type_name}",
        'identifier': identifier, # Pass the vendor/product name
        'language': 'English', # Hardcoded for now
        'report_type': report_type_name,
        'stages': stages if stages else None,
        'filtered_vendors': filtered_vendors if filtered_vendors else None,
        'deep_dive_vendors': deep_dive_vendors if deep_dive_vendors else None
        # Add other metadata if needed by the template
    }

    return pdf_generator.generate_pdf(
        sections,
        str(output_path),
        pdf_metadata
    ) 