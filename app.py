import streamlit as st
import os
import base64
from pathlib import Path
import time # For simulating wait
import re # For sanitizing identifiers in filenames

# Import orchestrator functions
from report_orchestrator import (
    run_vendor_research,
    run_product_research_initial,
    filter_vendors_based_on_answers # New function import
)
from config import OUTPUT_DIR # Import output directory config

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
    logo_path = Path("templates/assets/supervity_logo.png")
    if logo_path.exists():
        with open(logo_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    st.warning("Logo file not found at templates/assets/supervity_logo.png")
    return None

# --- Custom CSS (Optional - Add styles as needed) ---
def apply_custom_css():
    st.markdown("""
    <style>
        .stApp { /* Background, etc. */ }
        .logo-image { max-height: 60px; margin-bottom: 20px; }
        .report-container { margin-top: 20px; border: 1px solid #eee; padding: 15px; border-radius: 5px; }
        iframe { width: 100%; height: 700px; border: none; }
        /* Add more specific styles */
    </style>
    """, unsafe_allow_html=True)

apply_custom_css()

# --- Helper Function to Display PDF ---
def display_pdf(pdf_path: Path):
    if pdf_path and pdf_path.exists():
        try:
            with open(pdf_path, "rb") as f:
                base64_pdf = base64.b64encode(f.read()).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error displaying PDF: {e}")
    else:
        st.warning("PDF file not found or not generated.")

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
if 'generation_in_progress' not in st.session_state:
    st.session_state.generation_in_progress = False
# Product mode state
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
        st.session_state.generation_in_progress = False # Reset flag
        st.session_state.filtering_in_progress = False # Reset flag
        st.session_state.product_identifier = ""
        st.session_state.product_initial_run_complete = False
        st.session_state.product_base_dir = None
        st.session_state.filtering_questions = None
        st.session_state.filter_messages = []
        st.session_state.filter_answers_submitted = False
        st.session_state.filtered_vendors = None
        st.session_state.current_question_index = 0

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
    allow_submit = not st.session_state.get('generation_in_progress', False) and not st.session_state.get('filtering_in_progress', False) # Disable during both

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
        can_edit_product_input = not st.session_state.product_initial_run_complete and not st.session_state.generation_in_progress
        identifier_value_input = st.text_input(identifier_label, key=identifier_key, placeholder="Required: Enter product category", disabled=not can_edit_product_input)
        st.markdown("**Optional Filters:**")
        optional_inputs["required_certs"] = st.text_input("Required Certifications (comma-separated):", key="product_certs_input", disabled=not can_edit_product_input)
        optional_inputs["region"] = st.text_input("Geographic Region:", key="product_region_input", disabled=not can_edit_product_input)

    # Start Button
    if not st.session_state.generation_in_progress and not st.session_state.product_initial_run_complete:
        if st.button(submit_button_label, key="start_button", use_container_width=True, disabled=not allow_submit):
            # --- Input Validation ---
            valid_input = True
            if not identifier_value_input: # Check the actual input field value
                st.error(f"{identifier_label.replace(':','')} is required.")
                valid_input = False
            if not context_company_name:
                st.error("Your Company Name (Context) is required.")
                valid_input = False

            if valid_input:
                # Store identifier and trigger generation
                if research_mode == "Product Research":
                    st.session_state.product_identifier = identifier_value_input # Store the product name
                st.session_state.generation_in_progress = True
                st.rerun()

# --- Generation Execution Block ---
if st.session_state.generation_in_progress:
    st.header("⚙️ Processing Request...")
    st.info(f"Running {st.session_state.current_mode} for: **{identifier_value_input or st.session_state.product_identifier}**...")
    st.session_state.error_message = None # Clear previous errors
    success = False
    try:
        token_stats, pdf_path_result, base_dir_result, questions_result = None, None, None, None # Init results

        with st.spinner(f"Running {st.session_state.current_mode}... This may take several minutes."):
            if st.session_state.current_mode == "Vendor Research":
                token_stats, pdf_path_result = run_vendor_research(
                    vendor_name=identifier_value_input, # Use the just entered value
                    context_company_name=context_company_name,
                    optional_inputs=optional_inputs
                )
                st.session_state.report_generated = True

            elif st.session_state.current_mode == "Product Research":
                # Check if it's the initial run
                if not st.session_state.product_initial_run_complete:
                    token_stats, base_dir_result, questions_result = run_product_research_initial(
                        product_category=st.session_state.product_identifier, # Use stored identifier
                        context_company_name=context_company_name,
                        optional_inputs=optional_inputs
                    )
                    st.session_state.product_initial_run_complete = True
                    st.session_state.product_base_dir = base_dir_result
                    st.session_state.filtering_questions = questions_result
                    # Initialize chat history with the first question if available
                    if questions_result:
                        st.session_state.filter_messages = [{"role": "assistant", "content": questions_result[0]}]
                        st.session_state.current_question_index = 0
                    else:
                         st.session_state.filter_messages = [{"role": "assistant", "content": "No specific filtering questions generated. You can proceed or refine criteria manually later."}]


        # --- Process Results ---
        if token_stats:
            st.session_state.report_summary = token_stats.get('summary', {})
            if pdf_path_result: st.session_state.pdf_path = pdf_path_result
            success = True
        else:
            st.session_state.error_message = f"{st.session_state.current_mode} analysis failed during execution. Check logs."

    except Exception as e:
         st.session_state.error_message = f"An error occurred during generation: {str(e)}"
         import traceback
         print(f"Generation Error: {traceback.format_exc()}")
         success = False
    finally:
         st.session_state.generation_in_progress = False
         if success and st.session_state.current_mode == "Product Research":
              st.info("Initial product analysis complete. Please answer the filtering questions below.")
         elif success:
              st.success(f"{st.session_state.current_mode} processing complete!")
         st.rerun() # Update UI immediately after generation finishes or errors

# --- Filtering Execution Block ---
if st.session_state.get('filtering_in_progress', False):
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
                  st.session_state.filtering_in_progress = False
                  st.session_state.filter_answers_submitted = False
                  st.rerun()
             elif not st.session_state.product_base_dir or not Path(st.session_state.product_base_dir).exists():
                  st.error("Cannot filter: Initial product analysis directory not found or invalid.")
                  st.session_state.filtering_in_progress = False
                  st.session_state.filter_answers_submitted = False
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
         st.session_state.filtering_in_progress = False # Ensure this is always reset
         if success:
             st.success("Vendor list filtered based on your answers!")
         st.rerun() # Update UI with filtering results

# --- Display Area ---
st.header("📊 Research Results & Next Steps")

if research_mode == "Vendor Research":
    # --- Vendor Mode Display ---
    if st.session_state.report_generated and st.session_state.report_summary:
        summary = st.session_state.report_summary
        st.subheader("Generation Summary")
        # Display summary stats (adapt KPIs for dashboard later)
        col1, col2, col3 = st.columns(3)
        col1.metric("Execution Time", summary.get('formatted_execution_time', 'N/A'))
        col2.metric("Successful Sections", summary.get('successful_sections', 'N/A'))
        col3.metric("Failed Sections", summary.get('failed_sections', 'N/A'))
        # Add more summary info or dashboard elements here in Phase 5

        st.divider()
        st.subheader("Generated Report")
        pdf_path = st.session_state.pdf_path
        if pdf_path and pdf_path.exists():
            col_btn, col_spacer = st.columns([1, 3])
            with col_btn:
                 with open(pdf_path, "rb") as file:
                     st.download_button(
                         label="Download PDF Report",
                         data=file,
                         file_name=pdf_path.name, # Use the actual generated filename
                         mime="application/pdf",
                         key="download-pdf-button",
                         use_container_width=True
                     )
            st.info(f"Report saved to output folder relative path: {pdf_path.relative_to(Path.cwd()) if pdf_path.is_relative_to(Path.cwd()) else pdf_path}")
            # Display PDF Preview
            with st.container(): # Use container for layout control
                 st.markdown('<div class="report-container">', unsafe_allow_html=True)
                 display_pdf(pdf_path)
                 st.markdown('</div>', unsafe_allow_html=True)
        elif summary.get('successful_sections', 0) > 0:
             st.warning("Report sections were generated, but the PDF file could not be created or found. Please check the application logs and the output directory.")
             output_dir_guess = Path(OUTPUT_DIR) / f"{summary.get('research_mode','unknown')}_{re.sub(r'[\\/*?:\"<>| ]', '_', summary.get('identifier','unknown'))}_*"
             st.info(f"Check for markdown files in directories matching: {output_dir_guess}")
        else:
             st.error("Report generation failed, no sections were successfully created.")
    elif st.session_state.error_message:
        st.error(f"Report Generation Failed: {st.session_state.error_message}")
        st.info("Please check the input parameters and ensure the backend service is running correctly. Consult logs for more details.")
    elif not st.session_state.generation_in_progress: # Only show initial message if not loading
        st.info("Configure vendor research options in the sidebar and click 'Generate Vendor Report'.")

elif research_mode == "Product Research":
    # Display initial analysis summary if complete
    if st.session_state.product_initial_run_complete and st.session_state.report_summary:
        st.subheader(f"Initial Analysis: {st.session_state.product_identifier}")
        summary = st.session_state.report_summary
        col1, col2, col3 = st.columns(3)
        col1.metric("Analysis Time", summary.get('formatted_execution_time', 'N/A'))
        col2.metric("Successful Sections", summary.get('successful_sections', 'N/A'))
        col3.metric("Failed Sections", summary.get('failed_sections', 'N/A'))
        if st.session_state.product_base_dir:
            st.caption(f"Analysis files saved in: {st.session_state.product_base_dir}")
        st.divider()

    # Display filtering chat only if questions exist AND answers not submitted yet AND not currently filtering
    if st.session_state.product_initial_run_complete and st.session_state.filtering_questions and \
       not st.session_state.filter_answers_submitted and not st.session_state.filtering_in_progress:

        st.subheader("Refine Your Vendor Search")
        st.markdown("Please answer the questions below to filter vendors.")

        # Display chat history
        for message in st.session_state.filter_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Check if all questions have been asked/answered implicitly by history length
        # We expect pairs: assistant asks, user answers.
        num_questions = len(st.session_state.filtering_questions)
        num_expected_messages = num_questions * 2 # Q1, A1, Q2, A2...
        all_questions_answered = len(st.session_state.filter_messages) >= num_expected_messages

        if not all_questions_answered:
            # Chat input for the *next* user answer
            if prompt := st.chat_input("Your answer...", key=f"filter_chat_input_{st.session_state.current_question_index}"):
                st.session_state.filter_messages.append({"role": "user", "content": prompt})
                st.session_state.current_question_index += 1
                # Ask next question if available
                if st.session_state.current_question_index < num_questions:
                    next_question = st.session_state.filtering_questions[st.session_state.current_question_index]
                    st.session_state.filter_messages.append({"role": "assistant", "content": next_question})
                st.rerun() # Update chat display

        else: # All questions have been asked and answered (based on message count)
            st.info("All filtering questions answered.")
            if st.button("Submit Answers & Filter Vendors", key="submit_answers_button"):
                st.session_state.filter_answers_submitted = True
                st.session_state.filtering_in_progress = True
                st.rerun() # Trigger the filtering block

    # Display filtered vendors if filtering is complete
    elif st.session_state.filter_answers_submitted: # Check if submission step is done
         st.subheader("Filtered Vendor List")
         if st.session_state.filtered_vendors is not None: # Check if filtering result exists
             if st.session_state.filtered_vendors:
                 st.markdown("Based on your answers, the following vendors were prioritized:")
                 # Use columns for better layout if many vendors
                 cols = st.columns(3)
                 for i, vendor in enumerate(st.session_state.filtered_vendors):
                     with cols[i % 3]:
                         st.markdown(f"- **{vendor}**")
                 st.info("Vendor profiling and comparison (Phase 4) will focus on this list.")
                 if st.button("Generate Vendor Profiles & Comparison (Phase 4)", key="generate_profiles_button"):
                     st.warning("Phase 4: Vendor profiling and comparison logic not yet implemented.")
                     # Trigger Phase 4 orchestrator function here
             else: # Filtering ran but returned empty list
                  st.warning("No vendors matched your filtering criteria based on the interpretation.")
                  st.info("Consider restarting the product research with different filters or proceeding with the initial list (functionality TBD).")
         elif st.session_state.error_message: # Check if filtering itself failed
              st.error(f"Vendor filtering failed: {st.session_state.error_message}")
         else: # Filtering attempted but result is None (shouldn't normally happen)
              st.error("Vendor filtering process did not complete successfully. Check logs.")


    # Handle initial state or errors before initial analysis
    elif st.session_state.error_message:
        st.error(f"Product Research Failed: {st.session_state.error_message}")
    elif not st.session_state.generation_in_progress and not st.session_state.product_initial_run_complete:
        st.info("Configure product research options and click 'Start Initial Product Analysis'.")

st.divider()
st.caption("© 2024 Vendor & Product Research Agent")