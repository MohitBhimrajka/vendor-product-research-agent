import base64, os, re, time
from pathlib import Path
from typing import Dict, List

import streamlit as st


# ----------  generic ----------
def init_state():
    """Initialise all session keys exactly once."""
    defaults = dict(
        # Basic state
        state=None,
        gen_status={},           # {section: {'status': 'pending'|'running'|'success'|'error'}}
        report_summary=None,
        pdf_path=None,
        dashboard_data=None,
        
        # Vendor research variables
        vendor_data=None,
        vendor_filters={},
        
        # Product research variables
        product_data=None,
        product_filters={},
        product_data_dir=None,   # folder produced by product phase 1
        questions=[],
        answers=[],
        filtered_vendors=[],
        criteria=[],
        phase2_dash=None,
        deep_vendors=[],
        deep_results=None,
        final_pdf=None,
        
        # Context
        ctx_company=None,
    )
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def reset_state():
    """Reset session state while preserving essential variables for the current workflow."""
    # Keys to keep during reset
    keep = {
        "state",            # current wizard step
        "vendor_data",      # vendor name input
        "vendor_filters",   # vendor filters
        "product_data",     # product category input
        "product_filters",  # product filters
        "ctx_company",      # company context
    }
    
    # Store values of keys we want to keep
    preserved = {}
    for k in keep:
        if k in st.session_state:
            preserved[k] = st.session_state[k]
    
    # Clear all keys except those explicitly kept
    for k in list(st.session_state.keys()):
        if k not in keep:
            del st.session_state[k]
    
    # Restore preserved values
    for k, v in preserved.items():
        st.session_state[k] = v

    # Reinitialize gen_status to avoid None errors
    st.session_state.gen_status = {}


# ----------  visuals ----------
@st.cache_data
def _logo64() -> str | None:
    try:
        with open(os.path.join("static", "logo.png"), "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None


def show_logo():
    logo = _logo64()
    if logo:
        st.image(f"data:image/png;base64,{logo}", width=140)
    else:
        st.warning("Logo missing.")


def show_stepper(steps: List[str], current_idx: int):
    cols = st.columns(len(steps))
    for i, label in enumerate(steps):
        with cols[i]:
            icon = "✅" if i < current_idx else ("🔵" if i == current_idx else "⚪")
            st.markdown(f"{icon}<br/>{label}", unsafe_allow_html=True)


def download_pdf(path: Path):
    """Provide a download button for the PDF without preview."""
    if not path.exists():
        st.error(f"PDF file not found: {path}")
        return
    
    try:
        with open(path, "rb") as f:
            data = f.read()
        
        # Create a download button with modern styling
        st.download_button(
            label="📥 Download PDF Report",
            data=data,
            file_name=path.name,
            mime="application/pdf",
            use_container_width=True,
        )
        st.info(f"PDF Report saved to: {path}")
    except Exception as e:
        st.error(f"Error preparing PDF for download: {e}")


def markdown_tabs(markdown_dir: Path):
    """Display markdown files as tabs."""
    if not markdown_dir.exists():
        st.error(f"Markdown directory not found: {markdown_dir}")
        return
    
    # Find all markdown files
    markdown_files = sorted(list(markdown_dir.glob("*.md")))
    if not markdown_files:
        st.warning("No markdown files found to display.")
        return
    
    # Create a dictionary of section name to file path
    tab_files = {}
    for file_path in markdown_files:
        # Clean up the filename to make a nice tab name
        name = file_path.stem
        # Remove common prefixes for cleaner labels
        name = name.replace("vendor_", "").replace("product_", "")
        # Convert snake_case to Title Case
        name = " ".join(word.capitalize() for word in name.split("_"))
        tab_files[name] = file_path
    
    # Create tabs for each file
    tabs = st.tabs(list(tab_files.keys()))
    
    # Display content in each tab
    for i, (name, file_path) in enumerate(tab_files.items()):
        with tabs[i]:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                st.markdown(content)
            except Exception as e:
                st.error(f"Error reading markdown file {name}: {e}")


def status_bar():
    """Display a status bar for tracking section generation."""
    # Get current sections in progress and their status
    sections_status = st.session_state.get('gen_status', {})
    if not sections_status:
        st.info("Waiting to start processing...")
        return

    # Count by status
    status_counts = {
        "pending": 0,
        "running": 0,
        "success": 0,
        "error": 0,
        "skipped": 0,
        "interrupted": 0
    }
    
    for section, data in sections_status.items():
        status = data.get("status", "pending")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    total = sum(status_counts.values())
    completed = status_counts["success"] + status_counts["error"] + status_counts["skipped"] + status_counts["interrupted"]
    
    # Determine if we're in product research mode
    in_product_mode = (
        ("product_data" in st.session_state and st.session_state.product_data) or
        any(k.startswith('product_') for k in sections_status.keys())
    )
    
    # Add special handling for product research phases
    if in_product_mode:
        # Identify the current phase
        if any(k in sections_status for k in ["product_filter_questions", "vendor_filtering"]):
            st.subheader("Phase 1: Initial Analysis & Filtering")
        elif any(k.startswith("profile_") for k in sections_status):
            st.subheader("Phase 2: Vendor Profiles & Comparison")
        elif any(k in sections_status for k in ["comparison_matrix", "product_relevance"]):
            st.subheader("Phase 2: Comparison & Relevance Analysis") 
        else:
            st.subheader("Product Research Progress")
    else:
        st.subheader("Vendor Research Progress")
        
    # Show a progress bar reflecting overall completion
    progress_value = completed / total if total > 0 else 0
    st.progress(progress_value)
    
    # Display a summary of status counts
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
        <div><strong>Total sections:</strong> {total}</div>
        <div><strong>Completed:</strong> {completed} ({int(progress_value * 100)}%)</div>
        <div style="color: green;"><strong>Success:</strong> {status_counts["success"]}</div>
        <div style="color: red;"><strong>Error:</strong> {status_counts["error"]}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create a table of sections and their status with nice styling
    st.markdown("""
    <style>
    .section-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 10px;
    }
    .section-table th, .section-table td {
        padding: 8px;
        text-align: left;
        border-bottom: 1px solid #ddd;
    }
    .section-table tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    .status-running {
        color: #007bff;
        animation: pulse 1.5s infinite;
    }
    .status-success { color: #28a745; }
    .status-error { color: #dc3545; }
    .status-pending { color: #6c757d; }
    .status-skipped { color: #ffc107; }
    .status-interrupted { color: #fd7e14; }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    </style>
    <table class="section-table">
    <tr>
        <th>Section</th>
        <th>Status</th>
        <th>Time</th>
    </tr>
    """, unsafe_allow_html=True)
    
    # Sort sections by status (running first, then pending, then others alphabetically)
    def section_sort_key(item):
        section, data = item
        status = data.get("status", "pending")
        status_order = {"running": 0, "pending": 1, "success": 2, "error": 3, "skipped": 4, "interrupted": 5}
        return (status_order.get(status, 6), section)
    
    # Format section name for better display
    def format_section_name(section):
        # Remove common prefixes and convert underscores to spaces
        name = section.replace("vendor_", "").replace("product_", "")
        # Handle special cases for product research
        if name.startswith("profile_"):
            vendor_name = name.replace("profile_", "").replace("_", " ")
            return f"Profile: {vendor_name.title()}"
        # Convert snake_case to Title Case
        return " ".join(word.capitalize() for word in name.split("_"))
    
    for section, data in sorted(sections_status.items(), key=section_sort_key):
        status = data.get("status", "pending")
        execution_time = data.get("execution_time", 0)
        
        # Get appropriate status icon and class
        status_icons = {
            "running": "⏳",
            "pending": "⌛",
            "success": "✅",
            "error": "❌",
            "skipped": "⚠️",
            "interrupted": "🛑"
        }
        icon = status_icons.get(status, "❓")
        
        # Format time as appropriate
        if status == "running" or status == "pending":
            time_str = "-"
        elif execution_time > 0:
            if execution_time < 60:
                time_str = f"{execution_time:.1f}s"
            else:
                time_str = f"{execution_time/60:.1f}m"
        else:
            time_str = "-"
        
        st.markdown(f"""
        <tr>
            <td>{format_section_name(section)}</td>
            <td class="status-{status}">{icon} {status.capitalize()}</td>
            <td>{time_str}</td>
        </tr>
        """, unsafe_allow_html=True)
    
    st.markdown("</table>", unsafe_allow_html=True)

    # Add legend for product research phases if applicable
    if in_product_mode:
        st.markdown("""
        <div style="margin-top: 20px; padding: 10px; background-color: #f8f9fa; border-left: 4px solid #6c757d; font-size: 0.9em;">
        <strong>Product Research Phases:</strong>
        <ol style="margin: 5px 0 0 20px; padding: 0;">
            <li>Initial Analysis (Market, Features, Vendor Identification)</li>
            <li>Filtering Questions & Vendor Selection</li>
            <li>Vendor Profiles & Comparison Matrix</li>
            <li>Final Report Generation</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)


def dashboard_table(data: Dict):
    """Display dashboard data as a table using standard Streamlit components."""
    if not data:
        st.info("No dashboard data.")
        return
    
    # Create a cleaner display of the dashboard data
    st.subheader("📊 Research Summary Dashboard")
    
    # Use a card container for better styling
    with st.container():
        st.markdown("""
        <style>
        .dashboard-card {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        </style>
        <div class="dashboard-card">
        """, unsafe_allow_html=True)
        
        # Vendor dashboard
        if "financial_stability_assessment" in data:
            # Main metrics in a row with colored backgrounds - SMALLER SIZE
            col1, col2, col3 = st.columns(3)
            
            # Use custom styling for metrics - reduce padding and font size
            with col1:
                rating = data.get("financial_stability_assessment", "N/A")
                color = get_rating_color(rating)
                st.markdown(f"""
                <div style="text-align: center; padding: 6px; background-color: {color}; border-radius: 5px; margin-bottom: 8px;">
                    <h5 style="margin: 0; color: white; font-size: 14px;">Financial Stability</h5>
                    <h3 style="margin: 2px 0; color: white; font-size: 16px;">{rating}</h3>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                rating = data.get("operational_risk_assessment", "N/A")
                color = get_rating_color(rating)
                st.markdown(f"""
                <div style="text-align: center; padding: 6px; background-color: {color}; border-radius: 5px; margin-bottom: 8px;">
                    <h5 style="margin: 0; color: white; font-size: 14px;">Operational Risk</h5>
                    <h3 style="margin: 2px 0; color: white; font-size: 16px;">{rating}</h3>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                rating = data.get("compliance_risk_assessment", "N/A")
                color = get_rating_color(rating)
                st.markdown(f"""
                <div style="text-align: center; padding: 6px; background-color: {color}; border-radius: 5px; margin-bottom: 8px;">
                    <h5 style="margin: 0; color: white; font-size: 14px;">Compliance Risk</h5>
                    <h3 style="margin: 2px 0; color: white; font-size: 16px;">{rating}</h3>
                </div>
                """, unsafe_allow_html=True)
            
            # Overall suitability in a prominent position - SMALLER SIZE
            st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
            overall = data.get("overall_suitability", "N/A")
            overall_color = get_rating_color(overall)
            st.markdown(f"""
            <div style="text-align: center; padding: 8px; background-color: {overall_color}; border-radius: 5px; margin: 10px 0;">
                <h4 style="margin: 0; color: white; font-size: 16px;">Overall Suitability</h4>
                <h2 style="margin: 2px 0; color: white; font-size: 18px;">{overall}</h2>
            </div>
            """, unsafe_allow_html=True)
            
            # Key compliances
            st.markdown("### Key Compliance Status")
            compliance_checks = data.get("key_compliance_checks", {})
            if compliance_checks and isinstance(compliance_checks, dict):
                cols = st.columns(min(len(compliance_checks), 3))
                i = 0
                for cert, status in compliance_checks.items():
                    with cols[i % len(cols)]:
                        status_color = "#28a745" if status.lower() in ["yes", "compliant", "verified"] else "#dc3545"
                        st.markdown(f"""
                        <div style="padding: 8px; border-left: 4px solid {status_color}; background-color: #f8f9fa; margin-bottom: 8px;">
                            <div style="font-weight: bold;">{cert}</div>
                            <div style="color: {status_color};">{status}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    i += 1
            
            # Top risks
            st.markdown("### Top Identified Risks")
            top_risks = data.get("top_3_risks", [])
            if top_risks and isinstance(top_risks, list):
                for i, risk in enumerate(top_risks):
                    st.markdown(f"""
                    <div style="padding: 8px; border-left: 4px solid #dc3545; background-color: #f8f9fa; margin-bottom: 8px;">
                        <div style="font-weight: bold;">Risk {i+1}</div>
                        <div>{risk}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # Product research dashboard
        elif "identified_vendor_count" in data or "filtered_vendor_count" in data:
            # Product research layout - tailored for product analysis
            
            # Row 1: Key metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                total_vendors = data.get("identified_vendor_count", 0)
                filtered_vendors = data.get("filtered_vendor_count", 0)
                st.markdown(f"""
                <div style="text-align: center; padding: 15px; background-color: #4285f4; border-radius: 5px; margin-bottom: 15px;">
                    <h4 style="margin: 0; color: white; font-size: 16px;">Identified Vendors</h4>
                    <h2 style="margin: 5px 0; color: white;">{total_vendors}</h2>
                    <p style="margin: 0; color: white; font-size: 12px;">{filtered_vendors} filtered</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                growth_trend = data.get("market_growth_trend", "N/A")
                trend_color = "#4285f4"  # Default blue
                if "high" in growth_trend.lower() or "strong" in growth_trend.lower():
                    trend_color = "#0f9d58"  # Green for high growth
                elif "low" in growth_trend.lower() or "slow" in growth_trend.lower():
                    trend_color = "#f4b400"  # Yellow for low growth
                elif "decline" in growth_trend.lower() or "negative" in growth_trend.lower():
                    trend_color = "#db4437"  # Red for decline
                
                st.markdown(f"""
                <div style="text-align: center; padding: 15px; background-color: {trend_color}; border-radius: 5px; margin-bottom: 15px;">
                    <h4 style="margin: 0; color: white; font-size: 16px;">Market Growth</h4>
                    <h2 style="margin: 5px 0; color: white;">{growth_trend}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                # Use compliance standards count as the third metric
                compliance_standards = data.get("common_compliance_standards", [])
                standards_count = len(compliance_standards) if isinstance(compliance_standards, list) else 0
                
                st.markdown(f"""
                <div style="text-align: center; padding: 15px; background-color: #4285f4; border-radius: 5px; margin-bottom: 15px;">
                    <h4 style="margin: 0; color: white; font-size: 16px;">Key Compliance Standards</h4>
                    <h2 style="margin: 5px 0; color: white;">{standards_count}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            # Row 2: Top Vendors
            st.markdown("### Top Recommended Vendors")
            top_vendors = data.get("top_3_filtered_vendors", [])
            
            if top_vendors and isinstance(top_vendors, list):
                # Create a row of vendor cards
                vendor_cols = st.columns(min(len(top_vendors), 3))
                
                for i, vendor in enumerate(top_vendors):
                    with vendor_cols[i % len(vendor_cols)]:
                        medal = ["🥇", "🥈", "🥉"][i] if i < 3 else "🏅"
                        st.markdown(f"""
                        <div style="text-align: center; padding: 15px; background-color: #f8f9fa; border-radius: 5px; margin-bottom: 15px; border: 2px solid #4285f4;">
                            <h1 style="margin: 0; font-size: 24px;">{medal}</h1>
                            <h3 style="margin: 5px 0;">{vendor}</h3>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No top vendors data available.")
            
            # Row 3: Key Technology Trends
            st.markdown("### Key Technology Trends")
            tech_trends = data.get("key_tech_trends", [])
            
            if tech_trends and isinstance(tech_trends, list):
                # Create columns for trends
                trend_cols = st.columns(min(len(tech_trends), 3))
                for i, trend in enumerate(tech_trends):
                    with trend_cols[i % len(trend_cols)]:
                        st.markdown(f"""
                        <div style="padding: 10px; background-color: #f8f9fa; border-radius: 5px; margin-bottom: 10px; border-left: 4px solid #4285f4;">
                            <div style="font-weight: bold;">Trend {i+1}</div>
                            <div>{trend}</div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No technology trends data available.")
            
            # Row 4: Compliance Standards
            if compliance_standards and isinstance(compliance_standards, list):
                st.markdown("### Common Compliance Standards")
                st.markdown("<div style='display: flex; flex-wrap: wrap; gap: 10px;'>", unsafe_allow_html=True)
                
                for standard in compliance_standards:
                    st.markdown(f"""
                    <div style="background-color: #f0f4f8; padding: 8px 12px; border-radius: 20px; display: inline-block; margin: 5px;">
                        <span style="font-weight: bold; color: #4285f4;">✓</span> {standard}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)

        # If we have any data, close the container
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Add a link to view full report if applicable
        if st.session_state.get('pdf_path') or st.session_state.get('final_pdf'):
            pdf_path = st.session_state.get('final_pdf') or st.session_state.get('pdf_path')
            if pdf_path:
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📥 Download Complete PDF Report",
                        data=f,
                        file_name=Path(pdf_path).name,
                        mime="application/pdf",
                        use_container_width=True,
                    )


def get_rating_color(rating: str) -> str:
    """Get a color based on rating text."""
    rating = str(rating).lower()
    
    if rating in ["excellent", "strong", "high", "a+", "a", "a-", "5/5"]:
        return "#28a745"  # Green
    elif rating in ["good", "moderate", "medium", "b+", "b", "b-", "4/5"]:
        return "#17a2b8"  # Blue
    elif rating in ["fair", "average", "c+", "c", "c-", "3/5"]:
        return "#ffc107"  # Yellow
    elif rating in ["poor", "weak", "low", "d+", "d", "d-", "2/5", "1/5"]:
        return "#dc3545"  # Red
    else:
        return "#6c757d"  # Gray for unknown 