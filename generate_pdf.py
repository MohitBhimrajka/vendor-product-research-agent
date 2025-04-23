#!/usr/bin/env python3
import argparse
from pathlib import Path
from pdf_generator import process_markdown_files
import sys
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import logging
from rich.logging import RichHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("rich")

# Rich console for better output
console = Console()

def main():
    parser = argparse.ArgumentParser(description='Generate PDF from markdown files')
    parser.add_argument('company_name', help='Name of the company')
    parser.add_argument('language', help='Language of the report')
    parser.add_argument('--output-dir', '-o', help='Output directory', default='output')
    parser.add_argument('--template', '-t', help='Custom template file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Construct the full output path
    output_dir = Path(args.output_dir) / f"{args.company_name}_{args.language}"
    
    if not output_dir.exists():
        console.print(f"[red]Error: Directory not found: {output_dir}[/red]")
        sys.exit(1)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Generating PDF report...", total=None)
        
        try:
            pdf_path = process_markdown_files(
                output_dir,
                args.company_name,
                args.language,
                template_path=args.template
            )
            progress.update(task, completed=True)
            
            console.print(Panel.fit(
                f"PDF generated successfully!\nOutput: {pdf_path}",
                title="Success",
                border_style="green"
            ))
            
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"\n[red]Error generating PDF: {str(e)}[/red]", file=sys.stderr)
            if args.debug:
                logger.exception("Detailed error information:")
            sys.exit(1)

if __name__ == '__main__':
    main() 