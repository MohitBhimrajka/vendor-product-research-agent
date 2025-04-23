"""
Configuration file for the Vendor & Product Research Agent.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- LLM Configuration ---
LLM_MODEL = os.getenv('LLM_MODEL', 'gemini-2.5-pro-preview-03-25')
LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.63'))

# --- PDF Generation Configuration ---
PDF_CONFIG = {
    'SOURCES': {
        'AUTO_CONVERT_PARAGRAPH_TO_LIST': True,
        'SOURCE_HEADING_PATTERNS': ['Sources', 'References', 'Bibliography'],
        'MAX_URL_DISPLAY_LENGTH': 60,
    },
    'STYLING': {
        'TABLE_CLASS': 'enhanced-table',
        'SOURCES_LIST_CLASS': 'sources-list',
        'LONG_URL_CLASS': 'long-url',
        'AVOID_PAGE_BREAK_ELEMENTS': ['table', 'figure', 'pre', 'blockquote'],
    }
}

# --- Section Definitions ---

# === Vendor Research Mode Sections ===
VENDOR_SECTION_ORDER = [
    ("vendor_basic", "Basic Vendor Information"),
    ("vendor_products_services", "Product & Service Details"),
    ("vendor_financial_stability", "Financial Stability Assessment"),
    ("vendor_operational_capabilities", "Operational Capabilities"),
    ("vendor_compliance_certs", "Compliance & Certifications"),
    ("vendor_management_strategy", "Management & Strategy"),
    ("vendor_competitive_position", "Competitive Positioning (as Vendor)"),
    ("vendor_digital_transformation", "Digital Capabilities & Security"),
    ("vendor_crisis_continuity", "Operational Resilience & Continuity"),
    ("vendor_risk_assessment", "Consolidated Risk Assessment"),
    ("vendor_suitability_summary", "Vendor Suitability Summary"),
]
VENDOR_PROMPT_FUNCTIONS = [
    ("vendor_basic", "get_vendor_basic_prompt"),
    ("vendor_products_services", "get_vendor_products_services_prompt"),
    ("vendor_financial_stability", "get_vendor_financial_stability_prompt"),
    ("vendor_operational_capabilities", "get_vendor_operational_capabilities_prompt"),
    ("vendor_compliance_certs", "get_vendor_compliance_certs_prompt"),
    ("vendor_management_strategy", "get_vendor_management_strategy_prompt"),
    ("vendor_competitive_position", "get_vendor_competitive_position_prompt"),
    ("vendor_digital_transformation", "get_vendor_digital_transformation_prompt"),
    ("vendor_crisis_continuity", "get_vendor_crisis_continuity_prompt"),
    ("vendor_risk_assessment", "get_vendor_risk_assessment_prompt"),
    ("vendor_suitability_summary", "get_vendor_suitability_summary_prompt"),
]

# === Product Research Mode Sections (Initial Analysis) ===
# Sections generated *before* asking filtering questions
PRODUCT_INITIAL_SECTION_ORDER = [
    ("product_definition", "Product Category Definition & Scope"),
    ("product_market_overview", "Market Overview & Trends"),
    ("product_key_features", "Key Features & Technologies"),
    ("product_compliance_landscape", "Compliance & Certification Landscape"),
    ("product_vendor_identification", "Preliminary Vendor Identification") # Lists potential vendors
    # Filtering questions are generated based on these, but not part of the initial markdown report.
]
PRODUCT_INITIAL_PROMPT_FUNCTIONS = [
    ("product_definition", "get_product_definition_prompt"),
    ("product_market_overview", "get_product_market_overview_prompt"),
    ("product_key_features", "get_product_key_features_prompt"),
    ("product_compliance_landscape", "get_product_compliance_landscape_prompt"),
    ("product_vendor_identification", "get_product_vendor_identification_prompt"),
]

# === Product Research Mode Sections (Full Report - Defined Later in Phase 4) ===
PRODUCT_FULL_SECTION_ORDER = [
    # Will include initial sections + vendor profiles, comparison, relevance etc.
]
PRODUCT_FULL_PROMPT_FUNCTIONS = [
    # Will include initial prompts + prompts for profiles, comparison etc.
]

# --- Output Configuration ---
OUTPUT_DIR = "output" # Base directory for generated reports