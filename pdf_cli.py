#!/usr/bin/env python3

import argparse
from pathlib import Path
import sys
from pdf_generator import process_markdown_files
from typing import Optional, List, Dict, Set, Tuple
import os
import re
import datetime
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from rich.prompt import Prompt
from rich.panel import Panel
import shutil

console = Console()

def detect_companies_in_output(output_dir: Path) -> Dict[str, Set[str]]:
    """
    Detect available companies and their languages from the output directory.
    Returns a dictionary of company names and their available languages.
    """
    companies = {}
    
    # Output directory structure: output/CompanyName_Language_Date/markdown/*.md
    for company_dir in output_dir.glob("*_*_*"):
        if not company_dir.is_dir():
            continue
            
        # Parse directory name
        try:
            parts = company_dir.name.split('_')
            if len(parts) >= 2:
                company = parts[0]
                language = parts[1]
                
                # Check if the markdown directory exists
                markdown_dir = company_dir / "markdown"
                if markdown_dir.exists() and markdown_dir.is_dir() and list(markdown_dir.glob("*.md")):
                    if company not in companies:
                        companies[company] = set()
                    companies[company].add(language)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not process {company_dir}: {e}[/yellow]")
            continue
    
    return companies

def detect_companies(dir_path: Path) -> Dict[str, Set[str]]:
    """
    Detect available companies and their languages from markdown files.
    Returns a dictionary of company names and their available languages.
    """
    # First check if this is the output directory with our special structure
    output_companies = detect_companies_in_output(dir_path)
    if output_companies:
        return output_companies
    
    # If not using output structure, fall back to the original detection method
    companies = {}
    
    # Pattern to match company and language from filenames or content
    for md_file in dir_path.glob("**/*.md"):
        try:
            content = md_file.read_text(encoding='utf-8')
            
            # Try to extract company name and language from frontmatter
            frontmatter_match = re.search(r"---\s*\n(.*?)\n---", content, re.DOTALL)
            if frontmatter_match:
                frontmatter = frontmatter_match.group(1)
                company_match = re.search(r"company:\s*(.+)", frontmatter)
                language_match = re.search(r"language:\s*(.+)", frontmatter)
                
                if company_match and language_match:
                    company = company_match.group(1).strip()
                    language = language_match.group(1).strip()
                    
                    if company not in companies:
                        companies[company] = set()
                    companies[company].add(language)
                    continue
            
            # If no frontmatter, try to detect from filename pattern
            # Expected pattern: company_language_section.md
            parts = md_file.stem.split('_')
            if len(parts) >= 2:
                company = parts[0].replace('-', ' ').title()
                language = parts[1].replace('-', ' ').title()
                
                if company not in companies:
                    companies[company] = set()
                companies[company].add(language)
        
        except Exception as e:
            console.print(f"[yellow]Warning: Could not process {md_file}: {e}[/yellow]")
            continue
    
    return companies

def find_company_output_dir(output_dir: Path, company: str, language: str) -> Optional[Path]:
    """Find the most recent output directory for a company and language."""
    matching_dirs = []
    
    for company_dir in output_dir.glob(f"{company}_{language}_*"):
        if company_dir.is_dir():
            matching_dirs.append(company_dir)
    
    # Sort by creation date (newest first)
    matching_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    return matching_dirs[0] if matching_dirs else None

def display_companies(companies: Dict[str, Set[str]]) -> None:
    """Display available companies and their languages in a rich table."""
    if not companies:
        console.print("[red]No company reports found in the specified directory.[/red]")
        return
    
    table = Table(title="Available Company Reports")
    table.add_column("Index", style="cyan")
    table.add_column("Company", style="green")
    table.add_column("Available Languages", style="yellow")
    
    for idx, (company, languages) in enumerate(companies.items(), 1):
        table.add_row(
            str(idx),
            company,
            ", ".join(sorted(languages))
        )
    
    console.print(table)

def select_company(companies: Dict[str, Set[str]]) -> Tuple[Optional[str], Optional[str]]:
    """Interactive company and language selection."""
    if not companies:
        return None, None
    
    company_list = list(companies.keys())
    
    while True:
        try:
            choice = Prompt.ask(
                "\nSelect company by index (or 'q' to quit)",
                choices=[str(i) for i in range(1, len(company_list) + 1)] + ['q']
            )
            
            if choice.lower() == 'q':
                return None, None
            
            selected_company = company_list[int(choice) - 1]
            available_languages = sorted(companies[selected_company])
            
            # Display available languages for the selected company
            console.print(f"\n[green]Available languages for {selected_company}:[/green]")
            for idx, lang in enumerate(available_languages, 1):
                console.print(f"{idx}: {lang}")
            
            lang_choice = Prompt.ask(
                "\nSelect language by index",
                choices=[str(i) for i in range(1, len(available_languages) + 1)]
            )
            
            selected_language = available_languages[int(lang_choice) - 1]
            return selected_company, selected_language
            
        except (ValueError, IndexError):
            console.print("[red]Invalid selection. Please try again.[/red]")

def copy_company_files_from_output(input_path: Path, company: str, language: str, target_dir: Path) -> bool:
    """Copy relevant company files from output directory structure."""
    company_dir = find_company_output_dir(input_path, company, language)
    if not company_dir:
        return False
        
    # Get source markdown directory
    source_dir = company_dir / "markdown"
    if not source_dir.exists() or not source_dir.is_dir():
        return False
    
    # Create target directory
    os.makedirs(target_dir, exist_ok=True)
    
    # Copy all markdown files
    found_files = False
    for source_file in source_dir.glob("*.md"):
        target_file = target_dir / source_file.name
        shutil.copy2(source_file, target_file)
        console.print(f"[green]Copied {source_file.name} → {target_file.name}[/green]")
        found_files = True
    
    return found_files

def copy_company_files(input_path: Path, company: str, language: str, target_dir: Path) -> bool:
    """Copy relevant company files to the target directory."""
    # First check if this is the output directory structure
    if copy_company_files_from_output(input_path, company, language, target_dir):
        return True
    
    # Otherwise use standard file detection
    found_files = False
    
    # Create target directory
    os.makedirs(target_dir, exist_ok=True)
    
    # Pattern to match relevant files
    patterns = [
        f"{company.lower().replace(' ', '-')}_{language.lower()}*.md",
        f"{company.lower().replace(' ', '_')}_{language.lower()}*.md"
    ]
    
    for pattern in patterns:
        for source_file in input_path.glob(f"**/{pattern}"):
            # Extract section name from filename
            section = source_file.stem.split('_')[-1]
            target_file = target_dir / f"{section}.md"
            
            shutil.copy2(source_file, target_file)
            console.print(f"[green]Copied {source_file.name} → {target_file.name}[/green]")
            found_files = True
    
    return found_files

def main():
    parser = argparse.ArgumentParser(description="Generate PDF from markdown files")
    parser.add_argument("--input-dir", "-i", type=str, default="output", 
                       help="Directory containing markdown files (default: output)")
    parser.add_argument("--company-name", "-c", type=str, help="Company name for the report")
    parser.add_argument("--language", "-l", type=str, help="Language for the report")
    parser.add_argument("--template", "-t", type=str, help="Custom template path (optional)")
    parser.add_argument("--output-dir", "-o", type=str, help="Output directory for the PDF")
    parser.add_argument("--interactive", "-int", action="store_true", help="Use interactive mode")
    
    args = parser.parse_args()
    
    # If no input directory specified, use output directory
    input_dir = args.input_dir or "output"
    input_path = Path(input_dir)
    
    if not input_path.exists():
        console.print(f"[red]Error: Directory '{input_dir}' does not exist.[/red]")
        sys.exit(1)
    
    # Detect available companies and their languages
    companies = detect_companies(input_path)
    
    if args.interactive or (not args.company_name and not args.language):
        # Display available companies and get selection
        console.print(Panel.fit(
            "[bold cyan]PDF Report Generator[/bold cyan]\n\n"
            "This tool will generate a PDF report from markdown files in the output directory.",
            title="Welcome"
        ))
        
        display_companies(companies)
        company_name, language = select_company(companies)
        
        if not company_name or not language:
            console.print("[yellow]Operation cancelled.[/yellow]")
            sys.exit(0)
    else:
        company_name = args.company_name
        language = args.language
        
        if not company_name or not language:
            console.print("[red]Error: Both company name and language are required in non-interactive mode.[/red]")
            sys.exit(1)
    
    # Create timestamp for the report directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create output directory structure
    base_dir = Path(args.output_dir) if args.output_dir else Path(f"pdf_output/{company_name}_{language}_{timestamp}")
    markdown_dir = base_dir / "markdown"
    pdf_dir = base_dir / "pdf"
    
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Copy relevant files
    if not copy_company_files(input_path, company_name, language, markdown_dir):
        console.print(f"[red]Error: No matching files found for {company_name} in {language}[/red]")
        sys.exit(1)
    
    console.print("\n[cyan]Generating PDF report...[/cyan]")
    try:
        pdf_path = process_markdown_files(base_dir, company_name, language, args.template)
        if pdf_path and pdf_path.exists():
            console.print(f"\n[green]PDF report generated successfully: {pdf_path}[/green]")
        else:
            console.print("\n[red]Error: Failed to generate PDF report[/red]")
            sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error generating PDF: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main() 