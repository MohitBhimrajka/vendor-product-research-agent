from report_orchestrator import run_vendor_research
from config import VENDOR_PROMPT_FUNCTIONS

def generate(vendor_name, ctx_company, filters, status_dict):
    return run_vendor_research(
        vendor_name=vendor_name,
        context_company_name=ctx_company,
        optional_inputs=filters,
        status_dict=status_dict
    ) 