from pathlib import Path
from report_orchestrator import (
    run_product_research_initial, 
    filter_vendors_based_on_answers,
    run_product_research_phase2,
    trigger_vendor_deep_dives,
    generate_final_product_report
)
from typing import List, Optional  # Add type annotations

def run_initial(product_category, ctx_company, filters, status_dict):
    return run_product_research_initial(
        product_category=product_category,
        context_company_name=ctx_company,
        optional_inputs=filters,
        status_dict=status_dict
    )

def run_filter(base_dir, questions, answers, status_dict=None) -> List[str]:
    """
    Wrapper for filtering vendors. Ensures a list is always returned.
    """
    # Ensure we always return a list, even if filtering fails or returns None
    filtered_list: Optional[List[str]] = filter_vendors_based_on_answers(
        base_dir=base_dir,
        questions=questions,
        answers=answers,
        status_dict=status_dict
    )
    
    # Added additional safeguard - ensure filtered_list is a proper list
    if filtered_list is None or not isinstance(filtered_list, list):
        print(f"WARNING: filter_vendors_based_on_answers returned a {type(filtered_list)} instead of a list. Defaulting to empty list.")
        return []
        
    return filtered_list

def run_phase2(base_dir, product_category, filtered_vendors, criteria, status_dict):
    # Read context_company_name from config file if needed
    import yaml
    config_path = base_dir / "misc" / "generation_config.yaml"
    ctx_company = "Unknown Company"  # Default
    optional_inputs_from_config = {}
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f_cfg:
                gen_config = yaml.safe_load(f_cfg)
                if gen_config:
                    ctx_company = gen_config.get('context_company_name', ctx_company)
                    optional_inputs_from_config = gen_config.get('optional_inputs', {})
        except Exception as e:
            print(f"Warning: Could not load context from config for phase 2: {e}")

    return run_product_research_phase2(
        base_dir=base_dir,
        product_category=product_category,
        context_company_name=ctx_company,  # Pass loaded context
        optional_inputs=optional_inputs_from_config,  # Pass loaded context
        filtered_vendors=filtered_vendors,
        comparison_criteria=criteria,
        status_dict=status_dict
    )

def run_deepdive(base_dir, vendors_to_research, status_dict=None):
    # Read context_company_name from config file
    import yaml
    config_path = base_dir / "misc" / "generation_config.yaml"
    ctx_company = "Unknown Company"  # Default
    optional_inputs_from_config = {}
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f_cfg:
                gen_config = yaml.safe_load(f_cfg)
                if gen_config:
                    ctx_company = gen_config.get('context_company_name', ctx_company)
                    optional_inputs_from_config = gen_config.get('optional_inputs', {})
        except Exception as e:
            print(f"Warning: Could not load context from config for deep dive: {e}")

    return trigger_vendor_deep_dives(
        base_dir=base_dir,
        vendors_to_research=vendors_to_research,
        context_company_name=ctx_company,  # Pass loaded context
        optional_inputs=optional_inputs_from_config,  # Pass loaded context
        status_dict=status_dict
    )

def run_final(base_dir, deep_results, status_dict=None):
    # Read context info from config file
    import yaml
    config_path = base_dir / "misc" / "generation_config.yaml"
    ctx_company = "Unknown Company"  # Default
    product_category = "Unknown Product"
    optional_inputs_from_config = {}
    filtered_vendors_from_config = []  # Initialize empty

    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f_cfg:
                gen_config = yaml.safe_load(f_cfg)
                if gen_config:
                    ctx_company = gen_config.get('context_company_name', ctx_company)
                    product_category = gen_config.get('identifier', product_category)
                    optional_inputs_from_config = gen_config.get('optional_inputs', {})

            # Try loading filtered vendors from the saved file
            filtered_vendors_path = base_dir / "misc" / "filtered_vendors.txt"
            if filtered_vendors_path.exists():
                with open(filtered_vendors_path, 'r', encoding='utf-8') as f_vend:
                    lines = f_vend.readlines()
                    in_list_section = False
                    for line in lines:
                        if "## Filtered Vendor List" in line:
                            in_list_section = True
                            continue
                        if in_list_section and line.strip().startswith('- '):
                            filtered_vendors_from_config.append(line.strip()[2:])

        except Exception as e:
            print(f"Warning: Could not load context/filtered vendors from config for final report: {e}")

    return generate_final_product_report(
        base_dir=base_dir,
        product_category=product_category,  # Pass loaded context
        context_company_name=ctx_company,  # Pass loaded context
        optional_inputs=optional_inputs_from_config,  # Pass loaded context
        filtered_vendors=filtered_vendors_from_config,  # Pass loaded context
        deep_dive_vendors=list(deep_results.keys()) if deep_results else [],
        status_dict=status_dict
    ) 