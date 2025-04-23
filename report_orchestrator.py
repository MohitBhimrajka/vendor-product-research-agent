# test_agent_prompt.py

import asyncio
import base64
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional # Added Optional
from google import genai
from google.genai import types
import prompt_testing
import tiktoken
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import time
import re
import markdown
from markdown.extensions import fenced_code, tables, toc, attr_list, def_list, footnotes
from markdown.extensions.codehilite import CodeHiliteExtension
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from jinja2 import Environment, FileSystemLoader
import yaml
import logging
from tqdm import tqdm
import signal
import sys
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.logging import RichHandler
from rich.panel import Panel
from bs4 import BeautifulSoup
from pdf_generator import process_markdown_files
from config import SECTION_ORDER, AVAILABLE_LANGUAGES, PROMPT_FUNCTIONS, LLM_MODEL, LLM_TEMPERATURE

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

# Global flag for graceful shutdown
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle interrupt signals gracefully."""
    global shutdown_requested
    if not shutdown_requested:
        console.print("\n[yellow]Shutdown requested. Completing current tasks...[/yellow]")
        shutdown_requested = True
    else:
        console.print("\n[red]Force quitting...[/red]")
        sys.exit(1)

# Register signal handlers (moved to main)
# signal.signal(signal.SIGINT, signal_handler)
# signal.signal(signal.SIGTERM, signal_handler)

# Load environment variables from .env file
load_dotenv()

def count_tokens(text: str) -> int:
    """Count the number of tokens in a text string."""
    encoding = tiktoken.get_encoding("cl100k_base")  # Using OpenAI's encoding
    return len(encoding.encode(text))

def format_time(seconds: float) -> str:
    """Format time in seconds to a human-readable string."""
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    if minutes < 60:
        return f"{minutes} minutes {remaining_seconds:.2f} seconds"
    hours = int(minutes // 60)
    remaining_minutes = minutes % 60
    return f"{hours} hours {remaining_minutes} minutes {remaining_seconds:.2f} seconds"

def generate_content(client: genai.Client, prompt: str, output_path: Path) -> Dict:
    """Generate content for a single prompt and save to file. Returns token counts and timing."""
    start_time = time.time()
    try:
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            ),
        ]
        tools = [types.Tool(google_search=types.GoogleSearch())]
        generate_content_config = types.GenerateContentConfig(
            temperature=LLM_TEMPERATURE,
            tools=tools,
            response_mime_type="text/plain",
        )

        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Count input tokens
        input_tokens = count_tokens(prompt)

        # Collect output text
        full_output = ""

        # Open file for writing
        with open(output_path, 'w', encoding='utf-8') as f:
            response = client.models.generate_content_stream(
                model=LLM_MODEL,
                contents=contents,
                config=generate_content_config,
            )

            for chunk in response:
                if shutdown_requested:
                    raise InterruptedError("Generation interrupted by user")

                if chunk.text:
                    f.write(chunk.text)
                    f.flush()
                    full_output += chunk.text

        # Count output tokens
        output_tokens = count_tokens(full_output)

        execution_time = time.time() - start_time
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "execution_time": execution_time,
            "status": "success"
        }
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Error generating content for {output_path.name}: {str(e)}")
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "execution_time": execution_time,
            "status": "error",
            "error": str(e)
        }

def get_user_input() -> tuple[str, Optional[str], Optional[str], list[str], list[tuple[str, str]], str]:
    """Get company name, optional identifiers, languages, prompts, and context company name from user input."""
    company_name = input("\nEnter company name: ")
    ticker = input("Enter Stock Ticker Symbol (optional, press Enter to skip): ").strip() or None
    industry = input("Enter Primary Industry (optional, press Enter to skip): ").strip() or None
    context_company_name = input("Enter Context Company Name (default is NESIC): ").strip() or "NESIC"

    print("\nAvailable languages:")
    for key, lang in AVAILABLE_LANGUAGES.items():
        print(f"{key}: {lang}")

    while True:
        languages = input("\nSelect language(s) (1-10, comma separated, default is 1 for Japanese): ").strip()
        if not languages:
            languages = "1"

        # Split by comma and remove whitespace
        language_keys = [key.strip() for key in languages.split(",")]

        # Validate all language keys
        if all(key in AVAILABLE_LANGUAGES for key in language_keys):
            break
        print("Invalid selection. Please choose numbers between 1 and 10, separated by commas.")

    # Prompt selection
    print("\nAvailable report sections:")
    for idx, (section_id, prompt_func) in enumerate(PROMPT_FUNCTIONS, 1):
        print(f"{idx}: {section_id}")
    print("0: Generate entire report (all sections)")

    while True:
        sections = input("\nSelect sections (comma-separated numbers, or 0 for all): ").strip()
        if not sections:
            sections = "0"

        # Split by comma and remove whitespace
        section_indices_str = [idx.strip() for idx in sections.split(",")]

        # Validate section indices
        try:
            section_indices = [int(idx) for idx in section_indices_str]
            if 0 in section_indices:
                selected_prompts = PROMPT_FUNCTIONS
                break
            elif all(1 <= idx <= len(PROMPT_FUNCTIONS) for idx in section_indices):
                # Convert indices to 0-based and get selected prompts
                selected_prompts = [PROMPT_FUNCTIONS[idx-1] for idx in section_indices]
                break
            else:
                print(f"Invalid selection. Please choose numbers between 0 and {len(PROMPT_FUNCTIONS)}.")
        except ValueError:
            print("Invalid input. Please enter numbers separated by commas.")

    return company_name, ticker, industry, language_keys, selected_prompts, context_company_name

def generate_all_prompts(company_name: str, language: str, selected_prompts: list[tuple[str, str]], context_company_name: str, ticker: Optional[str] = None, industry: Optional[str] = None, progress=None, language_task_id=None):
    """Generate content for selected prompts in parallel, passing identifiers."""
    start_time = time.time()

    # Get API key from .env file
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file")

    client = genai.Client(api_key=api_key)

    # Create timestamp for the directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create base output directory with timestamp
    base_dir = Path("output") / f"{company_name}_{language}_{timestamp}"
    base_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    markdown_dir = base_dir / "markdown"
    pdf_dir = base_dir / "pdf"
    misc_dir = base_dir / "misc"

    for dir_path in [markdown_dir, pdf_dir, misc_dir]:
        dir_path.mkdir(exist_ok=True)

    # Save generation config in misc directory
    config = {
        "company_name": company_name,
        "ticker": ticker,
        "industry": industry,
        "language": language,
        "timestamp": datetime.now().isoformat(),
        "sections": [section[0] for section in selected_prompts],  # Only selected sections
        "model": LLM_MODEL,
        "temperature": LLM_TEMPERATURE,
        "context_company_name": context_company_name
    }
    with open(misc_dir / "generation_config.yaml", "w") as f:
        yaml.dump(config, f)

    # Calculate optimal number of workers for prompt generation
    max_workers_prompts = max(len(selected_prompts), 10)

    # Process all prompts
    results = {}

    # If no progress display is provided, create a dummy progress context
    class DummyProgress:
        def add_task(self, *args, **kwargs):
            return None
        def update(self, *args, **kwargs):
            pass

    progress = progress or DummyProgress()

    # Create section tasks if we have a real progress display
    section_tasks = {}
    if not isinstance(progress, DummyProgress):
        for prompt_name, _ in selected_prompts:
            task_desc = f"[green]{language}: {prompt_name:.<30}"
            section_tasks[prompt_name] = progress.add_task(task_desc, total=1, visible=True)

    with ThreadPoolExecutor(max_workers=max_workers_prompts) as executor:
        futures = []
        for prompt_name, prompt_func_name in selected_prompts:
            if shutdown_requested:
                break

            # Get the prompt function from the prompt_testing module
            prompt_func = getattr(prompt_testing, prompt_func_name)
            # *** Pass the identifiers to the prompt function ***
            if prompt_name == "strategy_research":
                prompt = prompt_func(company_name, language, ticker=ticker, industry=industry, context_company_name=context_company_name)
            else:
                prompt = prompt_func(company_name, language, ticker=ticker, industry=industry, context_company_name=context_company_name)
            output_path = markdown_dir / f"{prompt_name}.md"

            future = executor.submit(generate_content, client, prompt, output_path)
            futures.append((prompt_name, future))

        # Collect results
        for prompt_name, future in futures:
            try:
                if not shutdown_requested:
                    result = future.result()
                    results[prompt_name] = result

                    # Update progress for this section
                    if prompt_name in section_tasks:
                        progress.update(section_tasks[prompt_name],
                            advance=1,
                            description=f"[bold green]{language}: {prompt_name:.<30}✓"
                        )

                    # Update language-level progress if provided
                    if language_task_id is not None:
                        progress.update(language_task_id,
                            advance=1/len(selected_prompts),
                            description=f"[cyan]{language} Progress"
                        )
                else:
                    results[prompt_name] = {
                        "status": "interrupted",
                        "error": "Generation interrupted by user"
                    }
                    if prompt_name in section_tasks:
                        progress.update(section_tasks[prompt_name],
                            description=f"[yellow]{language}: {prompt_name:.<30}⚠"
                        )
            except Exception as e:
                logger.error(f"Error processing {prompt_name}: {str(e)}")
                results[prompt_name] = {
                    "status": "error",
                    "error": str(e)
                }
                if prompt_name in section_tasks:
                    progress.update(section_tasks[prompt_name],
                        description=f"[red]{language}: {prompt_name:.<30}✗"
                    )

    total_execution_time = time.time() - start_time

    # Compile token statistics
    token_stats = {
        "prompts": results,
        "summary": {
            "total_input_tokens": sum(r.get("input_tokens", 0) for r in results.values()),
            "total_output_tokens": sum(r.get("output_tokens", 0) for r in results.values()),
            "total_tokens": sum(r.get("total_tokens", 0) for r in results.values()),
            "total_execution_time": total_execution_time,
            "timestamp": datetime.now().isoformat(),
            "company_name": company_name,
            "ticker": ticker,
            "industry": industry,
            "language": language,
            "model": LLM_MODEL,
            "temperature": LLM_TEMPERATURE,
            "context_company_name": context_company_name,
            "successful_prompts": sum(1 for r in results.values() if r.get("status") == "success"),
            "failed_prompts": sum(1 for r in results.values() if r.get("status") in ["error", "interrupted"]),
            "interrupted": shutdown_requested
        }
    }

    # Save token statistics in misc directory
    stats_path = misc_dir / "token_usage_report.json"
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(token_stats, f, indent=2, ensure_ascii=False)

    return token_stats, base_dir

def main():
    try:
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Get user input including optional identifiers
        company_name, ticker, industry, language_keys, selected_prompts, context_company_name = get_user_input()

        tasks = []
        for language_key in language_keys:
            language = AVAILABLE_LANGUAGES[language_key]
            console.print(f"\nGenerating prompts for {company_name} (Ticker: {ticker or 'N/A'}, Industry: {industry or 'N/A'}) in {language}...")
            console.print(f"Using model: {LLM_MODEL} with temperature: {LLM_TEMPERATURE}")
            console.print(f"Context Company: {context_company_name}")
            console.print("Output will be saved in the 'output' directory.\n")
            # Store identifiers with the task
            tasks.append((company_name, language, ticker, industry, context_company_name))

        # Calculate optimal number of workers for language-level parallelization
        # Adjusted calculation slightly based on potential parallel API limits
        max_workers_languages = min(len(tasks) * 2, 10) # Limit workers slightly

        # Process all languages in parallel using ThreadPoolExecutor
        results = []

        # Create a single progress display for all languages
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="green", finished_style="green"),
            TaskProgressColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
            expand=True
        ) as progress:
            # Create language-level progress tasks
            language_tasks = {
                lang: progress.add_task(f"[cyan]{lang} Progress", total=len(selected_prompts))
                for _, lang, _, _, _ in tasks # Iterate through tasks to get lang
            }

            with ThreadPoolExecutor(max_workers=max_workers_languages) as executor:
                futures = []
                # Unpack identifiers when submitting
                for company, lang, tk, ind, ctx in tasks:
                    if shutdown_requested:
                        break
                    future = executor.submit(
                        generate_all_prompts,
                        company,
                        lang,
                        selected_prompts,  # Pass selected prompts
                        ctx,              # Pass context company name
                        ticker=tk,         # Pass ticker
                        industry=ind,       # Pass industry
                        progress=progress,
                        language_task_id=language_tasks[lang]
                    )
                    futures.append((company, lang, future))

                # Collect results
                for company, lang, future in futures:
                    try:
                        if not shutdown_requested:
                            token_stats, base_dir = future.result()
                            results.append((lang, token_stats, base_dir))

                            # Display results for this language
                            console.print(f"\n[bold]Generation Summary for {lang}:[/bold]")
                            console.print(Panel.fit(
                                "\n".join([
                                    f"Total Execution Time: {format_time(token_stats['summary']['total_execution_time'])}",
                                    f"Total Tokens: {token_stats['summary']['total_tokens']:,}",
                                    f"Successful Prompts: [green]{token_stats['summary']['successful_prompts']}[/]",
                                    f"Failed Prompts: [red]{token_stats['summary']['failed_prompts']}[/]"
                                ]),
                                title=f"Results - {lang}",
                                border_style="cyan"
                            ))

                            # Generate PDF if there were successful prompts and not interrupted
                            if token_stats['summary']['successful_prompts'] > 0 and not token_stats['summary']['interrupted']:
                                console.print(f"\n[bold cyan]Generating PDF report for {lang}...[/bold cyan]")
                                pdf_path = process_markdown_files(base_dir, company_name, lang)

                                if pdf_path:
                                    console.print(f"\n[green]PDF report generated for {lang}: {pdf_path}[/green]")
                                else:
                                    console.print(f"\n[yellow]PDF generation failed for {lang}.[/yellow]")
                            elif token_stats['summary']['interrupted']:
                                 console.print(f"\n[yellow]PDF generation skipped for {lang} due to interruption.[/yellow]")

                        else:
                            console.print(f"\n[yellow]Generation process interrupted for {lang}.[/yellow]")
                    except Exception as e:
                        console.print(f"\n[red]Error processing {lang}: {str(e)}[/red]")
                        logger.exception(f"Error processing {lang}")

        if shutdown_requested:
            console.print("\n[yellow]Generation process interrupted.[/yellow]")
            return

        # Display final summary for all languages
        if results:
            console.print("\n[bold]Overall Generation Summary:[/bold]")
            total_execution_time = sum(stats['summary']['total_execution_time'] for _, stats, _ in results)
            total_tokens = sum(stats['summary']['total_tokens'] for _, stats, _ in results)
            total_successful = sum(stats['summary']['successful_prompts'] for _, stats, _ in results)
            total_failed = sum(stats['summary']['failed_prompts'] for _, stats, _ in results)

            console.print(Panel.fit(
                "\n".join([
                    f"Total Languages Processed: {len(results)}",
                    f"Total Execution Time: {format_time(total_execution_time)}",
                    f"Total Tokens Across All Languages: {total_tokens:,}",
                    f"Total Successful Prompts: [green]{total_successful}[/]",
                    f"Total Failed Prompts: [red]{total_failed}[/]"
                ]),
                title="Overall Results",
                border_style="cyan"
            ))

    except KeyboardInterrupt:
        console.print("\n[yellow]Process interrupted by user.[/yellow]")
    except Exception as e:
        console.print(f"\nError occurred: {str(e)}")
        logger.exception("Unexpected error occurred")
        console.print("Please check your configuration and try again.")

if __name__ == "__main__":
    main()