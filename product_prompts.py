# product_prompts.py

import textwrap
from typing import Optional, Dict, Any, List
import json # Import json for parsing example

# --- Adapted Base Instruction Blocks for Product Research ---

# Focus: Objective market/product analysis, vendor identification, feature comparison.
# Audience: Internal teams (Sourcing, Product Mgmt, Strategy) evaluating options.
# Source Prioritization: Reputable industry reports, market analysis sites, vendor websites (for features/ID), standards bodies.

PRODUCT_ADDITIONAL_REFINED_INSTRUCTIONS = textwrap.dedent("""\
    **Additional Refined Instructions for Product Research (Zero Hallucination, Perfect Markdown, Objective Analysis):**

    *   **Mandatory Self-Check Before Final Output:**
        - Confirm:
            1. All requested product/market sections are included with correct headings.
            2. Factual statements about the **Product Category ('{identifier}')**, market trends, features, identified vendors, and compliance standards have inline citations [SSX] pointing to valid Vertex AI grounding URLs.
            3. Only permitted grounding URLs used.
            4. Markdown headings (`##`, `###`) and **perfect tables** follow the specified format (consistent columns, start/end pipes, accurate data vs. source). Use tables effectively for comparisons and vendor lists.
            5. A single "Sources" section at the end, properly formatted.
            6. Inline citations before punctuation where feasible.
            7. No fabricated data about market size, features, vendor capabilities, or compliance status. Silently omit unverified claims after exhaustive search. Use '-' in tables only if needed for structure after confirming data absence in source.
            8. **Objective Focus:** Primarily focus on objective analysis of the **Product Category ('{identifier}')** and the vendor landscape. Context for **'{context_company_name}'** should be applied *only* where explicitly requested (e.g., Relevance section).
            9. Verify recency of market reports, standards information, and vendor data used.
            10. Confirm key market figures, feature lists, vendor names, and compliance details against cited sources.
            11. Ensure lists (e.g., Key Features, Identified Vendors, Standards) are comprehensive based on source availability.
            12. Provide analytical depth where requested (explaining market drivers, technology trends, implications of standards).

    *   **Exactness of Table Columns:** (Same as Vendor mode, applies to feature matrices, vendor lists, etc.)
        - Every row MUST have the exact same number of columns, delimited by pipes (`|`). Start/End pipes mandatory. Separator line must match columns. Use '-' only for confirmed missing data for structure. Cite data within tables [SSX].

    *   **Quotes (Product Context):**
        - Quotes are less common here, but if quoting an analyst report or vendor marketing claim about a feature, attribute clearly with source and [SSX].

    *   **Exactness of Hyperlinks in Sources:**
        - Final "Sources" format: `* [Supervity Source X](Full_Vertex_AI_Grounding_URL) - Annotation [SSX].` Sequential numbering.
        - Annotation should state what specific product/market information is supported (e.g., supports market size estimate [SSX] and vendor Y identification [SSY]).

    *   **High-Priority Checklist (Product Research):**
        1. No fabrication about the market, product features, or vendors. Silently omit ungrounded data.
        2. Adhere strictly to Markdown formats (headings, lists, **perfect tables**).
        3. Use inline citations [SSX] matching final sources exactly for all market/product/vendor facts.
        4. Provide only one "Sources" section at the end.
        5. Use only provided grounding URLs.
        6. **Maintain Objective Focus** primarily on the product/market '{identifier}'.
        7. Complete internal self-check before concluding.
""")

PRODUCT_FINAL_SOURCE_LIST_INSTRUCTIONS = textwrap.dedent("""\
    **Final Source List Requirements (Product Research):**

    Conclude the *entire* research output with a clearly marked section titled "**Sources**".

    **1. Content - MANDATORY URL Type & Source Integrity:**
    *   **Exclusive Source Type:** List *only* the specific grounding redirect URLs provided by **Vertex AI Search** *for this query* regarding the **Product Category ('{identifier}')**, market trends, features, and identified vendors.
    *   **URL Pattern:** `https://vertexaisearch.cloud.google.com/grounding-api-redirect/...`. **Only this pattern.**
    *   **Strict Filtering:** No other URL types.
    *   **CRITICAL - No Hallucination:** Do **NOT invent or reuse URLs** if not provided *for this query*. If market data, a feature detail, or vendor info lacks a grounding URL after exhaustive search, silently omit it from the report body AND list no source.
    *   **Purpose:** Verify grounding data for the product/market request.

    **2. Formatting and Annotation (CRITICAL):**
    *   **Source Line Format:** New line, `* ` or `- `, Markdown link, annotation.
    *   **REQUIRED Format:**
        * [Supervity Source X](Full_Vertex_AI_Grounding_URL) - Annotation explaining product/market info supported (e.g., supports key feature list for '{identifier}' [SSX] and identifies Vendor Z [SSY]).
    *   **Sequential Labeling:** "Supervity Source 1", "Supervity Source 2", etc.
    *   **Annotation Requirement:** Immediate, " - ", brief, specific to info supported by [SSX], in English.

    **3. Quantity and Linkage:**
    *   List ***every distinct***, verifiable grounding URL provided *for this query* supporting content about the product/market/vendors via [SSX]. Do *not* include unused URLs.
    *   Accuracy over quantity.
    *   Every URL listed MUST correspond to facts/figures/statements referenced with [SSX].

    **4. Content Selection Based on Verifiable Grounding (Product Research):**
    *   **Prerequisite:** Include facts/features/vendors *only* if supported by a verifiable grounding URL from this query.
    *   **Omission:** Silently omit ungrounded details/vendors. Retain headings for structure if a whole subsection lacks data.

    **5. Final Check:**
    *   Verify exclusive use of valid, provided grounding URLs supporting cited facts.
    *   Verify format, linkage between citations and sources.
    *   "**Sources**" section appears only once, at the end.
    """)

PRODUCT_HANDLING_MISSING_INFO_INSTRUCTION = textwrap.dedent("""\
    *   **Handling Missing or Ungrounded Product/Market Information:**
        *   **Exhaustive Research First:** Conduct exhaustive research using reputable sources (see `PRODUCT_RESEARCH_DEPTH_INSTRUCTION`). Search diligently across *multiple relevant source types* (e.g., analyst reports snippets, market research summaries, vendor comparison articles, leading vendor websites for feature lists) for *each data point* before concluding unavailability. Check report/article dates.
        *   **Grounding Requirement:** Information is included only if:
            1. Located in a reliable source document relevant to the product/market.
            2. A corresponding, verifiable Vertex AI grounding URL is provided for this query.
        *   **Strict Silent Omission Policy:** If information cannot meet both conditions *after exhaustive research*, omit that specific fact, feature, vendor mention, or data point. Do **not** state 'Data not found'. If an entire subsection lacks grounded data, retain heading but omit content. Use `-` in tables only if needed for structure after confirming data absence in source.
        *   **No Inference/Fabrication:** Do not infer market sizes, guess features, or list vendors without grounding. Do not fabricate URLs.
    """)

PRODUCT_RESEARCH_DEPTH_INSTRUCTION = textwrap.dedent("""\
    *   **Product Research Depth & Source Prioritization:**
        *   **Exhaustive Search & Recency:** Conduct thorough research for the **Product Category ('{identifier}')**. Use the *latest available reputable sources*. Check publication dates. Cross-verify information where possible (e.g., feature lists across multiple vendors).
        *   **Multi-Source Strategy (Product Context):** Search across different source types:
            *   **Industry Analyst Reports (Snippets/Summaries):** Look for grounded snippets from Gartner, Forrester, IDC, etc., defining the market, key trends, major players, or core capabilities.
            *   **Market Research Firms (Summaries):** Check for grounded summaries of market size, growth forecasts, regional trends (e.g., Statista, Grand View Research summaries).
            *   **Reputable Tech/Business Publications:** Articles discussing the product category, key technologies, vendor comparisons, or user reviews (e.g., TechCrunch, WSJ, industry-specific journals) - *only if grounded*.
            *   **Leading Vendor Websites/Documentation:** Use official sites of *identified* leading vendors to confirm feature sets, target markets, technology used - *cite appropriately*.
            *   **Standards Bodies/Compliance Websites:** Official sources for relevant regulations or certifications (e.g., ISO.org, PCI Security Standards Council, government regulatory sites).
        *   **Source Quality:** Prioritize grounded analyst reports, market research summaries, and official standards bodies/vendor sites. Be critical of generic articles unless they cite specific data and are grounded.
        *   **Data Verification:** Cross-verify key features, common technologies, and major vendor names across multiple grounded sources if possible.
        *   **Geographic Scope:** Consider the specified `region` from optional inputs when analyzing market trends and vendor presence.
        *   **Compliance Focus:** Actively search for common compliance requirements or certifications mentioned in relation to the product category, especially those matching `required_certs` from optional inputs.
        *   **Confirmation of Unavailability (Internal):** Conclude information is unavailable only after diligent search across multiple relevant source types fails to yield verifiable, grounded data. Do not state this in the output.
    """)

PRODUCT_ANALYSIS_SYNTHESIS_INSTRUCTION = textwrap.dedent("""\
    *   **Analysis and Synthesis (Product Context):**
        *   Beyond listing facts, provide concise analysis (e.g., explain market drivers, discuss implications of technology trends, compare vendor approaches at a high level, assess the importance of certain compliance standards for this product).
        *   **Explain Trends:** Analyze *why* the market for '{identifier}' is growing/shrinking/shifting, based on sourced drivers [SSX]. Discuss the impact of key technologies identified [SSY].
        *   **Comparative Insights:** Highlight key differences in features or vendor focus areas observed during vendor identification [SSX]. Note common vs. differentiating features.
        *   **Implications:** Discuss the potential implications of market trends or compliance requirements for companies considering adopting '{identifier}' solutions.
        *   **Linking Information:** In summaries, connect market trends [SSX] with key features [SSY] and the types of vendors identified [SSZ].
    """)

PRODUCT_INLINE_CITATION_INSTRUCTION = textwrap.dedent("""\
    *   **Inline Citation Requirement (Product Research):**
        *   Every factual claim about the **Product Category ('{identifier}')**, market statistics, key features, identified vendors, or compliance standards **MUST** include an inline citation `[SSX]`.
        *   Place citation immediately after the supported statement, before punctuation.
        *   Cite appropriately if multiple facts from different sources are in one sentence.
        *   Reuse the same `[SSX]` if one source supports multiple points in a paragraph/table.
    """)

PRODUCT_SPECIFICITY_INSTRUCTION = textwrap.dedent("""\
    *   **Specificity and Granularity (Product Research):**
        *   For market data, include specific figures, currency, reporting periods/years, and the scope (e.g., "Global market size estimated at $X Billion in YYYY [SSX]").
        *   Define key technical terms or acronyms related to the product category.
        *   List specific feature names or technology standards where identified.
        *   Provide official names of identified vendors and relevant standards/certifications.
        *   Specify dates for trends or forecasts.
    """)

PRODUCT_AUDIENCE_CONTEXT_REMINDER = textwrap.dedent("""\
    *   **Audience Relevance (Product Research):** Keep the target audience (internal teams at **'{context_company_name}'** evaluating product/vendor options) in mind. Frame analysis to support decision-making regarding technology adoption, vendor selection, or market understanding. Focus on clarity, objectivity, and actionable insights. Apply context of **'{context_company_name}'** only in specifically designated sections later.
    """)

PRODUCT_BASE_FORMATTING_INSTRUCTIONS = textwrap.dedent("""\
    Output Format & Quality Requirements (Product Research):

    *   **Direct Start & No Conversational Text:** Begin directly with the first section heading (e.g., `## 1. Product Category Definition & Scope`). No intro/outro.

    *   **Strict Markdown Formatting Requirements:**
        *   Valid, consistent Markdown. Sections `##`, Subsections `###`. Lists `*` or `-`.
        *   **Tables (CRITICAL):** Use **perfect Markdown tables** for vendor lists, feature comparisons (later), compliance summaries. Ensure exact column counts, start/end pipes, matching separators. Cite data within tables [SSX]. Use `-` only for confirmed missing data needed for structure. Double-check tables.
        *   **Quotes:** Use `>` if quoting analyst reports or vendor claims.

    *   **Optimal Structure & Readability:**
        *   Use tables for lists of vendors, features, standards.
        *   Use bullet points for trends, key characteristics.
        *   Use paragraphs for definitions, market analysis, explanations.
        *   Maintain consistent formatting. Concise language.

    *   **Data Formatting Consistency (Market/Product Data):**
        *   Use standard English number formatting (commas).
        *   Specify currency for market values.
        *   Format dates consistently (YYYY-MM-DD or YYYY).
        *   Use consistent percentage formatting.

    *   **Section Completion Verification:**
        *   Include all requested initial product sections, in order, properly labeled.
        *   If verifiable data for an entire subsection is missing, retain heading, omit content.

    *   **Tone and Detail Level:**
        *   Professional, objective, analytical tone suited for market/technology assessment.
        *   Provide specific details (market figures, feature names, vendor names, standard names).

    *   **Completeness and Verification:**
        *   Address all requested points. Verify section presence and adherence to instructions. Perform final internal review.

    *   **Sources List:** Present at the very end, format: `* [Supervity Source X](URL) - Annotation [SSX].`

    *   **Inline Citation & Specificity:** Incorporate [SSX] for every factual claim and include specific dates/definitions/names.
    """)

PRODUCT_FINAL_REVIEW_INSTRUCTION = textwrap.dedent("""\
    *   **Internal Final Review (Initial Product Research):** Before concluding, review the generated response for **Product Category ('{identifier}')**:

        *   **Completeness Check:**
            * Every numbered initial product section requested is present with the correct heading.
            * Each section contains requested information points (definition, market trends, features, compliance overview, vendor list), or content silently omitted if ungrounded (headings retained).

        *   **Formatting Verification:**
            * Correct line breaks, section/subsection headings.
            * **Tables (Vendor List) are PERFECTLY formatted** (pipes, columns, separators, vendor names verified vs source).
            * Lists use consistent formatting.

        *   **Citation Integrity (Market/Product/Vendor ID Data):**
            * Every factual claim (market size, trend, feature, vendor name, standard) has an inline citation `[SSX]`.
            * Citations placed correctly. All citations correspond to entries that WILL BE in the final Sources list. Every source listed corresponds to at least one inline citation `[SSX]`.

        *   **Data Precision & Recency:**
            * Market values specify currency and period. Dates are consistent. Feature/Vendor/Standard names are specific.
            * Sources used are confirmed recent and grounded.

        *   **Content Quality & Objective Focus:**
            * Direct start, professional tone, adheres to silent omission. Logical flow.
            * Analysis is primarily focused objectively on the product/market **'{identifier}'**.

        Proceed to generate the final 'Sources' list only after confirming these conditions are met.
    """)


# --- Initial Product Research Prompt Generating Functions ---

def get_product_definition_prompt(identifier: str, language: str, context_company_name: str, **optional_inputs) -> str:
    """Prompt to define the product category."""
    formatted_additional_instructions = PRODUCT_ADDITIONAL_REFINED_INSTRUCTIONS.format(identifier=identifier, context_company_name=context_company_name)
    formatted_research_depth = PRODUCT_RESEARCH_DEPTH_INSTRUCTION.format(identifier=identifier, context_company_name=context_company_name)
    # ... include all other formatted base instructions ...
    formatted_handling_missing = PRODUCT_HANDLING_MISSING_INFO_INSTRUCTION.format(identifier=identifier)
    formatted_analysis_synthesis = PRODUCT_ANALYSIS_SYNTHESIS_INSTRUCTION.format(identifier=identifier, context_company_name=context_company_name)
    formatted_inline_citation = PRODUCT_INLINE_CITATION_INSTRUCTION.format(identifier=identifier)
    formatted_specificity = PRODUCT_SPECIFICITY_INSTRUCTION.format(identifier=identifier)
    formatted_audience_reminder = PRODUCT_AUDIENCE_CONTEXT_REMINDER.format(identifier=identifier, context_company_name=context_company_name)
    formatted_base_formatting = PRODUCT_BASE_FORMATTING_INSTRUCTIONS.format(identifier=identifier, context_company_name=context_company_name)
    formatted_final_review = PRODUCT_FINAL_REVIEW_INSTRUCTION.format(identifier=identifier, context_company_name=context_company_name)
    formatted_final_source_list = PRODUCT_FINAL_SOURCE_LIST_INSTRUCTIONS.format(identifier=identifier)

    prompt = f"""
**CRITICAL FOCUS:** Research *exclusively* the product category: **'{identifier}'**.

**Objective:** Define the Product Category '{identifier}', explaining its scope, primary purpose, target users, and key sub-categories if applicable.

**Target Audience:** {formatted_audience_reminder}

**Output Language:** English

**Research Requirements:** Use grounded industry definitions, analyst report snippets, reputable tech dictionaries. Ground every definition/scope statement with [SSX]. Use clear, concise language.
{formatted_handling_missing}
{formatted_research_depth}
{formatted_specificity}
{formatted_inline_citation}
{formatted_additional_instructions}

{formatted_base_formatting}

## 1. Product Category Definition & Scope: {identifier}

### 1.1 Definition
    *   Provide a clear, concise definition of what '{identifier}' is [SSX].
    *   Explain its primary purpose and the core problem(s) it solves [SSY].

### 1.2 Scope and Boundaries
    *   Describe the typical scope of solutions included within '{identifier}'. What functionalities are generally expected? [SSX]
    *   Mention related but distinct categories that '{identifier}' might be confused with, and clarify the boundaries [SSY].

### 1.3 Target Users/Industries
    *   Identify the typical users or departments within organizations that utilize '{identifier}' solutions [SSX].
    *   List key industries where '{identifier}' solutions are most commonly applied or have specific variations [SSY].

### 1.4 Key Sub-categories (if applicable)
    *   If '{identifier}' is a broad category, identify and briefly define its major sub-categories or types (e.g., for CRM: Sales CRM, Marketing CRM, Service CRM) [SSX].

{formatted_final_review}
{formatted_final_source_list}
"""
    return prompt

def get_product_market_overview_prompt(identifier: str, language: str, context_company_name: str, **optional_inputs) -> str:
    """Prompt for market overview and trends for the product category."""
    region_focus = optional_inputs.get('region')
    focus_instruction = f"Focus analysis on the specified region: **'{region_focus}'** if relevant data is found, but also provide global context." if region_focus else "Provide a global market overview unless regional data is prominent."

    # (Include all formatted base instructions here)
    formatted_additional_instructions = PRODUCT_ADDITIONAL_REFINED_INSTRUCTIONS.format(identifier=identifier, context_company_name=context_company_name)
    formatted_research_depth = PRODUCT_RESEARCH_DEPTH_INSTRUCTION.format(identifier=identifier, context_company_name=context_company_name)
    formatted_handling_missing = PRODUCT_HANDLING_MISSING_INFO_INSTRUCTION.format(identifier=identifier)
    formatted_analysis_synthesis = PRODUCT_ANALYSIS_SYNTHESIS_INSTRUCTION.format(identifier=identifier, context_company_name=context_company_name)
    formatted_inline_citation = PRODUCT_INLINE_CITATION_INSTRUCTION.format(identifier=identifier)
    formatted_specificity = PRODUCT_SPECIFICITY_INSTRUCTION.format(identifier=identifier)
    formatted_audience_reminder = PRODUCT_AUDIENCE_CONTEXT_REMINDER.format(identifier=identifier, context_company_name=context_company_name)
    formatted_base_formatting = PRODUCT_BASE_FORMATTING_INSTRUCTIONS.format(identifier=identifier, context_company_name=context_company_name)
    formatted_final_review = PRODUCT_FINAL_REVIEW_INSTRUCTION.format(identifier=identifier, context_company_name=context_company_name)
    formatted_final_source_list = PRODUCT_FINAL_SOURCE_LIST_INSTRUCTIONS.format(identifier=identifier)

    prompt = f"""
**CRITICAL FOCUS:** Research *exclusively* the market for product category: **'{identifier}'**.

**Objective:** Provide an overview of the market for '{identifier}', including size estimates, growth trends, key drivers, and significant recent developments. {focus_instruction}

**Target Audience:** {formatted_audience_reminder}

**Output Language:** English

**Research Requirements:** Use grounded market research summaries, analyst report snippets, reputable financial news discussing the sector. Ground every figure and trend statement with [SSX]. Include dates and scope (global/regional).
{formatted_handling_missing}
{formatted_research_depth}
{formatted_specificity}
{formatted_inline_citation}
{formatted_additional_instructions}

{formatted_base_formatting}

## 2. Market Overview & Trends: {identifier}

### 2.1 Market Size & Growth
    *   Provide the latest available estimates for the market size of '{identifier}' (specify currency, year, and scope - global or regional) [SSX].
    *   Report the projected market growth rate (e.g., CAGR %) for the next few years (specify timeframe and source) [SSY]. Note if growth is accelerating or decelerating.
    *   If regional data is found (especially for '{region_focus}'), present size/growth estimates for key regions [SSZ].

### 2.2 Key Market Drivers
    *   Identify and explain the major factors driving growth or adoption in the '{identifier}' market (e.g., digital transformation initiatives, regulatory changes, cost reduction pressures, specific technological advancements) [SSX].

### 2.3 Key Market Challenges/Restraints
    *   Identify and explain significant challenges or factors restraining market growth (e.g., high implementation costs, integration complexity, data security concerns, lack of skilled personnel) [SSX].

### 2.4 Recent Developments & Trends
    *   Summarize key recent trends shaping the '{identifier}' market (e.g., rise of AI-powered features, shift to cloud/SaaS models, increased focus on vertical solutions, vendor consolidation through M&A) [SSX].
    *   Mention any significant recent events (major vendor acquisitions, impactful regulatory changes, major technology breakthroughs) impacting the market [SSY].

{formatted_final_review}
{formatted_final_source_list}
"""
    return prompt


def get_product_key_features_prompt(identifier: str, language: str, context_company_name: str, **optional_inputs) -> str:
    """Prompt for key features and technologies in the product category."""
    # (Include all formatted base instructions here)
    formatted_additional_instructions = PRODUCT_ADDITIONAL_REFINED_INSTRUCTIONS.format(identifier=identifier, context_company_name=context_company_name)
    formatted_research_depth = PRODUCT_RESEARCH_DEPTH_INSTRUCTION.format(identifier=identifier, context_company_name=context_company_name)
    formatted_handling_missing = PRODUCT_HANDLING_MISSING_INFO_INSTRUCTION.format(identifier=identifier)
    formatted_analysis_synthesis = PRODUCT_ANALYSIS_SYNTHESIS_INSTRUCTION.format(identifier=identifier, context_company_name=context_company_name)
    formatted_inline_citation = PRODUCT_INLINE_CITATION_INSTRUCTION.format(identifier=identifier)
    formatted_specificity = PRODUCT_SPECIFICITY_INSTRUCTION.format(identifier=identifier)
    formatted_audience_reminder = PRODUCT_AUDIENCE_CONTEXT_REMINDER.format(identifier=identifier, context_company_name=context_company_name)
    formatted_base_formatting = PRODUCT_BASE_FORMATTING_INSTRUCTIONS.format(identifier=identifier, context_company_name=context_company_name)
    formatted_final_review = PRODUCT_FINAL_REVIEW_INSTRUCTION.format(identifier=identifier, context_company_name=context_company_name)
    formatted_final_source_list = PRODUCT_FINAL_SOURCE_LIST_INSTRUCTIONS.format(identifier=identifier)

    prompt = f"""
**CRITICAL FOCUS:** Research *exclusively* typical features and technologies for product category: **'{identifier}'**.

**Objective:** Identify and describe the common and differentiating features, functionalities, and underlying technologies typically found in '{identifier}' solutions.

**Target Audience:** {formatted_audience_reminder}

**Output Language:** English

**Research Requirements:** Use grounded sources like analyst reports comparing features, vendor documentation from market leaders, reputable tech reviews. Ground every feature/technology mention with [SSX].
{formatted_handling_missing}
{formatted_research_depth}
{formatted_specificity}
{formatted_inline_citation}
{formatted_additional_instructions}

{formatted_base_formatting}

## 3. Key Features & Technologies: {identifier}

### 3.1 Core Functionality / Standard Features
    *   List the essential features or core functionalities generally expected from any solution in the '{identifier}' category [SSX]. Briefly describe each.

### 3.2 Common Advanced / Differentiating Features
    *   List more advanced or optional features that often differentiate vendors in the '{identifier}' market (e.g., AI/ML capabilities, advanced analytics, customization options, specific integration modules) [SSX]. Describe what makes them advanced or differentiating.

### 3.3 Key Underlying Technologies
    *   Identify common underlying technologies or architectural approaches used in '{identifier}' solutions (e.g., Cloud-native vs. On-premise options, use of specific databases or programming languages if prominent, reliance on microservices, common API standards) [SSX].

### 3.4 Emerging Technologies & Trends
    *   Discuss any cutting-edge technologies or emerging trends being incorporated into '{identifier}' solutions (e.g., Generative AI integration, blockchain applications, edge computing aspects) [SSX]. Explain their potential impact.

{formatted_final_review}
{formatted_final_source_list}
"""
    return prompt

def get_product_compliance_landscape_prompt(identifier: str, language: str, context_company_name: str, **optional_inputs) -> str:
    """Prompt for common compliance standards in the product category."""
    required_certs_focus = optional_inputs.get('required_certs')
    focus_instruction = f"Pay special attention to standards relevant to: **'{required_certs_focus}'**." if required_certs_focus else "Identify generally relevant standards."

    # (Include all formatted base instructions here)
    formatted_additional_instructions = PRODUCT_ADDITIONAL_REFINED_INSTRUCTIONS.format(identifier=identifier, context_company_name=context_company_name)
    formatted_research_depth = PRODUCT_RESEARCH_DEPTH_INSTRUCTION.format(identifier=identifier, context_company_name=context_company_name)
    formatted_handling_missing = PRODUCT_HANDLING_MISSING_INFO_INSTRUCTION.format(identifier=identifier)
    formatted_analysis_synthesis = PRODUCT_ANALYSIS_SYNTHESIS_INSTRUCTION.format(identifier=identifier, context_company_name=context_company_name)
    formatted_inline_citation = PRODUCT_INLINE_CITATION_INSTRUCTION.format(identifier=identifier)
    formatted_specificity = PRODUCT_SPECIFICITY_INSTRUCTION.format(identifier=identifier)
    formatted_audience_reminder = PRODUCT_AUDIENCE_CONTEXT_REMINDER.format(identifier=identifier, context_company_name=context_company_name)
    formatted_base_formatting = PRODUCT_BASE_FORMATTING_INSTRUCTIONS.format(identifier=identifier, context_company_name=context_company_name)
    formatted_final_review = PRODUCT_FINAL_REVIEW_INSTRUCTION.format(identifier=identifier, context_company_name=context_company_name)
    formatted_final_source_list = PRODUCT_FINAL_SOURCE_LIST_INSTRUCTIONS.format(identifier=identifier)

    prompt = f"""
**CRITICAL FOCUS:** Research compliance standards relevant to product category: **'{identifier}'**.

**Objective:** Identify key industry standards, regulations, and certifications commonly expected or required for solutions within the '{identifier}' category. {focus_instruction}

**Target Audience:** {formatted_audience_reminder}

**Output Language:** English

**Research Requirements:** Use grounded sources like standards bodies websites (ISO, NIST), regulatory agency sites, analyst reports discussing compliance factors, leading vendor compliance pages. Ground every standard/regulation mention with [SSX].
{formatted_handling_missing}
{formatted_research_depth}
{formatted_specificity}
{formatted_inline_citation}
{formatted_additional_instructions}

{formatted_base_formatting}

## 4. Compliance & Certification Landscape: {identifier}

### 4.1 Common Industry Standards & Certifications
    *   List key certifications or standards frequently sought or attained by vendors in the '{identifier}' space (e.g., ISO 9001, ISO 27001, SOC 2 Type II, relevant industry-specific standards like HIPAA for healthcare tech, PCI DSS for payments) [SSX]. Briefly explain the relevance of each to this product category.
    *   Highlight any standards specified in `required_certs`: '{required_certs_focus or "None specified"}' and report findings related to their commonality or importance in this market [SSY].

### 4.2 Key Regulatory Considerations
    *   Identify major regulations that typically impact the development, deployment, or use of '{identifier}' solutions (e.g., Data Privacy: GDPR, CCPA; Accessibility: WCAG; Security: Specific government mandates; Environmental: RoHS, WEEE if hardware involved) [SSX]. Briefly explain the impact.

### 4.3 Regional Compliance Differences
    *   Note any significant regional variations in standards or regulations impacting '{identifier}' solutions, especially relevant for '{optional_inputs.get('region', 'Global')}' if specified [SSX].

### 4.4 Importance/Impact
    *   Analyze the typical importance of specific certifications or compliance adherence for vendor selection in the '{identifier}' market, based on sourced information [SSX]. (e.g., "SOC 2 is often a minimum requirement for enterprise SaaS vendors in this space [SSY]").

{formatted_final_review}
{formatted_final_source_list}
"""
    return prompt


def get_product_vendor_identification_prompt(identifier: str, language: str, context_company_name: str, **optional_inputs) -> str:
    """
    Generate a prompt for identifying key vendors/providers in a product category.
    
    Args:
        identifier: The product category name
        language: The language to use
        context_company_name: Company context name
        optional_inputs: Additional context variables
        
    Returns:
        Prompt for vendor identification
    """
    instructions = _format_product_instructions(identifier, context_company_name)
    
    # Add info from optional inputs if available
    region_context = ""
    if 'region' in optional_inputs and optional_inputs['region']:
        region_context = f"Focus primarily on vendors that serve the {optional_inputs['region']} region, but include major global providers if highly relevant."
    
    cert_context = ""
    if 'required_certs' in optional_inputs and optional_inputs['required_certs']:
        cert_context = f"Pay particular attention to vendors that are likely to meet these compliance requirements: {optional_inputs['required_certs']}."
    
    prompt = f"""
{instructions['base_formatting']}

## 5. Vendor Identification and Landscape

**Research Task:** Identify and analyze the major vendors/providers in the **{identifier}** market.

**Expected Output:**

1. Identify 10-15 significant vendors in the **{identifier}** space based on market share, reputation, and relevance.
2. Include a mix of established players and noteworthy emerging vendors when relevant.
3. For each identified vendor, provide a brief (1-2 sentences) description of their market positioning or key differentiator in the **{identifier}** space.
4. Comment on the general competitive landscape (e.g., highly consolidated vs. fragmented, regional variations, rapid change vs. stable).
5. Note any vendors with particularly strong positions in specific segments of the market.

{region_context}
{cert_context}

**IMPORTANT OUTPUT FORMAT:** After completing your full analysis, include a machine-readable list of ONLY the vendor names (without descriptions) following this exact format:

```
VENDOR_LIST_START
- Vendor Name 1
- Vendor Name 2
- Vendor Name 3
...
VENDOR_LIST_END
```

This structured format is CRITICAL for automated processing. The list must appear somewhere in your response, exactly as shown, with each vendor on a separate line preceded by "- " (dash and space).

{instructions['inline_citation']}

{instructions['research_depth']}

{instructions['handling_missing']}

{instructions['final_source_list']}
"""
    return prompt


# --- Prompt to Generate Filtering Questions (NEW) ---
def get_filtering_questions_prompt(product_category: str, initial_analysis_summary: str, context_company_name: str, optional_inputs: Dict) -> str:
    """Generates filtering questions based on initial product analysis."""
    # Note: This prompt doesn't need all the base instructions, it's a utility prompt.
    # It needs access to the summary of the initial analysis.

    # Construct a preamble summarizing the request context
    input_context = f"Initial analysis summary for '{product_category}':\n{initial_analysis_summary}\n\n"
    if optional_inputs.get('required_certs'):
        input_context += f"User indicated interest in certifications: {optional_inputs['required_certs']}.\n"
    if optional_inputs.get('region'):
        input_context += f"User indicated interest in region: {optional_inputs['region']}.\n"
    input_context += f"The requesting company is '{context_company_name}'."

    prompt = f"""
**Objective:** Based on the provided initial analysis summary for the product category '{product_category}', generate 3-5 insightful and distinct clarifying questions to ask the user ({context_company_name}). These questions should help filter the identified vendors or refine the research focus based on potential key differentiators or common decision criteria for this product category.

**Input Context:**
{input_context}

**Instructions:**
1.  **Analyze the Summary:** Understand the key features, market trends, compliance factors, and types of vendors mentioned for '{product_category}'.
2.  **Identify Key Decision Factors:** Determine the most likely factors a company like '{context_company_name}' would use to differentiate or select vendors in this space (e.g., company size focus, specific features, deployment model, technical architecture, key integrations, compliance needs, geographic requirements, pricing model preference, specific industry expertise).
3.  **Formulate Open-Ended Questions:** Create 3-5 clear, distinct, open-ended questions that prompt the user for their specific needs or priorities related to these decision factors. Avoid simple yes/no questions.
4.  **Natural Language:** Phrase the questions naturally, as if an assistant is asking for clarification.
5.  **Focus on Filtering:** The questions should aim to narrow down the vendor list or focus the subsequent deep-dive analysis.
6.  **Output Format:** Provide *only* the questions, each on a new line, preceded by a hyphen and a space (`- `). Do not include any introductory or concluding text, just the questions.

**Example Questions (for a different category like 'Cloud Storage'):**
- What is your expected primary use case for cloud storage (e.g., backup & archive, big data analytics, application data)?
- Are there specific compliance standards (like HIPAA or FedRAMP) that are mandatory for your needs?
- What is the approximate scale of data you anticipate storing initially and potentially growing to?
- Do you have preferences regarding cloud provider ecosystems (e.g., AWS, Azure, GCP) or a need for multi-cloud support?
- Are performance requirements (e.g., low latency access) a critical factor for your application?

**Generate 3-5 Questions for '{product_category}':**
"""
    return prompt


# --- New Prompt for Filtering Vendors ---
def get_filtered_vendor_list_prompt(
    product_category: str,
    initial_vendor_list: List[str],
    filtering_questions: List[str],
    user_answers: List[str] # List of user's answers in order
    ) -> str:
    """
    Generates a prompt to interpret user answers and filter the vendor list.
    """
    if len(filtering_questions) != len(user_answers):
        # Handle potential mismatch - maybe log warning and proceed cautiously
        print(f"Warning: Mismatch between questions ({len(filtering_questions)}) and answers ({len(user_answers)})")
        # Decide how to handle: error out, use partial, etc. Let's try using partial for now.
        min_len = min(len(filtering_questions), len(user_answers))
        filtering_questions = filtering_questions[:min_len]
        user_answers = user_answers[:min_len]


    # Format the Q&A pairs for the prompt
    qa_section = ""
    for i, question in enumerate(filtering_questions):
        qa_section += f"Question {i+1}: {question}\nUser Answer {i+1}: {user_answers[i]}\n\n"

    # Format the initial vendor list
    vendor_list_str = "\n".join([f"- {vendor}" for vendor in initial_vendor_list])

    prompt = f"""
**Objective:** Analyze the user's answers to the filtering questions regarding the product category '{product_category}' and refine the provided initial vendor list. Identify which vendors from the initial list best match the user's stated priorities and requirements.

**Context:**
*   **Product Category:** {product_category}
*   **Initial Vendor List:**
{vendor_list_str}

*   **User Filtering Q&A:**
{qa_section}

**Instructions:**
1.  **Interpret User Needs:** Carefully read the user's answers. Identify the key criteria, priorities, constraints, or preferences expressed (e.g., "must have strong AI features", "needs to support enterprise scale", "requires SOC 2 compliance", "prefers vendors with local support in Germany", "looking for cost-effective options").
2.  **Evaluate Initial Vendors (Conceptual):** Based *only* on general knowledge commonly associated with the vendors in the Initial List and the product category '{product_category}', assess how well each vendor might align with the user's interpreted needs. (You don't have deep vendor data here, rely on common associations - e.g., Salesforce is enterprise-focused, HubSpot often targets SMBs, certain vendors are known for specific features).
3.  **Filter the List:** Select the vendors from the **Initial Vendor List** that appear to be the *strongest potential matches* based on the user's answers. Prioritize vendors explicitly fitting key requirements.
4.  **Output Format:** Provide the filtered list of vendor names using the structured format below. If no vendors match, output only "NO_MATCHING_VENDORS".

FILTERED_VENDORS_START
[Vendor Name 1]
[Vendor Name 2]
[Vendor Name 3]
...
FILTERED_VENDORS_END

Important: Use the exact names from the initial vendor list. Do not add any explanation or other text outside the FILTERED_VENDORS_START and FILTERED_VENDORS_END markers.
"""
    return prompt


# --- Prompts for Phase 4 onwards (Vendor Profiles, Comparison, Relevance etc.) ---
# --- These will be defined in Phase 4 ---

# Helper to format base instructions for product prompts
def _format_product_instructions(identifier: str, context_company_name: str) -> Dict[str, str]:
    """Formats all base instruction blocks for product context."""
    # Reuse the base instruction variables defined earlier in this file
    return {
        "additional_refined": PRODUCT_ADDITIONAL_REFINED_INSTRUCTIONS.format(identifier=identifier, context_company_name=context_company_name),
        "research_depth": PRODUCT_RESEARCH_DEPTH_INSTRUCTION.format(identifier=identifier, context_company_name=context_company_name),
        "handling_missing": PRODUCT_HANDLING_MISSING_INFO_INSTRUCTION.format(identifier=identifier),
        "analysis_synthesis": PRODUCT_ANALYSIS_SYNTHESIS_INSTRUCTION.format(identifier=identifier, context_company_name=context_company_name),
        "inline_citation": PRODUCT_INLINE_CITATION_INSTRUCTION.format(identifier=identifier),
        "specificity": PRODUCT_SPECIFICITY_INSTRUCTION.format(identifier=identifier),
        "audience_reminder": PRODUCT_AUDIENCE_CONTEXT_REMINDER.format(identifier=identifier, context_company_name=context_company_name),
        "base_formatting": PRODUCT_BASE_FORMATTING_INSTRUCTIONS.format(identifier=identifier, context_company_name=context_company_name),
        "final_review": PRODUCT_FINAL_REVIEW_INSTRUCTION.format(identifier=identifier, context_company_name=context_company_name),
        "final_source_list": PRODUCT_FINAL_SOURCE_LIST_INSTRUCTIONS.format(identifier=identifier)
    }


# --- New Prompts for Phase 4 ---

def get_vendor_light_profile_prompt(
    vendor_name: str, # Specific vendor for this profile
    product_category: str,
    language: str,
    context_company_name: str,
    **optional_inputs
    ) -> str:
    """
    Generates a prompt for a CONCISE profile of a SINGLE vendor,
    focusing on aspects relevant to the product category.
    This reuses VENDOR base instructions for vendor-specific details.
    """
    # Use VENDOR instructions for vendor-specific grounding/formatting rules
    import vendor_prompts # Import needed for _format_all_instructions
    instructions = vendor_prompts._format_all_instructions(vendor_name, context_company_name)
    required_certs = optional_inputs.get('required_certs')
    certs_focus = f"Highlight status for certifications like '{required_certs}' if found." if required_certs else ""

    prompt = f"""
**CRITICAL FOCUS:** Generate a CONCISE profile for the specific vendor: **'{vendor_name}'**, focusing on their relevance to the product category **'{product_category}'**.

**Objective:** Provide a brief summary (2-3 paragraphs MAX, plus key bullet points/table) covering the vendor's core offering in '{product_category}', key strengths/weaknesses as a supplier for this category, notable compliance points, and basic company info. AVOID deep financial/operational analysis here - focus on relevance to the product.

**Target Audience:** {instructions['audience_reminder']} (Quick vendor snapshot for comparison)

**Output Language:** English

**Research Requirements:** Use vendor's official website (product pages, about us, compliance), grounded summaries. Ground claims with [SSX]. Be concise.
{instructions['handling_missing']}
{instructions['research_depth']} # Focus on product pages, compliance summaries
{instructions['specificity']} # Official vendor/product names
{instructions['inline_citation']}
{instructions['additional_refined']} # For vendor-specific details

{instructions['base_formatting']} # For structure

### Vendor Profile: {vendor_name} (Relevance to: {product_category})

*   **Core Offering in '{product_category}':** Briefly describe their main product/service in this specific category. What is their flagship offering called? [SSX]
*   **Key Strengths (for this category):** List 2-3 key strengths *as a supplier for {product_category}* (e.g., specific relevant feature, strong industry focus, key technology). Use bullet points [SSY].
*   **Potential Weaknesses/Gaps (for this category):** List 1-2 potential weaknesses *relevant to {product_category}* (e.g., missing a key feature common in the market, less experience in {context_company_name}'s industry compared to others) based on available info [SSZ].
*   **Compliance Highlights:**
    *   ISO 9001 Status: [Certified/Not Mentioned] [SSX]
    *   ISO 27001/SOC 2 Status: [Certified/Report Available/Not Mentioned] [SSY]
    *   {required_certs or 'Other Key Cert'}: [Status if found] [SSZ] {certs_focus}
*   **Basic Info:**
    *   Approx. Employee Size/Revenue Range (if easily found): [e.g., 500-1000 employees, ~$100M Revenue] [SSW]
    *   Headquarters Location: [City, Country] [SSV]
    *   Ownership Type: [Public/Private/Subsidiary] [SSU]

*   **Brief Summary Paragraph:** A concise 2-3 sentence overall summary of this vendor's apparent positioning and key characteristics for the '{product_category}' market based on the above points.

{instructions['final_review']}
{instructions['final_source_list']}
"""
    return prompt


def get_vendor_comparison_matrix_prompt(
    product_category: str,
    filtered_vendors: List[str],
    comparison_criteria: List[str], # Criteria selected by user/defined
    language: str,
    context_company_name: str,
    **optional_inputs
    ) -> str:
    """
    Generates a prompt to create a comparison matrix for the filtered vendors.
    """
    # Use PRODUCT instructions for market/feature context
    instructions = _format_product_instructions(product_category, context_company_name)
    vendor_list_str = "\n".join([f"- {v}" for v in filtered_vendors])
    criteria_str = "\n".join([f"- {c}" for c in comparison_criteria])

    prompt = f"""
**CRITICAL FOCUS:** Compare the specified vendors for the product category **'{product_category}'** based on the given criteria.

**Objective:** Create a **perfectly formatted Markdown table** comparing the vendors listed below across the specified criteria. Base the comparison *only* on publicly available, verifiable information obtained from grounded sources for each vendor. Use concise descriptions or ratings (e.g., Yes/No, High/Med/Low, specific feature names) in the table cells.

**Vendors to Compare:**
{vendor_list_str}

**Criteria for Comparison:**
{criteria_str}

**Target Audience:** {instructions['audience_reminder']} (Needs clear side-by-side comparison)

**Output Language:** English

**Research Requirements:** For each vendor and criterion, perform targeted searches using official vendor websites, product documentation, compliance pages, and grounded summaries. Ground each data point within the table using [SSX]. If information for a specific cell cannot be found after exhaustive search, use '-'. Be objective.
{instructions['handling_missing']}
{instructions['research_depth']} # Targeted search per vendor/criterion
{instructions['specificity']} # Use consistent terms for comparison
{instructions['inline_citation']} # Essential for table cells
{instructions['additional_refined']} # Ensure data accuracy per vendor

{instructions['base_formatting']} # CRITICAL for table format

## Vendor Comparison Matrix: {product_category}
"""
    # Dynamically build the header row
    header_vendors = " | ".join(filtered_vendors) if filtered_vendors else "Vendor A | Vendor B | Vendor C" # Placeholder if no vendors
    table_header = f"| Feature/Criterion | {header_vendors} | Source(s) Summary |\n"
    table_separator = f"|---------------------|{'|'.join(['-' * len(v) for v in filtered_vendors]) if filtered_vendors else '----------|----------|----------'}|-------------------|\n" # Adjust separator length
    
    # Add rows for each criterion dynamically
    table_body = ""
    for criterion in comparison_criteria:
        # Placeholder cells - LLM needs to fill these with grounded data [SSX]
        cells = " | ".join(['[Fill Data/Status] [SSX]' for _ in filtered_vendors]) if filtered_vendors else " - | - | - "
        table_body += f"| {criterion.ljust(25)} | {cells} | [List main sources, e.g., SS1, SS5, SS9] |\n" # Adjust padding

    prompt += table_header + table_separator + table_body + "\n" # Add final newline for spacing
    prompt += f"""
*Note: Use concise terms in cells (e.g., 'Yes', 'No', 'Partial', 'High', 'Low', specific version/feature name). Cite source(s) for each vendor's data point within or immediately after the cell content.*

{instructions['final_review']}
{instructions['final_source_list']}
"""
    return prompt


def get_product_relevance_prompt(
    product_category: str,
    market_summary: str, # Summary of market/features/compliance from initial run
    filtered_vendors: List[str],
    comparison_summary: str, # Summary of comparison results (or the matrix itself)
    language: str,
    context_company_name: str,
    **optional_inputs
    ) -> str:
    """
    Generates prompt to analyze relevance for the context company.
    """
    # Use PRODUCT instructions, but with context company focus
    instructions = _format_product_instructions(product_category, context_company_name)

    prompt = f"""
**CRITICAL FOCUS:** Analyze the relevance and potential fit of the **'{product_category}'** market and the leading/filtered vendors for the specific needs of **'{context_company_name}'**.

**Objective:** Based on the provided market analysis, feature landscape, compliance overview, and vendor comparison for '{product_category}', evaluate how well this product category and the top vendors align with the likely needs, priorities, and context of '{context_company_name}'.

**Provided Context:**
*   **Product Category:** {product_category}
*   **Requesting Company:** {context_company_name}
*   **Market/Feature/Compliance Summary:** {market_summary}
*   **Filtered Vendors:** {', '.join(filtered_vendors) if filtered_vendors else 'None specified/filtered'}
*   **Comparison Summary/Matrix:** {comparison_summary}
*   **Optional User Input:** Region: {optional_inputs.get('region', 'N/A')}, Required Certs: {optional_inputs.get('required_certs', 'N/A')}

**Target Audience:** {instructions['audience_reminder']} (Focus on fit for *us*)

**Output Language:** English

**Research Requirements:** This section primarily involves **analysis and synthesis** of the previously generated information. Use inline citations [SSX] to refer back to specific points made in the market overview, feature analysis, compliance landscape, or vendor comparison sections. Perform minimal *new* searches unless needed to clarify a specific point about '{context_company_name}'s likely context (if possible and grounded).
{instructions['handling_missing']}
{instructions['research_depth']} # Primarily synthesizing prior findings
{instructions['specificity']} # Connect specific features/trends to context company
{instructions['inline_citation']} # Reference previous sections' findings
{instructions['analysis_synthesis']} # CRITICAL for this section
{instructions['additional_refined']}

{instructions['base_formatting']}

## Relevance & Fit Analysis for {context_company_name}

### Relevance of '{product_category}' Market Trends
    *   Analyze how the key market drivers and trends identified for '{product_category}' [cite Sec 2 findings, e.g., SSX from Sec2] are relevant (or irrelevant) to '{context_company_name}'. Consider '{context_company_name}'s industry and likely strategic priorities.
    *   Discuss potential opportunities or threats these trends present specifically for '{context_company_name}' regarding this product category [cite Sec 2 findings].

### Fit of Key Features & Technologies
    *   Evaluate which of the common or differentiating features/technologies identified for '{product_category}' [cite Sec 3 findings, e.g., SSY from Sec3] are likely most important or beneficial for '{context_company_name}'s potential use cases. Justify the assessment.
    *   Identify any potential feature gaps or required integrations that '{context_company_name}' might need to consider [cite Sec 3 findings].

### Alignment with Compliance & Regional Needs
    *   Assess the importance of the identified compliance standards or certifications [cite Sec 4 findings, e.g., SSZ from Sec4] for '{context_company_name}', considering its industry and operational footprint. Does the general landscape meet the specified requirements ('{optional_inputs.get('required_certs', 'N/A')}')?
    *   Comment on the suitability of the vendor landscape considering the specified geographic region ('{optional_inputs.get('region', 'N/A')}') based on vendor presence noted earlier [cite Sec 5/Comparison findings].

### Vendor Suitability Context for '{context_company_name}'
    *   Based on the vendor comparison [cite Comparison Matrix/Summary], which of the filtered vendors seem like the strongest potential fit specifically for '{context_company_name}'s likely profile (e.g., considering scale, industry focus, specific feature needs identified above)? Briefly justify why.
    *   Highlight any major risks or trade-offs '{context_company_name}' should consider when evaluating these specific vendors [cite Sec 10 findings if deep dives done, or Comparison/Light Profile findings].

{instructions['final_review']}
{instructions['final_source_list']}
"""
    return prompt


def get_product_recommendations_prompt(
    product_category: str,
    analysis_summary: str, # Combined summary of market, features, vendors, relevance
    language: str,
    context_company_name: str,
    **optional_inputs
    ) -> str:
    """
    Generates prompt for outlook and recommendations tailored to context company.
    """
    instructions = _format_product_instructions(product_category, context_company_name)

    prompt = f"""
**CRITICAL FOCUS:** Provide a future outlook and actionable recommendations regarding the **'{product_category}'** market specifically for **'{context_company_name}'**.

**Objective:** Based on the comprehensive analysis performed (market trends, features, compliance, vendor landscape, relevance analysis), provide a forward-looking perspective and concrete recommendations for '{context_company_name}'.

**Provided Context:**
*   **Product Category:** {product_category}
*   **Requesting Company:** {context_company_name}
*   **Analysis Summary (Market, Features, Vendors, Relevance):** {analysis_summary}
*   **Optional User Input:** Region: {optional_inputs.get('region', 'N/A')}, Required Certs: {optional_inputs.get('required_certs', 'N/A')}

**Target Audience:** {instructions['audience_reminder']} (Needs actionable advice)

**Output Language:** English

**Research Requirements:** This section is primarily **analytical and advisory**, based on synthesizing previous findings. Use citations [SSX] to refer back to specific data points supporting the outlook or recommendations.
{instructions['handling_missing']}
{instructions['research_depth']} # Synthesize prior findings
{instructions['specificity']} # Actionable recommendations
{instructions['inline_citation']} # Reference evidence for outlook/recommendations
{instructions['analysis_synthesis']} # CRITICAL for outlook and recommendations
{instructions['additional_refined']}

{instructions['base_formatting']}

## Outlook & Recommendations for {context_company_name}

### Future Market Outlook (for '{product_category}')
    *   Summarize the likely future trajectory of the '{product_category}' market over the next 2-3 years, considering the trends identified [cite Sec 2 findings, e.g., SSX from Sec2].
    *   Highlight key technological advancements or market shifts expected to impact vendor offerings and user adoption [cite Sec 2/3 findings].
    *   Discuss potential long-term implications for companies like '{context_company_name}' that adopt or rely on this product category.

### Strategic Recommendations for '{context_company_name}'
    *   Provide 3-5 concrete, actionable recommendations for '{context_company_name}' regarding its strategy for '{product_category}'. Base these recommendations *directly* on the analysis findings (use bullet points):
        *   e.g., **Prioritize Vendors:** "Recommend focusing further evaluation efforts on Vendor A and Vendor C based on their strong feature alignment [cite Sec X findings] and compliance status [cite Sec Y findings]."
        *   e.g., **Address Specific Risks:** "Ensure thorough due diligence on Vendor B's financial stability given the concerns raised [cite Sec Z findings]."
        *   e.g., **Define Integration Strategy:** "Develop a clear integration plan, as connecting '{product_category}' solutions with existing System ABC appears to be a common challenge [cite Sec W findings]."
        *   e.g., **Consider Phased Adoption:** "Given the market volatility [cite Sec V findings], recommend a phased adoption approach starting with Department XYZ."
        *   e.g., **Negotiate Key Terms:** "Focus contract negotiations on [e.g., specific SLA guarantees, data residency clauses] based on identified compliance needs [cite Sec U findings]."
        *   e.g., **Monitor Market:** "Continuously monitor [e.g., specific emerging technology] as it may significantly disrupt the vendor landscape within 1-2 years [cite Sec T findings]."

### Suggested Next Steps
    *   Outline logical next steps for '{context_company_name}'s internal team (e.g., Procurement, IT) based on the recommendations:
        *   e.g., Initiate RFI/RFP process with shortlisted vendors (Vendor A, C).
        *   e.g., Conduct technical proof-of-concept (PoC) focusing on [specific feature/integration].
        *   e.g., Schedule vendor demonstrations and reference calls.
        *   e.g., Perform deeper dive / trigger full vendor research for shortlisted candidates.
        *   e.g., Re-evaluate internal requirements based on market findings.

{instructions['final_review']}
{instructions['final_source_list']}
"""
    return prompt


# --- New Prompt for Phase 5: Product Dashboard Summary ---

def get_product_dashboard_summary_prompt(full_report_content: str, filtered_vendor_list: Optional[List[str]] = None) -> str:
    """
    Generates a prompt to extract key dashboard KPIs from a completed product report.
    filtered_vendor_list is provided separately as it comes from state, not just the markdown.
    """
    vendor_count_note = f"The final filtered vendor list contains {len(filtered_vendor_list)} vendors: {', '.join(filtered_vendor_list)}." if filtered_vendor_list else "No vendors were selected after filtering."

    prompt = f"""
**Objective:** Analyze the provided Product Research Report Markdown content and extract specific Key Performance Indicators (KPIs) for a dashboard summary. Output the results ONLY as a valid JSON object.

**Input Report Content:**
```markdown
{full_report_content}
```

Additional Context:
{vendor_count_note}

Instructions:

Read Carefully: Process the entire report content, paying attention to market overview, features, compliance, and vendor identification/comparison sections.

Extract Specific KPIs: Identify and extract the following information precisely:

identified_vendor_count: The total number of vendors initially listed in the "Preliminary Vendor Identification" section (Section 5). Parse the table or list.

filtered_vendor_count: The number of vendors in the final filtered list (Use the count provided in the Additional Context above).

market_growth_trend: A concise description of the market trend from the "Market Overview & Trends" section (Section 2). Choose one: "Growing", "Stable", "Declining", or "Mixed/Unclear".

top_3_filtered_vendors: A JSON array containing the names of the first 3 vendors listed in the filtered vendor list provided in the Additional Context. If fewer than 3, list all available. If none, provide an empty array [].

key_tech_trends: A JSON array containing 2-3 key technology trends or prominent features mentioned in the "Key Features & Technologies" or "Market Overview" sections (Section 3 or 2). Summarize concisely (max 10 words per trend). Example: ["Increased AI Integration", "Shift to Cloud/SaaS Models", "Focus on Vertical Solutions"]

common_compliance_standards: A JSON array containing 2-3 key compliance standards or certifications frequently mentioned as relevant in the "Compliance & Certification Landscape" section (Section 4). Example: ["ISO 27001", "SOC 2", "GDPR"]

Handle Missing Data: If a specific piece of information cannot be clearly determined (e.g., market trend is ambiguous), use null or a reasonable default like "Unclear". For lists (top_3_filtered_vendors, key_tech_trends, common_compliance_standards), provide an empty array [] if none can be confidently extracted.

Output Format: Respond ONLY with a single, valid JSON object containing these keys and their extracted values. Do not include any introductory text, explanations, markdown formatting, or code fences around the JSON.

Example JSON Output Structure:

{{
  "identified_vendor_count": 8,
  "filtered_vendor_count": 3,
  "market_growth_trend": "Growing",
  "top_3_filtered_vendors": [
    "Vendor A Full Name",
    "Vendor C Full Name",
    "Vendor D Full Name"
  ],
  "key_tech_trends": [
    "AI-powered features becoming standard",
    "Strong push towards cloud-native architecture"
  ],
  "common_compliance_standards": [
    "SOC 2 Type II",
    "ISO 27001",
    "GDPR (for EU operations)"
  ]
}}

JSON Output:
"""
    return prompt