from pathlib import Path
from report_orchestrator import (
    run_product_research_initial, 
    filter_vendors_based_on_answers,
    run_product_research_phase2,
    trigger_vendor_deep_dives,
    generate_final_product_report
)

def run_initial(product_category, ctx_company, filters, status_dict):
    return run_product_research_initial(
        product_category=product_category,
        context_company_name=ctx_company,
        optional_inputs=filters,
        status_dict=status_dict
    )

def run_filter(base_dir, questions, answers, status_dict=None):
    return filter_vendors_based_on_answers(
        base_dir=base_dir,
        questions=questions,
        answers=answers,
        status_dict=status_dict
    )

def run_phase2(base_dir, product_category, filtered_vendors, criteria, status_dict):
    return run_product_research_phase2(
        base_dir=base_dir,
        product_category=product_category,
        context_company_name="",
        optional_inputs={},
        filtered_vendors=filtered_vendors,
        comparison_criteria=criteria,
        status_dict=status_dict
    )

def run_deepdive(base_dir, vendors_to_research, status_dict=None):
    return trigger_vendor_deep_dives(
        base_dir=base_dir,
        vendors_to_research=vendors_to_research,
        context_company_name="",
        optional_inputs={},
        status_dict=status_dict
    )

def run_final(base_dir, deep_results, status_dict=None):
    return generate_final_product_report(
        base_dir=base_dir,
        product_category="",
        context_company_name="",
        optional_inputs={},
        filtered_vendors=[],
        deep_dive_vendors=list(deep_results.keys()) if deep_results else [],
        status_dict=status_dict
    ) 