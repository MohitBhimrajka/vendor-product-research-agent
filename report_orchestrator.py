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
    PRODUCT_INITIAL_SECTION_ORDER, PRODUCT_INITIAL_PROMPT_FUNCTIONS, # Add product initial configs
    PRODUCT_FULL_SECTION_ORDER, PRODUCT_FULL_PROMPT_FUNCTIONS # Add product full configs for Phase 2+
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
def _generate_single_section(client: genai.Client, prompt: str, output_path: Path, section_id: str = None, status_dict: Dict = None) -> Dict:
    """Internal function: Generate content for a single prompt/section."""
    start_time = time.time()
    input_tokens = 0
    output_tokens = 0
    
    # Update status to running if status_dict is provided
    if status_dict is not None and section_id is not None:
        status_dict[section_id] = {"status": "running", "start_time": start_time}
    
    if shutdown_requested: # Check before starting work
        if status_dict is not None and section_id is not None:
            status_dict[section_id] = {"status": "skipped", "error": "Shutdown requested before start", "execution_time": 0}
        return {"status": "skipped", "error": "Shutdown requested before start", "execution_time": 0}

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        input_tokens = count_tokens(prompt)

        contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
        # Enable Gemini Grounding (formerly Google Search)
        tools = [types.Tool(google_search=types.GoogleSearch())]  # Removed result_count parameter
        generate_content_config = types.GenerateContentConfig(
            temperature=LLM_TEMPERATURE,
            # Grounding is enabled via the 'tools' parameter in the request
            tools=tools,  # Include tools configuration here
            response_mime_type="text/plain",
        )

        # Using streaming to get the full response
        full_output = ""
        for chunk in client.models.generate_content_stream(  # Use models.generate_content_stream instead
            model=LLM_MODEL,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text is not None:
                full_output += chunk.text

        if not full_output.strip():
            logger.warning(f"Generated empty content for {output_path.name}. Check prompt or model response.")

        output_tokens = count_tokens(full_output)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_output)

        execution_time = time.time() - start_time
        result = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "execution_time": execution_time,
            "status": "success"
        }
        
        # Update status_dict on success if provided
        if status_dict is not None and section_id is not None:
            status_dict[section_id] = {
                "status": "success",
                "execution_time": execution_time,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            }
            
        return result

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Error generating content for {output_path.name}: {str(e)}")
        error_message = f"Error generating content for {output_path.name}: {type(e).__name__} - {str(e)}"
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# Generation Error\n\nAn error occurred while generating this section:\n\n```\n{error_message}\n```")
        except Exception as write_e:
            logger.error(f"Additionally, failed to write error details to {output_path.name}: {write_e}")

        result = {
            "input_tokens": input_tokens,
            "output_tokens": 0,
            "total_tokens": input_tokens,
            "execution_time": execution_time,
            "status": "error",
            "error": error_message
        }
        
        # Update status_dict on error if provided
        if status_dict is not None and section_id is not None:
            status_dict[section_id] = {
                "status": "error",
                "error": error_message,
                "execution_time": execution_time,
                "input_tokens": input_tokens,
                "output_tokens": 0,
                "total_tokens": input_tokens
            }
            
        return result

def _generate_report_sections(
    research_mode: str,
    identifier: str,
    context_company_name: str,
    optional_inputs: Dict[str, Any],
    section_order_config: List[Tuple[str, str]], # e.g., VENDOR_SECTION_ORDER
    prompt_func_config: List[Tuple[str, str]], # e.g., VENDOR_PROMPT_FUNCTIONS
    prompt_module: Any, # The imported module (vendor_prompts or product_prompts)
    status_dict: Dict = None, # New parameter for status tracking
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

    # --- Initialize status dictionary if provided ---
    if status_dict is not None:
        for section_id, _ in prompt_func_config:
            if section_id not in status_dict:  # Initialize only if not already present
                status_dict[section_id] = {"status": "pending"}

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

    # Maximize workers for full parallelism
    max_workers = len(prompt_func_config)  # Use as many workers as there are tasks

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        # Process sections in the order specified by section_order_config
        for section_id, _ in section_order_config:
            if shutdown_requested:
                logger.warning(f"Shutdown requested, skipping section: {section_id}")
                results[section_id] = {"status": "skipped", "error": "Shutdown requested", "execution_time": 0}
                if status_dict is not None:
                    status_dict[section_id] = {"status": "skipped", "error": "Shutdown requested", "execution_time": 0}
                progress.update(section_tasks[section_id], description=f"[yellow]{section_id:.<30}⚠ (Skipped)", completed=1)
                continue

            # Find the corresponding prompt function for this section
            prompt_func_name = next((func for sec, func in prompt_func_config if sec == section_id), None)
            if not prompt_func_name:
                logger.error(f"No prompt function found for section: {section_id}")
                results[section_id] = {"status": "error", "error": f"No prompt function found for section: {section_id}", "execution_time": 0}
                if status_dict is not None:
                    status_dict[section_id] = {"status": "error", "error": f"No prompt function found for section: {section_id}", "execution_time": 0}
                progress.update(section_tasks[section_id], description=f"[red]{section_id:.<30}✗ (No Prompt)", completed=1)
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
                
                # Update status to running
                if status_dict is not None:
                    status_dict[section_id].update({"status": "running"})
                
                # Submit the task
                future = executor.submit(_generate_single_section, client, prompt, output_path, section_id, status_dict)
                futures[future] = section_id

            except AttributeError as attr_e:
                logger.error(f"Prompt function '{prompt_func_name}' not found in module {prompt_module.__name__}. Error: {attr_e}")
                results[section_id] = {"status": "error", "error": f"Prompt function '{prompt_func_name}' not found in {prompt_module.__name__}.", "execution_time": 0}
                if status_dict is not None:
                    status_dict[section_id] = {"status": "error", "error": f"Prompt function not found: {prompt_func_name}", "execution_time": 0}
                progress.update(section_tasks[section_id], description=f"[red]{section_id:.<30}✗ (Not Found)", completed=1)
            except Exception as e:
                logger.error(f"Error preparing prompt for {section_id}: {e}")
                import traceback
                logger.error(f"Detailed error trace: {traceback.format_exc()}")
                results[section_id] = {"status": "error", "error": f"Error preparing prompt: {str(e)}", "execution_time": 0}
                if status_dict is not None:
                    status_dict[section_id] = {"status": "error", "error": f"Error preparing prompt: {str(e)}", "execution_time": 0}
                progress.update(section_tasks[section_id], description=f"[red]{section_id:.<30}✗ (Prompt Error)", completed=1)

        logger.info(f"Submitted {len(futures)} sections for generation.")

        # --- Collect results as they complete ---
        temp_results = {}
        processed_count = 0
        logger.info("Waiting for section generation results...")
        
        # Process futures in order of completion
        for future in as_completed(futures):
            section_id = futures[future]
            try:
                # This is the blocking call where a hang might occur
                result = future.result()
                temp_results[section_id] = result
                
                # Update status immediately when a section completes
                if status_dict is not None:
                    status_dict[section_id].update({
                        "status": result.get("status", "unknown"),
                        "error": result.get("error"),
                        "execution_time": result.get("execution_time", 0)
                    })
                
                # Update progress immediately
                status_char = "✓" if result.get("status") == 'success' else ("✗" if result.get("status") == "error" else "⚠")
                color = "green" if result.get("status") == 'success' else ("red" if result.get("status") == "error" else "yellow")
                status_text = f"({result.get('status', 'unknown')})"
                progress.update(section_tasks[section_id],
                             advance=1,
                             description=f"[{color}]{section_id:.<30}{status_char} {status_text}")
                
                logger.debug(f"Result received for section: {section_id}, status: {result.get('status')}")
            except Exception as e:
                logger.error(f"Error retrieving result for {section_id}: {str(e)}")
                temp_results[section_id] = {"status": "error", "error": f"Future result error: {str(e)}", "execution_time": 0}
                if status_dict is not None:
                    status_dict[section_id].update({"status": "error", "error": f"Future result error: {str(e)}"})
                progress.update(section_tasks[section_id], description=f"[red]{section_id:.<30}✗ (Result Error)", completed=1)
            finally:
                processed_count += 1
                progress.update(main_task, completed=processed_count)
                logger.debug(f"Processed {processed_count}/{len(futures)} futures.")

        logger.info("All section generation futures completed.")

        # Update final results
        results = temp_results

    # --- Compile Stats & Save ---
    logger.info("Compiling final statistics...")
    total_execution_time = time.time() - start_time
    # Filter out skipped sections when calculating summary stats unless needed
    valid_results = {k: v for k, v in results.items() if v.get('status') != 'skipped'}
    
    # Calculate section counts and success percentage
    total_sections_requested = len(prompt_func_config)
    successful_sections_count = sum(1 for r in results.values() if r.get("status") == "success")
    success_percentage_val = (successful_sections_count / total_sections_requested * 100) if total_sections_requested > 0 else 0

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
            "successful_sections": successful_sections_count,
            "failed_sections": sum(1 for r in results.values() if r.get("status") == 'error'),
            "interrupted_sections": sum(1 for r in results.values() if r.get("status") == 'interrupted'),
            "skipped_sections": sum(1 for r in results.values() if r.get("status") == 'skipped'),
            "was_interrupted": shutdown_requested,
            "total_sections": total_sections_requested,
            "success_percentage": success_percentage_val
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
    status_dict: Dict = None, # Add status_dict parameter
    progress_context=None # Accept progress context from Streamlit
    ) -> Tuple[Optional[Dict], Optional[Path], Optional[Dict]]: # Added dashboard_data return
    """Runs the full vendor research process and dashboard summary."""
    global shutdown_requested
    if shutdown_requested: return None, None, None

    console.print(f"\n[bold blue]Starting Vendor Research for: {vendor_name}[/bold blue]")
    
    token_stats, base_dir = _generate_report_sections(
        research_mode='vendor', identifier=vendor_name, context_company_name=context_company_name,
        optional_inputs=optional_inputs, section_order_config=VENDOR_SECTION_ORDER, 
        prompt_func_config=VENDOR_PROMPT_FUNCTIONS, prompt_module=vendor_prompts,
        status_dict=status_dict, # Pass status_dict
        progress_context=progress_context
    )
    
    if not token_stats or not base_dir: return None, None, None
    
    # Store the base_dir in token_stats to ensure it's available for deep dive integration
    token_stats['base_dir'] = str(base_dir)
    
    # Only process PDF and dashboard if we have successful sections and weren't interrupted
    pdf_path = None 
    dashboard_data = None
    
    if token_stats['summary']['successful_sections'] > 0 and not token_stats['summary']['was_interrupted']:
        # Generate PDF
        try:
            pdf_path_generated = process_markdown_files(
                base_dir=base_dir, identifier=vendor_name, report_type_name="VendorReport",
                section_order=VENDOR_SECTION_ORDER
            )
            if pdf_path_generated and pdf_path_generated.exists():
                pdf_path = pdf_path_generated
                console.print(f"[green]PDF report generated: {pdf_path}[/green]")
            else:
                console.print("[red]PDF generation failed.[/red]")
        except Exception as e:
            console.print(f"[red]Error generating PDF: {e}[/red]")
            logger.exception(f"PDF Generation Error for {vendor_name}")
        
        # Generate Dashboard data
        dashboard_data = _generate_dashboard_data(base_dir, 'vendor', token_stats)

    # Format summary for display
    console.print(Panel.fit(
        f"Vendor Research for '{vendor_name}' processing complete.\n"
        f"Time: {token_stats['summary']['formatted_execution_time']}\n"
        f"Token Usage: {token_stats['summary']['total_tokens']} "
        f"[Input: {token_stats['summary']['total_input_tokens']}, Output: {token_stats['summary']['total_output_tokens']}]\n"
        f"Sections: {token_stats['summary']['successful_sections']}/{token_stats['summary']['total_sections']} "
        f"[{token_stats['summary']['success_percentage']:.1f}%]\n"
        f"PDF Generated: {'Yes' if pdf_path else 'No'}\n"
        f"Dashboard Data Generated: {'Yes' if dashboard_data and 'error' not in dashboard_data else 'No/Error'}\n"
        f"Output Dir: {base_dir}",
        title="Vendor Research Summary", border_style="blue"
    ))
    
    return token_stats, pdf_path, dashboard_data # Return dashboard data


# --- New Function for Initial Product Analysis ---
def run_product_research_initial(
    product_category: str,
    context_company_name: str,
    optional_inputs: Dict,
    status_dict: Dict = None, # Add status_dict parameter
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
        status_dict=status_dict, # Pass status_dict
        progress_context=progress_context
    )

    if not token_stats or not base_dir:
        console.print(f"[red]Initial product analysis section generation failed for {product_category}.[/red]")
        return None, None, None

    # --- Generate PDF for initial report ---
    initial_pdf_path = None
    if token_stats['summary']['successful_sections'] > 0 and not token_stats['summary']['was_interrupted']:
        console.print(f"\n[bold cyan]Generating initial PDF report for {product_category}...[/bold cyan]")
        try:
            # Use the specific section order for the initial analysis PDF
            initial_pdf_path = process_markdown_files(
                base_dir=base_dir,
                identifier=product_category,
                report_type_name="ProductInitialAnalysis", # Distinct name
                section_order=PRODUCT_INITIAL_SECTION_ORDER # Use the initial order config
            )
            if initial_pdf_path and initial_pdf_path.exists():
                console.print(f"\n[green]Initial PDF report generated: {initial_pdf_path}[/green]")
            else:
                console.print(f"\n[yellow]Initial PDF generation did not return a valid path for {product_category}.[/yellow]")
        except Exception as pdf_e:
            console.print(f"\n[red]Error during initial PDF generation for {product_category}: {pdf_e}[/red]")
            logger.exception(f"Initial PDF Generation Error for {base_dir}")
    # --- End PDF Generation ---

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

        # Update status to running if status_dict is provided
        if status_dict is not None:
            question_section_id = "product_filter_questions"
            if question_section_id not in status_dict:
                status_dict[question_section_id] = {"status": "pending"}
            status_dict[question_section_id].update({"status": "running"})

        # Use the updated method to generate content
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=question_gen_prompt)])]
        generate_content_config = types.GenerateContentConfig(
            temperature=0.7, # Higher temp for faster generation
            response_mime_type="text/plain",
        )

        # Use streaming to get the complete response
        raw_questions_text = ""
        for chunk in client.models.generate_content_stream(
            model=LLM_MODEL,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text is not None:
                raw_questions_text += chunk.text

        # Parse the '- ' prefixed lines into a list
        filtering_questions = [q.strip('- ').strip() for q in raw_questions_text.strip().split('\n') if q.strip().startswith('- ')]
        
        # Update status to complete if successful
        if status_dict is not None and filtering_questions:
            status_dict[question_section_id].update({
                "status": "success", 
                "execution_time": 0, # We don't track time for this separately
                "output": f"Generated {len(filtering_questions)} filtering questions"
            })
            
        console.print(f"[green]Generated {len(filtering_questions)} filtering questions.[/green]")
        
        # Save the questions to a file for reference
        questions_path = markdown_dir / "product_filter_questions.md"
        try:
            with open(questions_path, 'w', encoding='utf-8') as f:
                f.write(f"# Filter Questions for {product_category}\n\n")
                for i, q in enumerate(filtering_questions, 1):
                    f.write(f"{i}. {q}\n\n")
            logger.info(f"Saved {len(filtering_questions)} filter questions to {questions_path}")
        except Exception as save_e:
            logger.warning(f"Could not save filter questions to file: {save_e}")

    except Exception as e:
        logger.error(f"Failed to generate filtering questions: {e}")
        # Update status to error if failed
        if status_dict is not None:
            question_section_id = "product_filter_questions"
            status_dict[question_section_id].update({
                "status": "error", 
                "error": f"Failed to generate filtering questions: {str(e)}"
            })
        # Proceed without questions, but log the error

    # Return results including the questions
    return token_stats, base_dir, filtering_questions

def run_product_research(
    product_category: str, 
    context_company_name: str, 
    optional_inputs: Dict,
    progress_context=None
) -> Tuple[Optional[Dict], Optional[Path]]:
    """
    Multi-stage product research function.
    Stage 1: Initial analysis (definition, market, features, compliance, initial vendors)
    Stage 2: (Interactive) Vendor filtering, profiles, comparison, relevance, recommendations
    Stage 3: (Optional) Deep dives on selected vendors
    
    Note: In a real UI, stages 2-3 would be interactive based on user input.
    For CLI/testing, this runs a simplified process.
    """
    global shutdown_requested
    console.print(f"\n[bold magenta]Starting Product Research for: {product_category}[/bold magenta]")
    
    # --- Stage 1: Initial Analysis ---
    token_stats, base_dir, filtering_questions = run_product_research_initial(
        product_category=product_category,
        context_company_name=context_company_name,
        optional_inputs=optional_inputs,
        progress_context=progress_context
    )
    
    if not token_stats or not base_dir:
        console.print(f"[red]Product research initial analysis failed for {product_category}.[/red]")
        return None, None
    
    # Display summary panel with filtering questions if available
    questions_text = "\n".join([f"• {q}" for q in filtering_questions]) if filtering_questions else "None generated"
    console.print(Panel.fit(
        f"Product Research Initial Analysis for '{product_category}' complete.\n"
        f"Time: {token_stats['summary']['formatted_execution_time']}\n"
        f"Successful Sections: [green]{token_stats['summary']['successful_sections']}[/]\n"
        f"Failed Sections: [red]{token_stats['summary']['failed_sections']}[/]\n"
        f"Generated Filtering Questions: {len(filtering_questions) if filtering_questions else 0}\n"
        f"Output Dir: {base_dir}",
        title="Product Research Stage 1 Summary", border_style="magenta"
    ))
    
    # Generate a simple PDF with initial findings
    initial_pdf_path = None
    if token_stats['summary']['successful_sections'] > 0 and not token_stats['summary']['was_interrupted']:
        console.print(f"\n[bold cyan]Generating initial PDF report for {product_category}...[/bold cyan]")
        try:
            # Pass the correct section order for PDF generation
            initial_pdf_path = process_markdown_files(
                base_dir=base_dir,
                identifier=product_category,
                report_type_name="ProductInitialAnalysis",
                section_order=PRODUCT_INITIAL_SECTION_ORDER
            )
            if initial_pdf_path and initial_pdf_path.exists():
                console.print(f"\n[green]Initial PDF report generated: {initial_pdf_path}[/green]")
            else:
                console.print(f"\n[yellow]PDF generation did not return a valid path for {product_category}.[/yellow]")
        except Exception as pdf_e:
            console.print(f"\n[red]Error during PDF generation for {product_category}: {pdf_e}[/red]")
            logger.exception(f"PDF Generation Error for {base_dir}")
    
    if filtering_questions:
        console.print(Panel.fit(
            questions_text,
            title="Filtering Questions", border_style="cyan"
        ))
    
    # --- Stage 2: Interactive Vendor Filtering & Comparison (Simulated for CLI) ---
    # In a real UI, user would answer these questions and select comparison criteria
    # For now, we'll simulate this with some simple defaults
    
    # Default to all vendors if no filtering done
    filtered_vendors = []
    deep_dive_vendors = []  # Track vendors for deep dives
    deep_dive_results = {}  # Store deep dive results
    
    if filtering_questions:
        # CLI-only: Simulate user answers
        if not progress_context:  # Only do interactive mode in CLI, not when called from app
            console.print("\n[yellow]Interactive Filtering Mode (CLI only)[/yellow]")
            answers = []
            for i, question in enumerate(filtering_questions):
                answer = console.input(f"Question {i+1}: {question}\nYour Answer: ")
                answers.append(answer)
            
            # Process the answers to filter vendors
            filtered_vendors = filter_vendors_based_on_answers(base_dir, filtering_questions, answers)
            
            # Let user select comparison criteria
            default_criteria = ["Features", "Pricing Model", "Target Company Size", "Implementation Time"]
            criteria_input = console.input(f"Enter comparison criteria (comma-separated, default: {', '.join(default_criteria)}): ")
            comparison_criteria = [c.strip() for c in criteria_input.split(',')] if criteria_input.strip() else default_criteria
        else:
            # When called from app.py, we'll get filtered vendors and criteria from there
            console.print("[yellow]Skipping interactive filtering in non-CLI mode[/yellow]")
            filtered_vendors = []  # Will be provided by app.py
            comparison_criteria = []  # Will be provided by app.py
    else:
        # Extract all vendors from the vendor identification section
        vendor_id_section_file = base_dir / "markdown" / "product_vendor_identification.md"
        if vendor_id_section_file.exists():
            try:
                with open(vendor_id_section_file, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                # Extract vendors using YAML format (see filter_vendors_based_on_answers)
                yaml_pattern = r"VENDOR_LIST_START\s*\n(.*?)\s*VENDOR_LIST_END"
                yaml_match = re.search(yaml_pattern, md_content, re.DOTALL)
                if yaml_match:
                    vendor_list_text = yaml_match.group(1).strip()
                    filtered_vendors = [line[1:].strip() for line in vendor_list_text.split('\n') 
                                     if line.strip().startswith('-')]
            except Exception as e:
                logger.error(f"Error extracting vendors from vendor identification section: {e}")
                filtered_vendors = []
        # Default comparison criteria
        comparison_criteria = ["Features", "Pricing Model", "Target Company Size", "Implementation Time"]
    
    # If we have filtered vendors, run Phase 2
    if filtered_vendors:
        console.print(f"\n[bold green]Using filtered vendors: {', '.join(filtered_vendors)}[/bold green]")
        console.print(f"[bold green]Using comparison criteria: {', '.join(comparison_criteria)}[/bold green]")
        
        # Run Phase 2 with the filtered vendors
        phase2_stats = generate_product_report_phase2(
            base_dir=base_dir,
            product_category=product_category,
            context_company_name=context_company_name,
            optional_inputs=optional_inputs,
            filtered_vendors=filtered_vendors,
            comparison_criteria=comparison_criteria,
            progress_context=progress_context
        )
        
        if phase2_stats:
            console.print(Panel.fit(
                f"Product Research Phase 2 for '{product_category}' complete.\n"
                f"Time: {phase2_stats.get('formatted_execution_time', 'unknown')}\n"
                f"Successful Sections: [green]{phase2_stats.get('successful_sections', 0)}[/]\n"
                f"Failed Sections: [red]{phase2_stats.get('failed_sections', 0)}[/]",
                title="Product Research Stage 2 Summary", border_style="green"
            ))
            
            # --- Stage 3: Deep Dives (Optional, CLI Only) ---
            if not progress_context and filtered_vendors:  # Only in CLI mode
                deep_dive_vendors = []
                dive_option = console.input("\nDo you want to run deep dives on any vendors? (y/n): ").lower()
                if dive_option == 'y':
                    vendor_list = "\n".join([f"{i+1}. {v}" for i, v in enumerate(filtered_vendors)])
                    console.print(f"Available vendors:\n{vendor_list}")
                    selection = console.input("Enter vendor numbers (comma-separated) for deep dive: ")
                    try:
                        selected_indices = [int(idx.strip()) - 1 for idx in selection.split(',') if idx.strip().isdigit()]
                        deep_dive_vendors = [filtered_vendors[idx] for idx in selected_indices if 0 <= idx < len(filtered_vendors)]
                        
                        if deep_dive_vendors:
                            # Trigger deep dives
                            deep_dive_results = trigger_vendor_deep_dives(
                                base_dir=base_dir,
                                vendors_to_research=deep_dive_vendors,
                                context_company_name=context_company_name,
                                optional_inputs=optional_inputs
                            )
                            
                            # Display deep dive summary
                            deep_dive_summary = "\n".join([
                                f"• {vendor}: {'Success' if stats.get('summary', {}).get('successful_sections', 0) > 0 else 'Failed'}"
                                for vendor, (stats, _, _, _) in deep_dive_results.items()
                            ])
                            console.print(Panel.fit(
                                f"Deep Dive Results:\n{deep_dive_summary}",
                                title="Product Research Stage 3 Summary", border_style="yellow"
                            ))
                    except Exception as e:
                        logger.error(f"Error processing deep dive selection: {e}")
            
            # Generate a final PDF with all sections including deep dives
            final_pdf_path = None
            if phase2_stats.get('successful_sections', 0) > 0 and not phase2_stats.get('was_interrupted', False):
                console.print(f"\n[bold cyan]Generating final PDF report for {product_category}...[/bold cyan]")
                try:
                    # Generate the final product report with all sections and deep dives
                    final_pdf_path, final_dashboard_data = generate_final_product_report(
                        base_dir=base_dir,
                        product_category=product_category,
                        context_company_name=context_company_name,
                        optional_inputs=optional_inputs,
                        filtered_vendors=filtered_vendors,
                        deep_dive_vendors=deep_dive_vendors
                    )
                    
                    if final_pdf_path and final_pdf_path.exists():
                        console.print(f"\n[green]Final PDF report generated: {final_pdf_path}[/green]")
                        return token_stats, final_pdf_path  # Return the final PDF path
                    else:
                        console.print(f"\n[yellow]Final PDF generation did not return a valid path.[/yellow]")
                except Exception as pdf_e:
                    console.print(f"\n[red]Error during final PDF generation: {pdf_e}[/red]")
                    logger.exception(f"Final PDF Generation Error for {base_dir}")
        else:
            console.print("[yellow]Phase 2 did not return valid statistics.[/yellow]")
    else:
        console.print("[yellow]No vendors filtered/identified for Phase 2. Stopping at initial analysis.[/yellow]")
    
    # Return initial token stats and PDF path if no final PDF was generated
    return token_stats, initial_pdf_path


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
    answers: List[str],
    status_dict: Dict = None # Add status_dict parameter
) -> Optional[List[str]]:
    """
    Parses the initial vendor list, calls LLM to filter based on Q&A,
    and returns the filtered list.
    """
    global shutdown_requested
    if shutdown_requested: return None # Check for interrupt

    console.print("[magenta]Processing user answers to filter vendors...[/magenta]")
    
    # Update status to running if status_dict is provided
    filter_section_id = "vendor_filtering"
    if status_dict is not None:
        if filter_section_id not in status_dict:
            status_dict[filter_section_id] = {"status": "pending"}
        status_dict[filter_section_id].update({"status": "running"})

    # --- Step 1: Parse Initial Vendor List ---
    initial_vendors = []
    vendor_id_section_file = base_dir / "markdown" / "product_vendor_identification.md"
    if not vendor_id_section_file.exists():
        logger.error(f"Vendor identification file not found: {vendor_id_section_file}")
        if status_dict is not None:
            status_dict[filter_section_id].update({
                "status": "error", 
                "error": f"Vendor identification file not found: {vendor_id_section_file}"
            })
        return None # Cannot proceed without the initial list

    try:
        with open(vendor_id_section_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # --- PRIMARY PARSING METHOD: structured VENDOR_LIST format ---
        structured_format_found = False
        vendor_list_match = re.search(r"VENDOR_LIST_START\s*\n(.*?)\s*VENDOR_LIST_END", md_content, re.DOTALL)
        
        if vendor_list_match:
            structured_format_found = True
            vendor_list_text = vendor_list_match.group(1).strip()
            # Parse the list (each line should have a leading dash or asterisk)
            vendor_lines = [line.strip() for line in vendor_list_text.split('\n')]
            # Extract vendor names (remove leading "-" or "*" and spaces)
            for line in vendor_lines:
                if line.startswith('-') or line.startswith('*'):
                    vendor_name = line[1:].strip()
                    if vendor_name and not vendor_name.startswith('[') and not vendor_name.endswith('...]'):
                        initial_vendors.append(vendor_name)
            
            if initial_vendors:
                logger.info(f"Successfully parsed {len(initial_vendors)} vendors from VENDOR_LIST_START/END structured format")
        
        # --- FALLBACK PARSING METHODS (if structured format fails) ---
        if not structured_format_found or not initial_vendors:
            logger.warning("Could not find VENDOR_LIST_START/END format or no vendors extracted. Trying alternative formats...")
            
            # Try other structured formats (YAML, code blocks)
            alternative_patterns = [
                r"```yaml\s*\n(.*?)\s*```",
                r"```\s*\n(.*?)\s*```",
                r"VENDORS:\s*\n(.*?)(?:\n\n|\n#|\n\*\*|$)"
            ]
            
            for pattern in alternative_patterns:
                if initial_vendors: 
                    break  # Stop if we've already found vendors
                    
                match = re.search(pattern, md_content, re.DOTALL)
                if match:
                    vendor_list_text = match.group(1).strip()
                    vendor_lines = [line.strip() for line in vendor_list_text.split('\n')]
                    for line in vendor_lines:
                        if line.startswith('-') or line.startswith('*'):
                            vendor_name = line[1:].strip()
                            if vendor_name and not vendor_name.startswith('[') and not vendor_name.endswith('...]'):
                                initial_vendors.append(vendor_name)
                    
                    if initial_vendors:
                        logger.info(f"Parsed {len(initial_vendors)} vendors from alternative structured format: {pattern}")
            
            # Only proceed to more complex parsing if still no vendors found
            if not initial_vendors:
                logger.warning("No vendors found in any structured format. Attempting HTML parsing...")
                
                # Convert markdown to HTML for more reliable parsing
                html_content = markdown.markdown(md_content, extensions=['tables', 'extra'])
                soup = BeautifulSoup(html_content, 'html.parser')
    
                # Try parsing from a table first
                table = soup.find('table')
                if table:
                    rows = table.find_all('tr')
                    if len(rows) > 1: # Has data rows beyond header
                        for row in rows[1:]: # Skip header
                            first_cell = row.find(['td', 'th'])
                            if first_cell:
                                vendor_name = first_cell.get_text(strip=True)
                                if vendor_name and not vendor_name.startswith('[') and not vendor_name.endswith(']'):
                                     initial_vendors.append(vendor_name)
                        logger.info(f"Parsed {len(initial_vendors)} vendors from HTML table")
    
                # If no vendors from table, try bullet lists
                if not initial_vendors:
                    lists = soup.find_all(['ul', 'ol'])
                    for lst in lists:
                        items = lst.find_all('li')
                        for item in items:
                            vendor_name = item.get_text(strip=True).split('\n')[0]
                            # Basic filtering to avoid non-vendor items
                            if vendor_name and len(vendor_name) > 2 and not vendor_name.lower().startswith(("note:", "source:", "e.g.")):
                                initial_vendors.append(vendor_name.strip())
                    
                    if initial_vendors:
                        logger.info(f"Parsed {len(initial_vendors)} vendors from HTML lists")
                 
                # Last resort: aggressive heading-based extraction
                if not initial_vendors:
                    logger.warning("No vendors found in structured elements. Attempting aggressive text extraction...")
                    vendor_section_headings = ["identified vendors", "key vendors", "major vendors", "vendor list", "potential vendors"]
                    
                    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    for heading in headings:
                        heading_text = heading.get_text().lower()
                        if any(section in heading_text for section in vendor_section_headings):
                            next_el = heading.find_next(['p', 'ul', 'ol'])
                            while next_el and next_el.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                                if next_el.name == 'p':
                                    text = next_el.get_text()
                                    for candidate in re.split(r'[,;]\s*|\s+and\s+|\s*\n\s*', text):
                                        candidate = candidate.strip()
                                        if candidate and len(candidate) > 2 and candidate[0].isupper():
                                            initial_vendors.append(candidate)
                                next_el = next_el.find_next()
                    
                    if initial_vendors:
                        logger.warning(f"Extracted {len(initial_vendors)} potential vendors using aggressive text parsing - verify results")

        # --- Post-processing for all parsing methods ---
        # Clean up vendor names
        if initial_vendors:
            # Remove any placeholder text
            initial_vendors = [v for v in initial_vendors if not v.startswith('[') and not v.endswith(']') and v.strip() != '...']
            
            # Remove citation markers and parenthetical notes
            initial_vendors = [re.sub(r'\s*\[\w+\d*\]', '', v) for v in initial_vendors]  # [SS1], [1], etc.
            initial_vendors = [re.sub(r'\s*\([^)]*\)', '', v) for v in initial_vendors]   # (notes)
            
            # Sort and deduplicate
            initial_vendors = sorted(list(set(initial_vendors)))
            logger.info(f"Final cleaned vendor list: {initial_vendors}")
        
        if not initial_vendors:
            logger.error("Could not parse any vendors using any method. Check the vendor identification file format.")
            if status_dict is not None:
                status_dict[filter_section_id].update({
                    "status": "error", 
                    "error": "Could not parse any vendors using any method. Check the vendor identification file format."
                })
            return None

    except Exception as e:
        logger.error(f"Error parsing vendor list from {vendor_id_section_file}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        if status_dict is not None:
            status_dict[filter_section_id].update({
                "status": "error", 
                "error": f"Error parsing vendor list: {str(e)}"
            })
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

        # Use updated method to get filtered vendors
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=filter_prompt)])]
        generate_content_config = types.GenerateContentConfig(
            temperature=0.7  # Higher temp for faster generation
        )

        # Use streaming to get the complete response
        raw_filtered_text = ""
        for chunk in client.models.generate_content_stream(
            model=LLM_MODEL,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text is not None:
                raw_filtered_text += chunk.text
            
        # Check for the NO_MATCHING_VENDORS signal
        if "NO_MATCHING_VENDORS" in raw_filtered_text:
            filtered_vendors = []
            logger.info("LLM indicated no matching vendors based on user criteria.")
        else:
            # Try to parse the structured format first
            structured_pattern = r"FILTERED_VENDORS_START\s*\n(.*?)\s*FILTERED_VENDORS_END"
            structured_match = re.search(structured_pattern, raw_filtered_text, re.DOTALL)
            raw_filtered_list = [] # Store initially parsed names

            if structured_match:
                vendor_list_text = structured_match.group(1).strip()
                # Parse lines, removing '- ' if present
                raw_filtered_list = [
                    line.strip()[2:].strip() if line.strip().startswith('- ') else line.strip()
                    for line in vendor_list_text.split('\n')
                    if line.strip() and not line.strip().startswith('[') and not line.strip() == '...'
                ]
                logger.info(f"Parsed {len(raw_filtered_list)} potential vendors from structured format: {raw_filtered_list}")
            else:
                # Fallback logic (keep as is for now, but ideally LLM should always return structured)
                logger.warning("Structured format not found in LLM response, falling back to line-by-line parsing.")
                raw_filtered_list = [line.strip() for line in raw_filtered_text.strip().split('\n') if line.strip()]

            # --- Verification and Final List Creation ---
            filtered_vendors = [] # Final clean list
            verified_filtered_set = set() # Use a set for efficient lookup during verification

            for potential_vendor in raw_filtered_list:
                # Normalize the vendor name suggested by LLM
                normalized_potential = potential_vendor.lower().replace("inc.", "").replace("ltd.", "").replace("corporation", "").replace("corp.", "").strip()

                # Check against initial vendors
                matched_original_name = None
                for initial_vendor in initial_vendors:
                    normalized_initial = initial_vendor.lower().replace("inc.", "").replace("ltd.", "").replace("corporation", "").replace("corp.", "").strip()

                    # More flexible matching (handle cases like "Dell" vs "Dell Technologies")
                    # Check if one is a substring of the other OR very similar
                    if normalized_potential == normalized_initial or normalized_potential in normalized_initial or normalized_initial in normalized_potential:
                         # Check if we already added this original vendor
                         if initial_vendor not in verified_filtered_set:
                             matched_original_name = initial_vendor # Store the original name
                             break # Found a match

                if matched_original_name:
                    filtered_vendors.append(matched_original_name)
                    verified_filtered_set.add(matched_original_name) # Add original name to set
                else:
                    logger.warning(f"Vendor '{potential_vendor}' suggested by LLM doesn't clearly match any initial vendor. Excluding.")

            if len(raw_filtered_list) != len(filtered_vendors):
                logger.warning(f"LLM suggested {len(raw_filtered_list)} vendors but only {len(filtered_vendors)} were verified against the initial list.")

            # Ensure the final list is unique and sorted
            filtered_vendors = sorted(list(set(filtered_vendors)))

            logger.info(f"Final filtered vendor list: {filtered_vendors}") # Should now contain clean names

        logger.info(f"Final filtered vendor list: {filtered_vendors}")
        
        # Update status to success
        if status_dict is not None:
            status_dict[filter_section_id].update({
                "status": "success", 
                "execution_time": 0, # We don't track time for this separately
                "output": f"Filtered down to {len(filtered_vendors)} vendors"
            })
            
    except Exception as e:
        logger.error(f"Error calling LLM for vendor filtering: {e}")
        import traceback
        logger.error(traceback.format_exc())
        filtered_vendors = None
        
        # Update status to error
        if status_dict is not None:
            status_dict[filter_section_id].update({
                "status": "error", 
                "error": f"Error filtering vendors: {str(e)}"
            })

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
                    
            # Also save as markdown file for visibility in the UI
            markdown_dir = base_dir / "markdown"
            with open(markdown_dir / "filtered_vendors.md", 'w', encoding='utf-8') as f:
                f.write(f"# Filtered Vendors\n\n")
                f.write(f"Based on your answers to the filtering questions, the following vendors were identified as the best matches for your needs:\n\n")
                for vendor in filtered_vendors:
                    f.write(f"- **{vendor}**\n")
                f.write(f"\n\n## Your Filtering Criteria\n\n")
                for i, (q, a) in enumerate(zip(questions, answers)):
                    f.write(f"**Q{i+1}:** {q}\n\n")
                    f.write(f"**A{i+1}:** {a}\n\n")
                    
        except Exception as e:
            logger.error(f"Error saving filtered vendor list: {e}")

    return filtered_vendors

# --- New Helper Function for gathering content from markdown files ---
def _gather_markdown_content(
    base_dir: Path,
    section_ids: List[str]
) -> str:
    """
    Reads and concatenates content from specified markdown files.
    Returns the combined content as a string.
    """
    markdown_dir = base_dir / "markdown"
    combined_content = ""
    
    for section_id in section_ids:
        md_path = markdown_dir / f"{section_id}.md"
        if md_path.exists():
            try:
                with open(md_path, 'r', encoding='utf-8') as f:
                    combined_content += f"\n\n## {section_id.replace('_', ' ').title()}\n\n"
                    combined_content += f.read()
            except Exception as e:
                logger.warning(f"Could not read {md_path} for content gathering: {e}")
    
    return combined_content

# --- New Function for Phase 4: Profiles, Comparison, Relevance ---
def generate_product_report_phase2(
    base_dir: Path, # Base directory from initial run
    product_category: str,
    context_company_name: str,
    optional_inputs: Dict,
    filtered_vendors: List[str],
    comparison_criteria: List[str], # From user selection
    status_dict: Dict = None, # Add status_dict parameter
    progress_context=None
) -> Tuple[Optional[Dict], Optional[Dict]]: # Returns (summary_stats, dashboard_data)
    """
    Generates light profiles, comparison matrix, and relevance sections.
    Appends markdown files to the existing base_dir/markdown.
    Returns updated token statistics summary AND dashboard data for this phase.
    """
    global shutdown_requested
    phase2_start_time = time.time()
    console.print(f"\n[bold green]Starting Product Report Phase 2 (Profiles, Comparison, Relevance) for: {product_category}[/bold green]")

    markdown_dir = base_dir / "markdown"
    if not markdown_dir.exists():
        logger.error(f"Markdown directory not found for Phase 2: {markdown_dir}")
        return None, None

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: logger.error("GEMINI_API_KEY not found."); return None, None
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Google GenAI Client: {e}"); return None, None

    phase2_results = {}
    tasks_to_run = [] # List of tuples: (section_id, prompt_func, args_dict, output_filename)

    # 1. Prepare Light Profile Tasks
    if filtered_vendors:
        for vendor in filtered_vendors:
            # --- ENSURE CONSISTENT SANITIZATION ---
            # Use the same sanitization as app.py will use later
            sanitized_vendor = re.sub(r'[^a-zA-Z0-9_]', '_', vendor)
            section_id = f"profile_{sanitized_vendor}" # Use sanitized name for internal ID
            output_filename = f"{section_id}.md" # Output filename
            # --- END SANITIZATION UPDATE ---
            
            tasks_to_run.append((
                section_id,
                product_prompts.get_vendor_light_profile_prompt, # Use the correct function
                { # Args for the prompt function
                    'vendor_name': vendor,
                    'product_category': product_category,
                    'language': "English",
                    'context_company_name': context_company_name,
                    **optional_inputs
                },
                output_filename
            ))
    else:
        logger.warning("No filtered vendors provided for profiling.")

    # 2. Prepare Comparison Matrix Task (if vendors and criteria exist)
    if filtered_vendors and comparison_criteria:
        tasks_to_run.append((
            "comparison_matrix",
            product_prompts.get_vendor_comparison_matrix_prompt,
            {
                'product_category': product_category,
                'filtered_vendors': filtered_vendors,
                'comparison_criteria': comparison_criteria,
                'language': "English",
                'context_company_name': context_company_name,
                **optional_inputs
            },
            "comparison_matrix.md"
        ))
    else:
        logger.warning("Skipping comparison matrix (no vendors or criteria).")

    # Gather content from relevant markdown files for summaries
    market_summary = _gather_markdown_content(
        base_dir, 
        ["market_overview", "market_trends", "market_segmentation"]
    )
    if not market_summary:
        market_summary = "[Market Summary from Initial Analysis - Placeholder]"
        logger.warning("Could not find market summary content, using placeholder.")
    
    # For comparison summary, we'll attempt to get it, but will likely only have it AFTER comparison_matrix is generated
    # So this might be empty for the relevance prompt initially
    comparison_summary = _gather_markdown_content(base_dir, ["comparison_matrix"])
    if not comparison_summary:
        comparison_summary = "[Comparison Summary - Placeholder]"
        logger.warning("No comparison matrix content found yet, using placeholder.")
    
    # Gather all available analysis for the recommendations
    analysis_sections = [
        "market_overview", "market_trends", "market_segmentation", 
        "feature_analysis", "pricing_models", "integration_options"
    ]
    analysis_summary = _gather_markdown_content(base_dir, analysis_sections)
    if not analysis_summary:
        analysis_summary = "[Combined Analysis Summary - Placeholder]"
        logger.warning("Could not find analysis content, using placeholder.")

    # 3. Prepare Relevance & Recommendations Tasks with gathered summaries
    tasks_to_run.append((
        "product_relevance",
        product_prompts.get_product_relevance_prompt,
        {
            'product_category': product_category,
            'market_summary': market_summary, 
            'filtered_vendors': filtered_vendors or [],
            'comparison_summary': comparison_summary,
            'language': "English",
            'context_company_name': context_company_name,
            **optional_inputs
        },
        "product_relevance.md"
    ))

    # Assume recommendations prompt exists
    if hasattr(product_prompts, 'get_product_recommendations_prompt'):
         tasks_to_run.append((
             "product_recommendations",
             product_prompts.get_product_recommendations_prompt,
             {
                 'product_category': product_category,
                 'analysis_summary': analysis_summary,
                 'language': "English",
                 'context_company_name': context_company_name,
                 **optional_inputs
             },
             "product_recommendations.md"
         ))

    # --- Initialize status dictionary if provided ---
    if status_dict is not None:
        for section_id, _, _, _ in tasks_to_run:
            if section_id not in status_dict:  # Initialize only if not already present
                status_dict[section_id] = {"status": "pending"}

    # --- Execute Phase 2 Tasks ---
    progress = progress_context or Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(),
            TaskProgressColumn(), TimeElapsedColumn(), console=console, transient=True
        )
    main_task_p2 = progress.add_task(f"Generating Phase 2 sections...", total=len(tasks_to_run))

    section_tasks_p2 = {
        task_id: progress.add_task(f"[green]{task_id[:30]:.<30}", total=1, visible=True, parent=main_task_p2)
        for task_id, _, _, _ in tasks_to_run
    }

    # Maximize workers for Phase 2
    max_workers = len(tasks_to_run)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        # Order tasks based on their presence in PRODUCT_FULL_SECTION_ORDER
        # This ensures sections are processed in the correct order
        # Start by extracting the section IDs from PRODUCT_FULL_SECTION_ORDER
        product_full_section_ids = [section_id for section_id, _ in PRODUCT_FULL_SECTION_ORDER]
        
        # Sort tasks_to_run based on their order in product_full_section_ids
        # For profile sections, maintain their original order since they're not explicitly in PRODUCT_FULL_SECTION_ORDER
        
        # First sort vendor profiles (they'll all be under 'vendor_light_profiles' in the config)
        profile_tasks = [(section_id, prompt_func, args_dict, output_filename) 
                         for section_id, prompt_func, args_dict, output_filename in tasks_to_run
                         if section_id.startswith('profile_')]
                         
        # Now get non-profile tasks and sort them based on PRODUCT_FULL_SECTION_ORDER
        non_profile_tasks = [(section_id, prompt_func, args_dict, output_filename)
                            for section_id, prompt_func, args_dict, output_filename in tasks_to_run
                            if not section_id.startswith('profile_')]
        
        # Custom sort function that looks up position in product_full_section_ids
        def get_section_position(section_id):
            # For non-profile sections, find their exact position
            if section_id in product_full_section_ids:
                return product_full_section_ids.index(section_id)
            # For special sections, find the related section
            elif section_id == "comparison_matrix":
                # Should come after vendor profiles
                try:
                    return product_full_section_ids.index("comparison_matrix") 
                except ValueError:
                    # If not found, place after vendor_light_profiles
                    try:
                        return product_full_section_ids.index("vendor_light_profiles") + 0.5
                    except ValueError:
                        return len(product_full_section_ids) # Fallback to the end
            elif section_id == "product_relevance":
                # Relevance analysis comes after comparison
                try:
                    return product_full_section_ids.index("product_relevance")
                except ValueError:
                    try:
                        return product_full_section_ids.index("comparison_matrix") + 0.5
                    except ValueError:
                        return len(product_full_section_ids)
            elif section_id == "product_recommendations":
                # Recommendations come near the end
                try:
                    return product_full_section_ids.index("product_recommendations")
                except ValueError:
                    try:
                        return product_full_section_ids.index("product_relevance") + 0.5
                    except ValueError:
                        return len(product_full_section_ids)
            # Default position for unknown sections
            return len(product_full_section_ids) + 1
        
        # Sort non-profile tasks
        sorted_non_profile_tasks = sorted(non_profile_tasks, key=lambda x: get_section_position(x[0]))
        
        # First process profiles (they're conceptually one section)
        for task in profile_tasks:
            section_id, prompt_func, args_dict, output_filename = task
            if shutdown_requested:
                 phase2_results[section_id] = {"status": "skipped", "error": "Shutdown requested", "execution_time": 0}
                 if status_dict is not None:
                     status_dict[section_id] = {"status": "skipped", "error": "Shutdown requested", "execution_time": 0}
                 progress.update(section_tasks_p2[section_id], description=f"[yellow]{section_id[:30]:.<30}⚠ (Skipped)", completed=1)
                 continue
            try:
                 # Update status to running
                 if status_dict is not None:
                     status_dict[section_id].update({"status": "running"})
                 
                 # Simple argument filtering
                 import inspect
                 sig = inspect.signature(prompt_func)
                 valid_args = {k: v for k, v in args_dict.items() if k in sig.parameters}

                 prompt = prompt_func(**valid_args)
                 output_path = markdown_dir / output_filename
                 
                 # Submit the task
                 future = executor.submit(_generate_single_section, client, prompt, output_path, section_id, status_dict)
                 futures[future] = section_id
            except Exception as e:
                 logger.error(f"Error preparing Phase 2 prompt for {section_id}: {e}")
                 phase2_results[section_id] = {"status": "error", "error": f"Error preparing prompt: {e}", "execution_time": 0}
                 if status_dict is not None:
                     status_dict[section_id] = {"status": "error", "error": f"Error preparing prompt: {e}", "execution_time": 0}
                 progress.update(section_tasks_p2[section_id], description=f"[red]{section_id[:30]:.<30}✗ (Prompt Error)", completed=1)
                 
        # Then process non-profile tasks in correct order
        for task in sorted_non_profile_tasks:
            section_id, prompt_func, args_dict, output_filename = task
            if shutdown_requested:
                 phase2_results[section_id] = {"status": "skipped", "error": "Shutdown requested", "execution_time": 0}
                 if status_dict is not None:
                     status_dict[section_id] = {"status": "skipped", "error": "Shutdown requested", "execution_time": 0}
                 progress.update(section_tasks_p2[section_id], description=f"[yellow]{section_id[:30]:.<30}⚠ (Skipped)", completed=1)
                 continue
            try:
                 # Update status to running
                 if status_dict is not None:
                     status_dict[section_id].update({"status": "running"})
                 
                 # Simple argument filtering
                 import inspect
                 sig = inspect.signature(prompt_func)
                 valid_args = {k: v for k, v in args_dict.items() if k in sig.parameters}

                 prompt = prompt_func(**valid_args)
                 output_path = markdown_dir / output_filename
                 
                 # Submit the task
                 future = executor.submit(_generate_single_section, client, prompt, output_path, section_id, status_dict)
                 futures[future] = section_id
            except Exception as e:
                 logger.error(f"Error preparing Phase 2 prompt for {section_id}: {e}")
                 phase2_results[section_id] = {"status": "error", "error": f"Error preparing prompt: {e}", "execution_time": 0}
                 if status_dict is not None:
                     status_dict[section_id] = {"status": "error", "error": f"Error preparing prompt: {e}", "execution_time": 0}
                 progress.update(section_tasks_p2[section_id], description=f"[red]{section_id[:30]:.<30}✗ (Prompt Error)", completed=1)

        processed_count = 0
        # Process futures in order of completion
        for future in as_completed(futures):
            section_id = futures[future]
            try:
                result = future.result()
                phase2_results[section_id] = result
                
                # Update status immediately when a section completes
                if status_dict is not None:
                    status_dict[section_id].update({
                        "status": result.get("status", "unknown"),
                        "error": result.get("error"),
                        "execution_time": result.get("execution_time", 0)
                    })
                
                # Update progress immediately
                status_char = "✓" if result.get("status") == 'success' else ("✗" if result.get("status") == "error" else "⚠")
                color = "green" if result.get("status") == 'success' else ("red" if result.get("status") == "error" else "yellow")
                status_text = f"({result.get('status', 'unknown')})"
                progress.update(section_tasks_p2[section_id],
                             advance=1,
                             description=f"[{color}]{section_id[:30]:.<30}{status_char} {status_text}")
                
                logger.debug(f"Result received for section: {section_id}, status: {result.get('status')}")
            except Exception as e:
                 logger.error(f"Error processing Phase 2 result for {section_id}: {str(e)}")
                 phase2_results[section_id] = {"status": "error", "error": f"Future result error: {str(e)}", "execution_time": 0}
                 if status_dict is not None:
                     status_dict[section_id].update({"status": "error", "error": f"Future result error: {str(e)}"})
                 progress.update(section_tasks_p2[section_id], description=f"[red]{section_id[:30]:.<30}✗ (Result Error)", completed=1)
            finally:
                 processed_count += 1
                 progress.update(main_task_p2, completed=processed_count)
                 logger.debug(f"Processed {processed_count}/{len(futures)} futures.")

    # --- Compile Stats for Phase 2 ---
    phase2_execution_time = time.time() - phase2_start_time
    valid_results_p2 = {k: v for k, v in phase2_results.items() if v.get('status') != 'skipped'}
    phase2_summary = {
        "total_input_tokens": sum(r.get("input_tokens", 0) for r in valid_results_p2.values()),
        "total_output_tokens": sum(r.get("output_tokens", 0) for r in valid_results_p2.values()),
        "total_tokens": sum(r.get("total_tokens", 0) for r in valid_results_p2.values()),
        "total_execution_time": phase2_execution_time,
        "formatted_execution_time": format_time(phase2_execution_time),
        "successful_sections": sum(1 for r in phase2_results.values() if r.get("status") == "success"),
        "failed_sections": sum(1 for r in phase2_results.values() if r.get("status") == 'error'),
        "interrupted_sections": sum(1 for r in phase2_results.values() if r.get("status") == 'interrupted'),
        "skipped_sections": sum(1 for r in phase2_results.values() if r.get("status") == 'skipped'),
        "was_interrupted": shutdown_requested,
        "phase": 2,
        "sections_generated": list(phase2_results.keys())
    }

    # --- Generate Dashboard Data for Phase 2 ---
    phase2_dashboard_data = None
    if phase2_summary.get('successful_sections', 0) > 0 and not phase2_summary.get('was_interrupted', False):
        try:
            # We need to pass token_stats-like structure to _generate_dashboard_data
            # Let's use PRODUCT_FULL_SECTION_ORDER as the reference for now,
            # as Phase 2 contributes towards the full report.
            phase2_stats_for_dashboard = {
                "research_mode": "product",
                "identifier": product_category,
                # Use the FULL order because Phase 2 builds part of it
                "section_order_used": [s[0] for s in PRODUCT_FULL_SECTION_ORDER]
            }
            # Pass filtered_vendors context
            phase2_dashboard_data = _generate_dashboard_data(
                base_dir, 'product', phase2_stats_for_dashboard, filtered_vendors
            )
        except Exception as dash_e:
            logger.error(f"Error generating Phase 2 dashboard data: {dash_e}")
    # --- End Dashboard Generation ---

    # Optionally save phase 2 stats separately or merge with main stats file
    try:
         misc_dir = base_dir / "misc"
         stats_path_p2 = misc_dir / "generation_summary_phase2.json"
         with open(stats_path_p2, 'w', encoding='utf-8') as f:
             json.dump({"phase2_results": phase2_results, "phase2_summary": phase2_summary}, f, indent=2, ensure_ascii=False)
    except Exception as e:
         logger.warning(f"Could not save phase 2 summary JSON: {e}")

    if progress_context is None: progress.stop()
    console.print(f"[green]Product Report Phase 2 generation finished.[/green]")
    return phase2_summary, phase2_dashboard_data # Return both summary and dashboard data


# --- New Function for Phase 4: Trigger Deep Dives ---
def trigger_vendor_deep_dives(
    base_dir: Path, # Base dir of the product research
    vendors_to_research: List[str],
    context_company_name: str,
    optional_inputs: Dict, # Original product optional inputs
    status_dict: Dict = None, # Add status_dict parameter
    progress_context=None
) -> Dict[str, Tuple[Optional[Dict], Optional[Path], Optional[Dict], Optional[Path]]]: # Added base_dir to return tuple
    """
    Triggers deep dives AND generates individual dashboard data for each.
    Returns dict {vendor_name: (stats, pdf_path, dashboard_data, base_dir)}
    The base_dir is returned to help locate the deep dive content for PDF generation.
    """
    global shutdown_requested
    if shutdown_requested: return {}
    
    if not vendors_to_research:
        logger.warning("No vendors to research provided for deep dives.")
        return {}
    
    console.print(f"\n[bold blue]Starting Deep Dive Vendor Research for {len(vendors_to_research)} vendors...[/bold blue]")
    deep_dive_results = {}
    
    # Initialize status for deep dive if status_dict is provided
    if status_dict is not None:
        deep_dive_section_id = "vendor_deep_dives"
        if deep_dive_section_id not in status_dict:
            status_dict[deep_dive_section_id] = {"status": "pending"}
        status_dict[deep_dive_section_id].update({
            "status": "running",
            "vendors": vendors_to_research,
            "completed": 0
        })
    
    # Use provided progress or create a new one
    progress = progress_context or Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(),
            TaskProgressColumn(), TimeElapsedColumn()
    )
    
    # Only create a progress bar if not provided externally
    progress_bar_external = progress_context is not None
    if not progress_bar_external:
        progress.start()
    
    # Create a main task if using our progress
    main_task_dd = None
    if not progress_bar_external:
        main_task_dd = progress.add_task(f"[cyan]Deep Dive Vendor Research", total=len(vendors_to_research))
    
    try:
        # Start parallel processing of vendors with maximum concurrency
        max_workers = len(vendors_to_research)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_vendor = {}
            # --- MODIFICATION: Clean names before submitting ---
            cleaned_vendors_to_research = []
            for vendor_name in vendors_to_research:
                 # Basic cleaning - assumes the list might still have issues
                 cleaned_name = vendor_name.strip()
                 if cleaned_name.startswith('- '):
                     cleaned_name = cleaned_name[2:].strip()
                 if cleaned_name: # Avoid empty names
                     cleaned_vendors_to_research.append(cleaned_name)
                 else:
                     logger.warning(f"Skipping deep dive for invalid/empty vendor name derived from: '{vendor_name}'")

            if not cleaned_vendors_to_research:
                 logger.warning("No valid vendor names remaining after cleaning for deep dives.")
                 return {}

            logger.info(f"Cleaned vendor list for deep dive: {cleaned_vendors_to_research}")
            # --- END MODIFICATION ---
            
            # Create vendor-specific status tracking if status_dict is provided
            if status_dict is not None:
                for vendor_name in cleaned_vendors_to_research:
                    vendor_section_id = f"deep_dive_{re.sub(r'[^a-zA-Z0-9_]', '_', vendor_name)}"
                    if vendor_section_id not in status_dict:
                        status_dict[vendor_section_id] = {"status": "pending", "vendor": vendor_name}

            # Submit tasks using CLEANED names
            for vendor_name in cleaned_vendors_to_research: # Use the cleaned list
                # Check if we should continue 
                if shutdown_requested:
                    continue
                
                # Create vendor-specific status dict for this vendor
                vendor_status_dict = None
                if status_dict is not None:
                    vendor_section_id = f"deep_dive_{re.sub(r'[^a-zA-Z0-9_]', '_', vendor_name)}"
                    status_dict[vendor_section_id].update({"status": "running"})
                    vendor_status_dict = {}  # Create a fresh status dict for this vendor
                
                # Each future runs the full vendor research process
                future = executor.submit(
                    run_vendor_research,
                    vendor_name=vendor_name, # Pass the CLEAN name
                    context_company_name=context_company_name,
                    optional_inputs=optional_inputs,
                    status_dict=vendor_status_dict, # Pass the vendor-specific status dict
                    # Don't pass progress_context - each subprocess should manage its own
                )
                future_to_vendor[future] = vendor_name # Store the CLEAN name
            
            # Process results as they complete
            for future in as_completed(future_to_vendor):
                vendor_name = future_to_vendor[future]
                try:
                    if not shutdown_requested:
                        # run_vendor_research now returns (stats, pdf, dashboard)
                        token_stats, pdf_path, dashboard_data = future.result()
                        # Store all values plus the base_dir (available in token_stats)
                        vendor_base_dir = token_stats.get('base_dir') if token_stats else None
                        deep_dive_results[vendor_name] = (token_stats, pdf_path, dashboard_data, vendor_base_dir)
                        
                        # Update status for the individual vendor
                        if status_dict is not None:
                            vendor_section_id = f"deep_dive_{re.sub(r'[^a-zA-Z0-9_]', '_', vendor_name)}"
                            status = "success" if token_stats and token_stats.get('summary', {}).get('successful_sections', 0) > 0 else "error"
                            status_dict[vendor_section_id].update({
                                "status": status,
                                "vendor": vendor_name,
                                "base_dir": vendor_base_dir,
                                "pdf_path": str(pdf_path) if pdf_path else None,
                                "sections_generated": token_stats.get('summary', {}).get('successful_sections', 0) if token_stats else 0
                            })
                            
                            # Update the overall deep dive status
                            deep_dive_section_id = "vendor_deep_dives"
                            completed = status_dict[deep_dive_section_id].get("completed", 0) + 1
                            status_dict[deep_dive_section_id].update({
                                "completed": completed,
                                "total": len(cleaned_vendors_to_research),
                                "progress": completed / len(cleaned_vendors_to_research)
                            })
                        
                        if not progress_bar_external and main_task_dd:
                            progress.update(main_task_dd, advance=1, description=f"Deep Dive Complete: {vendor_name}")
                        logger.info(f"Successfully completed deep dive for vendor: {vendor_name}")
                        
                        # Log the base directory to make it easier to find
                        if vendor_base_dir:
                            logger.info(f"Vendor {vendor_name} deep dive directory: {vendor_base_dir}")
                        else:
                            logger.warning(f"Could not determine base directory for {vendor_name} deep dive")
                    else:
                        deep_dive_results[vendor_name] = ({"summary": {"was_interrupted": True}}, None, None, None)
                        logger.warning(f"Skipping/Interrupting deep dive for vendor: {vendor_name}")
                        
                        # Update status for interrupted vendor
                        if status_dict is not None:
                            vendor_section_id = f"deep_dive_{re.sub(r'[^a-zA-Z0-9_]', '_', vendor_name)}"
                            status_dict[vendor_section_id].update({
                                "status": "interrupted",
                                "error": "Shutdown requested during execution"
                            })
                except Exception as e:
                    deep_dive_results[vendor_name] = ({"summary": {"error": str(e)}}, None, None, None)
                    logger.error(f"Error during deep dive for vendor {vendor_name}: {e}")
                    
                    # Update status for failed vendor
                    if status_dict is not None:
                        vendor_section_id = f"deep_dive_{re.sub(r'[^a-zA-Z0-9_]', '_', vendor_name)}"
                        status_dict[vendor_section_id].update({
                            "status": "error",
                            "error": str(e)
                        })
                        
                    if not progress_bar_external and main_task_dd:
                        progress.update(main_task_dd, description=f"Error in Deep Dive: {vendor_name}")
    
    except Exception as e:
        logger.error(f"Error in deep dive management: {e}")
        
        # Update overall deep dive status
        if status_dict is not None:
            deep_dive_section_id = "vendor_deep_dives"
            status_dict[deep_dive_section_id].update({
                "status": "error",
                "error": f"Error in deep dive management: {str(e)}"
            })
    finally:
        # Update final status for the deep dive process
        if status_dict is not None:
            deep_dive_section_id = "vendor_deep_dives"
            success_count = sum(1 for v, (stats, _, _, _) in deep_dive_results.items() 
                          if stats and stats.get('summary', {}).get('successful_sections', 0) > 0)
            
            # Mark overall status based on success ratio
            overall_status = "success"
            if not deep_dive_results:
                overall_status = "error"
            elif success_count == 0:
                overall_status = "error"
            elif success_count < len(cleaned_vendors_to_research):
                overall_status = "partial"
                
            status_dict[deep_dive_section_id].update({
                "status": overall_status,
                "completed": len(deep_dive_results),
                "success_count": success_count,
                "total": len(cleaned_vendors_to_research),
                "progress": 1.0  # Mark as complete
            })
            
        if not progress_bar_external:
            progress.stop()
    
    # Save the deep dive base directories for future reference
    try:
        misc_dir = base_dir / "misc"
        misc_dir.mkdir(exist_ok=True)
        with open(misc_dir / "deep_dive_directories.json", 'w', encoding='utf-8') as f:
            # Create a mapping of vendor names to their base directories
            vendor_dirs = {
                vendor: str(results[3]) if results[3] else None
                for vendor, results in deep_dive_results.items()
            }
            json.dump(vendor_dirs, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Could not save deep dive directories mapping: {e}")
    
    # Summarize results
    success_count = sum(1 for v, (stats, _, _, _) in deep_dive_results.items() 
                      if stats and stats.get('summary', {}).get('successful_sections', 0) > 0)
    console.print(f"[green]Deep Dive Research Complete. {success_count} of {len(vendors_to_research)} vendors processed successfully.[/green]")
    
    return deep_dive_results

# --- NEW: Function to generate final Product PDF and potentially a final dashboard ---
def generate_final_product_report(
    base_dir: Path,
    product_category: str,
    context_company_name: str,
    optional_inputs: Dict,
    filtered_vendors: List[str],
    deep_dive_vendors: List[str], # Vendors for whom deep dives were run
    status_dict: Dict = None, # Add status_dict parameter
    progress_context=None
) -> Tuple[Optional[Path], Optional[Dict]]: # Returns (final_pdf_path, final_dashboard_data)
    """
    Generates the final combined PDF for product research and the final dashboard data.
    """
    console.print(f"\n[bold blue]Generating Final Combined Product Report PDF for: {product_category}[/bold blue]")
    final_pdf_path = None
    final_dashboard_data = None
    
    # Initialize status if status_dict is provided
    if status_dict is not None:
        final_report_section_id = "final_product_report"
        if final_report_section_id not in status_dict:
            status_dict[final_report_section_id] = {"status": "pending"}
        status_dict[final_report_section_id].update({
            "status": "running",
            "product_category": product_category,
            "filtered_vendors": filtered_vendors,
            "deep_dive_vendors": deep_dive_vendors
        })

    try:
        # Get deep dive directories from saved mapping if it exists
        deep_dive_dirs = {}
        deep_dive_dirs_path = base_dir / "misc" / "deep_dive_directories.json"
        if deep_dive_dirs_path.exists():
            try:
                with open(deep_dive_dirs_path, 'r', encoding='utf-8') as f:
                    deep_dive_dirs = json.load(f)
                console.print(f"[green]Loaded deep dive directory mapping for {len(deep_dive_dirs)} vendors.[/green]")
            except Exception as e:
                logger.warning(f"Could not load deep dive directories mapping: {e}")
                if status_dict is not None:
                    status_dict[final_report_section_id].update({
                        "warning": f"Could not load deep dive directories mapping: {str(e)}"
                    })
        else:
            logger.warning("Deep dive directories mapping file not found. Some content might be missing from the final PDF.")
            if status_dict is not None:
                status_dict[final_report_section_id].update({
                    "warning": "Deep dive directories mapping file not found"
                })
            
        # Check if we have any deep dive directories to use
        if deep_dive_vendors and not deep_dive_dirs:
            logger.warning("Deep dive vendors specified but no directory mapping found.")
            if status_dict is not None:
                status_dict[final_report_section_id].update({
                    "warning": "Deep dive vendors specified but no directory mapping found"
                })
        
        # Generate the final PDF using the full section order
        pdf_path_generated = process_markdown_files(
            base_dir=base_dir,
            identifier=product_category,
            report_type_name="ProductReportFull", # Use a distinct name
            section_order=PRODUCT_FULL_SECTION_ORDER, # Use the full order
            filtered_vendors=filtered_vendors,
            deep_dive_vendors=deep_dive_vendors,
            deep_dive_dirs=deep_dive_dirs # Pass the directory mapping to find vendor content
        )
        if pdf_path_generated and pdf_path_generated.exists():
            final_pdf_path = pdf_path_generated
            console.print(f"[green]Final PDF generated: {final_pdf_path}[/green]")

            # Generate dashboard data based on the *final* state
            # We need to reconstruct the 'token_stats' to pass the correct section order
            final_token_stats = {
                 "research_mode": "product",
                 "identifier": product_category,
                 "section_order_used": PRODUCT_FULL_SECTION_ORDER # Pass the full order
            }
            final_dashboard_data = _generate_dashboard_data(base_dir, 'product', final_token_stats, filtered_vendors)
            
            # Update status to success
            if status_dict is not None:
                status_dict[final_report_section_id].update({
                    "status": "success",
                    "pdf_path": str(final_pdf_path),
                    "has_dashboard": final_dashboard_data is not None
                })

        else:
            console.print("[red]Final PDF generation failed.[/red]")
            if status_dict is not None:
                status_dict[final_report_section_id].update({
                    "status": "error",
                    "error": "Final PDF generation failed"
                })

    except Exception as e:
        console.print(f"[red]Error during final product report generation: {e}[/red]")
        logger.exception(f"Final Product PDF/Dashboard Error for {base_dir}")
        if status_dict is not None:
            status_dict[final_report_section_id].update({
                "status": "error",
                "error": f"Error during final product report generation: {str(e)}"
            })

    return final_pdf_path, final_dashboard_data

# --- New Helper Function for Dashboard Data ---
def _generate_dashboard_data(
    base_dir: Path,
    research_mode: str,
    token_stats: Dict, # Pass the stats from main generation
    filtered_vendors: Optional[List[str]] = None # Needed for product dashboard context
    ) -> Optional[Dict]:
    """
    Reads generated markdown, calls LLM summary prompt, parses JSON response.
    """
    global shutdown_requested
    if shutdown_requested: return None

    console.print(f"\n[bold cyan]Generating Dashboard Data for {research_mode} report...[/bold cyan]")
    dashboard_data = None
    markdown_dir = base_dir / "markdown"
    full_report_content = ""

    # Determine which section order was used based on the mode and stats
    section_order_used = token_stats.get("section_order_used", [])
    if not section_order_used:
         logger.warning("Cannot determine section order used from token_stats for dashboard generation.")
         # Fallback based on mode - less reliable if structure changes
         if research_mode == 'vendor':
             # Use the actual config list of tuples here for fallback
             section_order_used_tuples = VENDOR_SECTION_ORDER
         elif research_mode == 'product':
             # Use the actual config list of tuples here for fallback
             section_order_used_tuples = PRODUCT_FULL_SECTION_ORDER # Assume full report for final dashboard
         else: return None
         # Extract just the IDs if using fallback
         section_order_used = [sid for sid, _ in section_order_used_tuples]

    # Concatenate markdown files in the correct order
    for section_id in section_order_used: # Iterate over the list of strings directly
         # Handle special multi-file sections if needed (or assume simple files for now)
         if section_id in ["vendor_light_profiles", "vendor_deep_dives"]:
              # For now, skip these complex sections in the summary input,
              # as the prompt relies on specific section names like 'Section 10'.
              # TODO: Enhance this if dashboard needs data from profiles/deep dives.
              continue

         md_path = markdown_dir / f"{section_id}.md"
         if md_path.exists():
             try:
                 with open(md_path, 'r', encoding='utf-8') as f:
                     # Find the corresponding title from the original config for better context
                     title = section_id.replace('_', ' ').title() # Default title
                     original_config = VENDOR_SECTION_ORDER if research_mode == 'vendor' else PRODUCT_FULL_SECTION_ORDER
                     for sid_cfg, title_cfg in original_config:
                         if sid_cfg == section_id:
                             title = title_cfg
                             break
                     full_report_content += f"\n\n## {title}\n\n" # Use title
                     full_report_content += f.read()
             except Exception as e:
                 logger.warning(f"Could not read {md_path} for dashboard summary: {e}")
         # else: logger.warning(f"Markdown file {md_path.name} not found for dashboard summary.") # Optional warning

    if not full_report_content.strip():
        logger.error(f"No markdown content found in {markdown_dir} to generate dashboard data.")
        return None

    # Select the correct summary prompt
    summary_prompt = None
    summary_prompt_args = {}
    summary_prompt_func = None
    if research_mode == 'vendor':
        if hasattr(vendor_prompts, 'get_vendor_dashboard_summary_prompt'):
            summary_prompt_func = vendor_prompts.get_vendor_dashboard_summary_prompt
            summary_prompt_args = {'full_report_content': full_report_content}
    elif research_mode == 'product':
         if hasattr(product_prompts, 'get_product_dashboard_summary_prompt'):
            summary_prompt_func = product_prompts.get_product_dashboard_summary_prompt
            summary_prompt_args = {
                 'full_report_content': full_report_content,
                 'filtered_vendor_list': filtered_vendors # Pass this extra context
            }

    if not summary_prompt_func:
         logger.error(f"Dashboard summary prompt function not found for mode: {research_mode}")
         return None

    try:
        summary_prompt = summary_prompt_func(**summary_prompt_args)

        # Call LLM for summary using the updated API
        api_key = os.getenv("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key)
        
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=summary_prompt)])]
        generate_content_config = types.GenerateContentConfig(
            temperature=0.7,  # Higher temp for faster generation
            response_mime_type="text/plain",
        )
        
        # Use streaming to get complete response
        raw_json_text = ""
        try:
            for chunk in client.models.generate_content_stream(
                model=LLM_MODEL,
                contents=contents,
                config=generate_content_config,
            ):
                if chunk.text is not None:
                    raw_json_text += chunk.text
                    
            # Clean potential markdown fences
            cleaned_json_text = re.sub(r"```(json)?|\s*```", "", raw_json_text, flags=re.IGNORECASE).strip()
            try:
                dashboard_data = json.loads(cleaned_json_text)
                logger.info("Successfully parsed dashboard JSON data.")
            except json.JSONDecodeError as json_e:
                logger.error(f"Failed to parse JSON response for dashboard: {json_e}")
                logger.error(f"Raw response was: {raw_json_text}")
                
                # Retry once with a more explicit prompt for valid JSON
                try:
                    logger.info("Attempting one retry with explicit JSON formatting instructions...")
                    retry_prompt = f"""
You previously returned a response that could not be parsed as valid JSON. Please fix the JSON formatting issues and return ONLY a valid JSON object with no additional text.

Original prompt summary: Generate dashboard data for {research_mode} report.

Your previous response had JSON parsing errors. Return ONLY valid JSON following this exact structure example:
{{
  "title": "Example Dashboard Data",
  "summary": "Brief summary text",
  "key_metrics": [
    {{ "name": "Metric 1", "value": "Value 1" }},
    {{ "name": "Metric 2", "value": "Value 2" }}
  ]
}}

IMPORTANT: Return ONLY the JSON object, with no additional text, markdown formatting, or code block syntax.
"""
                    # Use updated API for retry
                    retry_contents = [types.Content(role="user", parts=[types.Part.from_text(text=retry_prompt)])]
                    retry_config = types.GenerateContentConfig(temperature=0.7)  # Higher temp for faster generation
                    
                    # Use streaming to get retry response
                    retry_text = ""
                    for chunk in client.models.generate_content_stream(
                        model=LLM_MODEL,
                        contents=retry_contents,
                        config=retry_config,
                    ):
                        if chunk.text is not None:
                            retry_text += chunk.text
                    
                    # Extra cleaning for the retry attempt
                    retry_text = re.sub(r"```(json)?|\s*```", "", retry_text, flags=re.IGNORECASE).strip()
                    dashboard_data = json.loads(retry_text)
                    logger.info("Successfully parsed dashboard JSON data on retry attempt.")
                    
                except Exception as retry_e:
                    logger.error(f"Retry attempt also failed: {retry_e}")
                    dashboard_data = {
                        "error": "Failed to parse summary JSON after retry", 
                        "raw_response": raw_json_text
                    }
        except Exception as e:
            logger.error(f"Error generating dashboard content: {str(e)}")
            dashboard_data = {"error": f"Exception during dashboard generation: {str(e)}"}

    except Exception as e:
        logger.error(f"Error during dashboard data generation: {e}")
        dashboard_data = {"error": f"Exception during summary generation: {str(e)}"}

    # Validate and fill in missing values with defaults
    if dashboard_data and 'error' not in dashboard_data:
        try:
            # Define expected keys for each mode
            if research_mode == 'vendor':
                expected_keys = [
                    "financial_stability_assessment", "operational_risk_assessment", 
                    "compliance_risk_assessment", "key_compliance_checks", 
                    "top_3_risks", "overall_suitability"
                ]
                # Ensure expected keys exist with defaults for vendor mode
                for key in expected_keys:
                    if key not in dashboard_data:
                        if key in ["key_compliance_checks"]:
                            dashboard_data[key] = {}
                        elif key in ["top_3_risks"]:
                            dashboard_data[key] = []
                        else:
                            dashboard_data[key] = "N/A"
                
            elif research_mode == 'product':
                expected_keys = [
                    "identified_vendor_count", "filtered_vendor_count", "market_growth_trend",
                    "top_3_filtered_vendors", "key_tech_trends", "common_compliance_standards"
                ]
                # Ensure expected keys exist with defaults for product mode
                for key in expected_keys:
                    if key not in dashboard_data:
                        if key in ["top_3_filtered_vendors", "key_tech_trends", "common_compliance_standards"]:
                            dashboard_data[key] = []
                        elif key in ["identified_vendor_count", "filtered_vendor_count"]:
                            dashboard_data[key] = 0
                        else:
                            dashboard_data[key] = "N/A"
            
            # Validate types and convert if needed
            for key, value in dashboard_data.items():
                # Convert non-list values to lists where needed
                if key in ["top_3_risks", "top_3_filtered_vendors", "key_tech_trends", "common_compliance_standards"]:
                    if not isinstance(value, list):
                        if value is None:
                            dashboard_data[key] = []
                        elif isinstance(value, str):
                            # Split by commas if it's a single string
                            dashboard_data[key] = [item.strip() for item in value.split(",") if item.strip()]
                        else:
                            # Convert other types to a single-item list
                            dashboard_data[key] = [str(value)]
                
                # Convert dictionaries
                if key in ["key_compliance_checks"]:
                    if not isinstance(value, dict):
                        dashboard_data[key] = {}
                
                # Ensure numeric values
                if key in ["identified_vendor_count", "filtered_vendor_count"]:
                    if not isinstance(value, int) or value < 0:
                        try:
                            dashboard_data[key] = int(value) if value is not None else 0
                        except (ValueError, TypeError):
                            dashboard_data[key] = 0
                
                # Ensure string values for text fields
                if key in ["financial_stability_assessment", "operational_risk_assessment", 
                          "compliance_risk_assessment", "overall_suitability", "market_growth_trend"]:
                    if not isinstance(value, str) or not value:
                        dashboard_data[key] = str(value) if value is not None else "N/A"
            
            logger.info("Dashboard data validated and defaults applied where needed.")
        except Exception as e:
            logger.warning(f"Error during dashboard data validation: {e}")
            # Don't overwrite the dashboard data if validation fails, just log the error

    # Save dashboard data
    if dashboard_data:
        try:
            misc_dir = base_dir / "misc"
            dash_path = misc_dir / "dashboard_data.json"
            with open(dash_path, 'w', encoding='utf-8') as f:
                json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Could not save dashboard data JSON: {e}")

    return dashboard_data

# --- Function Aliases for Backward Compatibility ---
# app.py is importing run_product_research_phase2 but the function is named generate_product_report_phase2
# Update to include status_dict parameter
run_product_research_phase2 = generate_product_report_phase2

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