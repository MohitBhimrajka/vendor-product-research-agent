"""
Configuration file for the PDF generation project.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# LLM Configuration - Can be overridden with environment variables
LLM_MODEL = os.getenv('LLM_MODEL', 'gemini-2.5-pro-preview-03-25')
LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.63'))

# PDF Generation Configuration
PDF_CONFIG = {
    # Sources section processing options
    'SOURCES': {
        'AUTO_CONVERT_PARAGRAPH_TO_LIST': True,  # Try to convert paragraph-style sources to lists
        'SOURCE_HEADING_PATTERNS': ['Sources', 'References', 'Bibliography'],  # Headings to identify source sections
        'MAX_URL_DISPLAY_LENGTH': 60,  # Maximum characters to display for long URLs
    },
    
    # Visual styling options
    'STYLING': {
        'TABLE_CLASS': 'enhanced-table',
        'SOURCES_LIST_CLASS': 'sources-list',
        'LONG_URL_CLASS': 'long-url',
        'AVOID_PAGE_BREAK_ELEMENTS': ['table', 'figure', 'pre', 'blockquote'],
    }
}

# Section order and titles for the final report
SECTION_ORDER = [
    ("basic", "Basic Information"),
    ("vision", "Vision Analysis"),
    ("management_strategy", "Management Strategy"),
    ("management_message", "Management Message"),
    ("crisis", "Crisis Management"),
    ("digital_transformation", "Digital Transformation Analysis"),
    ("financial", "Financial Analysis"),
    ("competitive", "Competitive Landscape"),
    ("regulatory", "Regulatory Environment"),
    ("business_structure", "Business Structure"),
    ("strategy_research", "Strategy Research")
]

# List of prompt functions to run - mapping section IDs to prompt functions
PROMPT_FUNCTIONS = [
    ("basic", "get_basic_prompt"),
    ("financial", "get_financial_prompt"),
    ("competitive", "get_competitive_landscape_prompt"),
    ("management_strategy", "get_management_strategy_prompt"),
    ("regulatory", "get_regulatory_prompt"),
    ("crisis", "get_crisis_prompt"),
    ("digital_transformation", "get_digital_transformation_prompt"),
    ("business_structure", "get_business_structure_prompt"),
    ("vision", "get_vision_prompt"),
    ("management_message", "get_management_message_prompt"),
    ("strategy_research", "get_strategy_research_prompt")
] 