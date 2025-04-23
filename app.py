import streamlit as st
import os
import time
import base64
import re
from pathlib import Path
from datetime import datetime
import yaml
from typing import List, Tuple, Optional, Dict, Set

# Import functions from test_agent_prompt.py directly
from report_orchestrator import (
    generate_content,
    generate_all_prompts,
    count_tokens,
    format_time
)
from pdf_generator import process_markdown_files
from config import SECTION_ORDER, AVAILABLE_LANGUAGES, PROMPT_FUNCTIONS, LLM_MODEL, LLM_TEMPERATURE
from google import genai

# Configure page settings
st.set_page_config(
    page_title="Account Research AI Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load logo
@st.cache_data
def get_logo_base64():
    with open("templates/assets/supervity_logo.png", "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Function to display PDF in Streamlit
def display_pdf(pdf_path):
    with open(pdf_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')

    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# Check if a markdown file contains proper content with a "Sources" heading
def validate_markdown(file_path: Path) -> bool:
    """
    Check if a markdown file contains a "Sources" heading at any level.
    This is a simple heuristic to determine if the file contains proper content.

    Args:
        file_path: Path to the markdown file

    Returns:
        bool: True if the file is valid, False otherwise
    """
    if not file_path.exists() or file_path.stat().st_size == 0:
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check if the markdown has a "Sources" heading at any level
        sources_pattern = re.compile(r'^#+\s+Sources', re.MULTILINE)
        if sources_pattern.search(content):
            return True

        # Alternative patterns that might indicate valid content
        alt_patterns = [
            re.compile(r'^#+\s+参考資料', re.MULTILINE),  # Japanese "References"
            re.compile(r'^#+\s+出典', re.MULTILINE),      # Japanese "Sources"
            re.compile(r'^#+\s+References', re.MULTILINE),
            re.compile(r'^#+\s+Bibliography', re.MULTILINE),
            re.compile(r'\[SSX\]', re.MULTILINE)         # Citation markers
        ]

        for pattern in alt_patterns:
            if pattern.search(content):
                return True

        return False
    except Exception:
        return False

# Custom wrapper around generate_all_prompts to integrate with Streamlit
def generate_report_with_progress(company_name: str, language: str, selected_prompts: List[Tuple[str, str]], context_company_name: str, ticker: Optional[str] = None, industry: Optional[str] = None):
    """Wrapper around generate_all_prompts with Streamlit progress indicators"""
    # Create a Streamlit progress display
    progress_bar = st.progress(0)
    status_text = st.empty()
    status_text.text("Initializing report generation...")

    # Define a simple progress class that integrates with Streamlit
    class StreamlitProgress:
        def __init__(self):
            self.tasks = {}
            self.current_progress = 0

        def add_task(self, description, total=1, visible=True):
            task_id = len(self.tasks)
            self.tasks[task_id] = {"description": description, "total": total, "completed": 0}
            return task_id

        def update(self, task_id, advance=0, description=None):
            if task_id not in self.tasks:
                return

            if advance > 0:
                self.tasks[task_id]["completed"] += advance
                # Calculate overall progress as average of all tasks
                total_progress = sum(task["completed"] / task["total"] for task in self.tasks.values()) / len(self.tasks)
                progress_bar.progress(min(total_progress, 1.0))

            if description:
                self.tasks[task_id]["description"] = description
                status_text.text(description.replace("[bold green]", "").replace("[cyan]", "").replace("[/]", ""))

    # Call the original function with our progress display
    try:
        token_stats, base_dir = generate_all_prompts(
            company_name,
            language,
            selected_prompts,
            context_company_name,
            ticker=ticker,
            industry=industry,
            progress=StreamlitProgress()
        )

        # Check if the initial generation failed completely
        if not token_stats or not base_dir:
             raise Exception("Initial report generation failed. Cannot proceed to validation.")

        # Validate all markdown files and rerun invalid ones
        markdown_dir = base_dir / "markdown"
        if not markdown_dir.exists():
            raise Exception(f"Markdown directory not found after initial generation: {markdown_dir}")

        invalid_files: Dict[str, Path] = {}

        status_text.text("Validating generated markdown files...")

        # First check - validate each markdown file
        for prompt_name, _ in selected_prompts:
            md_file = markdown_dir / f"{prompt_name}.md"
            if not validate_markdown(md_file):
                invalid_files[prompt_name] = md_file
                status_text.text(f"Found invalid content in {prompt_name}.md, will retry...")

        # Re-run prompts for invalid files if any
        if invalid_files:
            status_text.text(f"Re-running {len(invalid_files)} prompts with invalid content...")

            # Create API client
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in .env file")
            client = genai.Client(api_key=api_key)

            # Get remaining invalid prompt pairs
            invalid_prompts = [(name, next(p[1] for p in selected_prompts if p[0] == name))
                              for name in invalid_files.keys()]

            # Create a progress indicator for retries
            retry_progress = StreamlitProgress()
            for retry_idx, (prompt_name, prompt_func_name) in enumerate(invalid_prompts):
                retry_task = retry_progress.add_task(f"Retrying {prompt_name}...", total=1)

                # Get the prompt function from prompt_testing module
                import prompt_testing
                prompt_func = getattr(prompt_testing, prompt_func_name)

                # Generate the prompt with proper parameters
                if prompt_name == "strategy_research":
                    prompt = prompt_func(
                        company_name,
                        language,
                        ticker=ticker,
                        industry=industry,
                        context_company_name=context_company_name
                    )
                else:
                    prompt = prompt_func(
                        company_name,
                        language,
                        ticker=ticker,
                        industry=industry,
                        context_company_name=context_company_name
                    )

                # Generate content
                status_text.text(f"Retrying {prompt_name}...")
                result = generate_content(client, prompt, invalid_files[prompt_name])

                # Update token stats
                if result["status"] == "success":
                    token_stats["prompts"][prompt_name] = result
                    token_stats["summary"]["total_input_tokens"] += result["input_tokens"]
                    token_stats["summary"]["total_output_tokens"] += result["output_tokens"]
                    token_stats["summary"]["total_tokens"] += result["total_tokens"]
                    token_stats["summary"]["successful_prompts"] += 1

                    # --- CORRECTED LOGIC ---
                    # If a prompt succeeded on retry, decrement the failed count,
                    # but ensure the count doesn't go below zero.
                    if token_stats["summary"]["failed_prompts"] > 0:
                        token_stats["summary"]["failed_prompts"] -= 1
                    # --- END CORRECTION ---

                retry_progress.update(retry_task, advance=1, description=f"Retried {prompt_name}")

            # Second check - validate retried files
            still_invalid = []
            for prompt_name in invalid_files:
                md_file = markdown_dir / f"{prompt_name}.md"
                if not validate_markdown(md_file):
                    still_invalid.append(prompt_name)

            if still_invalid:
                status_text.text(f"Warning: {len(still_invalid)} files still have invalid content: {', '.join(still_invalid)}")
            else:
                status_text.text("All files validated successfully after retries!")
        else:
            status_text.text("All markdown files validated successfully!")

        # Return the results
        pdf_path = None
        if token_stats['summary']['successful_prompts'] > 0:
            # Define PDF path relative to base_dir
            pdf_file_name = f"{company_name}_{language}_Report.pdf"
            pdf_path = base_dir / "pdf" / pdf_file_name

            # Ensure PDF directory exists
            (base_dir / "pdf").mkdir(parents=True, exist_ok=True)

            # Check if PDF needs generation (only if markdown exists and PDF doesn't)
            markdown_files_exist = any((markdown_dir / f"{name}.md").exists() for name, _ in selected_prompts)
            if markdown_files_exist and not pdf_path.exists():
                status_text.text("Generating PDF from markdown files...")
                generated_pdf_path = process_markdown_files(base_dir, company_name, language)
                if generated_pdf_path:
                     pdf_path = generated_pdf_path # Update path if generated
                else:
                     pdf_path = None # PDF generation failed
                     status_text.text("PDF generation failed.")
            elif not markdown_files_exist:
                 status_text.text("No markdown files found to generate PDF.")
                 pdf_path = None
            else:
                 status_text.text("PDF already exists or no markdown generated.")
                 # Keep existing pdf_path if it exists

        status_text.text("Report generation complete!")
        progress_bar.empty()

        return token_stats, pdf_path, base_dir

    except Exception as e:
        status_text.text(f"Error: {str(e)}")
        st.error(f"Error during report generation: {str(e)}")
        # Ensure None is returned for all parts if an error occurs
        return None, None, None


# Add custom CSS with Supervity brand colors
def apply_custom_css():
    st.markdown("""
    <style>
    /* Supervity Brand Colors */
    :root {
        /* Primary Colors */
        --primary-black: #000000;
        --primary-white: #ffffff;
        --primary-navy: #000b37;
        --primary-lime: #85c20b;

        /* Secondary Colors */
        --secondary-dark-gray: #474747;
        --secondary-light-gray: #c7c7c7;
        --secondary-soft-blue: #8289ec;
        --secondary-light-lime: #c3fb54;

        /* Complementary Colors */
        --comp-coral: #ff9a5a;
        --comp-purple: #b181ff;
        --comp-cyan: #31b8e1;
        --comp-pink: #ff94a8;
    }

    .stApp {
        background-color: #f7f7f7;
    }

    /* Header styling */
    .main-header-container {
        background-color: var(--primary-navy);
        padding: 2rem 1rem 1rem 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .main-header {
        color: var(--primary-white);
        text-align: center;
        padding: 0;
        margin: 0.5rem 0;
        font-size: 2.5rem;
        font-weight: 700;
    }

    .sub-header {
        color: var(--primary-lime);
        text-align: center;
        font-size: 1.2rem;
        font-weight: 400;
        margin-bottom: 1rem;
    }

    /* Logo styling */
    .logo-container {
        text-align: center;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .logo-image {
        max-width: 80px;
        max-height: 80px;
        height: auto;
        width: auto;
        margin: 0 auto;
    }

    /* Form styling */
    .form-container {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }

    .form-header {
        color: var(--primary-navy);
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }

    /* Button styling */
    .stButton>button {
        width: 100%;
        padding: 0.75rem;
        background-color: var(--primary-lime);
        color: var(--primary-navy);
        font-weight: bold;
        border: none;
        border-radius: 6px;
        transition: all 0.3s;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 1rem;
    }

    .stButton>button:hover {
        background-color: var(--secondary-light-lime);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }

    /* Section styling */
    .section-title {
        color: var(--primary-navy);
        font-weight: bold;
        margin-top: 2rem;
        font-size: 1.5rem;
        border-bottom: 2px solid var(--primary-lime);
        padding-bottom: 0.5rem;
    }

    /* Stats cards styling */
    .report-stats {
        padding: 1rem;
        background-color: white;
        border-radius: 8px;
        margin-top: 1rem;
        border-left: 4px solid var(--primary-lime);
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
    }

    /* Input fields styling */
    div[data-baseweb="input"] {
        border-radius: 6px;
    }

    div[data-baseweb="input"]:focus-within {
        border-color: var(--primary-lime);
        box-shadow: 0 0 0 1px var(--primary-lime);
    }

    /* Sidebar styling */
    .css-1cypcdb, .css-163ttbj {
        background-color: var(--primary-navy);
    }

    section[data-testid="stSidebar"] .css-1vq4p4l {
        padding-top: 5rem;
    }

    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        color: var(--primary-white);
    }

    /* Success message */
    div[data-baseweb="notification"] {
        background-color: var(--primary-lime);
        border-color: var(--primary-lime);
        color: var(--primary-navy);
    }

    /* Footer */
    .footer {
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid var(--secondary-light-gray);
        text-align: center;
        color: var(--secondary-dark-gray);
        font-size: 0.9rem;
    }

    /* Custom metric styles */
    .metric-card {
        background-color: white;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
        text-align: center;
        height: 100%;
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--primary-navy);
        margin: 0.5rem 0;
    }

    .metric-label {
        font-size: 1rem;
        color: var(--secondary-dark-gray);
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .metric-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
        color: var(--primary-lime);
    }

    /* PDF container */
    .pdf-container {
        margin-top: 2rem;
        padding: 1rem;
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f0f2f6;
        border-radius: 6px;
        padding: 0.5rem;
        font-weight: 600;
        color: var(--primary-navy);
    }

    .streamlit-expanderHeader:hover {
        background-color: #e6e9ef;
    }

    .streamlit-expanderContent {
        border: 1px solid #e6e9ef;
        border-top: none;
        border-radius: 0 0 6px 6px;
        padding: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Custom metric component
def metric_card(icon, label, value):
    return f"""
    <div class="metric-card">
        <div class="metric-icon">{icon}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """

# App title and styling
apply_custom_css()

# Header with Supervity branding
st.markdown('<div class="main-header-container">', unsafe_allow_html=True)
logo_html = f'<div class="logo-container"><img src="data:image/png;base64,{get_logo_base64()}" class="logo-image"></div>'
st.markdown(logo_html, unsafe_allow_html=True)
st.markdown('<h1 class="main-header">Account Research AI Agent</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Your intelligent research assistant for comprehensive company analysis</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Main form
st.markdown('<div class="form-container">', unsafe_allow_html=True)
st.markdown('<h2 class="form-header">Research Configuration</h2>', unsafe_allow_html=True)

with st.form("report_generator_form"):
    col1, col2 = st.columns(2)

    with col1:
        # Required inputs
        target_company = st.text_input(
            "Target Company Name",
            placeholder="Enter the name of the company you want to research",
            help="The company you want to generate a research report about"
        )
        context_company = st.text_input(
            "Context Company",
            placeholder="Enter your company name",
            help="Required: Your company name that will appear as the author of the report"
        )
        ticker = st.text_input(
            "Stock Ticker Symbol",
            placeholder="Optional: AAPL, MSFT, GOOG, etc.",
            help="The stock ticker symbol of the target company (if publicly traded)"
        )
        industry = st.text_input(
            "Primary Industry",
            placeholder="Optional: Technology, Healthcare, Finance, etc.",
            help="The primary industry sector of the target company"
        )

        # Language options - convert dictionary to list of tuples for selectbox
        language_options = [(key, value) for key, value in AVAILABLE_LANGUAGES.items()]
        selected_language_option = st.selectbox(
            "Select Language",
            options=language_options,
            format_func=lambda x: f"{x[1]} ({x[0]})",
            index=1  # Index 1 corresponds to English
        )

    with col2:
        # Advanced options with expander
        with st.expander("Advanced Options", expanded=False):
            # Section selection
            st.subheader("Section Selection")
            section_options = [name for name, _ in PROMPT_FUNCTIONS]
            selected_sections = st.multiselect(
                "Select Sections to Generate",
                options=section_options,
                default=section_options,
                help="Choose which sections to include in the report. By default, all sections are selected."
            )

    # Generate report button
    generate_button = st.form_submit_button("Generate Report")

st.markdown('</div>', unsafe_allow_html=True)

# Add additional information for the user
st.info("**Help Tips:**  \n"
        "• Target Company Name: The company you want to research  \n"
        "• Context Company: YOUR company that will create the report  \n"
        "• Stock Ticker Symbol: The ticker of the target company (e.g., AAPL for Apple)  \n"
        "• Primary Industry: The main industry of the target company")

# Handle form submission
if generate_button:
    if not target_company:
        st.error("Please enter a target company name.")
    elif not context_company:
        st.error("Please enter your company name as the context company.")
    else:
        # Get selected language
        language_key, language = selected_language_option

        # Filter selected prompts
        if selected_sections:
            selected_prompts = [(section_id, prompt_func) for section_id, prompt_func in PROMPT_FUNCTIONS if section_id in selected_sections]
        else:
            selected_prompts = PROMPT_FUNCTIONS

        # Generate report
        with st.spinner(f"Generating report for {target_company} in {language}..."):
            token_stats, pdf_path, base_dir = generate_report_with_progress(
                target_company,
                language,
                selected_prompts,
                context_company,
                ticker=ticker if ticker else None,
                industry=industry if industry else None
            )

        if token_stats and pdf_path and pdf_path.exists(): # Added check for pdf_path existence
            # Display success message and stats
            st.success(f"Report for {target_company} generated successfully!")

            # Display report statistics
            st.markdown('<h3 class="section-title">Report Statistics</h3>', unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(
                    metric_card(
                        "📊",
                        "Total Tokens",
                        f"{token_stats['summary']['total_tokens']:,}"
                    ),
                    unsafe_allow_html=True
                )

            with col2:
                st.markdown(
                    metric_card(
                        "⏱️",
                        "Generation Time",
                        format_time(token_stats['summary']['total_execution_time'])
                    ),
                    unsafe_allow_html=True
                )

            with col3:
                st.markdown(
                    metric_card(
                        "✅",
                        "Successful Sections",
                        token_stats['summary']['successful_prompts']
                    ),
                    unsafe_allow_html=True
                )

            # Display PDF preview
            st.markdown('<h3 class="section-title">Report Preview</h3>', unsafe_allow_html=True)
            st.markdown('<div class="pdf-container">', unsafe_allow_html=True)
            display_pdf(pdf_path)
            st.markdown('</div>', unsafe_allow_html=True)

            # Download button for PDF
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                with open(pdf_path, "rb") as file:
                    st.download_button(
                        label="Download PDF Report",
                        data=file,
                        file_name=f"{target_company}_{language}_Report.pdf",
                        mime="application/pdf",
                        key="download-pdf"
                    )

            # Save location
            st.info(f"Report saved to: {pdf_path}")
        elif token_stats and not pdf_path: # Case where generation finished but PDF failed or wasn't created
             st.warning("Report generation completed, but PDF could not be generated or found. Please check the logs.")
             # You might still want to show stats here
        else: # Case where generate_report_with_progress returned None for stats/path
            st.error("Failed to generate report. Please check the logs for details.")

# Add footer
st.markdown('<div class="footer">', unsafe_allow_html=True)
st.markdown('© 2024 Account Research AI Agent by Supervity', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)