"""
Configuration file for the Vendor & Product Research Agent.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- LLM Configuration ---
LLM_MODEL = os.getenv('LLM_MODEL', 'gemini-2.5-pro-preview-03-25')
LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.63')) # Using the requested temp

# --- PDF Generation Configuration (Copied from original, review later if needed) ---
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

# --- Section Definitions (Placeholders - To be populated in Phase 1 & 2) ---

# Vendor Research Mode Sections
VENDOR_SECTION_ORDER = [
    # Example: ("vendor_basic", "Basic Vendor Information"),
    # Add actual vendor sections here in Phase 1
]
VENDOR_PROMPT_FUNCTIONS = [
    # Example: ("vendor_basic", "get_vendor_basic_prompt"),
    # Add actual vendor prompt mappings here in Phase 1
]

# Product Research Mode Sections (Initial Analysis)
PRODUCT_INITIAL_SECTION_ORDER = [
    # Example: ("product_definition", "Product Category Definition & Scope"),
    # Add actual initial product sections here in Phase 2
]
PRODUCT_INITIAL_PROMPT_FUNCTIONS = [
    # Example: ("product_definition", "get_product_definition_prompt"),
    # Add actual initial product prompt mappings here in Phase 2
]

# Product Research Mode Sections (Full Report - including profiles, comparison)
PRODUCT_FULL_SECTION_ORDER = [
    # Example: ("product_definition", "Product Category Definition & Scope"),
    # ... other sections ...
    # Example: ("vendor_profiles", "Vendor Profile Summaries"),
    # Example: ("comparison_matrix", "Feature Comparison Matrix"),
    # Add actual full product report sections here in Phase 4
]
PRODUCT_FULL_PROMPT_FUNCTIONS = [
    # Example: ("product_definition", "get_product_definition_prompt"),
    # ... other mappings ...
    # Example: ("vendor_profiles", "get_vendor_light_profiles_prompt"), # Note: May represent multiple vendors
    # Example: ("comparison_matrix", "get_vendor_comparison_matrix_prompt"),
    # Add actual full product report mappings here in Phase 4
]

# --- Output Configuration ---
OUTPUT_DIR = "output" # Base directory for generated reports