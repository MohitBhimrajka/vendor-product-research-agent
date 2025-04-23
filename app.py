import streamlit as st
import os
import base64
from pathlib import Path
# Import orchestrator functions when they are ready
# from report_orchestrator import run_vendor_research, run_product_research

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
    return None

# --- Custom CSS (Optional - can copy from original if desired) ---
def apply_custom_css():
    # Basic styles or copy/adapt from original app.py
    st.markdown("""
    <style>
        .stApp {
            /* Add any basic styling */
        }
        .logo-image {
            max-height: 60px; /* Adjust size */
            margin-bottom: 20px;
        }
        /* Add more styles as needed */
    </style>
    """, unsafe_allow_html=True)

apply_custom_css()

# --- Header ---
logo_b64 = get_logo_base64()
if logo_b64:
    st.image(f"data:image/png;base64,{logo_b64}", width=150) # Adjust width as needed

st.title("Vendor & Product Research AI Agent")
st.markdown("Your intelligent assistant for supplier and market analysis.")
st.divider()

# --- Main App Logic (Placeholder) ---

st.sidebar.header("Research Configuration")

# 1. Mode Selection
research_mode = st.sidebar.selectbox(
    "Select Research Mode:",
    ("Vendor Research", "Product Research"),
    key="research_mode_select"
)

# 2. Context Company (Always needed)
context_company_name = st.sidebar.text_input(
    "Your Company Name (Context):",
    placeholder="Enter your company name",
    key="context_company_input"
)

st.sidebar.divider()

# --- Mode-Specific Inputs & Execution ---

if research_mode == "Vendor Research":
    st.header("🔬 Deep Vendor Research")
    st.markdown("Analyze a specific vendor's capabilities, stability, and risks.")

    with st.form("vendor_research_form"):
        vendor_name = st.text_input("Vendor Name:", key="vendor_name_input")
        st.markdown("**Optional Filters:**")
        product_category_vendor = st.text_input("Product/Service Category Provided by Vendor:", key="vendor_prod_cat_input")
        required_certs_vendor = st.text_input("Required Certifications (comma-separated):", key="vendor_certs_input")
        region_vendor = st.text_input("Geographic Region of Supply:", key="vendor_region_input")

        submitted_vendor = st.form_submit_button("Generate Vendor Report")

        if submitted_vendor:
            if not vendor_name:
                st.error("Vendor Name is required.")
            elif not context_company_name:
                st.error("Your Company Name (Context) is required.")
            else:
                st.info(f"Starting vendor research for: **{vendor_name}**")
                st.warning("Vendor research generation logic not yet implemented in this phase.")
                # --- Call orchestrator in Phase 1 ---
                # optional_inputs = {
                #     "product_category": product_category_vendor or None,
                #     "required_certs": required_certs_vendor or None,
                #     "region": region_vendor or None,
                # }
                # with st.spinner("Generating vendor report... Please wait."):
                #     run_vendor_research(vendor_name, context_company_name, optional_inputs)
                #     st.success("Vendor report generation process finished (check console/output folder).") # Placeholder message
                #     # Add PDF display logic later

elif research_mode == "Product Research":
    st.header("📦 Product & Market Landscape Research")
    st.markdown("Analyze a product category, identify leading vendors, and compare them.")

    with st.form("product_research_form"):
        product_category = st.text_input("Product/Service Category:", key="product_cat_input")
        st.markdown("**Optional Filters:**")
        required_certs_product = st.text_input("Required Certifications (comma-separated):", key="product_certs_input")
        region_product = st.text_input("Geographic Region:", key="product_region_input")

        submitted_product = st.form_submit_button("Start Product Research")

        if submitted_product:
            if not product_category:
                st.error("Product/Service Category is required.")
            elif not context_company_name:
                st.error("Your Company Name (Context) is required.")
            else:
                st.info(f"Starting product research for: **{product_category}**")
                st.warning("Product research generation logic (including interaction) not yet implemented in this phase.")
                # --- Call orchestrator in Phase 2 ---
                # optional_inputs = {
                #     "required_certs": required_certs_product or None,
                #     "region": region_product or None,
                # }
                # with st.spinner("Starting product analysis..."):
                     # Trigger initial product analysis (Phase 2)
                     # Handle interactive filtering (Phase 3)
                     # Trigger profiles/comparison (Phase 4)
                #     st.success("Product research process placeholder finished.")
                #     # Add interactive elements and PDF display later


st.divider()
st.markdown("---")
st.caption("© 2024 Vendor & Product Research Agent")