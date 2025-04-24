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
        # Keep track of generated IDs to ensure uniqueness
        generated_ids = set()

        for h_tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            h_tag['class'] = h_tag.get('class', []) + [f'heading-{h_tag.name}']

            if not h_tag.get('id'):
                heading_text = h_tag.get_text().strip()
                base_id = re.sub(r'[^\w\s-]', '', heading_text.lower())
                base_id = re.sub(r'[\s-]+', '-', base_id).strip('-') # Ensure it doesn't start/end with '-'

                # --- ADD UNIQUENESS CHECK ---
                final_id = base_id
                counter = 1
                while final_id in generated_ids:
                    final_id = f"{base_id}-{counter}"
                    counter += 1
                # --- END UNIQUENESS CHECK ---

                if final_id: # Only add ID if one could be generated
                    h_tag['id'] = final_id
                    generated_ids.add(final_id) # Add the final ID to the set

            # Existing IDs might also clash, add them to the set
            elif h_tag.get('id') in generated_ids:
                 # Optionally, log a warning about predefined duplicate IDs
                 print(f"Warning: Duplicate predefined ID found: {h_tag.get('id')}")
            elif h_tag.get('id'):
                 generated_ids.add(h_tag.get('id'))

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
            render_context = {
                'sections': processed_sections,
                'generation_timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'toc': self._generate_toc(processed_sections),
                'metadata': metadata,  # Pass the metadata dictionary under the key 'metadata'
                # Add top-level variables expected by the template
                'company_name': metadata.get('context_company_name', 'Context Company'),
                'logo_path': metadata.get('logo_path', None),
                'favicon_path': metadata.get('favicon_path', None),
                'generation_date': datetime.now().strftime("%Y-%m-%d")
            }
            rendered_html = self.template.render(**render_context)
            
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
    section_order: List[Tuple[str, str]] = None,
    filtered_vendors: List[str] = None,
    deep_dive_vendors: List[str] = None,
    deep_dive_dirs: Dict[str, str] = None,
    stages: Optional[Dict] = None
) -> Optional[Path]:
    """
    Process all markdown files in a directory and generate a PDF.
    Args:
        base_dir: Base directory containing markdown/ and pdf/ subdirectories
        identifier: Vendor or product name
        report_type_name: Type of report (e.g., "VendorReport", "ProductReport")
        section_order: List of tuples (section_id, section_title) defining the order
        filtered_vendors: (For product reports) List of vendor names after filtering
        deep_dive_vendors: (For product reports) List of vendors with deep dives
        deep_dive_dirs: (For product reports) Dict mapping vendor names to their deep dive directories
        stages: (For product reports) Dict with stage information for the report

    Returns:
        Path to the generated PDF file or None if error
    """
    markdown_dir = base_dir / "markdown"
    pdf_dir = base_dir / "pdf"
    
    if not markdown_dir.exists():
        print(f"Markdown directory does not exist: {markdown_dir}")
        return None
    
    pdf_dir.mkdir(exist_ok=True)
    
    if section_order is None:
        print("Warning: No section order provided. Using alphabetical order.")
        section_files = sorted(markdown_dir.glob("*.md"))
        section_order = [(p.stem, p.stem.replace('_', ' ').title()) for p in section_files]
    
    # Collect sections in the specified order
    sections = []
    for section_id, section_title in section_order:
        section_file = markdown_dir / f"{section_id}.md"
        
        # Skip missing files but warn about them
        if not section_file.exists():
            print(f"Warning: Section file not found: {section_file}")
            continue
        
        # Read the content from the file
        try:
            with open(section_file, 'r', encoding='utf-8') as f:
                section_content = f.read()
            
            # Create the PDFSection with correct field names
            sections.append(PDFSection(
                id=section_id,
                title=section_title,
                content=section_content
            ))
        except Exception as e:
            print(f"Error reading section file {section_file}: {e}")
            continue
    
    # Add deep dive sections if specified
    if deep_dive_vendors and deep_dive_dirs:
        # Attempt to import VENDOR_SECTION_ORDER for structuring deep dives
        try:
            from config import VENDOR_SECTION_ORDER
        except ImportError:
            VENDOR_SECTION_ORDER = None
            print("Warning: VENDOR_SECTION_ORDER not found in config. Deep dive sections will be ordered alphabetically.")

        # Add a main container section for all deep dives
        deep_dive_container_added = False

        for vendor_name in deep_dive_vendors:
            if vendor_name not in deep_dive_dirs or not deep_dive_dirs[vendor_name]:
                print(f"Warning: Deep dive directory for vendor {vendor_name} not found in mapping.")
                continue

            vendor_dir_str = deep_dive_dirs[vendor_name]
            vendor_dir = Path(vendor_dir_str)
            vendor_markdown_dir = vendor_dir / "markdown"

            if not vendor_markdown_dir.exists():
                print(f"Warning: Markdown directory for vendor {vendor_name} not found: {vendor_markdown_dir}")
                continue

            # Add the main "Deep Dive: Vendor Name" section header only once
            if not deep_dive_container_added:
                 sections.append(PDFSection(
                      id="vendor_deep_dives_container", # ID for the container
                      title="Selected Vendor Deep Dives",
                      content="# Selected Vendor Deep Dives\n\nThis section contains detailed research for selected vendors." # Placeholder content for the container page
                 ))
                 deep_dive_container_added = True


            # Add a subsection for this specific vendor under the main container
            vendor_deep_dive_section_id_prefix = f"deep_dive_{re.sub(r'[^a-zA-Z0-9_]', '_', vendor_name.lower())}"
            vendor_intro_content = f"## Deep Dive: {vendor_name}\n\n" # Start with H2 for vendor name

            # Process sections within this vendor's deep dive based on VENDOR_SECTION_ORDER
            vendor_sections_content = ""
            section_files_to_process = []

            if VENDOR_SECTION_ORDER:
                # Use defined order
                for dd_section_id, dd_section_title in VENDOR_SECTION_ORDER:
                    file_path = vendor_markdown_dir / f"{dd_section_id}.md"
                    if file_path.exists():
                        section_files_to_process.append((dd_section_id, dd_section_title, file_path))
                    # else: # Optional: Warn if a file from the order is missing
                    #     print(f"Debug: Deep dive file missing for {vendor_name}: {file_path.name}")
            else:
                # Fallback to alphabetical order
                sorted_files = sorted(vendor_markdown_dir.glob("*.md"))
                for file_path in sorted_files:
                     # Simple title from filename if no order defined
                     dd_section_id = file_path.stem
                     dd_section_title = dd_section_id.replace('_', ' ').title()
                     section_files_to_process.append((dd_section_id, dd_section_title, file_path))

            # Read and add content for each section of this vendor
            for _, dd_section_title, file_path in section_files_to_process:
                 try:
                     with open(file_path, 'r', encoding='utf-8') as f:
                         content = f.read().strip()
                         if content:
                              # Add as H3 subsection under the vendor's H2
                              vendor_sections_content += f"### {dd_section_title}\n\n{content}\n\n"
                 except Exception as e:
                      print(f"Error reading deep dive file {file_path} for {vendor_name}: {e}")

            # Append the combined content for this vendor as a single section in the PDF structure
            # This section will render with H2 for Vendor Name and H3s for subsections
            if vendor_sections_content:
                 sections.append(PDFSection(
                     id=f"{vendor_deep_dive_section_id_prefix}_content",
                     title=f"Deep Dive: {vendor_name}", # Title for TOC
                     content=vendor_intro_content + vendor_sections_content # Combine intro H2 + subsections H3s
                 ))
            else:
                 print(f"Warning: No content found in deep dive markdown files for {vendor_name}")
    
    # Configure and initialize the PDF generator
    template_path = str(Path(__file__).parent / "templates" / "enhanced_report_template.html")
    pdf_generator = EnhancedPDFGenerator(template_path=template_path)
    
    # Generate output path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{report_type_name}_{re.sub(r'[\\/*?:\"<>|]', '_', identifier)}_{timestamp}.pdf"
    output_path = pdf_dir / output_filename
    
    # Pass necessary metadata for the template
    pdf_metadata = {
        'title': f"{identifier} - {report_type_name}",
        'identifier': identifier, # Pass the vendor/product name
        'language': 'English', # Hardcoded for now
        'report_type': report_type_name,
        'stages': stages if stages else None,
        'filtered_vendors': filtered_vendors if filtered_vendors else None,
        'deep_dive_vendors': deep_dive_vendors if deep_dive_vendors else None,
        'context_company_name': 'Unknown Company' # Default, will be overwritten if available
    }

    # Attempt to get context company name if base_dir/misc/generation_config.yaml exists
    config_path = base_dir / "misc" / "generation_config.yaml"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f_cfg:
                gen_config = yaml.safe_load(f_cfg)
                if gen_config and 'context_company_name' in gen_config:
                    pdf_metadata['context_company_name'] = gen_config['context_company_name']
        except Exception as e:
            print(f"Warning: Could not load context_company_name from config file: {e}")

    # Add logo/favicon paths (adjust as needed)
    # Example: Assuming they are in static/assets relative to pdf_generator.py parent
    static_assets_dir = Path(__file__).parent / 'templates' / 'assets'
    logo_file = static_assets_dir / 'logo.png' # Adjust filename if needed
    favicon_file = static_assets_dir / 'favicon.ico' # Adjust filename if needed

    pdf_metadata['logo_path'] = f"file://{logo_file.resolve()}" if logo_file.exists() else None
    pdf_metadata['favicon_path'] = f"file://{favicon_file.resolve()}" if favicon_file.exists() else None
    
    # Generate the PDF
    try:
        pdf_path = pdf_generator.generate_pdf(
            sections,
            str(output_path),
            pdf_metadata
        )
        print(f"PDF generated: {pdf_path}")
        return pdf_path
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return None 