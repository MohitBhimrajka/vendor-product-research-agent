import streamlit as st
from pathlib import Path
from ui.states import AppState
from ui.forms import vendor_form, product_form
from ui import helpers as ui
from services.vendor import generate as run_vendor
from services.product import (run_initial,
                               run_filter,
                               run_phase2,
                               run_deepdive,
                               run_final)

# ----------  configuration ----------
st.set_page_config(page_title="Vendor & Product Research",
    page_icon="🔍",
    layout="wide",
                   initial_sidebar_state="expanded")

ui.init_state()
ui.show_logo()
st.title("Vendor & Product Research AI Agent")

# ----------  wizard stepper ----------
step_labels = ["Home", "Running", "Results", "Complete"]
current_index = {
    AppState.HOME: 0,
    AppState.GENERATING_VENDOR: 1, AppState.GENERATING_PRODUCT_INIT: 1,
    AppState.AWAITING_FILTER: 1, AppState.FILTERING: 1,
    AppState.AWAITING_PHASE2: 1, AppState.GENERATING_PHASE2: 1,
    AppState.AWAITING_DEEPDIVE: 1, AppState.GENERATING_DEEPDIVE: 1,
    AppState.AWAITING_FINAL: 1, AppState.GENERATING_FINAL: 1,
    AppState.VENDOR_DONE: 2, AppState.COMPLETE: 3,
}[st.session_state.state or AppState.HOME]
ui.show_stepper(step_labels, current_index)

st.divider()

# ----------  HOME ----------
if st.session_state.state is None or st.session_state.state == AppState.HOME:
    # Reset all state when returning to home
    if st.session_state.state == AppState.HOME:
        ui.reset_state()
        
    mode = st.radio("Choose mode", ["Vendor research", "Product research"])
    company = st.text_input("Your company name *", key="ctx_company_input")
    
    # Store company name in session state
    if company:
        st.session_state.ctx_company = company
        
    st.markdown("---")

    if mode == "Vendor research":
        vendor, filters = vendor_form()
        st.session_state.vendor_filters = filters
        st.session_state.vendor_data = vendor
    else:
        category, filters = product_form()
        st.session_state.product_data = category
        st.session_state.product_filters = filters

# ----------  GENERATING VENDOR ----------
elif st.session_state.state == AppState.GENERATING_VENDOR:
    ui.status_bar()
    with st.status("Running vendor research …", expanded=True) as status:
        # We already have vendor_data, vendor_filters, and ctx_company in session_state
        # so we don't need to reset state here
        stats, pdf, dash = run_vendor(
            st.session_state.vendor_data,
            st.session_state.ctx_company,
            st.session_state.vendor_filters,
            st.session_state.gen_status,
        )
        # Store report stats for display
        st.session_state.report_summary = stats.get('summary', {}) if stats else {}
        st.session_state.pdf_path = pdf
        st.session_state.dashboard_data = dash
        st.session_state.state = AppState.VENDOR_DONE
        status.update(label="✅ finished", state="complete")
    st.rerun()

# ----------  VENDOR DONE ----------
elif st.session_state.state == AppState.VENDOR_DONE:
    # Extract the base directory from the PDF path
    pdf_path = Path(st.session_state.pdf_path)
    output_dir = pdf_path.parent.parent
    markdown_dir = output_dir / "markdown"
    
    # Display dashboard data
    ui.dashboard_table(st.session_state.dashboard_data)
    
    # Layout for report content and PDF download - side by side
    st.subheader("📄 Research Report")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Show report content as tabs
        ui.markdown_tabs(markdown_dir)
    
    with col2:
        # Add PDF download in the right column
        with st.container():
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border: 1px solid #dee2e6;">
                <h4 style="margin-top: 0;">Download Report</h4>
            """, unsafe_allow_html=True)
            
            # Create a download button
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📥 Download PDF",
                    data=f,
                    file_name=pdf_path.name,
                    mime="application/pdf",
                    use_container_width=True,
                )
            
            st.markdown(f"<small>Saved to: {pdf_path.name}</small>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Display report stats
            if st.session_state.report_summary:
                st.markdown("<br>", unsafe_allow_html=True)
                with st.container():
                    st.markdown("""
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border: 1px solid #dee2e6;">
                        <h4 style="margin-top: 0;">Report Statistics</h4>
                    """, unsafe_allow_html=True)
                    
                    summary = st.session_state.report_summary
                    st.metric("Sections", summary.get("successful_sections", 0))
                    st.metric("Processing Time", summary.get("formatted_execution_time", "N/A"))
                    st.metric("Total Tokens", summary.get("total_tokens", 0))
                    st.markdown("</div>", unsafe_allow_html=True)
    
    # Add start over button
    if st.button("Start over"):
        ui.reset_state()
        st.session_state.state = AppState.HOME
        st.rerun()

# ----------  PRODUCT wizard ----------
# (1) generating initial
elif st.session_state.state == AppState.GENERATING_PRODUCT_INIT:
    ui.status_bar()
    with st.status("Running initial analysis …", expanded=True) as s:
        # Keep product_data, product_filters, and ctx_company
        stats, data_dir, questions = run_initial(
            st.session_state.product_data,
            st.session_state.ctx_company,
            st.session_state.product_filters,
            st.session_state.gen_status,
        )
        # Store report stats for display
        st.session_state.report_summary = stats.get('summary', {}) if stats else {}
        st.session_state.product_data_dir = data_dir
        st.session_state.questions = questions
        st.session_state.answers = []
        st.session_state.state = AppState.AWAITING_FILTER
        s.update(label="✅ finished", state="complete")
    st.rerun()

# (2) filter Q&A
elif st.session_state.state == AppState.AWAITING_FILTER:
    # Extract the markdown directory and PDF path
    output_dir = Path(st.session_state.product_data_dir)
    markdown_dir = output_dir / "markdown"
    pdf_files = list((output_dir / "pdf").glob("*.pdf"))
    initial_pdf = pdf_files[-1] if pdf_files else None
    
    # Display initial analysis results in a cleaner format
    with st.container():
        st.subheader("📊 Initial Analysis Results")
        tab1, tab2 = st.tabs(["Analysis Overview", "Detailed Report"])
        
        with tab1:
            # Status summary in a clean card layout
            st.markdown("""
            <style>
            .status-card {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 15px;
                border: 1px solid #e9ecef;
            }
            .status-header {
                font-weight: bold;
                font-size: 1.1em;
                margin-bottom: 10px;
                color: #495057;
            }
            .status-metric {
                display: inline-block;
                padding: 5px 10px;
                margin-right: 8px;
                margin-bottom: 8px;
                background-color: #e9ecef;
                border-radius: 20px;
                font-size: 0.9em;
            }
            .status-success {
                background-color: #d4edda;
                color: #155724;
            }
            .status-error {
                background-color: #f8d7da;
                color: #721c24;
            }
            .status-pending {
                background-color: #fff3cd;
                color: #856404;
            }
            .section-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                grid-gap: 10px;
                margin-top: 10px;
            }
            .section-item {
                padding: 8px 12px;
                border-radius: 5px;
                background-color: #e9ecef;
                font-size: 0.9em;
            }
            .section-success {
                background-color: #d4edda;
                border-left: 3px solid #28a745;
            }
            </style>
            <div class="status-card">
                <div class="status-header">Phase 1: Initial Analysis & Filtering</div>
            """, unsafe_allow_html=True)
            
            # Count section statuses
            status_counts = {"success": 0, "error": 0, "pending": 0, "running": 0}
            for section, data in st.session_state.gen_status.items():
                status = data.get("status", "pending")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Display metrics
            total = sum(status_counts.values())
            completed = status_counts["success"] + status_counts["error"]
            progress_pct = int((completed / total) * 100) if total > 0 else 0
            
            st.markdown(f"""
                <div style="margin-bottom: 15px;">
                    <span class="status-metric">Total: {total}</span>
                    <span class="status-metric">Completed: {completed} ({progress_pct}%)</span>
                    <span class="status-metric status-success">Success: {status_counts["success"]}</span>
                    <span class="status-metric status-error">Error: {status_counts["error"]}</span>
                </div>
            """, unsafe_allow_html=True)
            
            # Display section grid with status
            st.markdown('<div class="section-grid">', unsafe_allow_html=True)
            for section, data in sorted(st.session_state.gen_status.items()):
                status = data.get("status", "pending")
                section_name = section.replace("product_", "").replace("vendor_", "").replace("_", " ").title()
                icon = "✅" if status == "success" else "❌" if status == "error" else "⏳"
                st.markdown(f"""
                    <div class="section-item section-{status}">
                        {icon} {section_name}
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Add PDF download button
            st.markdown('</div>', unsafe_allow_html=True)
            if initial_pdf and initial_pdf.exists():
                col1, col2 = st.columns([3, 1])
    with col2:
                    with open(initial_pdf, "rb") as f:
                        st.download_button(
                            label="📥 Download Initial Report",
                            data=f,
                            file_name=initial_pdf.name,
                            mime="application/pdf",
                            use_container_width=True
                        )
        
    with tab2:
            # Show full markdown tabs
            ui.markdown_tabs(markdown_dir)

    st.divider()

    # Q&A section with progress indicator and better styling
    st.subheader("🔍 Filtering Questions")
    
    if st.session_state.questions:
        # Progress bar with better styling
        q_idx = len(st.session_state.answers)
        total_q = len(st.session_state.questions)
        progress_pct = q_idx / total_q
        
        st.markdown(f"""
        <div style="margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="font-size: 0.9em; color: #6c757d;">Progress</span>
                <span style="font-size: 0.9em; color: #6c757d;">{q_idx}/{total_q} Questions</span>
            </div>
            <div style="height: 10px; background-color: #e9ecef; border-radius: 5px;">
                <div style="width: {progress_pct * 100}%; height: 100%; background-color: #007bff; border-radius: 5px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Question card with better styling
        if q_idx < total_q:
            st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #007bff; margin-bottom: 15px;">
                <h4 style="margin-top: 0;">Question {q_idx+1} of {total_q}</h4>
                <p style="color: #495057;">{st.session_state.questions[q_idx]}</p>
            </div>
            """, unsafe_allow_html=True)
            
            ans = st.text_input("Your answer", key=f"answer_{q_idx}")
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("Next", type="primary" if q_idx < total_q-1 else "secondary", use_container_width=True):
                    if ans:  # Only append if there's an answer
                        st.session_state.answers.append(ans)
                        st.rerun()
                    else:
                        st.warning("Please provide an answer before proceeding.")
        else:
            st.success("All questions answered! You can now filter vendors based on your criteria.")
            if st.button("Filter vendors", type="primary"):
                st.session_state.state = AppState.FILTERING
                st.rerun()
    else:
        st.warning("No filtering questions were generated. You can proceed directly to vendor selection.")
        if st.button("Continue to vendor selection", type="primary"):
            st.session_state.filtered_vendors = []
            st.session_state.state = AppState.AWAITING_PHASE2
            st.rerun()

# Filtering stage - runs the filter on user's answers
elif st.session_state.state == AppState.FILTERING:
    ui.status_bar()
    with st.status("Filtering vendors …", expanded=True) as s:
        st.session_state.filtered_vendors = run_filter(
            Path(st.session_state.product_data_dir),
            st.session_state.questions,
            st.session_state.answers,
            st.session_state.gen_status
        )
        st.session_state.state = AppState.AWAITING_PHASE2
        s.update(label="✅ finished", state="complete")
        st.rerun()

# (3) choose comparison & run phase-2
elif st.session_state.state == AppState.AWAITING_PHASE2:
    # Display filtered vendors if any
    if st.session_state.filtered_vendors:
        # Show status summary
        st.markdown("""
        <style>
        .vendor-card {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            height: 100%;
            border: 1px solid #e9ecef;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .vendor-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .vendor-name {
            font-weight: bold;
            font-size: 1.2em;
            margin-bottom: 10px;
            color: #495057;
        }
        .criteria-option {
            display: flex;
            align-items: center;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 5px;
            margin-bottom: 8px;
            border: 1px solid #e9ecef;
            cursor: pointer;
        }
        .criteria-option:hover {
            background-color: #e9ecef;
        }
        </style>
        <div style="background-color: #d4edda; padding: 10px 15px; border-radius: 5px; margin-bottom: 20px;">
            <h3 style="margin: 0; color: #155724;">✅ Vendor Filtering Complete</h3>
            <p style="margin: 5px 0 0 0; color: #155724;">
                Based on your answers, we've identified {len(st.session_state.filtered_vendors)} suitable vendors.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Vendor cards in a visually appealing grid
        st.subheader("Selected Vendors")
        
        # Create a grid of cards with equal height
        num_cols = min(3, len(st.session_state.filtered_vendors))
        cols = st.columns(num_cols)
        
        for i, vendor in enumerate(st.session_state.filtered_vendors):
            with cols[i % num_cols]:
                st.markdown(f"""
                <div class="vendor-card">
                    <div class="vendor-name">{vendor}</div>
                    <div style="font-size: 2em; margin: 10px 0;">{"🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "🏅"}</div>
                </div>
                <br>
                """, unsafe_allow_html=True)
        
        st.divider()
        
        # Comparison criteria selector with visual improvements
        st.subheader("Select Comparison Criteria")
        st.markdown("Choose criteria for comparing these vendors in the analysis:")
        
        # Default criteria options
        criteria_options = [
            ("Core features", "Essential product capabilities and functionalities", True),
            ("Tech stack", "Technology infrastructure and implementation details", True),
            ("Pricing", "Cost models, pricing tiers, and payment structures", True),
            ("Support", "Service levels, customer support, and assistance options", False),
            ("Certifications", "Industry standards, compliance, and certification details", False)
        ]
        
        # Create a more visual selection interface
        selected_criteria = []
        for option, description, default in criteria_options:
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"""
                <div style="padding: 5px 0;">
                    <div style="font-weight: bold;">{option}</div>
                    <div style="color: #6c757d; font-size: 0.9em;">{description}</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.checkbox("", value=default, key=f"criteria_{option}"):
                    selected_criteria.append(option)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Visually differentiate the CTA button
        if st.button("Generate Comparison Matrix & Profiles", type="primary", disabled=not selected_criteria, use_container_width=True):
            st.session_state.criteria = selected_criteria
            st.session_state.state = AppState.GENERATING_PHASE2
            st.rerun()
        else:
            st.warning("No vendors were filtered based on your criteria.")
            # Provide options for the user with better visual distinction
            st.subheader("Options")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; height: 100%;">
                    <h4 style="margin-top: 0;">Retry Filtering</h4>
                    <p>Return to the filtering questions and provide different answers.</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Return to questions", key="return_to_filter", use_container_width=True):
                    st.session_state.answers = []  # Reset answers
                    st.session_state.state = AppState.AWAITING_FILTER
                    st.rerun()
            
            with col2:
                st.markdown("""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; height: 100%;">
                    <h4 style="margin-top: 0;">Manual Selection</h4>
                    <p>Choose vendors manually from the complete list of identified options.</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Select manually", key="skip_to_manual", use_container_width=True):
                    st.session_state.state = AppState.AWAITING_PHASE2
                    # Retrieve all identified vendors from the product_vendor_identification.md file
                    try:
                        output_dir = Path(st.session_state.product_data_dir)
                        vendor_file = output_dir / "markdown" / "product_vendor_identification.md"
                        if vendor_file.exists():
                            import re
                            with open(vendor_file, 'r') as f:
                                content = f.read()
                            # Simple extraction of vendor names - improve this if needed
                            vendors = []
                            for line in content.split('\n'):
                                if line.strip().startswith('- ') or line.strip().startswith('* '):
                                    vendor = line.strip()[2:].strip()
                                    if vendor and not vendor.startswith('[') and not vendor.endswith('...]'):
                                        vendors.append(vendor)
                            if vendors:
                                st.session_state.filtered_vendors = vendors
                            else:
                                st.info("No vendor identification file found. Please enter vendors manually.")
                    except Exception as e:
                        st.error(f"Error retrieving vendors: {e}")
                    st.rerun()

# Phase 2 generation - profiles and comparison matrix
elif st.session_state.state == AppState.GENERATING_PHASE2:
    ui.status_bar()
    with st.status("Building profiles & matrix …", expanded=True) as s:
        phase2_stats, phase2_dash = run_phase2(
            Path(st.session_state.product_data_dir),
            st.session_state.product_data,
            st.session_state.filtered_vendors,
            st.session_state.criteria,
            st.session_state.gen_status,
        )
        # Update report summary with the latest data
        st.session_state.report_summary = phase2_stats.get('summary', {}) if phase2_stats else {}
        st.session_state.phase2_dash = phase2_dash
        st.session_state.state = AppState.AWAITING_DEEPDIVE
        s.update(label="✅ finished", state="complete")
        st.rerun()

# (4) deep-dive selection
elif st.session_state.state == AppState.AWAITING_DEEPDIVE:
    # Extract the markdown directory
    output_dir = Path(st.session_state.product_data_dir)
    markdown_dir = output_dir / "markdown"
    
    # Layout for dashboard and report content/PDF
    if st.session_state.phase2_dash:
        st.markdown("""
        <style>
        .dashboard-container {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            border: 1px solid #e9ecef;
        }
        .section-title {
            font-weight: bold;
            font-size: 1.3em;
            margin-bottom: 15px;
            color: #343a40;
            border-bottom: 1px solid #e9ecef;
            padding-bottom: 10px;
        }
        .vendor-select-card {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            border: 1px solid #e9ecef;
            transition: background-color 0.2s;
        }
        .vendor-select-card:hover {
            background-color: #e9ecef;
        }
        .vendor-select-card.selected {
            background-color: #cfe2ff;
            border-color: #9ec5fe;
        }
        </style>
        <div class="dashboard-container">
            <div class="section-title">📊 Research Summary Dashboard</div>
        """, unsafe_allow_html=True)
        ui.dashboard_table(st.session_state.phase2_dash)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Report content and PDF download side by side
    st.markdown('<div class="section-title">📑 Analysis & Comparison</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    
    with col1:
        ui.markdown_tabs(markdown_dir)
    
    with col2:
        # Add PDF download if any available
        pdf_files = list((output_dir / "pdf").glob("*.pdf"))
        if pdf_files:
            with st.container():
                st.markdown("""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border: 1px solid #dee2e6; margin-bottom: 15px;">
                    <h4 style="margin-top: 0;">Download Report</h4>
                """, unsafe_allow_html=True)
                
                # Create a download button for the most recent PDF
                pdf_path = pdf_files[-1]  # Most recent PDF
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📥 Download PDF",
                        data=f,
                        file_name=pdf_path.name,
                        mime="application/pdf",
                        use_container_width=True,
                    )
            
                st.markdown(f"<small>Saved to: {pdf_path.name}</small>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            
                # Display report stats
                if st.session_state.report_summary:
                    with st.container():
                        st.markdown("""
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border: 1px solid #dee2e6;">
                            <h4 style="margin-top: 0;">Report Statistics</h4>
                        """, unsafe_allow_html=True)
                        
                        summary = st.session_state.report_summary
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Sections", summary.get("successful_sections", 0))
                        with col2:
                            st.metric("Time", summary.get("formatted_execution_time", "N/A"))
                        st.metric("Total Tokens", summary.get("total_tokens", 0))
                        st.markdown("</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # Deep dive selection with improved visual design
    st.markdown('<div class="section-title">🔎 Optional: Vendor Deep Dive</div>', unsafe_allow_html=True)
    st.markdown("""
    <p style="margin-bottom: 15px;">
        Select vendors for an in-depth analysis with comprehensive research on their products, 
        reputation, and suitability for your needs.
    </p>
    """, unsafe_allow_html=True)
    
    # Visual vendor selection cards
    selected_vendors = []
    cols = st.columns(min(3, len(st.session_state.filtered_vendors)))
    
    for i, vendor in enumerate(st.session_state.filtered_vendors):
        with cols[i % len(cols)]:
            is_selected = st.checkbox(f"Select {vendor}", key=f"deep_dive_{vendor}")
            st.markdown(f"""
            <div class="vendor-select-card {'selected' if is_selected else ''}">
                <div style="font-weight: bold; font-size: 1.1em;">{vendor}</div>
                <div style="font-size: 0.9em; color: #6c757d; margin: 5px 0;">
                    {"Selected for deep dive" if is_selected else "Click to select"}
                </div>
            </div>
            """, unsafe_allow_html=True)
            if is_selected:
                selected_vendors.append(vendor)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if selected_vendors:
            if st.button("Run Deep-Dive Analysis", type="primary", use_container_width=True):
                st.session_state.deep_vendors = selected_vendors
                st.session_state.state = AppState.GENERATING_DEEPDIVE
            st.rerun()
    with col2:
        button_text = "Skip Deep-Dive" if not selected_vendors else "Proceed to Final Report"
        if st.button(button_text, type="secondary", use_container_width=True):
            st.session_state.deep_vendors = []
            st.session_state.state = AppState.GENERATING_FINAL
            st.rerun()

# Deep-dive generation
elif st.session_state.state == AppState.GENERATING_DEEPDIVE:
    ui.status_bar()
    with st.status("Running vendor deep dives …", expanded=True) as s:
        st.info(f"Performing deep analysis on {len(st.session_state.deep_vendors)} vendors. This may take some time...")
        
        deep_results = run_deepdive(
            Path(st.session_state.product_data_dir),
            st.session_state.deep_vendors,
            st.session_state.gen_status
        )
        st.session_state.deep_results = deep_results
        st.session_state.state = AppState.AWAITING_FINAL
        
        s.update(label="✅ Deep dives completed", state="complete")
        st.rerun()

# (5) display deep dive results and option to generate final report
elif st.session_state.state == AppState.AWAITING_FINAL:
    # Extract the markdown directory for the main product research
    output_dir = Path(st.session_state.product_data_dir)
    markdown_dir = output_dir / "markdown"
    
    # Visual styling
    st.markdown("""
    <style>
    .results-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #e9ecef;
    }
    .deep-dive-header {
        background-color: #cfe2ff;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 4px solid #0d6efd;
    }
    .summary-box {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        border: 1px solid #e9ecef;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display the main product research dashboard
    if st.session_state.phase2_dash:
        st.markdown("""
        <div class="results-container">
            <h3 style="margin-top: 0; margin-bottom: 15px;">📊 Research Summary Dashboard</h3>
        """, unsafe_allow_html=True)
        ui.dashboard_table(st.session_state.phase2_dash)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Check if we have deep dive results to display
    if st.session_state.deep_results and len(st.session_state.deep_results) > 0:
        st.markdown("""
        <div class="deep-dive-header">
            <h3 style="margin-top: 0;">🔎 Deep Dive Results</h3>
            <p style="margin-bottom: 0;">
                Detailed analysis of selected vendors with comprehensive insights.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create tabs for each vendor's deep dive results
        vendor_tabs = st.tabs(list(st.session_state.deep_results.keys()))
        
        for i, (vendor, results_tuple) in enumerate(st.session_state.deep_results.items()):
            with vendor_tabs[i]:
                if isinstance(results_tuple, tuple) and len(results_tuple) >= 3:
                    stats, pdf_path, dashboard_data = results_tuple[:3]
                    
                    # Deep dive base directory (4th item in the tuple if available)
                    deep_dir = results_tuple[3] if len(results_tuple) >= 4 else None
                    
                    # Layout for deep dive results
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Display dashboard for this vendor
                        if dashboard_data:
                            st.markdown("""
                            <div class="summary-box">
                                <h4 style="margin-top: 0;">Vendor Summary Dashboard</h4>
                            """, unsafe_allow_html=True)
                            ui.dashboard_table(dashboard_data)
                            st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Display deep dive content if available
                        if deep_dir and Path(deep_dir).exists():
                            vendor_markdown_dir = Path(deep_dir) / "markdown"
                            if vendor_markdown_dir.exists():
                                ui.markdown_tabs(vendor_markdown_dir)
                            else:
                                st.warning(f"No markdown content found for {vendor} deep dive.")
                    
                    with col2:
                        # PDF download for this vendor's deep dive
                        if pdf_path and Path(pdf_path).exists():
                            with st.container():
                                st.markdown("""
                                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border: 1px solid #dee2e6; margin-bottom: 15px;">
                                    <h4 style="margin-top: 0;">Download Report</h4>
                                """, unsafe_allow_html=True)
                                
                                with open(pdf_path, "rb") as f:
                                    st.download_button(
                                        label="📥 Download PDF",
                                        data=f,
                                        file_name=Path(pdf_path).name,
                                        mime="application/pdf",
                                        key=f"download_{vendor}",
                                        use_container_width=True,
                                    )
            
                                st.markdown(f"<small>Saved to: {Path(pdf_path).name}</small>", unsafe_allow_html=True)
                                st.markdown("</div>", unsafe_allow_html=True)
            
                                # Display vendor-specific stats
                                if stats and stats.get('summary'):
                                    with st.container():
                                        st.markdown("""
                                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border: 1px solid #dee2e6;">
                                            <h4 style="margin-top: 0;">Report Statistics</h4>
                                        """, unsafe_allow_html=True)
                                        
                                        summary = stats.get('summary', {})
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.metric("Sections", summary.get("successful_sections", 0))
                                        with col2:
                                            st.metric("Time", summary.get("formatted_execution_time", "N/A"))
                                        st.metric("Total Tokens", summary.get("total_tokens", 0))
                                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.error(f"Invalid results data for {vendor}")
    
    # Final report generation button with better call-to-action
    st.markdown("""
    <div style="background-color: #e9ecef; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: center; border: 1px solid #dee2e6;">
        <h2 style="margin-top: 0;">📊 Generate Final Report</h2>
        <p>
            Create a comprehensive final report that combines all analysis, comparisons, and deep dives
            into a single professional document.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Center the generate button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Generate Final Comprehensive Report", type="primary", use_container_width=True):
            st.session_state.state = AppState.GENERATING_FINAL
            st.rerun()

# Final report generation
elif st.session_state.state == AppState.GENERATING_FINAL:
    ui.status_bar()
    with st.status("Generating final comprehensive report …", expanded=True) as s:
        final_pdf, final_dash = run_final(
            Path(st.session_state.product_data_dir),
            st.session_state.deep_results if hasattr(st.session_state, 'deep_results') else {},
            st.session_state.gen_status
        )
        st.session_state.final_pdf = final_pdf
        st.session_state.final_dash = final_dash
        st.session_state.state = AppState.COMPLETE
        
        s.update(label="✅ Final report generated", state="complete")
        st.rerun()

# Complete stage - display final results
elif st.session_state.state == AppState.COMPLETE:
    st.success("Research completed! Here are your results.")
    
    # Get the appropriate PDF path and dashboard data
    pdf_path = None
    markdown_dir = None
    
    if hasattr(st.session_state, 'final_pdf') and st.session_state.final_pdf:
        pdf_path = Path(st.session_state.final_pdf)
        # Final PDF is typically in the same structure (base_dir/pdf/...)
        markdown_dir = pdf_path.parent.parent / "markdown"
    elif hasattr(st.session_state, 'pdf_path') and st.session_state.pdf_path:
        pdf_path = Path(st.session_state.pdf_path)
        markdown_dir = pdf_path.parent.parent / "markdown"
    
    # Get the appropriate dashboard data
    dashboard_data = None
    if hasattr(st.session_state, 'final_dash') and st.session_state.final_dash:
        dashboard_data = st.session_state.final_dash
    elif hasattr(st.session_state, 'dashboard_data') and st.session_state.dashboard_data:
        dashboard_data = st.session_state.dashboard_data
    elif hasattr(st.session_state, 'phase2_dash') and st.session_state.phase2_dash:
        dashboard_data = st.session_state.phase2_dash
    
    # Display dashboard
    if dashboard_data:
        ui.dashboard_table(dashboard_data)
    
    # Layout for report content and PDF download - side by side
    if pdf_path and pdf_path.exists() and markdown_dir and markdown_dir.exists():
        st.subheader("📄 Full Research Report")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Show report content as tabs
            ui.markdown_tabs(markdown_dir)
        
        with col2:
            # Add PDF download in the right column
            with st.container():
                st.markdown("""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border: 1px solid #dee2e6;">
                    <h4 style="margin-top: 0;">Download Report</h4>
                """, unsafe_allow_html=True)
                
                # Create a download button
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📥 Download PDF",
                        data=f,
                        file_name=pdf_path.name,
                        mime="application/pdf",
                        use_container_width=True,
                    )
                
                st.markdown(f"<small>Saved to: {pdf_path.name}</small>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Display report stats
                if st.session_state.report_summary:
                    st.markdown("<br>", unsafe_allow_html=True)
                    with st.container():
                        st.markdown("""
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border: 1px solid #dee2e6;">
                            <h4 style="margin-top: 0;">Report Statistics</h4>
                        """, unsafe_allow_html=True)
                        
                        summary = st.session_state.report_summary
                        st.metric("Sections", summary.get("successful_sections", 0))
                        st.metric("Processing Time", summary.get("formatted_execution_time", "N/A"))
                        st.metric("Total Tokens", summary.get("total_tokens", 0))
                        st.markdown("</div>", unsafe_allow_html=True)
    
    # Start again button
    if st.button("Start again"):
        ui.reset_state()
        st.session_state.state = AppState.HOME
        st.rerun()