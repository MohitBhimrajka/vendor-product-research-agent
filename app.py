import streamlit as st
import os
import base64
from pathlib import Path
import time # For simulating wait
import re # For sanitizing identifiers in filenames
import json # Import json for potentially displaying raw data
from typing import Dict

# Import orchestrator functions
from report_orchestrator import (
    run_vendor_research,
    run_product_research_initial,
    filter_vendors_based_on_answers, # New function import
    run_product_research_phase2, # Phase 2 function
    trigger_vendor_deep_dives,     # New import
    generate_final_product_report # New import for final step
)
from config import OUTPUT_DIR, PRODUCT_FULL_SECTION_ORDER, VENDOR_SECTION_ORDER, VENDOR_PROMPT_FUNCTIONS, PRODUCT_INITIAL_PROMPT_FUNCTIONS
# Import PDF generator function
from pdf_generator import process_markdown_files

# --- Page Config ---
st.set_page_config(
    page_title="Vendor & Product Research Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Logo ---
@st.cache_data
def get_logo_base64():
    try:
        logo_path = os.path.join("static", "logo.png")
        with open(logo_path, "rb") as f:
            data = f.read()
            return base64.b64encode(data).decode()
    except Exception as e:
        print(f"Error loading logo: {e}")
        return None

# --- Custom CSS (Optional - Add styles as needed) ---
def apply_custom_css():
    css = """
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .header-logo {
        max-height: 60px;
        margin-bottom: 20px;
    }
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

apply_custom_css()

# --- Helper Function to Display PDF ---
def display_pdf(pdf_path: Path):
    if pdf_path and pdf_path.exists():
        try:
            with open(pdf_path, "rb") as f:
                base64_pdf = base64.b64encode(f.read()).decode('utf-8')
            
            display_text = f"""
            <div style="text-align: center; margin-bottom: 10px;">
                <a href="data:application/pdf;base64,{base64_pdf}" download="{pdf_path.name}" target="_blank">
                    <button style="background-color: #4CAF50; color: white; padding: 10px 24px; border: none; border-radius: 4px; cursor: pointer;">
                        Download PDF
                    </button>
                </a>
            </div>
            <iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>
            """
            st.markdown(display_text, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error displaying PDF: {e}")
    else:
        st.error(f"PDF file not found: {pdf_path}")

# --- Helper Function to Display Generation Status ---
def display_generation_status(status_dict: Dict):
    if not status_dict:
        return

    st.subheader("Generation Progress:")
    cols = st.columns(3) # Adjust columns as needed
    col_index = 0
    sorted_sections = sorted(status_dict.keys()) # Display alphabetically or by config order if available

    for section_id in sorted_sections:
        info = status_dict[section_id]
        status = info.get("status", "pending")
        
        # Determine icon based on status
        icon = "⏳" if status == "running" else \
               "✅" if status == "success" else \
               "❌" if status == "error" else \
               "⚠️" if status == "skipped" or status == "interrupted" else \
               "🔄" if status == "pending" else \
               "❓" # Default unknown icon
        
        # Format section name nicely for display
        section_name = section_id.replace('_', ' ').title()
        
        # Create status text with icon
        status_text = f"{icon} {section_name}"
        
        # Add to appropriate column
        with cols[col_index % len(cols)]:
            # Apply styling based on status
            if status == "success":
                st.markdown(f"<div style='color: green; margin-bottom: 5px;'>{status_text}</div>", unsafe_allow_html=True)
            elif status == "error":
                st.markdown(f"<div style='color: red; margin-bottom: 5px;'>{status_text}</div>", unsafe_allow_html=True)
                # Optionally show error details in expandable section
                if "error" in info:
                    with st.expander("Error details", expanded=False):
                        st.write(info["error"])
            elif status == "running":
                st.markdown(f"<div style='color: blue; margin-bottom: 5px;'>{status_text}</div>", unsafe_allow_html=True)
            elif status in ["skipped", "interrupted"]:
                st.markdown(f"<div style='color: orange; margin-bottom: 5px;'>{status_text}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='margin-bottom: 5px;'>{status_text}</div>", unsafe_allow_html=True)
            
            # Optionally show timing for completed tasks
            if status == "success" and "execution_time" in info:
                st.caption(f"Done in {info['execution_time']:.1f}s")
        
        col_index += 1
    
    st.divider()

# --- Helper Function to Display Dashboard ---
def display_dashboard(dashboard_data):
    if not dashboard_data or 'error' in dashboard_data:
        st.warning(f"Could not display dashboard data. Error: {dashboard_data.get('error', 'Unknown') if dashboard_data else 'No data'}")
        if dashboard_data and 'raw_response' in dashboard_data:
             with st.expander("Show Raw Summary Response"):
                  st.code(dashboard_data['raw_response'], language=None)
        return

    st.subheader("📊 Dashboard Summary")

    # --- Vendor Dashboard ---
    if "financial_stability_assessment" in dashboard_data: # Check for vendor keys
        col1, col2, col3 = st.columns(3)
        col1.metric("Financial Stability", dashboard_data.get("financial_stability_assessment", "N/A"))
        col2.metric("Operational Risk", dashboard_data.get("operational_risk_assessment", "N/A"))
        col3.metric("Compliance Risk", dashboard_data.get("compliance_risk_assessment", "N/A"))

        st.markdown("**Key Compliance Checks:**")
        compliance_checks = dashboard_data.get("key_compliance_checks", {})
        if compliance_checks and isinstance(compliance_checks, dict):
            # Display as table or formatted string
            compliance_cols = st.columns(min(len(compliance_checks), 4))  # Limit to 4 columns max
            i = 0
            for cert, status in compliance_checks.items():
                 with compliance_cols[i % len(compliance_cols)]:
                      st.markdown(f"**{cert}:** {status}")
                 i += 1
        else:
            st.markdown("N/A")

        st.markdown("**Top Identified Risks:**")
        top_risks = dashboard_data.get("top_3_risks", [])
        if top_risks and isinstance(top_risks, list) and len(top_risks) > 0:
            for risk in top_risks:
                if risk:  # Only display non-empty values
                    st.markdown(f"- {risk}")
        else:
            st.markdown("N/A")

        st.metric("Overall Suitability Recommendation", dashboard_data.get("overall_suitability", "N/A"))

    # --- Product Dashboard ---
    elif "identified_vendor_count" in dashboard_data: # Check for product keys
        col1, col2, col3 = st.columns(3)
        col1.metric("Initial Vendors Identified", dashboard_data.get("identified_vendor_count", "N/A"))
        col2.metric("Vendors After Filtering", dashboard_data.get("filtered_vendor_count", "N/A"))
        col3.metric("Market Growth Trend", dashboard_data.get("market_growth_trend", "N/A"))

        st.markdown("**Top Filtered Vendors:**")
        top_vendors = dashboard_data.get("top_3_filtered_vendors", [])
        if top_vendors and isinstance(top_vendors, list) and len(top_vendors) > 0:
            vendors_to_display = [v for v in top_vendors if v]  # Filter out empty or None values
            if vendors_to_display:
                st.markdown(", ".join([f"**{v}**" for v in vendors_to_display]))
            else:
                st.markdown("N/A")
        else:
            st.markdown("N/A")

        st.markdown("**Key Technology Trends:**")
        tech_trends = dashboard_data.get("key_tech_trends", [])
        if tech_trends and isinstance(tech_trends, list) and len(tech_trends) > 0:
            for trend in tech_trends:
                if trend:  # Only display non-empty values
                    st.markdown(f"- {trend}")
        else:
            st.markdown("N/A")

        st.markdown("**Common Compliance Standards:**")
        comp_standards = dashboard_data.get("common_compliance_standards", [])
        if comp_standards and isinstance(comp_standards, list) and len(comp_standards) > 0:
            for std in comp_standards:
                if std:  # Only display non-empty values
                    st.markdown(f"- {std}")
        else:
            st.markdown("N/A")

    else:
        st.warning("Unrecognized dashboard data format.")
        with st.expander("Show Raw Dashboard Data"):
            st.json(dashboard_data)

# --- Initialize Session State for State Management ---
if 'current_task' not in st.session_state:
    st.session_state.current_task = None  # Initial state

# Define all possible states
# None: Initial state, ready for input
# generating_vendor_report: Processing vendor report generation
# vendor_report_completed: Vendor report generation is complete, showing results
# generating_product_initial: Processing initial product analysis
# awaiting_filter_input: Waiting for user to answer filtering questions
# filtering_vendors: Processing filtering based on user answers
# awaiting_phase2_setup: Showing filtered vendors, waiting for user to select comparison criteria
# generating_phase2: Processing phase 2 (profiles, comparison, relevance)
# awaiting_deepdive_selection: Waiting for user to select vendors for deep dive
# generating_deepdives: Processing deep dive vendor research
# awaiting_final_pdf: Waiting for user to trigger final PDF generation
# generating_final_pdf: Processing final PDF generation
# complete: Final PDF has been generated, showing results

# --- Unified State Management Helper Functions ---
def is_input_allowed():
    """Determine if user input should be allowed based on current task"""
    # Only allow input in specific states
    input_allowed_states = [None, 'vendor_report_completed', 'awaiting_filter_input', 
                            'awaiting_phase2_setup', 'awaiting_deepdive_selection', 
                            'awaiting_final_pdf', 'complete']
    return st.session_state.current_task in input_allowed_states

def is_product_input_allowed():
    """Determine if product category input should be allowed"""
    # Only allow product input in initial state or completed state
    return st.session_state.current_task in [None, 'complete']

def store_inputs_for_later():
    """Store current inputs in session state for later use"""
    # Store context_company_name, optional_inputs and identifiers
    st.session_state.optional_inputs_storage = {
        'optional_inputs': optional_inputs.copy(),
        'context_company_name': context_company_name
    }
    
    # Store identifier based on mode
    if research_mode == "Product Research":
        st.session_state.optional_inputs_storage['product_identifier'] = st.session_state.get(identifier_key, "")
        # Also store in convenient access location
        st.session_state.product_identifier = st.session_state.get(identifier_key, "")
    else:  # Vendor Research mode
        st.session_state.optional_inputs_storage['vendor_identifier'] = st.session_state.get(identifier_key, "")
        # Also store in convenient access location
        st.session_state.vendor_name = st.session_state.get(identifier_key, "")

def get_stored_inputs():
    """Retrieve stored inputs for later stages"""
    if not st.session_state.optional_inputs_storage:
        return {}, "", ""
        
    stored_inputs = st.session_state.optional_inputs_storage.get('optional_inputs', {})
    stored_company = st.session_state.optional_inputs_storage.get('context_company_name', '')
    
    if research_mode == "Product Research":
        stored_identifier = st.session_state.optional_inputs_storage.get('product_identifier', '')
    else:
        stored_identifier = st.session_state.optional_inputs_storage.get('vendor_identifier', '')
        
    return stored_inputs, stored_company, stored_identifier

def reset_state():
    """Reset all session state variables"""
    # Keep minimal state but reset task
    st.session_state.current_task = None
    
    # Reset all tracking variables
    for key in ['report_generated', 'report_summary', 'pdf_path', 'error_message',
                'vendor_name', 'product_identifier', 'product_base_dir',
                'filtering_questions', 'filter_messages', 'filtered_vendors',
                'current_question_index', 'filter_answers', 'selected_comparison_criteria',
                'phase2_summary', 'phase2_dashboard_data', 'deep_dive_selection',
                'deep_dive_results', 'final_pdf_path', 'dashboard_data', 'optional_inputs_storage']:
        if key in st.session_state:
            if isinstance(st.session_state[key], dict):
                st.session_state[key] = {}
            elif isinstance(st.session_state[key], list):
                st.session_state[key] = []
            else:
                st.session_state[key] = None
    
    # Reset boolean flags to false
    for key in ['generation_in_progress', 'product_initial_run_complete', 
                'filter_answers_submitted', 'filtering_in_progress',
                'phase2_run_complete', 'phase2_in_progress',
                'deep_dive_in_progress', 'final_pdf_generated',
                'final_pdf_in_progress', 'trigger_final_product_report']:
        if key in st.session_state:
            st.session_state[key] = False
    st.session_state.generation_status = {} # Reset generation status

# --- Initialize Session State ---
if 'report_generated' not in st.session_state:
    st.session_state.report_generated = False
if 'report_summary' not in st.session_state:
    st.session_state.report_summary = None
if 'pdf_path' not in st.session_state:
    st.session_state.pdf_path = None
if 'error_message' not in st.session_state:
    st.session_state.error_message = None
if 'current_mode' not in st.session_state:
    st.session_state.current_mode = "Vendor Research" # Default mode
if 'dashboard_data' not in st.session_state:
    st.session_state.dashboard_data = None # For vendor mode or final product mode
if 'phase2_dashboard_data' not in st.session_state:
    st.session_state.phase2_dashboard_data = None # For product mode after phase 2
if 'generation_status' not in st.session_state:
    st.session_state.generation_status = {} # Holds status of each section

# New unified state management
if 'current_task' not in st.session_state:
    st.session_state.current_task = None  # None, 'generating_vendor_report', 'vendor_report_completed', 
                                          # 'generating_product_initial', 'awaiting_filter_input', 
                                          # 'filtering_vendors', 'displaying_filtered_results'

# Legacy flags - will be removed after refactoring is complete
if 'generation_in_progress' not in st.session_state:
    st.session_state.generation_in_progress = False
if 'vendor_name' not in st.session_state:
    st.session_state.vendor_name = ""  # Store vendor name
if 'product_identifier' not in st.session_state:
    st.session_state.product_identifier = "" # Store product name
if 'product_initial_run_complete' not in st.session_state:
    st.session_state.product_initial_run_complete = False
if 'product_base_dir' not in st.session_state:
    st.session_state.product_base_dir = None
if 'filtering_questions' not in st.session_state:
    st.session_state.filtering_questions = None
# Chat history for filtering questions
if 'filter_messages' not in st.session_state:
    st.session_state.filter_messages = [] # List of {"role": "assistant/user", "content": ...}
if 'filter_answers_submitted' not in st.session_state:
    st.session_state.filter_answers_submitted = False
if 'filtering_in_progress' not in st.session_state:
    st.session_state.filtering_in_progress = False
if 'filtered_vendors' not in st.session_state:
    st.session_state.filtered_vendors = None
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0
if 'filter_answers' not in st.session_state:
    st.session_state.filter_answers = {}
if 'comparison_criteria_options' not in st.session_state:
    # Define potential criteria (could be dynamically generated later)
    st.session_state.comparison_criteria_options = [
        "Core Features Match", "Technology Stack", "Target Customer Size",
        "Key Certifications (ISO27001/SOC2)", "Geographic Coverage",
        "Support Options", "Pricing Model (Stated/Inferred)"
    ]
if 'selected_comparison_criteria' not in st.session_state:
    st.session_state.selected_comparison_criteria = []
if 'phase2_run_complete' not in st.session_state:
    st.session_state.phase2_run_complete = False
if 'phase2_in_progress' not in st.session_state:
    st.session_state.phase2_in_progress = False
if 'phase2_summary' not in st.session_state:
    st.session_state.phase2_summary = None
if 'deep_dive_selection' not in st.session_state:
    st.session_state.deep_dive_selection = []
if 'deep_dive_in_progress' not in st.session_state:
    st.session_state.deep_dive_in_progress = False
if 'deep_dive_results' not in st.session_state:
    st.session_state.deep_dive_results = None
if 'final_pdf_generated' not in st.session_state:
    st.session_state.final_pdf_generated = False
if 'final_pdf_path' not in st.session_state:
    st.session_state.final_pdf_path = None
if 'final_pdf_in_progress' not in st.session_state:
    st.session_state.final_pdf_in_progress = False
if 'optional_inputs_storage' not in st.session_state:
    st.session_state.optional_inputs_storage = {}

# --- Header ---
logo_b64 = get_logo_base64()
if logo_b64:
    # Use columns for better layout if needed
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image(f"data:image/png;base64,{logo_b64}", width=150)
    with col2:
        st.title("Vendor & Product Research AI Agent")
        st.markdown("Your intelligent assistant for supplier and market analysis.")
else:
    st.title("Vendor & Product Research AI Agent")
    st.markdown("Your intelligent assistant for supplier and market analysis.")
st.divider()

# --- Main App Logic ---

# Sidebar for Configuration
with st.sidebar:
    st.header("⚙️ Research Configuration")

    # --- Reset Function ---
    def reset_state():
        st.session_state.report_generated = False
        st.session_state.report_summary = None
        st.session_state.pdf_path = None
        st.session_state.error_message = None
        st.session_state.current_task = None  # Reset the unified state
        st.session_state.generation_in_progress = False # Reset flag
        st.session_state.filtering_in_progress = False # Reset flag
        st.session_state.vendor_name = ""
        st.session_state.product_identifier = ""
        st.session_state.product_initial_run_complete = False
        st.session_state.product_base_dir = None
        st.session_state.filtering_questions = None
        st.session_state.filter_messages = []
        st.session_state.filter_answers_submitted = False
        st.session_state.filtered_vendors = None
        st.session_state.current_question_index = 0
        st.session_state.filter_answers = {}
        st.session_state.comparison_criteria_options = [
            "Core Features Match", "Technology Stack", "Target Customer Size",
            "Key Certifications (ISO27001/SOC2)", "Geographic Coverage",
            "Support Options", "Pricing Model (Stated/Inferred)"
         ]
        st.session_state.selected_comparison_criteria = []
        st.session_state.phase2_run_complete = False
        st.session_state.phase2_in_progress = False
        st.session_state.deep_dive_in_progress = False
        st.session_state.final_pdf_generated = False
        st.session_state.final_pdf_in_progress = False
        st.session_state.optional_inputs_storage = {}
        st.session_state.generation_status = {} # Reset generation status

    # 1. Mode Selection
    research_mode = st.selectbox(
        "Select Research Mode:",
        ("Vendor Research", "Product Research"),
        key="research_mode_select",
        index=0 if st.session_state.current_mode == "Vendor Research" else 1, # Maintain selection across runs
        on_change=reset_state
    )
    st.session_state.current_mode = research_mode # Store current mode

    # 2. Context Company
    context_company_name = st.text_input(
        "Your Company Name (Context):",
        placeholder="Required: Enter your company name",
        key="context_company_input",
        help="Your company's name, used for context in analysis."
    )

    st.divider()

    # --- Mode-Specific Inputs ---
    optional_inputs = {} # Initialize dict for optional inputs
    submit_button_label = ""
    identifier_label = ""
    identifier_key = ""
    identifier_value_input = "" # Use a different var name to avoid conflict with state
    
    # Determine if inputs should be enabled based on current task
    allow_submit = st.session_state.current_task is None  # Only allow submit in initial state
    
    # For backwards compatibility during transition
    if not hasattr(st.session_state, 'current_task') or st.session_state.current_task is None:
        allow_submit = not st.session_state.get('generation_in_progress', False) and not st.session_state.get('filtering_in_progress', False)

    if research_mode == "Vendor Research":
        st.subheader("Vendor Details")
        identifier_label = "Vendor Name:"
        identifier_key = "vendor_name_input"
        submit_button_label = "Generate Vendor Report"
        identifier_value_input = st.text_input(identifier_label, key=identifier_key, placeholder="Required: Enter vendor name", disabled=not allow_submit)
        st.markdown("**Optional Filters:**")
        optional_inputs["product_category"] = st.text_input("Product/Service Category Provided by Vendor:", key="vendor_prod_cat_input", disabled=not allow_submit)
        optional_inputs["required_certs"] = st.text_input("Required Certifications (comma-separated):", key="vendor_certs_input", disabled=not allow_submit)
        optional_inputs["region"] = st.text_input("Geographic Region of Supply:", key="vendor_region_input", disabled=not allow_submit)

    elif research_mode == "Product Research":
        st.subheader("Product Details")
        identifier_label = "Product/Service Category:"
        identifier_key = "product_cat_input"
        submit_button_label = "Start Initial Product Analysis"
        # Only allow input if initial analysis isn't done
        can_edit_product_input = allow_submit and not st.session_state.product_initial_run_complete
        
        # For backwards compatibility
        if not hasattr(st.session_state, 'current_task'):
            can_edit_product_input = not st.session_state.product_initial_run_complete and not st.session_state.generation_in_progress
            
        identifier_value_input = st.text_input(identifier_label, key=identifier_key, placeholder="Required: Enter product category", disabled=not can_edit_product_input)
        st.markdown("**Optional Filters:**")
        optional_inputs["required_certs"] = st.text_input("Required Certifications (comma-separated):", key="product_certs_input", disabled=not can_edit_product_input)
        optional_inputs["region"] = st.text_input("Geographic Region:", key="product_region_input", disabled=not can_edit_product_input)

    # Start Button
    if (st.session_state.current_task is None and not st.session_state.product_initial_run_complete) or \
       (not hasattr(st.session_state, 'current_task') and not st.session_state.generation_in_progress and not st.session_state.product_initial_run_complete):
        if st.button(submit_button_label, key="start_button", use_container_width=True, disabled=not allow_submit):
            # --- Input Validation ---
            # Read directly from widget state using keys
            identifier_value = st.session_state.get(identifier_key, "")  # Use .get for safety
            
            valid_input = True
            if not identifier_value:
                st.error(f"{identifier_label.replace(':','')} is required.")
                valid_input = False
            if not context_company_name:
                st.error("Your Company Name (Context) is required.")
                valid_input = False

            if valid_input:
                # Store inputs needed for later phases
                st.session_state.optional_inputs_storage = {
                    'optional_inputs': optional_inputs.copy(),
                    'context_company_name': context_company_name
                }
                if research_mode == "Product Research":
                    st.session_state.optional_inputs_storage['product_identifier'] = identifier_value
                    st.session_state.product_identifier = identifier_value
                    st.session_state.current_task = "generating_product_initial"  # Set task state
                else:  # Vendor Research mode
                    st.session_state.optional_inputs_storage['vendor_identifier'] = identifier_value
                    st.session_state.vendor_name = identifier_value
                    st.session_state.current_task = "generating_vendor_report"  # Set task state
                    
                # Now set the generation flag and rerun
                st.session_state.generation_in_progress = True
                st.rerun()

# --- Generation Execution Block ---
if st.session_state.current_task in ["generating_vendor_report", "generating_product_initial"] or \
   (not hasattr(st.session_state, 'current_task') and st.session_state.generation_in_progress):
    
    # --- Initialize status dict at the start of generation if empty ---
    if not st.session_state.generation_status:
        # Determine which sections will be run based on mode
        if st.session_state.current_mode == "Vendor Research":
            sections_to_run = [s[0] for s in VENDOR_PROMPT_FUNCTIONS]
        elif st.session_state.current_mode == "Product Research":
            sections_to_run = [s[0] for s in PRODUCT_INITIAL_PROMPT_FUNCTIONS]
        else:
            sections_to_run = []
        # Initialize status dictionary
        st.session_state.generation_status = {sec_id: {"status": "pending"} for sec_id in sections_to_run}

    st.header("⚙️ Processing Your Request...")
    # Replace the progress bar with status display
    # progress_bar = st.progress(0)
    status_text = st.empty()
    status_text.info("Running report generation... please wait. Status updates below.")
    
    # --- Display the generation status ---
    display_generation_status(st.session_state.generation_status)
    
    try:
        # Only run the generation logic if we haven't completed yet
        if 'generation_complete' not in st.session_state or not st.session_state.generation_complete:
            success = False
            
            if st.session_state.current_mode == "Vendor Research":
                vendor_name = st.session_state.vendor_name
                
                # Pass status_dict to orchestrator
                token_stats, pdf_path_result, dashboard_result = run_vendor_research(
                    vendor_name=vendor_name,
                    context_company_name=context_company_name,
                    optional_inputs=optional_inputs,
                    status_dict=st.session_state.generation_status  # Pass status dictionary
                )
                
                # Store in session state
                st.session_state.report_generated = True
                st.session_state.report_summary = token_stats.get('summary', {}) if token_stats else None
                st.session_state.pdf_path = pdf_path_result
                st.session_state.dashboard_data = dashboard_result # Store dashboard data
                
                # status_text.text(f"Completed vendor research for: {vendor_name}")
                
            elif st.session_state.current_mode == "Product Research":
                product_category = st.session_state.product_identifier
                
                # Pass status_dict to orchestrator
                token_stats, base_dir_result, questions_result = run_product_research_initial(
                    product_category=product_category,
                    context_company_name=context_company_name,
                    optional_inputs=optional_inputs,
                    status_dict=st.session_state.generation_status  # Pass status dictionary
                )
                
                # Store initial results
                st.session_state.product_initial_run_complete = True
                st.session_state.product_base_dir = base_dir_result
                st.session_state.report_summary = token_stats.get('summary', {}) if token_stats else None
                
                # Set up filtering questions if available
                st.session_state.filtering_questions = questions_result
                if questions_result:
                    st.session_state.filter_messages = [{"role": "assistant", "content": questions_result[0]}]
                    st.session_state.current_question_index = 0
                
                # status_text.text(f"Completed initial analysis for: {product_category}")
            
            success = bool(token_stats and not token_stats.get('summary', {}).get('was_interrupted', False))
            st.session_state.generation_complete = True
            st.session_state.generation_success = success
                
    except Exception as e:
        st.error(f"Error during generation: {str(e)}")
        st.session_state.error_message = str(e)
        import traceback
        print(f"Generation Error: {traceback.format_exc()}")
        st.session_state.generation_complete = True
        st.session_state.generation_success = False
        
    finally:
        # Check if generation has completed
        if st.session_state.get('generation_complete', False):
            st.session_state.generation_in_progress = False # Stop the rerun loop
            
            # Clear the 'Running...' status text
            status_text.empty()
            
            # Show final status
            display_generation_status(st.session_state.generation_status)
            
            if st.session_state.get('generation_success', False):
                st.success("Report generation completed successfully!")
                # Update current_task based on the mode and completion status
                if st.session_state.current_mode == "Vendor Research":
                    st.session_state.current_task = "vendor_report_completed"
                elif st.session_state.current_mode == "Product Research":
                    if st.session_state.filtering_questions:
                        st.session_state.current_task = "awaiting_filter_input"
                    else:
                        st.session_state.current_task = "awaiting_filter_input"
                        st.warning("Initial analysis complete, but no filtering questions were generated.")
            else:
                st.error("Report generation encountered an error or was interrupted.")
                # Reset task on failure to allow retry from the start
                st.session_state.current_task = None
            
            # Reset temporary flags
            if 'generation_complete' in st.session_state:
                del st.session_state.generation_complete
            if 'generation_success' in st.session_state:
                del st.session_state.generation_success
                
            # Final rerun to show results
            time.sleep(0.5)
            st.rerun()
    
    # --- Add rerun loop to update status display ---
    # If generation is still in progress, wait and rerun to get status updates
    if st.session_state.get('generation_in_progress', False):
        time.sleep(2)  # Wait 2 seconds before next check
        st.rerun()  # Rerun the script to update the UI

# --- Filtering Execution Block ---
if st.session_state.current_task == "filtering_vendors" or \
   (not hasattr(st.session_state, 'current_task') and st.session_state.get('filtering_in_progress', False)):
    st.header("⚙️ Filtering Vendors...")
    st.info("Processing your answers to refine the vendor list...")
    st.session_state.error_message = None
    success = False
    try:
         with st.spinner("Filtering vendors based on your input..."):
             # Extract answers from chat history
             user_answers = [msg["content"] for msg in st.session_state.filter_messages if msg["role"] == "user"]

             if not user_answers or len(user_answers) != len(st.session_state.filtering_questions):
                  st.warning("Please ensure you have answered all filtering questions before submitting.")
                  # Don't proceed if answers are incomplete
                  st.session_state.current_task = "awaiting_filter_input"  # Revert to awaiting input
                  st.session_state.filtering_in_progress = False  # For backwards compatibility
                  st.session_state.filter_answers_submitted = False  # For backwards compatibility
                  st.rerun()
             elif not st.session_state.product_base_dir or not Path(st.session_state.product_base_dir).exists():
                  st.error("Cannot filter: Initial product analysis directory not found or invalid.")
                  st.session_state.current_task = "awaiting_filter_input"  # Revert to awaiting input
                  st.session_state.filtering_in_progress = False  # For backwards compatibility
                  st.session_state.filter_answers_submitted = False  # For backwards compatibility
                  st.rerun()
             else:
                  # Call the filter_vendors_based_on_answers function
                  filtered_vendor_list = filter_vendors_based_on_answers(
                       base_dir=Path(st.session_state.product_base_dir),
                       questions=st.session_state.filtering_questions,
                       answers=user_answers
                  )
                  # Store the result in session state
                  st.session_state.filtered_vendors = filtered_vendor_list
                  success = filtered_vendor_list is not None # None indicates failure

    except Exception as e:
         st.session_state.error_message = f"An error occurred during filtering: {str(e)}"
         import traceback
         print(f"Filtering Error: {traceback.format_exc()}")
         success = False
    finally:
         # Update task state based on success
         if success:
             st.session_state.current_task = "displaying_filtered_results"
             st.success("Vendor list filtered based on your answers!")
         else:
             st.session_state.current_task = "awaiting_filter_input"  # Go back to input state on failure
         
         # For backwards compatibility
         st.session_state.filtering_in_progress = False # Ensure this is always reset
         if success:
             st.session_state.filter_answers_submitted = True
             
         st.rerun() # Update UI with filtering results

# --- Phase 2 Execution Block (Vendor Comparison Matrix, etc.) ---
if st.session_state.current_task == "generating_phase2": # NEW Check
    # --- Initialize status dict for phase 2 if empty ---
    if not st.session_state.generation_status:
        # Determine sections for phase 2 (profiles, comparison, etc.)
        phase2_sections = ["comparison_matrix", "product_relevance", "product_recommendations"]
        if st.session_state.filtered_vendors:
             # Add profile sections for each vendor
             phase2_sections.extend([f"profile_{re.sub(r'[^a-zA-Z0-9_]', '_', v)}" for v in st.session_state.filtered_vendors])
        # Initialize status dictionary
        st.session_state.generation_status = {sec_id: {"status": "pending"} for sec_id in phase2_sections}

    st.header("⚙️ Generating Profiles, Comparison & Recommendations...")
    status_text_p2 = st.empty()
    status_text_p2.info("Running Phase 2 processing... Status updates below.")
    
    # Display Phase 2 generation status
    display_generation_status(st.session_state.generation_status)
    
    try:
        # Only run the generation logic if we haven't completed yet
        if 'phase2_complete' not in st.session_state or not st.session_state.phase2_complete:
            success = False
            
            # Pass the status_dict to run_product_research_phase2
            phase2_summary, phase2_dashboard_data = run_product_research_phase2(
                base_dir=Path(st.session_state.product_base_dir),
                product_category=st.session_state.product_identifier,
                context_company_name=context_company_name,
                optional_inputs=optional_inputs,
                filtered_vendors=st.session_state.filtered_vendors,
                comparison_criteria=st.session_state.selected_comparison_criteria,
                status_dict=st.session_state.generation_status  # Pass status dictionary
            )
            
            # Store in session state
            if phase2_summary:
                st.session_state.phase2_run_complete = True
                st.session_state.phase2_summary = phase2_summary
                st.session_state.phase2_dashboard_data = phase2_dashboard_data # Store dashboard data
                success = True
            
            st.session_state.phase2_complete = True
            st.session_state.phase2_success = success
    
    except Exception as e:
        st.error(f"Error during Phase 2 processing: {str(e)}")
        import traceback
        print(f"Phase 2 Error: {traceback.format_exc()}")
        st.session_state.phase2_complete = True
        st.session_state.phase2_success = False
        
    finally:
        # Check if phase 2 has completed
        if st.session_state.get('phase2_complete', False):
            st.session_state.phase2_in_progress = False # Stop the rerun loop
            
            # Clear the 'Running...' status text
            status_text_p2.empty()
            
            # Show final status
            display_generation_status(st.session_state.generation_status)
            
            # --- ADD STATE TRANSITION ---
            if st.session_state.get('phase2_success', False):
                st.success("Phase 2 completed successfully!")
                st.session_state.phase2_run_complete = True # Set legacy completion flag
                st.session_state.current_task = "awaiting_deepdive_selection" # Transition state
            else:
                st.error("Phase 2 processing encountered an error.")
                # Revert state on error
                st.session_state.current_task = "displaying_filtered_results" # Go back to comparison setup
            
            # Reset temporary flags
            if 'phase2_complete' in st.session_state:
                del st.session_state.phase2_complete
            if 'phase2_success' in st.session_state:
                del st.session_state.phase2_success
                
            st.rerun()
            # --- END STATE TRANSITION ---
    
    # --- Add rerun loop to update status display ---
    # If phase 2 is still in progress, wait and rerun to get status updates
    if st.session_state.get('phase2_in_progress', False):
        time.sleep(2)  # Wait 2 seconds before next check
        st.rerun()  # Rerun the script to update the UI

# --- Deep Dive Execution Block ---
if st.session_state.current_task == "generating_deepdives": # Check if task is deep dive generation
    st.header("⚙️ Running Deep Dive Vendor Research...")
    try:
        success = False
        with st.spinner("Processing deep dives (this may take several minutes)..."):
            base_dir = Path(st.session_state.product_base_dir)
            # Use the CLEAN vendor names from deep_dive_selection
            vendors_to_research = st.session_state.deep_dive_selection

            # Ensure vendors_to_research contains clean names
            print(f"DEBUG: Vendors selected for deep dive: {vendors_to_research}")

            deep_dive_results_dict = trigger_vendor_deep_dives(
                base_dir=base_dir,
                vendors_to_research=vendors_to_research,
                context_company_name=st.session_state.optional_inputs_storage.get('context_company_name', ''),
                optional_inputs=st.session_state.optional_inputs_storage.get('optional_inputs', {})
            )

            st.session_state.deep_dive_results = deep_dive_results_dict
            success = bool(deep_dive_results_dict)

    except Exception as e:
        st.error(f"Error during deep dive processing: {str(e)}")
        import traceback
        print(f"Deep Dive Error: {traceback.format_exc()}")
        success = False
    finally:
        st.session_state.deep_dive_in_progress = False # Reset legacy flag
        # --- ADD STATE TRANSITION HERE ---
        if success:
            st.success("Deep dive research completed!")
            st.session_state.current_task = "awaiting_final_pdf" # Transition to next state
        else:
            st.error("Deep dive processing encountered an error.")
            # Decide where to go on error - maybe back to selection?
            st.session_state.current_task = "awaiting_deepdive_selection"
        # --- END STATE TRANSITION ---
        time.sleep(1)
        st.rerun()

# --- Final PDF/Dashboard Generation Trigger (NEW BLOCK) ---
if 'trigger_final_product_report' not in st.session_state:
    st.session_state.trigger_final_product_report = False

# if st.session_state.trigger_final_product_report: # OLD Check
if st.session_state.current_task == "generating_final_pdf": # NEW Check
     st.header("⚙️ Generating Final Report & Dashboard...")
     st.session_state.error_message = None
     success = False
     try:
          with st.spinner("Generating final combined PDF and dashboard summary..."):
               # Retrieve necessary state
               base_dir = Path(st.session_state.product_base_dir)
               product_category = st.session_state.product_identifier
               filtered_vendors = st.session_state.filtered_vendors
               deep_dive_vendors = st.session_state.deep_dive_selection # Vendors selected for deep dive

               # Call the final generation function
               final_pdf_path, final_dashboard_data = generate_final_product_report(
                    base_dir=base_dir,
                    product_category=product_category,
                    context_company_name=context_company_name, # Ensure context is available
                    optional_inputs=st.session_state.optional_inputs_storage, # Pass optional inputs
                    filtered_vendors=filtered_vendors,
                    deep_dive_vendors=deep_dive_vendors
               )

               if final_pdf_path:
                    st.session_state.final_pdf_path = final_pdf_path
                    st.session_state.dashboard_data = final_dashboard_data # Store final dashboard
                    st.session_state.final_pdf_generated = True
                    success = True
               else:
                    st.session_state.error_message = "Failed to generate final PDF report."

     except Exception as e:
          st.session_state.error_message = f"An error occurred during final report generation: {str(e)}"
          import traceback
          print(f"Final Report Error: {traceback.format_exc()}")
          success = False
     finally:
          # st.session_state.trigger_final_product_report = False # No longer needed
          # --- ADD STATE TRANSITION ---
          if success:
              st.success("Final combined report and dashboard generated!")
              st.session_state.final_pdf_generated = True # Set legacy flag
              st.session_state.current_task = "complete" # Transition state
          else:
              st.error("Final report generation encountered an error.")
              # Revert state on error
              st.session_state.current_task = "awaiting_final_pdf"
          st.rerun()
          # --- END STATE TRANSITION ---

# --- Display Area ---
st.header("📊 Research Results & Next Steps")

# --- Display final status if generation just completed ---
if not st.session_state.get('generation_in_progress', False) and \
   not st.session_state.get('phase2_in_progress', False) and \
   st.session_state.generation_status:
    # Check if any sections are still running (shouldn't be, but just in case)
    if any(info.get('status') == 'running' for info in st.session_state.generation_status.values()):
        st.warning("Generation process ended, but some tasks might still be marked as running. Displaying last known status.")
    
    # Display final status only if we have something to show and results aren't loaded yet
    if not st.session_state.get('report_generated', False) or \
       (st.session_state.current_mode == "Product Research" and not st.session_state.get('product_initial_run_complete', False)):
        display_generation_status(st.session_state.generation_status)

# Display Vendor Mode Results
if research_mode == "Vendor Research":
    if st.session_state.dashboard_data: 
        display_dashboard(st.session_state.dashboard_data) # Display dashboard first
        
    if st.session_state.report_generated and st.session_state.report_summary:
        # Display summary stats
        summary = st.session_state.report_summary
        st.subheader("Report Summary")
        
        stats_col1, stats_col2 = st.columns(2)
        with stats_col1:
            st.metric("Successful Sections", summary.get("successful_sections", 0))
            st.metric("Processing Time", summary.get("formatted_execution_time", "N/A"))
        with stats_col2:
            st.metric("Total Tokens Used", summary.get("total_tokens", 0))
            st.metric("Status", "Complete" if not summary.get("was_interrupted", False) else "Interrupted")
            
        st.divider()
        # PDF Display
        if st.session_state.pdf_path and Path(st.session_state.pdf_path).exists():
            st.subheader("Generated Vendor Report")
            pdf_path = Path(st.session_state.pdf_path)
            col_btn, col_spacer = st.columns([1, 3])
            with col_btn:
                with open(pdf_path, "rb") as file:
                    st.download_button(
                        label="Download PDF",
                        data=file,
                        file_name=pdf_path.name,
                        mime="application/pdf",
                        key="download-btn",
                        use_container_width=True
                    )
            
            # File path info
            st.info(f"Report saved to: {pdf_path.relative_to(Path.cwd()) if pdf_path.is_relative_to(Path.cwd()) else pdf_path}")
            
            # PDF preview
            with st.container():
                st.markdown('<div class="report-container">', unsafe_allow_html=True)
                display_pdf(pdf_path)
                st.markdown('</div>', unsafe_allow_html=True)
        elif st.session_state.error_message:
            st.error(f"Error: {st.session_state.error_message}")
    elif st.session_state.error_message:
        st.error(f"Error: {st.session_state.error_message}")
    elif not st.session_state.generation_in_progress and not st.session_state.report_generated:
        st.info("Configure vendor research options and click 'Generate Vendor Report'.")

# Display Product Mode Results Stages
elif research_mode == "Product Research":
    # Stage 1: Initial Analysis Done, Awaiting Filtering Input
    if st.session_state.current_task == "awaiting_filter_input":
        st.subheader("Filter Vendors Based on Your Needs")
        st.info("Please answer the questions below to help narrow down the vendor list.")

        # Display initial analysis PDF if available
        if st.session_state.product_base_dir:
            initial_pdf_dir = Path(st.session_state.product_base_dir) / "pdf"
            if initial_pdf_dir.exists():
                pdf_files = list(initial_pdf_dir.glob("ProductInitialAnalysis_*.pdf"))
                if pdf_files:
                    with st.expander("View Initial Product Analysis Report", expanded=False):
                        display_pdf(pdf_files[0])

        # Display chat messages
        if "filter_messages" not in st.session_state:
             st.session_state.filter_messages = []
        if "current_question_index" not in st.session_state:
             st.session_state.current_question_index = 0
        if "filter_answers" not in st.session_state:
             st.session_state.filter_answers = {} # Stores {question: answer}

        # Add the first question if messages are empty and questions exist
        if not st.session_state.filter_messages and st.session_state.filtering_questions:
             st.session_state.filter_messages.append({"role": "assistant", "content": st.session_state.filtering_questions[0]})

        # Display existing chat messages
        for message in st.session_state.filter_messages:
             with st.chat_message(message["role"]):
                  st.markdown(message["content"])

        # Chat input for user's answer
        prompt = st.chat_input("Your answer...")
        if prompt:
            # Add user message to chat history
            st.session_state.filter_messages.append({"role": "user", "content": prompt})

            # Store the answer
            current_question = st.session_state.filtering_questions[st.session_state.current_question_index]
            st.session_state.filter_answers[current_question] = prompt

            # Move to the next question or finish
            st.session_state.current_question_index += 1
            if st.session_state.current_question_index < len(st.session_state.filtering_questions):
                # Ask the next question
                next_question = st.session_state.filtering_questions[st.session_state.current_question_index]
                st.session_state.filter_messages.append({"role": "assistant", "content": next_question})
            else:
                # All questions answered, add submit button
                st.session_state.filter_messages.append({"role": "assistant", "content": "Thank you! Click the button below to filter the vendors based on your answers."})
                # Set flag to show button (handled below)

            st.rerun() # Rerun to display new messages

        # Check if all questions have been asked (based on message history)
        # Count assistant messages asking questions + final confirmation message
        assistant_question_msgs = sum(1 for msg in st.session_state.filter_messages
                                      if msg["role"] == "assistant" and msg["content"] in st.session_state.filtering_questions)
        all_questions_asked = assistant_question_msgs == len(st.session_state.filtering_questions)
        # Also check if last message is the confirmation message
        last_message_is_confirmation = (st.session_state.filter_messages and
                                         st.session_state.filter_messages[-1]["role"] == "assistant" and
                                         "Click the button below" in st.session_state.filter_messages[-1]["content"])

        # Show submit button only after all questions are answered and confirmation is shown
        if all_questions_asked and last_message_is_confirmation:
            if st.button("Filter Vendors Now", key="submit_filter_answers"):
                 # Transition state to start filtering
                 st.session_state.current_task = "filtering_vendors"
                 st.session_state.error_message = None # Clear previous errors
                 st.rerun()

    # Stage 2: Filtering Done, Awaiting Phase 2 Trigger
    elif st.session_state.current_task == "displaying_filtered_results":
        # Keep existing UI for displaying filtered list & comparison setup
        st.subheader("Filtered Vendor List")
        if st.session_state.filtered_vendors is not None:
             if st.session_state.filtered_vendors:
                  st.success(f"Found {len(st.session_state.filtered_vendors)} matching vendors:")
                  # Display vendors in a more readable format
                  vendor_cols = st.columns(min(len(st.session_state.filtered_vendors), 4))
                  for i, vendor in enumerate(st.session_state.filtered_vendors):
                        with vendor_cols[i % len(vendor_cols)]:
                            st.markdown(f"- **{vendor}**")
             else:
                  st.warning("No vendors matched your filtering criteria.")

             # --- Comparison Criteria Setup ---
             st.subheader("Setup Vendor Comparison")
             st.write("Select criteria for comparing the filtered vendors:")
             selected_criteria = st.multiselect(
                  "Comparison Criteria:",
                  options=st.session_state.comparison_criteria_options,
                  default=st.session_state.comparison_criteria_options[:3], # Default to first 3
                  key="comparison_select"
             )
             st.session_state.selected_comparison_criteria = selected_criteria

             # --- Trigger Phase 2 Button ---
             if selected_criteria and st.session_state.filtered_vendors:
                  if st.button("Generate Comparison & Profiles", key="trigger_phase2"):
                        # Prepare arguments for Phase 2 run (using stored values)
                        stored_optional_inputs = st.session_state.optional_inputs_storage.get('optional_inputs', {})
                        stored_context_company = st.session_state.optional_inputs_storage.get('context_company_name', '')
                        stored_product_category = st.session_state.optional_inputs_storage.get('product_identifier', '')

                        # Set flags and rerun
                        st.session_state.phase2_in_progress = True # Use this flag to trigger execution block
                        st.session_state.current_task = "generating_phase2" # Set state
                        st.session_state.error_message = None
                        st.rerun()
             elif not st.session_state.filtered_vendors:
                 st.info("Cannot proceed to comparison as no vendors were filtered.")

        else:
             st.error("Filtering results not available. Please try again or check logs.")
             if st.session_state.error_message:
                  st.error(f"Filtering Error: {st.session_state.error_message}")

    # Stage 3: Phase 2 Done, Display Intermediate Results, Awaiting Deep Dive Trigger
    elif st.session_state.current_task == "awaiting_deepdive_selection":
        st.subheader("Phase 2 Results: Profiles & Comparison")
        
        # --- Display final generation status from Phase 2 ---
        if st.session_state.generation_status:
            display_generation_status(st.session_state.generation_status)
        
        if st.session_state.phase2_dashboard_data: 
            display_dashboard(st.session_state.phase2_dashboard_data) # Display Phase 2 Dashboard
        
        # Display Vendor Profiles, Comparison Matrix, and Relevance sections
        base_dir = Path(st.session_state.product_base_dir)
        markdown_dir = base_dir / "markdown"
        
        if markdown_dir.exists():
            # Display Vendor Profiles
            if st.session_state.filtered_vendors:
                with st.expander("Vendor Profiles", expanded=True):
                    for vendor in st.session_state.filtered_vendors:
                        # Create a sanitized filename based on vendor name
                        sanitized_vendor = re.sub(r'[^a-zA-Z0-9_]', '_', vendor)
                        profile_path = markdown_dir / f"profile_{sanitized_vendor}.md"
                        
                        if profile_path.exists():
                            try:
                                with open(profile_path, 'r', encoding='utf-8') as f:
                                    profile_content = f.read()
                                st.subheader(f"{vendor}")
                                st.markdown(profile_content)
                                st.divider()
                            except Exception as e:
                                st.warning(f"Could not read profile for {vendor}: {str(e)}")
                        else:
                            st.warning(f"No profile found for {vendor}")
            
            # Display Comparison Matrix
            comparison_path = markdown_dir / "comparison_matrix.md"
            if comparison_path.exists():
                with st.expander("Vendor Comparison Matrix", expanded=True):
                    try:
                        with open(comparison_path, 'r', encoding='utf-8') as f:
                            comparison_content = f.read()
                        st.markdown(comparison_content)
                    except Exception as e:
                        st.warning(f"Could not read comparison matrix: {str(e)}")
            
            # Display Relevance Analysis
            relevance_path = markdown_dir / "product_relevance.md"
            if relevance_path.exists():
                with st.expander("Relevance & Fit Analysis", expanded=True):
                    try:
                        with open(relevance_path, 'r', encoding='utf-8') as f:
                            relevance_content = f.read()
                        st.markdown(relevance_content)
                    except Exception as e:
                        st.warning(f"Could not read relevance analysis: {str(e)}")
        else:
            st.warning(f"Markdown directory not found at {markdown_dir}")
         
        # Deep dive vendor selection
        st.subheader("Vendor Deep Dive Selection (Optional)")
        st.write("Select vendors for detailed analysis:")
        vendors_for_deep_dive = st.multiselect(
            "Select vendors for detailed research:",
            options=st.session_state.filtered_vendors,
            key="deep_dive_selection_input"
        )
        st.session_state.deep_dive_selection = vendors_for_deep_dive

        # Add trigger button for deep dives
        if len(vendors_for_deep_dive) > 0:
            if st.button("Run Deep Dives on Selected Vendors", key="trigger_deep_dives"):
                # Use stored inputs from initial phase
                stored_optional_inputs = st.session_state.optional_inputs_storage.get('optional_inputs', {})
                stored_context_company = st.session_state.optional_inputs_storage.get('context_company_name', '')
                
                # Fill in any missing values from current sidebar (fallback)
                if not stored_context_company:
                    stored_context_company = context_company_name
                if not stored_optional_inputs:
                    stored_optional_inputs = optional_inputs
                
                # Set flags and trigger deep dives - use state machine
                st.session_state.deep_dive_in_progress = True # Keep for backward compatibility 
                st.session_state.current_task = "generating_deepdives" # Use state machine
                st.session_state.error_message = None
                st.rerun()

        # Add trigger for final PDF if NO deep dives are selected
        if not vendors_for_deep_dive:
            if st.button("Generate Final Report (No Deep Dives)", key="generate_final_pdf_no_dd"):
                st.session_state.current_task = "generating_final_pdf"
                st.session_state.error_message = None
                st.rerun()

    # Stage 4: Deep Dives Done, Awaiting Final PDF Trigger
    elif st.session_state.current_task == "awaiting_final_pdf":
        st.subheader("Deep Dive Results Summary")

        if st.session_state.deep_dive_results:
            # Loop through results: {vendor: (stats, pdf_path, dashboard_data, deep_dive_dir)}
            for vendor, result_tuple in st.session_state.deep_dive_results.items():
                 # Check if result_tuple is valid
                 if not isinstance(result_tuple, tuple) or len(result_tuple) < 4:
                     st.error(f"Incomplete deep dive result format for {vendor}. Skipping display.")
                     print(f"DEBUG: Invalid deep dive result for {vendor}: {result_tuple}")
                     continue

                 stats, pdf_path, dashboard_data, deep_dive_dir = result_tuple

                 # Display vendor-specific results
                 with st.expander(f"Deep Dive: {vendor}", expanded=True):
                     # Display vendor dashboard if available
                     if dashboard_data and isinstance(dashboard_data, dict) and 'error' not in dashboard_data:
                         st.subheader(f"Dashboard Summary: {vendor}")
                         display_dashboard(dashboard_data) # Use existing dashboard display function
                     elif dashboard_data and isinstance(dashboard_data, dict) and 'error' in dashboard_data:
                          st.warning(f"Could not generate dashboard for {vendor}. Error: {dashboard_data['error']}")
                          if 'raw_response' in dashboard_data:
                               with st.expander("Show Raw Dashboard Response"):
                                    st.code(dashboard_data['raw_response'], language=None)

                     # Display PDF download button if available
                     if pdf_path and Path(pdf_path).exists():
                         col_btn_dd, col_spacer_dd = st.columns([1, 3])
                         with col_btn_dd:
                             try:
                                 with open(pdf_path, "rb") as file:
                                     st.download_button(
                                         label=f"Download {vendor} PDF",
                                         data=file,
                                         file_name=Path(pdf_path).name,
                                         mime="application/pdf",
                                         key=f"download-dd-{vendor}-btn", # Unique key
                                         use_container_width=True
                                     )
                             except Exception as file_e:
                                 st.error(f"Error reading PDF file for {vendor}: {file_e}")

                         # Option to view PDF inline
                         if st.checkbox(f"View {vendor} PDF inline", key=f"view-dd-{vendor}-pdf"): # Unique key
                             display_pdf(Path(pdf_path))
                     elif pdf_path:
                          st.warning(f"Deep dive PDF path found for {vendor}, but file does not exist: {pdf_path}")
                     else:
                          st.info(f"No deep dive PDF generated or found for {vendor}.")

                     # Show basic stats
                     if stats and isinstance(stats.get('summary'), dict):
                         summary = stats.get('summary')
                         stats_col1, stats_col2 = st.columns(2)
                         with stats_col1:
                             st.metric("Successful Sections", summary.get("successful_sections", 0))
                             st.metric("Processing Time", summary.get("formatted_execution_time", "N/A"))
                         with stats_col2:
                             st.metric("Total Tokens Used", summary.get("total_tokens", 0))
                             st.metric("Status", "Complete" if not summary.get("was_interrupted", False) else "Interrupted")
                             if summary.get('error'):
                                 st.error(f"Error: {summary.get('error')}")
                     else:
                         st.warning(f"No valid stats summary available for {vendor}")
        else:
            st.warning("No deep dive results available or deep dives were skipped.")

        # Button to trigger final combined report
        final_generation_in_progress = (st.session_state.current_task == "generating_final_pdf")
        if st.button("Generate Final Combined PDF Report", key="trigger_final_pdf", disabled=final_generation_in_progress):
            # Set state and trigger final generation
            st.session_state.current_task = "generating_final_pdf"
            st.session_state.error_message = None
            st.rerun()

    # Stage 5: Final PDF Generated
    elif st.session_state.current_task == "complete": # NEW Check
         st.subheader("Final Combined Product Report")
         if st.session_state.dashboard_data: 
             display_dashboard(st.session_state.dashboard_data) # Display FINAL dashboard
             
         st.divider()
         if st.session_state.final_pdf_path and Path(st.session_state.final_pdf_path).exists():
             # Display final PDF download & preview
             pdf_path = Path(st.session_state.final_pdf_path)
             col_btn, col_spacer = st.columns([1, 3])
             with col_btn:
                 with open(pdf_path, "rb") as file:
                     st.download_button(
                         label="Download Final PDF", 
                         data=file, 
                         file_name=pdf_path.name, 
                         mime="application/pdf", 
                         key="download-final-pdf-button", 
                         use_container_width=True
                     )
             st.info(f"Final report saved to: {pdf_path.relative_to(Path.cwd()) if pdf_path.is_relative_to(Path.cwd()) else pdf_path}")
             with st.container():
                 st.markdown('<div class="report-container">', unsafe_allow_html=True)
                 display_pdf(pdf_path)
                 st.markdown('</div>', unsafe_allow_html=True)
         else:
             st.error("Final PDF generated but path is invalid or file not found.")

    # Handle initial state or errors before initial analysis
    elif st.session_state.error_message:
        st.error(f"Product Research Error: {st.session_state.error_message}")
    elif not st.session_state.generation_in_progress and not st.session_state.product_initial_run_complete:
        st.info("Configure product research options and click 'Start Initial Product Analysis'.")


st.divider()
st.caption("© 2024 Vendor & Product Research Agent")