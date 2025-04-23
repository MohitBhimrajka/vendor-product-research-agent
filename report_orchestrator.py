import asyncio
import base64
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from google import genai
from google.genai import types
# Import the new prompt module
import vendor_prompts
# Placeholder import for product prompts - will use in Phase 2
import product_prompts
import tiktoken
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import time
import re
import markdown
from bs4 import BeautifulSoup
import yaml
import logging
import signal
import sys
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.logging import RichHandler
from rich.panel import Panel

# Import PDF generator and config
from pdf_generator import process_markdown_files # Assuming pdf_generator is ready
# Import specific configurations needed
from config import (
    LLM_MODEL, LLM_TEMPERATURE, OUTPUT_DIR,
    VENDOR_SECTION_ORDER, VENDOR_PROMPT_FUNCTIONS,
    PRODUCT_INITIAL_SECTION_ORDER, PRODUCT_INITIAL_PROMPT_FUNCTIONS # Add product initial configs
    # Add PRODUCT configs later
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)]
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
        console.print("\n[yellow]Shutdown requested. Finishing current generation tasks...[/yellow]")
        shutdown_requested = True
    else:
        # Allow forcing quit if interrupted again
        console.print("\n[red]Force quitting NOW...[/red]")
        sys.exit(1)

# Load environment variables from .env file
load_dotenv()

# --- Helper Functions (Token Counting, Time Formatting) ---
def count_tokens(text: str) -> int:
    """Count the number of tokens in a text string."""
    try:
        # Ensure text is a string
        if not isinstance(text, str):
            text = str(text)
        encoding = tiktoken.get_encoding("cl100k_base") # Using OpenAI's encoding
        return len(encoding.encode(text))
    except Exception as e:
        logger.warning(f"Tiktoken counting failed: {e}. Returning character count / 4.")
        # Fallback for safety
        return len(str(text)) // 4

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

# --- Core Content Generation Logic ---
def _generate_single_section(client: genai.Client, prompt: str, output_path: Path) -> Dict:
    """Internal function: Generate content for a single prompt/section."""
    start_time = time.time()
    input_tokens = 0
    output_tokens = 0
    if shutdown_requested: # Check before starting work
        return {"status": "skipped", "error": "Shutdown requested before start", "execution_time": 0}

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        input_tokens = count_tokens(prompt)

        contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
        # Enable Gemini Grounding (formerly Google Search)
        tools = [types.Tool(google_search=types.GoogleSearch(result_count=10))] # Request more results for grounding
        generate_content_config = types.GenerateContentConfig(
            temperature=LLM_TEMPERATURE,
            # Grounding is enabled via the 'tools' parameter in the request
            # tool_config=types.ToolConfig(google_search_config=types.GoogleSearchConfig(disable_attribution=False)), # Optional: Keep attribution
            response_mime_type="text/plain",
        )

        # Using blocking call for simplicity in threading, stream handling adds complexity
        response = client.generate_content(
            model=LLM_MODEL,
            contents=contents,
            tools=tools, # Include tools for grounding
            generation_config=generate_content_config,
            request_options={'timeout': 600} # 10 minute timeout per section
        )

        # Check for blocked content or missing parts
        if not response.candidates:
            block_reason_msg = "Unknown reason (no candidates)"
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                 block_reason_msg = f"Reason: {response.prompt_feedback.block_reason.name}"
                 if hasattr(response.prompt_feedback, 'safety_ratings'):
                     block_reason_msg += f" Details: {response.prompt_feedback.safety_ratings}"
            raise ValueError(f"Content blocked or generation failed. {block_reason_msg}")

        # Safely access content parts
        full_output = ""
        if response.candidates[0].content and response.candidates[0].content.parts:
            full_output = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
        else:
             logger.warning(f"No content parts found in response for {output_path.name}. Response: {response.candidates[0].finish_reason}")
             # Potentially check finish_reason (e.g., SAFETY, RECITATION, OTHER)

        if not full_output.strip():
             logger.warning(f"Generated empty content for {output_path.name}. Check prompt or model response (Finish Reason: {response.candidates[0].finish_reason}).")
             # Consider returning an error status if empty content is unacceptable
             # return { ... "status": "error", "error": "Generated empty content" }

        output_tokens = count_tokens(full_output)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_output)

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
        error_message = f"Error generating content for {output_path.name}: {type(e).__name__} - {str(e)}"
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# Generation Error\n\nAn error occurred while generating this section:\n\n```\n{error_message}\n```")
        except Exception as write_e:
            logger.error(f"Additionally, failed to write error details to {output_path.name}: {write_e}")

        return {
            "input_tokens": input_tokens,
            "output_tokens": 0,
            "total_tokens": input_tokens,
            "execution_time": execution_time,
            "status": "error",
            "error": error_message
        }

def _generate_report_sections(
    research_mode: str,
    identifier: str,
    context_company_name: str,
    optional_inputs: Dict[str, Any],
    section_order_config: List[Tuple[str, str]], # e.g., VENDOR_SECTION_ORDER
    prompt_func_config: List[Tuple[str, str]], # e.g., VENDOR_PROMPT_FUNCTIONS
    prompt_module: Any, # The imported module (vendor_prompts or product_prompts)
    progress_context=None # Rich progress context
    ) -> Tuple[Optional[Dict], Optional[Path]]:
    """
    Core function to generate sections for a given mode (vendor/product).
    Manages directory setup, parallel execution, stats collection.
    """
    start_time = time.time()
    global shutdown_requested

    # --- API Client Setup ---
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found in .env file")
        return None, None
    try:
        # Configure client options for retries, etc. if needed
        client = genai.Client(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Google GenAI Client: {e}")
        return None, None

    # --- Directory Setup ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_identifier = re.sub(r'[\\/*?:"<>| ]', "_", identifier) # Sanitize more aggressively
    base_dir_name = f"{research_mode}_{sanitized_identifier}_{timestamp}"
    base_dir = Path(OUTPUT_DIR) / base_dir_name
    try:
        base_dir.mkdir(parents=True, exist_ok=True)
        markdown_dir = base_dir / "markdown"
        pdf_dir = base_dir / "pdf"
        misc_dir = base_dir / "misc"
        markdown_dir.mkdir(exist_ok=True)
        pdf_dir.mkdir(exist_ok=True)
        misc_dir.mkdir(exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create output directories in {base_dir}: {e}")
        return None, None

    # --- Save Generation Config ---
    config_data = {
        "research_mode": research_mode,
        "identifier": identifier,
        "context_company_name": context_company_name,
        "optional_inputs": optional_inputs,
        "timestamp": datetime.now().isoformat(),
        "sections_requested": [section_id for section_id, _ in prompt_func_config],
        "section_order_used": [section_id for section_id, _ in section_order_config],
        "model": LLM_MODEL,
        "temperature": LLM_TEMPERATURE,
    }
    try:
        with open(misc_dir / "generation_config.yaml", "w", encoding='utf-8') as f:
            yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)
    except Exception as e:
        logger.warning(f"Could not save generation config: {e}")

    # --- Parallel Section Generation ---
    results = {}
    # Use provided progress context or create a dummy one
    progress = progress_context or Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(),
            TaskProgressColumn(), TimeElapsedColumn(), console=console, transient=True
        )
    main_task = progress.add_task(f"Generating {research_mode} report sections...", total=len(prompt_func_config))

    # Create section tasks for detailed progress
    section_tasks = {
        section_id: progress.add_task(f"[cyan]{section_id:.<30}", total=1, visible=True, parent=main_task)
        for section_id, _ in prompt_func_config
    }

    max_workers = min(len(prompt_func_config), 8) # Limit concurrency slightly more

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for section_id, prompt_func_name in prompt_func_config:
            if shutdown_requested:
                logger.warning(f"Shutdown requested, skipping section: {section_id}")
                results[section_id] = {"status": "skipped", "error": "Shutdown requested", "execution_time": 0}
                progress.update(section_tasks[section_id], description=f"[yellow]{section_id:.<30}⚠ (Skipped)", completed=1)
                continue

            try:
                prompt_func = getattr(prompt_module, prompt_func_name)
                prompt_args = {
                    'identifier': identifier,
                    'language': "English", # Hardcoded
                    'context_company_name': context_company_name,
                    **optional_inputs
                }
                # Simple argument filtering (improve if needed)
                import inspect
                sig = inspect.signature(prompt_func)
                valid_args = {k: v for k, v in prompt_args.items() if k in sig.parameters}

                prompt = prompt_func(**valid_args)
                output_path = markdown_dir / f"{section_id}.md"
                future = executor.submit(_generate_single_section, client, prompt, output_path)
                futures[future] = section_id

            except AttributeError:
                 logger.error(f"Prompt function '{prompt_func_name}' not found in module. Skipping.")
                 results[section_id] = {"status": "error", "error": f"Prompt function '{prompt_func_name}' not found.", "execution_time": 0}
                 progress.update(section_tasks[section_id], description=f"[red]{section_id:.<30}✗ (Not Found)", completed=1)
            except Exception as e:
                logger.error(f"Error preparing prompt for {section_id}: {e}")
                results[section_id] = {"status": "error", "error": f"Error preparing prompt: {e}", "execution_time": 0}
                progress.update(section_tasks[section_id], description=f"[red]{section_id:.<30}✗ (Prompt Error)", completed=1)

        processed_count = 0
        for future in as_completed(futures):
            section_id = futures[future]
            try:
                if not shutdown_requested: # Check again in case it was set while task ran
                    result = future.result()
                    results[section_id] = result
                    status_char = "✓" if result['status'] == 'success' else "✗"
                    color = "green" if result['status'] == 'success' else "red"
                    progress.update(section_tasks[section_id],
                                    advance=1,
                                    description=f"[{color}]{section_id:.<30}{status_char}")
                else:
                    # Task finished, but shutdown was requested during its run or while waiting
                    results[section_id] = {"status": "interrupted", "error": "Shutdown requested during execution", "execution_time": 0} # Assume 0 time if interrupted? Or try to get partial?
                    progress.update(section_tasks[section_id], description=f"[yellow]{section_id:.<30}⚠ (Interrupted)")

            except Exception as e:
                logger.error(f"Error processing result for {section_id}: {str(e)}")
                results[section_id] = {"status": "error", "error": f"Future result error: {str(e)}", "execution_time": 0} # Assume 0 time if future failed badly
                progress.update(section_tasks[section_id], description=f"[red]{section_id:.<30}✗ (Result Error)", completed=1)
            finally:
                 processed_count += 1
                 progress.update(main_task, completed=processed_count) # Update main task progress


    # --- Compile Stats & Save ---
    total_execution_time = time.time() - start_time
    # Filter out skipped sections when calculating summary stats unless needed
    valid_results = {k: v for k, v in results.items() if v.get('status') != 'skipped'}

    token_stats = {
        "research_mode": research_mode,
        "identifier": identifier,
        "context_company_name": context_company_name,
        "optional_inputs": optional_inputs,
        "timestamp": datetime.now().isoformat(),
        "sections_requested": [section_id for section_id, _ in prompt_func_config],
        "section_order_used": [section_id for section_id, _ in section_order_config],
        "model": LLM_MODEL,
        "temperature": LLM_TEMPERATURE,
        "sections": results, # Include all results, even skipped/errors
        "summary": {
            "total_input_tokens": sum(r.get("input_tokens", 0) for r in valid_results.values()),
            "total_output_tokens": sum(r.get("output_tokens", 0) for r in valid_results.values()),
            "total_tokens": sum(r.get("total_tokens", 0) for r in valid_results.values()),
            "total_execution_time": total_execution_time,
            "formatted_execution_time": format_time(total_execution_time),
            "timestamp": datetime.now().isoformat(),
            "successful_sections": sum(1 for r in results.values() if r.get("status") == "success"),
            "failed_sections": sum(1 for r in results.values() if r.get("status") == 'error'),
            "interrupted_sections": sum(1 for r in results.values() if r.get("status") == 'interrupted'),
            "skipped_sections": sum(1 for r in results.values() if r.get("status") == 'skipped'),
            "was_interrupted": shutdown_requested
        }
    }

    try:
        stats_path = misc_dir / "generation_summary.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(token_stats, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Could not save generation summary JSON: {e}")

    # Stop progress bar if it was created internally
    if progress_context is None:
         progress.stop()

    return token_stats, base_dir


# --- Research Mode Execution Functions ---

def run_vendor_research(
    vendor_name: str,
    context_company_name: str,
    optional_inputs: Dict,
    progress_context=None # Accept progress context from Streamlit
    ) -> Tuple[Optional[Dict], Optional[Path]]:
    """Runs the full vendor research process."""
    console.print(f"\n[bold blue]Starting Vendor Research for: {vendor_name}[/bold blue]")

    # Use the actual function to generate sections
    token_stats, base_dir = _generate_report_sections(
        research_mode='vendor',
        identifier=vendor_name,
        context_company_name=context_company_name,
        optional_inputs=optional_inputs,
        section_order_config=VENDOR_SECTION_ORDER, # Use actual config
        prompt_func_config=VENDOR_PROMPT_FUNCTIONS, # Use actual config
        prompt_module=vendor_prompts, # Use the imported module
        progress_context=progress_context
    )

    # Check if generation was successful before proceeding
    if not token_stats or not base_dir:
        console.print(f"[red]Vendor research section generation failed for {vendor_name}.[/red]")
        return None, None # Indicate failure

    # Display Summary Panel
    console.print(Panel.fit(
        f"Vendor Research for '{vendor_name}' processing complete.\n"
        f"Time: {token_stats['summary']['formatted_execution_time']}\n"
        f"Successful Sections: [green]{token_stats['summary']['successful_sections']}[/]\n"
        f"Failed Sections: [red]{token_stats['summary']['failed_sections']}[/]\n"
        f"Interrupted: {'Yes' if token_stats['summary']['was_interrupted'] else 'No'}\n"
        f"Output Dir: {base_dir}",
        title="Vendor Research Summary", border_style="blue"
    ))

    # Generate PDF only if successful and not interrupted
    pdf_path = None
    if token_stats['summary']['successful_sections'] > 0 and not token_stats['summary']['was_interrupted']:
        console.print(f"\n[bold cyan]Generating PDF report for {vendor_name}...[/bold cyan]")
        try:
            # Pass the correct section order for PDF generation
            pdf_path_generated = process_markdown_files(
                base_dir=base_dir,
                company_name=vendor_name, # Use vendor name for file name
                language="VendorReport", # Use a generic identifier
                section_order=VENDOR_SECTION_ORDER # Pass the correct order
            )
            if pdf_path_generated and pdf_path_generated.exists():
                pdf_path = pdf_path_generated # Store the valid path
                console.print(f"\n[green]PDF report generated: {pdf_path}[/green]")
            else:
                 console.print(f"\n[yellow]PDF generation did not return a valid path for {vendor_name}.[/yellow]")
        except Exception as pdf_e:
            console.print(f"\n[red]Error during PDF generation for {vendor_name}: {pdf_e}[/red]")
            logger.exception(f"PDF Generation Error for {base_dir}")

    # Return results including the PDF path if generated
    return token_stats, pdf_path


# --- New Function for Initial Product Analysis ---
def run_product_research_initial(
    product_category: str,
    context_company_name: str,
    optional_inputs: Dict,
    progress_context=None
) -> Tuple[Optional[Dict], Optional[Path], Optional[List[str]]]:
    """
    Runs the initial stage of product research: market analysis, vendor ID,
    and generates filtering questions.
    Returns: (token_stats, base_dir, filtering_questions)
    """
    console.print(f"\n[bold magenta]Starting Initial Product Analysis for: {product_category}[/bold magenta]")

    # Step 1: Generate initial analysis sections
    token_stats, base_dir = _generate_report_sections(
        research_mode='product',
        identifier=product_category,
        context_company_name=context_company_name,
        optional_inputs=optional_inputs,
        section_order_config=PRODUCT_INITIAL_SECTION_ORDER, # Use initial product config
        prompt_func_config=PRODUCT_INITIAL_PROMPT_FUNCTIONS, # Use initial product config
        prompt_module=product_prompts, # Use the product prompts module
        progress_context=progress_context
    )

    if not token_stats or not base_dir:
        console.print(f"[red]Initial product analysis section generation failed for {product_category}.[/red]")
        return None, None, None

    # Step 2: Extract summary from generated sections for question generation
    # Simple approach: concatenate relevant sections (e.g., market, features, vendors)
    initial_summary_content = ""
    summary_sections = ["product_market_overview", "product_key_features", "product_vendor_identification", "product_compliance_landscape"] # Sections to feed into question gen
    markdown_dir = base_dir / "markdown"
    for section_id in summary_sections:
        md_path = markdown_dir / f"{section_id}.md"
        if md_path.exists():
            try:
                with open(md_path, 'r', encoding='utf-8') as f:
                    initial_summary_content += f"\n\n## {section_id.replace('_', ' ').title()}\n\n"
                    initial_summary_content += f.read()
            except Exception as e:
                logger.warning(f"Could not read {md_path} for summary: {e}")

    if not initial_summary_content.strip():
        logger.error("Failed to gather summary content from initial product analysis sections.")
        return token_stats, base_dir, None # Return stats/dir but no questions

    # Step 3: Generate Filtering Questions using a separate LLM call
    filtering_questions = None
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key) # Re-initialize client or reuse if passed differently
        console.print("[magenta]Generating filtering questions based on analysis...[/magenta]")

        question_gen_prompt = product_prompts.get_filtering_questions_prompt(
            product_category=product_category,
            initial_analysis_summary=initial_summary_content,
            context_company_name=context_company_name,
            optional_inputs=optional_inputs
        )

        # Simple blocking call for the questions
        response = client.generate_content(
            model=LLM_MODEL, # Use same model or potentially a faster one if suitable
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=question_gen_prompt)])],
            generation_config=types.GenerateContentConfig(temperature=0.5) # Lower temp for focused questions
        )

        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            raw_questions_text = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
            # Parse the '- ' prefixed lines into a list
            filtering_questions = [q.strip('- ').strip() for q in raw_questions_text.strip().split('\n') if q.strip().startswith('- ')]
            console.print(f"[green]Generated {len(filtering_questions)} filtering questions.[/green]")
        else:
             logger.warning("LLM did not generate filtering questions.")
             if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                  logger.warning(f"Reason: {response.prompt_feedback.block_reason}")

    except Exception as e:
        logger.error(f"Failed to generate filtering questions: {e}")
        # Proceed without questions, but log the error

    # Return results including the questions
    return token_stats, base_dir, filtering_questions

def run_product_research(product_category: str, context_company_name: str, optional_inputs: Dict):
    """Product research function that calls the initial analysis as first step."""
    console.print(f"\n[bold magenta]Starting Product Research for: {product_category}[/bold magenta]")
    
    # Call the initial research function first
    token_stats, base_dir, filtering_questions = run_product_research_initial(
        product_category=product_category,
        context_company_name=context_company_name,
        optional_inputs=optional_inputs
    )
    
    if not token_stats or not base_dir:
        console.print(f"[red]Product research initial analysis failed for {product_category}.[/red]")
        return None, None
    
    # For now, just return the initial analysis results
    # Later phases will implement the interactive filtering and vendor comparison
    
    # Generate a simple PDF with initial findings
    pdf_path = None
    if token_stats['summary']['successful_sections'] > 0 and not token_stats['summary']['was_interrupted']:
        console.print(f"\n[bold cyan]Generating initial PDF report for {product_category}...[/bold cyan]")
        try:
            # Pass the correct section order for PDF generation
            pdf_path_generated = process_markdown_files(
                base_dir=base_dir,
                identifier=product_category,
                report_type_name="ProductInitialAnalysis",
                section_order=PRODUCT_INITIAL_SECTION_ORDER
            )
            if pdf_path_generated and pdf_path_generated.exists():
                pdf_path = pdf_path_generated
                console.print(f"\n[green]Initial PDF report generated: {pdf_path}[/green]")
            else:
                console.print(f"\n[yellow]PDF generation did not return a valid path for {product_category}.[/yellow]")
        except Exception as pdf_e:
            console.print(f"\n[red]Error during PDF generation for {product_category}: {pdf_e}[/red]")
            logger.exception(f"PDF Generation Error for {base_dir}")
    
    # Display summary panel with filtering questions if available
    questions_text = "\n".join([f"• {q}" for q in filtering_questions]) if filtering_questions else "None generated"
    console.print(Panel.fit(
        f"Product Research Initial Analysis for '{product_category}' complete.\n"
        f"Time: {token_stats['summary']['formatted_execution_time']}\n"
        f"Successful Sections: [green]{token_stats['summary']['successful_sections']}[/]\n"
        f"Failed Sections: [red]{token_stats['summary']['failed_sections']}[/]\n"
        f"Generated Filtering Questions: {len(filtering_questions) if filtering_questions else 0}\n"
        f"Output Dir: {base_dir}",
        title="Product Research Summary", border_style="magenta"
    ))
    
    if filtering_questions:
        console.print(Panel.fit(
            questions_text,
            title="Filtering Questions", border_style="cyan"
        ))
    
    return token_stats, pdf_path


def main_cli():
    """Basic CLI interaction for testing."""
    console.print(Panel.fit("[bold]Vendor & Product Research Agent (CLI Runner)[/bold]", border_style="yellow"))

    mode = console.input("Select mode ([1] Vendor / [2] Product): ")

    if mode == '1':
        vendor_name = console.input("Enter Vendor Name: ").strip()
        if not vendor_name:
            console.print("[red]Vendor name cannot be empty.[/red]"); return
        context_company = console.input("Enter Your Company Name (Context): ").strip()
        if not context_company:
            console.print("[red]Context company name cannot be empty.[/red]"); return

        prod_cat = console.input("Optional: Product Category from Vendor: ").strip()
        certs = console.input("Optional: Required Certifications (comma-sep): ").strip()
        region = console.input("Optional: Geographic Region: ").strip()
        optional_inputs = {
            "product_category": prod_cat or None,
            "required_certs": certs or None,
            "region": region or None,
        }
        # Run with internal progress bar
        run_vendor_research(vendor_name, context_company, optional_inputs)
    elif mode == '2':
        product_category = console.input("Enter Product Category: ").strip()
        if not product_category:
            console.print("[red]Product category cannot be empty.[/red]"); return
        context_company = console.input("Enter Your Company Name (Context): ").strip()
        if not context_company:
            console.print("[red]Context company name cannot be empty.[/red]"); return

        certs = console.input("Optional: Required Certifications (comma-sep): ").strip()
        region = console.input("Optional: Geographic Region: ").strip()
        optional_inputs = {
            "required_certs": certs or None,
            "region": region or None,
        }
        run_product_research(product_category, context_company, optional_inputs) # Placeholder call
    else:
        console.print("[red]Invalid mode selected.[/red]")


# --- Placeholders for Phase 4 Prompts (Keep as is) ---
def get_vendor_light_profiles_prompt():
    """Placeholder for Phase 4: Generate light profiles for filtered vendors"""
    pass

def get_vendor_comparison_matrix_prompt():
    """Placeholder for Phase 4: Generate comparison matrix for filtered vendors"""
    pass

def get_product_relevance_prompt():
    """Placeholder for Phase 4: Generate product relevance analysis"""
    pass

# --- New Filter Vendors Function ---
def filter_vendors_based_on_answers(
    base_dir: Path, # Directory containing the initial product analysis
    questions: List[str],
    answers: List[str]
) -> Optional[List[str]]:
    """
    Parses the initial vendor list, calls LLM to filter based on Q&A,
    and returns the filtered list.
    """
    global shutdown_requested
    if shutdown_requested: return None # Check for interrupt

    console.print("[magenta]Processing user answers to filter vendors...[/magenta]")

    # --- Step 1: Parse Initial Vendor List ---
    initial_vendors = []
    vendor_id_section_file = base_dir / "markdown" / "product_vendor_identification.md"
    if not vendor_id_section_file.exists():
        logger.error(f"Vendor identification file not found: {vendor_id_section_file}")
        return None # Cannot proceed without the initial list

    try:
        with open(vendor_id_section_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # Convert markdown to HTML to reliably parse table/lists
        html_content = markdown.markdown(md_content, extensions=['tables', 'extra'])
        soup = BeautifulSoup(html_content, 'html.parser')

        # Try parsing a table first (assuming table has vendor name in first column)
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')
            if len(rows) > 1: # Check if there are data rows beyond header
                for row in rows[1:]: # Skip header row
                    first_cell = row.find(['td', 'th']) # Find first cell (th for header, td for data)
                    if first_cell:
                        vendor_name = first_cell.get_text(strip=True)
                        if vendor_name: # Avoid empty cells
                             initial_vendors.append(vendor_name)
                logger.info(f"Parsed {len(initial_vendors)} vendors from table.")

        # If no table or no vendors found in table, try parsing bullet points
        if not initial_vendors:
             logger.info("No table found or no vendors parsed from table, trying bullet points...")
             # Look for list items (ul/ol -> li)
             lists = soup.find_all(['ul', 'ol'])
             for lst in lists:
                  items = lst.find_all('li')
                  for item in items:
                       # Assume vendor name is the main text of the list item
                       vendor_name = item.get_text(strip=True).split('\n')[0] # Get first line roughly
                       # Basic filtering to avoid generic list items
                       if vendor_name and len(vendor_name) > 2 and not vendor_name.lower().startswith(("note:", "source:", "e.g.")):
                           initial_vendors.append(vendor_name.strip())
             logger.info(f"Parsed {len(initial_vendors)} potential vendors from lists.")

        # Basic deduplication
        initial_vendors = sorted(list(set(initial_vendors)))

        if not initial_vendors:
            logger.error("Could not parse any vendors from the identification file.")
            return None

        logger.info(f"Initial vendor list parsed: {initial_vendors}")

    except Exception as e:
        logger.error(f"Error parsing vendor list from {vendor_id_section_file}: {e}")
        return None

    # --- Step 2: Call LLM to Filter ---
    filtered_vendors = None
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key)

        # Get product category from config file (more robust than passing)
        config_path = base_dir / "misc" / "generation_config.yaml"
        product_category = "Unknown Product"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f_cfg:
                config_data = yaml.safe_load(f_cfg)
                product_category = config_data.get("identifier", product_category)

        filter_prompt = product_prompts.get_filtered_vendor_list_prompt(
            product_category=product_category,
            initial_vendor_list=initial_vendors,
            filtering_questions=questions,
            user_answers=answers
        )

        # Blocking call for filtering
        response = client.generate_content(
            model=LLM_MODEL, # Or maybe a faster model?
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=filter_prompt)])],
            generation_config=types.GenerateContentConfig(temperature=0.3) # Low temp for factual filtering
        )

        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            raw_filtered_text = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
            # Parse the response (one vendor name per line)
            if "NO_MATCHING_VENDORS" in raw_filtered_text:
                 filtered_vendors = []
            else:
                 filtered_vendors = [line.strip() for line in raw_filtered_text.strip().split('\n') if line.strip()]
                 # Optional: Verify filtered vendors are subset of initial list (sanity check)
                 verified_filtered = [v for v in filtered_vendors if any(
                     vendor.lower() in v.lower() or v.lower() in vendor.lower() for vendor in initial_vendors
                 )]
                 if len(verified_filtered) != len(filtered_vendors):
                      logger.warning("LLM filter response included vendors not in the initial list. Using only verified subset.")
                      filtered_vendors = verified_filtered

            logger.info(f"LLM returned filtered vendor list: {filtered_vendors}")
        else:
            logger.error("LLM failed to return a filtered vendor list.")
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                 logger.error(f"Reason: {response.prompt_feedback.block_reason}")
            filtered_vendors = None # Indicate failure

    except Exception as e:
        logger.error(f"Error calling LLM for vendor filtering: {e}")
        import traceback
        logger.error(traceback.format_exc())
        filtered_vendors = None

    # Save the filtered vendor list to the base_dir for reference
    if filtered_vendors is not None:
        try:
            misc_dir = base_dir / "misc"
            misc_dir.mkdir(exist_ok=True)
            with open(misc_dir / "filtered_vendors.txt", 'w', encoding='utf-8') as f:
                f.write(f"# Filtered Vendors based on User Answers\n\n")
                f.write(f"## Original Questions and Answers\n\n")
                for i, (q, a) in enumerate(zip(questions, answers)):
                    f.write(f"Q{i+1}: {q}\n")
                    f.write(f"A{i+1}: {a}\n\n")
                f.write(f"## Filtered Vendor List\n\n")
                for vendor in filtered_vendors:
                    f.write(f"- {vendor}\n")
        except Exception as e:
            logger.error(f"Error saving filtered vendor list: {e}")

    return filtered_vendors

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    try:
        main_cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Process interrupted by user.[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]An unexpected error occurred in main execution:[/]")
        logger.exception(e)