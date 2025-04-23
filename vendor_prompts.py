# vendor_prompts.py

import textwrap
from typing import Optional, Dict, Any

# --- Adapted Base Instruction Blocks for Vendor Research ---

# NOTE: These are adapted from the customer research originals.
# Key changes: Focus on vendor capability, stability, risk, compliance, supply chain.
# Audience context shifted to procurement/sourcing/risk professionals.
# Source prioritization emphasizes vendor's specs, financials, certs, BCP info.

VENDOR_ADDITIONAL_REFINED_INSTRUCTIONS = textwrap.dedent("""\
    **Additional Refined Instructions for Vendor Research (Zero Hallucination, Perfect Markdown, Strict Entity Coverage):**

    *   **Mandatory Self-Check Before Final Output:**
        - Before producing the final answer, confirm:
            1. All requested vendor sections are fully included with correct headings.
            2. All factual statements about the **Vendor ('{identifier}')** (capabilities, financials, compliance, incidents) have inline citations [SSX] pointing to valid Vertex AI URLs in the final Sources list.
            3. Only the permitted Vertex AI grounding URLs are used—no external or fabricated links.
            4. Markdown headings (`##`, `###`) and **perfect tables** follow the specified format (consistent columns, start/end pipes, accurate data vs. source).
            5. A single "Sources" section is present, properly labeled, and each source is on its own line.
            6. Inline citations appear before punctuation where feasible.
            7. No data or sources are invented about the **Vendor ('{identifier}')**. If information (e.g., specific cert, financial ratio, capacity detail) is omitted due to lack of verifiable grounding after exhaustive search, this is done silently without comment. Use '-' in tables *only* if needed for structure after confirming data absence in source.
            8.  **Strict Vendor Focus:** Strictly reference only the **exact Vendor named: '{identifier}'**. Verify you are NOT including data from similarly named but unrelated entities. Confirm if data relates to the parent/consolidated entity or a specific subsidiary relevant to supply, and report accordingly based ONLY on the source [SSX].
            9. Verify recency and relevance of all primary vendor sources used (Financial Reports for stability, Product Specs, QMS docs, Certifications, BCP info if public). Check document publication dates.
            10. Confirm key financial figures, operational details (locations, capacity if found), compliance statuses, and table data points against cited sources for the **Vendor ('{identifier}')**. **Verify specifically that all financial data has valid [SSX] citations linked to provided grounding URLs.**
            11. Ensure lists (e.g., Certifications, Key Facilities, Risks) are complete based on source availability for the **Vendor ('{identifier}')**.
            12. Confirm analytical depth provided where requested (explaining 'why' regarding stability trends, risk factors, capability limitations).

    *   **Exactness of Table Columns:**
        - Each row in any table **MUST** have the exact same number of columns as the header row, delimited by pipes (`|`).
        - Use exactly one pipe (`|`) at the beginning and end of each row.
        - Ensure header separator lines (`|---|---|`) match the number of columns precisely.
        - If data for a specific cell is missing *in the source* about the **Vendor ('{identifier}')** after exhaustive search, use a simple hyphen (-) as a placeholder *only if necessary* to maintain table structure. Do not add explanatory text.
        - Always include an inline citation [SSX] if referencing factual numbers or specific statuses within a table cell or in a note below the table referencing the table's data. Verify the cited data matches the source.

    *   **Quotes with Inline Citations (Vendor Context):**
        - Any verbatim quote from the **Vendor ('{identifier}')**'s management or reports must include:
            1. The speaker's name/title or document reference/date in parentheses.
            2. An inline citation [SSX] immediately following.
        - Focus on quotes relevant to quality, reliability, operational strategy, risk management, or product innovation.

    *   **Exactness of Hyperlinks in Sources:**
        - The final "Sources" section format: `* [Supervity Source X](Full_Vertex_AI_Grounding_URL) - Brief annotation [SSX].`
        - Number sources sequentially. Provide no additional domain expansions.
        - Annotation should state what specific vendor information (e.g., FY2023 Revenue [SSX], ISO 9001 Certification status [SSY]) the link supports.

    *   **Do Not Summarize Sources:**
        - Reference only the specific vendor claim(s) the link supports.

    *   **High-Priority Checklist (Vendor Research - Must Not Be Violated):**
        1. No fabrication about the **Vendor ('{identifier}')**: Silently omit rather than invent ungrounded data after exhaustive search.
        2. Adhere strictly to the specified Markdown formats (headings, lists, **perfect tables**).
        3. Use inline citations [SSX] matching final sources exactly for all **Vendor ('{identifier}')** facts.
        4. Provide only one "Sources" section at the end.
        5. Use only provided grounding URLs.
        6.  **Enforce Vendor Entity Coverage (CRITICAL):** If '{identifier}' is the target vendor, DO NOT include other similarly named but unrelated entities. Verify target entity identity throughout.
        7. Complete an internal self-check (see above) to ensure compliance before concluding.
""")

VENDOR_FINAL_SOURCE_LIST_INSTRUCTIONS = textwrap.dedent("""\
    **Final Source List Requirements (Vendor Research):**

    Conclude the *entire* research output with a clearly marked section titled "**Sources**".

    **1. Content - MANDATORY URL Type & Source Integrity:**
    *   **Exclusive Source Type:** This list **MUST** contain *only* the specific grounding redirect URLs provided directly by the **Vertex AI Search system** *for this specific query* regarding the **Vendor ('{identifier}')**.
    *   **URL Pattern:** URLs typically follow `https://vertexaisearch.cloud.google.com/grounding-api-redirect/...`. **Only this pattern is permitted.**
    *   **Strict Filtering:** Absolutely **DO NOT** include any other URL type.
    *   **CRITICAL - No Hallucination:** **Do NOT invent or reuse `vertexaisearch.cloud.google.com/...` URLs** if not explicitly provided as grounding results *for this query about the Vendor ('{identifier}')*. If a vendor fact lacks a grounding URL after exhaustive search, silently omit the fact from the report body AND list no source for it.
    *   **Purpose:** Verify grounding data for the **Vendor ('{identifier}')** for this request.

    **2. Formatting and Annotation (CRITICAL FOR PARSING):**
    *   **Source Line Format:** New line per source, start with `* ` or `- `, follow with Markdown link and annotation.
    *   **REQUIRED Format:**
        * [Supervity Source X](Full_Vertex_AI_Grounding_URL) - Annotation explaining exactly what vendor information is supported (e.g., supports Vendor '{identifier}'s QMS details [SSX] and key facility locations [SSY]).
    *   **Sequential Labeling:** Use "Supervity Source 1", "Supervity Source 2", etc.
    *   **Annotation Requirement:** Immediate, separated by " - ", brief, specific to vendor info supported by [SSX], and in English.

    **3. Quantity and Linkage:**
    *   List ***every distinct***, verifiable Vertex AI grounding URL provided *for this query* that directly supports content presented about the **Vendor ('{identifier}')** via an inline citation [SSX]. Do *not* include unused grounding URLs.
    *   Accuracy over quantity.
    *   Every grounding URL listed MUST correspond to vendor facts/figures/statements referenced with [SSX].

    **4. Content Selection Based on Verifiable Grounding (Vendor Research):**
    *   **Prerequisite for Inclusion:** Only include facts, figures, details, or quotes about the **Vendor ('{identifier}')** if supported by a verifiable grounding URL from this query after exhaustive search.
    *   **Omission of Ungrounded Vendor Facts/Sections:** Silently omit specific vendor details if ungrounded. If a whole section about the vendor lacks grounded data, retain the heading but omit the content.

    **5. Final Check:**
    *   Verify exclusive use of valid, provided grounding URLs supporting cited vendor facts.
    *   Verify format, linkage between citations and sources.
    *   The "**Sources**" section appears only once, at the end.
    """)

VENDOR_HANDLING_MISSING_INFO_INSTRUCTION = textwrap.dedent("""\
    *   **Handling Missing or Ungrounded Vendor Information:**
        *   **Exhaustive Research First:** Conduct exhaustive research using primarily official **Vendor ('{identifier}')** sources (see `VENDOR_RESEARCH_DEPTH_INSTRUCTION`). Search diligently across *multiple relevant primary sources* (e.g., latest Annual Report for financials, specific product pages/datasheets, Quality/Compliance sections on website, Certifications DBs if applicable, BCP summaries if public) for *each data point* before concluding information is unavailable. Check document publication dates.
        *   **Grounding Requirement for Inclusion:** Information about the **Vendor ('{identifier}')** is included only if:
            1. The information is located in a reliable source document related to the vendor.
            2. A corresponding, verifiable Vertex AI grounding URL (matching the pattern `https://vertexaisearch.cloud.google.com/grounding-api-redirect/...`) is provided in the search results for this query about the vendor.
        *   **Strict Silent Omission Policy:** If information about the **Vendor ('{identifier}')** cannot meet both conditions *after exhaustive research*, omit that specific fact, sentence, or data point entirely. Do **not** include statements like 'Data not found' or 'Information unavailable'. If an entire subsection lacks verifiable grounded data about the vendor, retain the heading but omit the content. If a table cell requires a placeholder for structure, use only `-` without explanation (verify data is missing *in the vendor's source*).
        *   **No Inference/Fabrication:** Do not infer, guess, or estimate ungrounded vendor information. Do not fabricate grounding URLs.
    """)

VENDOR_RESEARCH_DEPTH_INSTRUCTION = textwrap.dedent("""\
    *   **Vendor Research Depth & Source Prioritization:**
        *   **Exhaustive Search & Recency:** Conduct thorough research for all requested information points about the **Vendor ('{identifier}')**. Dig beyond surface summaries. **MANDATORY: Prioritize and use the absolute *latest* available official vendor sources.** Check document/website publication/revision dates. Critically, cross-verify information across *multiple relevant primary vendor sources* before accepting it.
        *   **Multi-Document Search Strategy (Vendor Context):** For each key data point (e.g., specific financial ratios for stability, product specs, certifications held, facility locations, key management, risk factors), search across *different types* of official vendor documents (e.g., Annual Report [focus on financials, risk factors, business overview], Financial Statements + Footnotes, Official Filings, Investor Relations Presentations, Company Website [Product pages, About Us, Compliance/Quality sections, Careers/Locations sections], specific Datasheets/Manuals if accessible, ESG/Sustainability Reports, BCP/DR summaries if published, official Press Releases).
        *   **Primary Vendor Source Focus (MANDATORY):** Use official **Vendor ('{identifier}')** sources primarily:
            *   Latest Annual Reports (focus on financial health, risk factors, segment data relevant to supply)
            *   Official Financial Statements & **Footnotes** (for stability analysis)
            *   Official Filings (SEC, EDGAR, local equivalents)
            *   Investor Relations Presentations & Materials (for strategy, investment plans relevant to capability/capacity)
            *   Official Corporate Website sections (e.g., "Products/Services", "About Us", "Locations", "Quality", "Compliance", "Sustainability", "Investor Relations", "Careers") - check "last updated" dates.
            *   Specific Product/Service Datasheets, Technical Specifications, Manuals (if publicly available or referenced).
            *   ESG/Sustainability/CSR Reports (for compliance, ethical sourcing, environmental data).
            *   Business Continuity / Disaster Recovery plan summaries (if published).
            *   Official Press Releases detailing operational changes, certifications, incidents, facility news.
        *   **Permitted Secondary Sources (Use Sparingly & Grounded):**
            *   Reputable Credit Rating Agency reports (S&P, Moody's, Fitch, R&I, JCR) - Cite agency and date [SSX].
            *   Official Certification Body Databases (e.g., ISO cert lookup if possible and grounded).
            *   Reputable Financial News (Bloomberg, Reuters, Nikkei, WSJ) for major events (e.g., large fines, facility closures, major M&A) *only if grounded and ideally cross-verified*.
            *   Reputable Industry Analyst reports discussing the vendor's *capabilities* or *market position* (e.g., Gartner MQ snippet if grounded).
        *   **Forbidden Sources:** Wikipedia, generic blogs/forums, social media (unless official vendor channel linking to primary source), news aggregators, competitor websites (except for basic comparison in competitive positioning section, handled carefully).
        *   **Data Verification:** Cross-verify critical vendor figures (e.g., revenue/profit for stability trend, key certifications, major locations) between sources where possible.
        *   **Group Structure Handling (Vendor Context):** Clearly identify if data refers to the consolidated parent group **Vendor ('{identifier}')** or a specific subsidiary relevant to the supply chain. Report consolidated financials for stability unless subsidiary financials are available and relevant. Acknowledge potential data limitations for non-public subsidiaries.
        *   **Calculation Guidelines:** If calculating financial ratios for the vendor (e.g., Current Ratio, D/E ratio):
            *   Calculate only if all base data is available and verifiable from grounded vendor sources.
            *   State the formula used (e.g., "Current Ratio (Calculated: Current Assets [SSX] / Current Liabilities [SSY])") and cite sources for all base data points.
        *   **Confirmation of Unavailability (Internal):** Only conclude vendor information is unavailable *internally* after a diligent, confirmed search across *multiple* relevant primary vendor source *types* fails to yield verifiable, grounded data. **Do not state this conclusion in the output.**
    """)

VENDOR_ANALYSIS_SYNTHESIS_INSTRUCTION = textwrap.dedent("""\
    *   **Analysis and Synthesis (Vendor Context):**
        *   Beyond listing factual vendor information, provide concise analysis where requested (e.g., explain financial stability trends, discuss implications of certifications or lack thereof, assess operational risks, evaluate alignment with *Context Company's* potential needs).
        *   **Explicitly address "why" for the Vendor ('{identifier}'):** Explain *why* financial trends are occurring [SSX], what drives their operational choices [SSY], or the significance of their compliance status [SSZ], based on sourced information or vendor management commentary. Quantify trends (e.g., "Vendor Debt-to-Equity increased from X to Y [SSX] potentially due to recent acquisition mentioned...").
        *   **Comparative Analysis (Vendor Context):** Compare vendor data points YoY [SSX]. If comparing to industry benchmarks or other vendors (in competitive section), use *only* reliable, grounded benchmark/competitor data [SSY].
        *   **Risk Focus:** Frame analysis around potential risks the vendor poses to the *Context Company* (supply chain, financial, compliance, reputational).
        *   **Capability Assessment:** Evaluate the vendor's capabilities (operational, technical, compliance) against standard requirements or potentially against the *Context Company's* likely needs (if product category is provided).
        *   **Linking Information:** In summary sections (Risk Assessment, Suitability Summary), explicitly tie together findings from different sections about the **Vendor ('{identifier}')** to present a coherent overall assessment (e.g., link financial stability [SSX] with operational capacity [SSY] and compliance record [SSZ] to assess overall reliability).
    """)

VENDOR_INLINE_CITATION_INSTRUCTION = textwrap.dedent("""\
    *   **Inline Citation Requirement (Vendor Research):**
        *   Every factual claim, data point (including figures/statuses in tables), direct quote, and specific summary about the **Vendor ('{identifier}')** **MUST** include an inline citation in the format `[SSX]`, where X corresponds exactly to the sequential number of the source in the final Sources list.
        *   Place the inline citation immediately after the supported statement and **before punctuation** when possible (e.g., "The vendor holds ISO 9001 certification [SS1].").
        *   If a single sentence contains multiple distinct vendor facts from different sources, cite each appropriately (e.g., "Their revenue was $100M [SS1] and they operate 3 key facilities [SS2].").
        *   If a single source supports multiple vendor facts within a paragraph or table, reuse the same `[SSX]`.
        *   This ensures that each fact about the **Vendor ('{identifier}')** is directly verifiable.
    """)

VENDOR_SPECIFICITY_INSTRUCTION = textwrap.dedent("""\
    *   **Specificity and Granularity (Vendor Research):**
        *   For all time-sensitive vendor data points (e.g., financials, employee counts, certifications validity, facility info, incidents), include specific dates or reporting periods (e.g., "as of 2024-03-31", "for FY2023 ended Dec 31, 2023", "ISO 9001:2015 certified on YYYY-MM-DD, valid until YYYY-MM-DD").
        *   Define any industry-specific or vendor-specific terms or acronyms on their first use.
        *   Quantify qualitative descriptions about the vendor with specific numbers or percentages where available (e.g., "consistent profitability with operating margin averaging X% over 3 years [SSX]").
        *   List concrete examples rather than vague categories when describing vendor capabilities, risks, or compliance measures. Use official product/service names used by the vendor.
    """)

VENDOR_AUDIENCE_CONTEXT_REMINDER = textwrap.dedent("""\
    *   **Audience Relevance (Vendor Research):** Keep the target audience (e.g., Procurement, Supply Chain, Risk Management professionals at **'{context_company_name}'**) in mind. Frame analysis and summaries to highlight vendor reliability, capability, financial stability, compliance posture, operational risks, and overall suitability *as a supplier or partner for {context_company_name}*. Use terminology common in sourcing and risk assessment.
    """)

VENDOR_BASE_FORMATTING_INSTRUCTIONS = textwrap.dedent("""\
    Output Format & Quality Requirements (Vendor Research):

    *   **Direct Start & No Conversational Text:** Begin the response directly with the first requested section heading (e.g., `## 1. Basic Vendor Information`). No introductory or concluding remarks.

    *   **Strict Markdown Formatting Requirements:**
        *   Use valid and consistent Markdown.
        *   **Section Formatting:** Sections MUST be numbered exactly as specified (e.g., `## 1. Basic Vendor Information`). Use `##` for main sections.
        *   **Subsection Formatting:** Use `###` for subsections.
        *   **List Formatting:** Use asterisks (`*`) or hyphens (`-`) for bullets with consistent indentation (4 spaces for sub-bullets).
        *   **Tables (CRITICAL):** Format all tables with *perfect* Markdown table syntax for the **Vendor ('{identifier}')**:
            *   **Exact Column Count:** Every row **MUST** have the *exact same number of columns* delimited by pipes (`|`).
            *   **Mandatory Start/End Pipes:** Every row **MUST** begin and end with a pipe (`|`).
            *   **Header Separator Match:** The separator line (`|---|---|...`) **MUST** match the number of header columns exactly.
            *   **Alignment (Visual Aid):** Visually align pipes using spaces.
            *   **Table Data Integrity:** Every vendor data point/status in a table MUST be verified against the cited source [SSX] for accuracy and correct reporting period.
            *   **Missing Data Placeholder:** Use only a hyphen (`-`) for data confirmed missing *in the vendor's source* after exhaustive search, if needed for structure.
            *   **Example Perfect Table:**
                | Header 1        | Header 2      | Status      | Source(s) | <--- Ends with pipe
                |-----------------|---------------|-------------|-----------| <--- Matches 4 columns, ends with pipe
                | Facility A      | Location City | Operational | [SS1]     | <--- Matches 4 columns, ends with pipe
                | Certification X | ISO 9001:2015 | Active      | [SS2]     | <--- Matches 4 columns, ends with pipe
                | Financial Ratio | 1.5           | -           | [SS1, SS3]| <--- Matches 4 columns, ends with pipe
            *   **Consequence of Error:** Incorrect tables will fail rendering. Double-check every table.
        *   **Code Blocks:** Use triple backticks (```) if needed (less common in vendor reports).
        *   **Quotes:** Use Markdown quote syntax (`>`) for direct vendor quotations.

    *   **Optimal Structure & Readability:**
        *   Use tables for structured vendor data (financials, locations, certifications, risks).
        *   Use bullet points for lists (capabilities, compliance points, risk factors).
        *   Use paragraphs for narrative analysis and context about the vendor.
        *   Maintain consistent formatting.
        *   **Conciseness:** Detailed yet concise. Be specific about the vendor.

    *   **Data Formatting Consistency (Vendor Data):**
        *   Use appropriate thousands separators for numbers (English standard: comma).
        *   **Currency Specification:** Always specify currency (e.g., $, €, JPY, USD, EUR) for all vendor monetary values with reporting period.
        *   Format dates consistently (YYYY-MM-DD preferred).
        *   Use consistent percentage formatting (e.g., 12.5%).

    *   **Section Completion Verification:**
        *   Every section requested MUST be included.
        *   Sections in exact order.
        *   Each section properly labeled.
        *   If verifiable data for an entire vendor subsection is missing after exhaustive research, omit the *content*, but **retain the subsection heading**.

    *   **Tone and Detail Level:**
        *   Professional, objective, analytical tone suited for vendor assessment by **'{context_company_name}'**.
        *   Provide granular vendor detail (figures, dates, specs, certifications) while avoiding promotional language.

    *   **Completeness and Verification:**
        *   Address all requested points in each vendor section (providing information or silently omitting if ungrounded).
        *   Verify all sections and the Sources list are present and adhere to instructions.
        *   Perform a final internal review.

    *   **Sources List:** Present at the very end, adhering strictly to format: `* [Supervity Source X](URL) - Annotation [SSX].`

    *   **Inline Citation & Specificity:** Incorporate [SSX] for every factual vendor claim and include specific dates/definitions.
    """)

VENDOR_FINAL_REVIEW_INSTRUCTION = textwrap.dedent("""\
    *   **Internal Final Review (Vendor Research):** Before generating the 'Sources' list, review your generated response for **Vendor ('{identifier}')**:

        *   **Completeness Check:**
            * Every numbered vendor section requested is present with the correct heading.
            * Each section contains all requested vendor subsections and information points, or content silently omitted if ungrounded (headings retained).
            * Key sections like Financial Stability, Operational Capabilities, Compliance, Risk Assessment, Suitability Summary are substantially addressed based on available grounded data for the vendor.

        *   **Formatting Verification:**
            * Correct line breaks, section/subsection headings.
            * **Tables are PERFECTLY formatted** (pipes, columns, separators, vendor data accuracy check vs source, minimal '-' usage).
            * Lists use consistent formatting.

        *   **Citation Integrity (Vendor Data):**
            * Every factual claim about **Vendor ('{identifier}')** has an inline citation `[SSX]`.
            * **Specifically verify financial data points, certification statuses, operational details, and table entries for correct [SSX] citations.**
            * Citations placed correctly (before punctuation).
            * All citations correspond exactly to entries that WILL BE in the final Sources list.
            * Every source listed corresponds to at least one inline citation `[SSX]` referring to **Vendor ('{identifier}')**.

        *   **Data Precision & Recency (Vendor Data):**
            * All monetary values for the vendor specify currency and reporting period.
            * All dates (financials, certifications, incidents) are specific and reflect the latest available grounded data for the vendor.
            * Numerical data is precise with units. Vendor names/product names are official.
            * Primary vendor sources used are confirmed recent and grounded.

        *   **Content Quality & Vendor Focus:**
            * Direct start, professional tone, no placeholders (except table `-`).
            * Adherence to silent omission handling instructions for vendor data.
            * Logical flow. Analytical depth provided where required (explaining 'why' for stability, risk).
            * Analysis is consistently focused on assessing the **Vendor ('{identifier}')** from the perspective of **'{context_company_name}'** (reliability, capability, risk).

        *   **Single-Entity Focus (CRITICAL):**
            *   Ensure analysis and data strictly pertains to the specified **Vendor ('{identifier}')**. Verify no data from similarly named but unrelated entities.

        Proceed to generate the final 'Sources' list only after confirming these conditions are met.
    """)

# --- Vendor Prompt Generating Functions ---

# Helper function to format all base instructions
def _format_all_instructions(identifier: str, context_company_name: str) -> Dict[str, str]:
    """Formats all base instruction blocks with specific context."""
    return {
        "additional_refined": VENDOR_ADDITIONAL_REFINED_INSTRUCTIONS.format(identifier=identifier, context_company_name=context_company_name),
        "research_depth": VENDOR_RESEARCH_DEPTH_INSTRUCTION.format(identifier=identifier, context_company_name=context_company_name),
        "handling_missing": VENDOR_HANDLING_MISSING_INFO_INSTRUCTION.format(identifier=identifier),
        "analysis_synthesis": VENDOR_ANALYSIS_SYNTHESIS_INSTRUCTION.format(identifier=identifier, context_company_name=context_company_name),
        "inline_citation": VENDOR_INLINE_CITATION_INSTRUCTION.format(identifier=identifier),
        "specificity": VENDOR_SPECIFICITY_INSTRUCTION.format(identifier=identifier),
        "audience_reminder": VENDOR_AUDIENCE_CONTEXT_REMINDER.format(identifier=identifier, context_company_name=context_company_name),
        "base_formatting": VENDOR_BASE_FORMATTING_INSTRUCTIONS.format(identifier=identifier, context_company_name=context_company_name),
        "final_review": VENDOR_FINAL_REVIEW_INSTRUCTION.format(identifier=identifier, context_company_name=context_company_name),
        "final_source_list": VENDOR_FINAL_SOURCE_LIST_INSTRUCTIONS.format(identifier=identifier)
    }

def get_vendor_basic_prompt(identifier: str, language: str, context_company_name: str, **optional_inputs) -> str:
    """Generates the prompt for basic vendor information."""
    instructions = _format_all_instructions(identifier, context_company_name)

    prompt = f"""
**CRITICAL FOCUS:** Research *exclusively* the specific vendor: **'{identifier}'**. Verify identity rigorously.

**Objective:** Compile core identifying and structural information about the Vendor '{identifier}'. Focus on factual data relevant for initial vendor screening.

**Target Audience:** {instructions['audience_reminder']}

**Output Language:** English

**Research Requirements:** Use latest official vendor sources. Ground every fact with [SSX]. Use perfect Markdown.
{instructions['handling_missing']}
{instructions['research_depth']}
{instructions['specificity']}
{instructions['inline_citation']}
{instructions['additional_refined']}

{instructions['base_formatting']}

## 1. Basic Vendor Information

### 1.1 Core Identification
    *   **Full Legal Vendor Name:** '{identifier}' [SSX] (Verify exact legal name if possible)
    *   **Stock Ticker Symbol / Security Code:** (If publicly traded) [SSX]
    *   **Primary Industry Classification:** (e.g., GICS, NAICS - specify standard) [SSX]
    *   **Date of Establishment/Incorporation:** (YYYY-MM-DD, for longevity assessment) [SSX]
    *   **Full Registered Headquarters Address:** [SSX]
    *   **Main Corporate Telephone Number:** [SSX]
    *   **Official Corporate Website URL:** [SSX]

### 1.2 Size & Scale Indicators
    *   **Most Recently Reported Total Number of Employees:** (Specify count and 'as of' date, note trend if available YoY [SSY]) [SSX]
    *   **Most Recently Reported Total Revenue:** (Specify amount, currency, and fiscal year end date, for general scale) [SSX]
    *   **Key Operational Locations/Facilities:** (List major manufacturing sites, R&D centers, distribution hubs, data centers relevant to potential supply, include city/country. Use a **perfectly formatted Markdown table** if many.) [SSX]
        *   Example Perfect Table:
            | Facility Type        | Location (City, Country) | Primary Function        | Source(s) |
            |----------------------|--------------------------|-------------------------|-----------|
            | Manufacturing Plant  | Exampleville, USA        | Product Line A Assembly | [SSX]     |
            | R&D Center           | Testburg, Germany        | Core Technology Dev     | [SSY]     |
            | Primary Data Center  | Serverton, UK            | Cloud Service Hosting   | [SSZ]     |
            | ...                  | ...                      | ...                     |           |

### 1.3 Brief Business Overview
    *   Provide a concise summary (1-2 paragraphs) of the **Vendor ('{identifier}')**'s core business operations, primary products/services offered (especially related to '{optional_inputs.get('product_category', 'Not Specified')}' if provided), and main customer types/markets served, based on latest official reports [SSX].

### 1.4 Ownership Snippet
    *   State ownership type (e.g., Publicly Traded on [Exchange], Privately Held, Subsidiary of [Parent Company]) [SSX].
    *   Mention if owned by Private Equity if clearly stated [SSY].

{instructions['final_review']}
{instructions['final_source_list']}
"""
    return prompt

def get_vendor_products_services_prompt(identifier: str, language: str, context_company_name: str, **optional_inputs) -> str:
    """Generates the prompt for vendor product/service details."""
    instructions = _format_all_instructions(identifier, context_company_name)
    product_category_focus = optional_inputs.get('product_category')
    focus_instruction = f"Pay special attention to products/services related to the category: **'{product_category_focus}'**." if product_category_focus else "Provide a general overview of main products/services."

    prompt = f"""
**CRITICAL FOCUS:** Research *exclusively* the specific vendor: **'{identifier}'**. Verify identity rigorously.

**Objective:** Detail the key products and services offered by Vendor '{identifier}', focusing on aspects relevant to potential procurement by '{context_company_name}'. {focus_instruction}

**Target Audience:** {instructions['audience_reminder']}

**Output Language:** English

**Research Requirements:** Use vendor's official product pages, datasheets, brochures, service descriptions. Ground every feature/spec claim with [SSX]. Use perfect Markdown.
{instructions['handling_missing']}
{instructions['research_depth']}
{instructions['specificity']}
{instructions['inline_citation']}
{instructions['additional_refined']}

{instructions['base_formatting']}

## 2. Product & Service Details (Vendor: {identifier})

### 2.1 Primary Product/Service Categories
    *   List the main categories of products or services offered by the vendor '{identifier}' [SSX].
    *   For each category, provide a brief description of its scope [SSY].

### 2.2 Detailed Offerings (Focus: {product_category_focus or 'General'})
    *   Describe specific, named products or service lines within the relevant categories. Use official vendor terminology [SSX].
    *   For key offerings (especially if related to '{product_category_focus}'):
        *   **Key Features/Specifications:** List critical features, technical specs, performance metrics as stated in official documentation (e.g., capacity, speed, materials used, software version) [SSX]. Present in bullet points or a **perfectly formatted Markdown table** if comparing multiple related products.
        *   **Technology Used:** Mention underlying technologies if highlighted by the vendor (e.g., AI/ML components, specific platform dependencies, proprietary algorithms) [SSY].
        *   **Target Use Cases/Applications:** Describe the intended applications or problems the product/service solves, according to the vendor [SSZ].
        *   **Differentiation:** Highlight unique selling propositions or differentiators claimed by the vendor for these offerings [SSW].
    *   Example Structure for a Product:
        *   **Product Name:** [Official Name, e.g., "Vendor QuantumLeap CRM v3.0"] [SSX]
        *   **Category:** [e.g., Customer Relationship Management Software] [SSX]
        *   **Key Features:**
            *   AI-powered lead scoring module [SSY]
            *   Integrated marketing automation tools [SSY]
            *   Scalable architecture supporting up to X users [SSZ]
            *   Mobile application access [SSZ]
        *   **Technology:** Built on [Platform Name], utilizes [Specific AI library] [SSW]
        *   **Target:** Mid-to-Large Enterprises in [Industry] sector [SSX]
        *   **Claimed Differentiator:** "Proprietary predictive churn analysis outperforms competitors by Y%" [SSV]

### 2.3 Support, Maintenance, and SLAs (Service Level Agreements)
    *   Describe the standard support and maintenance options offered for relevant products/services, if publicly documented (e.g., support hours, response time targets, included services) [SSX].
    *   Mention any stated Service Level Agreements (SLAs) regarding uptime, performance, or issue resolution, if available [SSY]. Be specific about metrics and targets cited.

### 2.4 Product Roadmap & Innovation (if available)
    *   Summarize any publicly stated information about the vendor's future product roadmap, upcoming releases, or key areas of R&D focus relevant to their offerings [SSX].
    *   Comment on the vendor's apparent pace of innovation or product updates based on release history or announcements, if discernible from sources [SSY].

{instructions['final_review']}
{instructions['final_source_list']}
"""
    return prompt

def get_vendor_financial_stability_prompt(identifier: str, language: str, context_company_name: str, **optional_inputs) -> str:
    """Generates the prompt for vendor financial stability assessment."""
    instructions = _format_all_instructions(identifier, context_company_name)

    prompt = f"""
**CRITICAL FOCUS:** Research *exclusively* the specific vendor: **'{identifier}'**. Verify identity rigorously.

**Objective:** Assess the financial stability and risk profile of Vendor '{identifier}' using the last 3 full fiscal years of available data. Focus on metrics indicating reliability and sustainability as a supplier.

**Target Audience:** {instructions['audience_reminder']} (Focus on financial risk to supply chain)

**Output Language:** English

**Research Requirements:** Use vendor's official financial reports (Annual Reports, Filings, Financial Statements + Footnotes). Ground every figure and ratio with [SSX]. Calculate ratios only if base data is grounded, state formula, cite base data sources. Use **perfect Markdown tables**. Verify data accuracy.
{instructions['handling_missing']}
{instructions['research_depth']} # Emphasizes financial sources
{instructions['specificity']} # Emphasizes dates and currency
{instructions['inline_citation']} # Critical for financials
{instructions['analysis_synthesis']} # Emphasize stability trends and risk implications
{instructions['additional_refined']} # Verify financial data citations

{instructions['base_formatting']} # Enforces perfect tables

## 3. Financial Stability Assessment (Vendor: {identifier})

### 3.1 Key Financial Metrics (3-Year Trend for Stability)
    *   Present the following metrics for Vendor '{identifier}' for the last 3 full fiscal years in a **perfectly formatted Markdown table**. Specify currency and fiscal year end date for each value. Verify data accuracy. Cite sources [SSX] for every numerical cell. Use '-' only for data confirmed missing in source after exhaustive search.
        | Metric                            | FYXXXX (YYYY-MM-DD) | FYYYYY (YYYY-MM-DD) | FYZZZZ (YYYY-MM-DD) | Notes / Calculation Basis (Cite Base Data Sources) | Source(s) |
        |-----------------------------------|---------------------|---------------------|---------------------|----------------------------------------------------|-----------|
        | Total Revenue (Unit)              | Value [SSX]         | Value [SSY]         | Value [SSZ]         | (Indicates scale trend)                            | [SSX, SSY, SSZ]|
        | Operating Income (Unit)           | Value [SSX]         | Value [SSY]         | Value [SSZ]         | (Indicates core profitability)                     | [SSX, SSY, SSZ]|
        | Operating Margin (%)              | Value [SSA]         | Value [SSB]         | Value [SSC]         | (Calc: OpInc[SSX]/Rev[SSX], etc.)                  | [SSA, SSB, SSC]|
        | Net Income (Parent) (Unit)        | Value [SSX]         | Value [SSY]         | Value [SSZ]         | (Overall profitability)                            | [SSX, SSY, SSZ]|
        | Net Cash from Operations (Unit)   | Value [SSX]         | Value [SSY]         | Value [SSZ]         | (Ability to generate cash internally)              | [SSX, SSY, SSZ]|
        | Total Assets (Unit)               | Value [SSX]         | Value [SSY]         | Value [SSZ]         |                                                    | [SSX, SSY, SSZ]|
        | Total Liabilities (Unit)          | Value [SSX]         | Value [SSY]         | Value [SSZ]         |                                                    | [SSX, SSY, SSZ]|
        | Total Shareholders' Equity (Unit) | Value [SSX]         | Value [SSY]         | Value [SSZ]         |                                                    | [SSX, SSY, SSZ]|
        | Current Assets (Unit)             | Value [SSX]         | Value [SSY]         | Value [SSZ]         | (For liquidity calc)                               | [SSX, SSY, SSZ]|
        | Current Liabilities (Unit)        | Value [SSX]         | Value [SSY]         | Value [SSZ]         | (For liquidity calc)                               | [SSX, SSY, SSZ]|
        | Total Interest-Bearing Debt (Unit)| Value [SSX]         | Value [SSY]         | Value [SSZ]         | (If available)                                     | [SSX, SSY, SSZ]|
        | EBITDA (Unit)                     | Value [SSX]         | Value [SSY]         | Value [SSZ]         | (If available/calculable)                          | [SSX, SSY, SSZ]|

### 3.2 Profitability & Efficiency Trends
    *   Analyze the trend in Operating Margin for Vendor '{identifier}' over the 3 years. Is it stable, increasing, or decreasing [SSA, SSB, SSC]? Explain potential drivers mentioned in sources (e.g., cost controls, pricing power shifts, specify period) [SSX].
    *   Analyze the trend in Net Income for Vendor '{identifier}'. Comment on consistency and any significant one-off impacts mentioned in reports (specify year) [SSY].
    *   Evaluate if profitability appears sustainable based on trends and source commentary [SSZ].

### 3.3 Liquidity Assessment (Short-Term Stability)
    *   Calculate and present the Current Ratio (Current Assets [SSX] / Current Liabilities [SSY]) for Vendor '{identifier}' for the last 3 years (e.g., FYXXXX: Value [SSZ], FYYYYY: Value [SSW],...). State formula and cite base data. Analyze the trend – is short-term liquidity improving or worsening? Mention if below/above industry norms if known and grounded [SSV].
    *   Calculate and present the Quick Ratio ((Current Assets [SSX] - Inventory [SSY]) / Current Liabilities [SSZ]) if inventory data is available and verifiable [SSW]. State formula and cite base data. Analyze the trend – how reliant is liquidity on inventory?
    *   Analyze the trend in Net Cash from Operations [SSX, SSY, SSZ]. Is the vendor consistently generating positive cash flow from its core business? Are there concerning fluctuations (specify periods)?

### 3.4 Solvency Assessment (Long-Term Stability)
    *   Calculate and present the Debt-to-Equity Ratio (Total Liabilities [SSX] / Total Shareholders' Equity [SSY] OR Total Debt [SSZ] / Total Equity [SSW] - specify which is used and cite base data) for Vendor '{identifier}' for the last 3 years (e.g., FYXXXX: Value [SSA], FYYYYY: Value [SSB],...). Analyze the trend – is leverage increasing or decreasing? Comment on whether the level seems appropriate for the industry (if benchmarks are known/grounded) [SSC].
    *   If Interest-Bearing Debt data is available [SSX, SSY, SSZ], analyze its trend relative to Equity [SSW] or EBITDA [SSV] (e.g., Debt/EBITDA ratio, if calculable, cite data). High or rapidly rising debt can be a risk factor.
    *   Comment on overall balance sheet strength based on Equity Ratio (Equity [SSX] / Assets [SSY]) trend (cite data).

### 3.5 Credit Ratings (if available)
    *   List current credit ratings for Vendor '{identifier}' from major agencies (e.g., S&P, Moody's, Fitch, R&I, JCR) in a **perfectly formatted Markdown table**. Include rating, outlook (stable/positive/negative), and date of rating [SSX]. Verify data. Use '-' only for missing data.
        | Agency  | Rating      | Outlook  | Date       | Source(s) |
        |---------|-------------|----------|------------|-----------|
        | S&P     | e.g., BBB+  | e.g., Stable | YYYY-MM-DD | [SSX]     |
        | Moody's | e.g., Baa1  | e.g., Positive| YYYY-MM-DD | [SSY]     |
        | Fitch   | -           | -        | -          | -         |
        | R&I     | e.g., A-    | e.g., Stable | YYYY-MM-DD | [SSZ]     |
        | JCR     | -           | -        | -          | -         |
        | ...     | ...         | ...      | ...        |           |
    *   Summarize key factors or concerns mentioned in the rating agencies' rationale for Vendor '{identifier}', if available and grounded [SSX, SSY, SSZ].

### 3.6 Financial Stability Summary & Risk Assessment
    *   Provide a concluding paragraph summarizing the overall financial stability of Vendor '{identifier}' based purely on the analysis in Sections 3.1-3.5.
    *   Highlight key strengths (e.g., consistent profitability [SSZ], strong liquidity trend based on Current Ratio [SSW], declining leverage based on D/E ratio [SSA, SSB]). Use specific metrics and trends with citations.
    *   Identify key potential financial risks or concerns (e.g., declining margins [SSA, SSB, SSC], high dependence on debt [SSX, SSY, SSZ], negative operating cash flow in FYZZZZ [SSZ], recent rating downgrade [SSX]). Use specific metrics and trends with citations.
    *   Conclude with an overall assessment of the level of financial risk associated with this vendor (e.g., Low, Moderate, High) based *only* on the verifiable public data presented.

{instructions['final_review']}
{instructions['final_source_list']}
"""
    return prompt

def get_vendor_operational_capabilities_prompt(identifier: str, language: str, context_company_name: str, **optional_inputs) -> str:
    """Generates the prompt for vendor operational capabilities."""
    instructions = _format_all_instructions(identifier, context_company_name)
    product_category_focus = optional_inputs.get('product_category')
    focus_instruction = f"Focus should be on capabilities relevant to supplying: **'{product_category_focus}'**." if product_category_focus else "Describe general operational capabilities."

    prompt = f"""
**CRITICAL FOCUS:** Research *exclusively* the specific vendor: **'{identifier}'**. Verify identity rigorously.

**Objective:** Detail the operational capabilities of Vendor '{identifier}', focusing on aspects relevant to its ability to reliably supply products/services. {focus_instruction}

**Target Audience:** {instructions['audience_reminder']} (Focus on supply reliability, quality, capacity)

**Output Language:** English

**Research Requirements:** Use vendor's official website (locations, quality sections), reports (operations overview, risk factors), press releases (facility news). Ground every claim with [SSX]. Use **perfect Markdown tables**.
{instructions['handling_missing']}
{instructions['research_depth']} # Focus on Ops sections, press releases
{instructions['specificity']} # Location details, capacity units
{instructions['inline_citation']}
{instructions['analysis_synthesis']} # Focus on capability assessment & risk
{instructions['additional_refined']} # Verify locations, capacity

{instructions['base_formatting']} # Enforces perfect tables

## 4. Operational Capabilities (Vendor: {identifier})

### 4.1 Manufacturing / Service Delivery Footprint
    *   List key manufacturing plants, service delivery centers, R&D facilities, or distribution hubs operated by Vendor '{identifier}' that are relevant to potential supply. Use a **perfectly formatted Markdown table**. Include Location (City, Country), Primary Function, and any relevant Size/Capacity indicator mentioned (e.g., sq footage, production volume, # employees if specific to site and grounded) [SSX]. Verify data. Use '-' for missing data confirmed in source.
        | Facility Type         | Location (City, Country) | Primary Function / Product Focus | Size/Capacity Notes (if stated) | Source(s) |
        |-----------------------|--------------------------|----------------------------------|---------------------------------|-----------|
        | Manufacturing Plant   | Exampleville, USA [SSX]  | Product Line A Assembly [SSX]    | 100,000 sq ft [SSX]             | [SSX]     |
        | Service Center        | Supportburg, India [SSY] | Global Tech Support Tier 1/2[SSY]| 500+ agents [SSY]               | [SSY]     |
        | Distribution Hub      | Logistics Central, NL[SSZ]| European Distribution [SSZ]      | -                               | [SSZ]     |
        | R&D Facility          | Innovation City, JP[SSW] | New Product Research [SSW]       | 200 scientists [SSW]            | [SSW]     |
        | ...                   | ...                      | ...                              | ...                             |           |
    *   Analyze the geographic concentration or dispersion of these key facilities based on the table above. Discuss potential risks associated with geographic concentration (e.g., natural disasters, geopolitical issues in 'Exampleville, USA') based on locations listed [SSX, SSY, SSZ, SSW].

### 4.2 Production Capacity & Lead Times (if available)
    *   Report any publicly stated production capacity figures for relevant product lines (e.g., X units per year for Product Line A, Y tons per month for Material Z) [SSX]. Specify product and timeframe (e.g., "as stated in FY2023 report").
    *   Mention any typical or standard lead times quoted by the vendor for relevant products/services, if found in official documentation (e.g., "Standard lead time for Product B is 4-6 weeks") [SSY].
    *   Discuss any recent news or statements regarding capacity expansions (e.g., "Opened new plant in Location [SSZ]"), constraints (e.g., "Reported chip shortages impacting output [SSA]"), or investments by the vendor [SSB]. Cite sources.

### 4.3 Quality Management Systems (QMS)
    *   Describe the vendor's stated approach to quality management [SSX]. Does the vendor explicitly mention adherence to specific QMS frameworks (e.g., "Adheres to ISO 9001 principles [SSY]", "Utilizes Six Sigma methodology [SSZ]")? (Specific certifications covered in Sec 5).
    *   Mention any publicly disclosed quality metrics or performance indicators used by the vendor, if available (e.g., "Targets <0.1% defect rate [SSW]", "Reports 99.5% on-time delivery [SSV]"). Cite sources.
    *   Note any recent (last 2-3 years) product recalls, significant quality issues (e.g., FDA warning letter), or quality awards mentioned in grounded sources [SSU]. Provide details and dates.

### 4.4 Logistics & Supply Chain Management (Vendor's Perspective)
    *   Describe the vendor's stated logistics capabilities (e.g., "Operates own fleet of trucks [SSX]", "Partners with DHL and FedEx for global distribution [SSY]", "Maintains X regional warehouses [SSZ]"). Cite sources.
    *   Summarize the vendor's approach to managing its *own* supply chain, if discussed (e.g., "Sources key components from region X [SSW]", "Reports dual-sourcing strategy for critical materials [SSV]", "Mentions use of supply chain risk platform [SSU]"). This indicates their resilience. Cite sources.
    *   Note any recent significant disruptions to the vendor's *own* supply chain or logistics operations reported in grounded sources (e.g., "Port congestion delayed imports in Q4 2023 [SST]", "Key supplier bankruptcy impacted production [SSR]"). Cite sources and dates.

### 4.5 Technological Capabilities (Operational Context)
    *   Describe the use of technology within the vendor's manufacturing or service delivery processes, if highlighted (e.g., "Implemented factory automation project [SSX]", "Uses MES for real-time production tracking [SSY]", "Employs AI for predictive maintenance [SSZ]"). Cite sources.
    *   Comment on the apparent technological sophistication of their operations based on available evidence [SSW]. Does it appear modern or lagging for their industry?

{instructions['final_review']}
{instructions['final_source_list']}
"""
    return prompt

def get_vendor_compliance_certs_prompt(identifier: str, language: str, context_company_name: str, **optional_inputs) -> str:
    """Generates the prompt for vendor compliance and certifications."""
    instructions = _format_all_instructions(identifier, context_company_name)
    required_certs_focus = optional_inputs.get('required_certs')
    product_category = optional_inputs.get('product_category')
    focus_instruction = f"Pay special attention to certifications like **'{required_certs_focus}'**." if required_certs_focus else "Identify key standard certifications."
    industry_focus_instruction = f"Check for industry-specific compliance relevant to **'{product_category}'**." if product_category else ""

    prompt = f"""
**CRITICAL FOCUS:** Research *exclusively* the specific vendor: **'{identifier}'**. Verify identity rigorously.

**Objective:** Identify and verify the vendor '{identifier}'s adherence to relevant industry standards, regulations, and certifications, crucial for risk assessment and meeting '{context_company_name}' requirements. {focus_instruction} {industry_focus_instruction}

**Target Audience:** {instructions['audience_reminder']} (Focus on compliance risks, meeting standards)

**Output Language:** English

**Research Requirements:** Use vendor's official website (Compliance, Quality, Sustainability, Trust Center), ESG/CSR reports, Annual Reports. Verify status and dates. Ground every claim with [SSX]. Use **perfect Markdown tables**. Search for {required_certs_focus if required_certs_focus else 'ISO 9001, ISO 27001, SOC 2, ISO 14001'}.
{instructions['handling_missing']}
{instructions['research_depth']} # Focus on Compliance/Quality/ESG sections
{instructions['specificity']} # Certification names, dates, scope
{instructions['inline_citation']}
{instructions['analysis_synthesis']} # Implications of compliance/non-compliance
{instructions['additional_refined']} # Verify certification status and dates

{instructions['base_formatting']} # Enforces perfect tables

## 5. Compliance & Certifications (Vendor: {identifier})

### 5.1 Key Certifications Status
    *   Present key certifications held by Vendor '{identifier}' in a **perfectly formatted Markdown table**. Verify status, scope, and validity date if available. Use '-' for missing data confirmed in source. {focus_instruction}
        | Certification Name | Status (e.g., Certified, Compliant) | Scope (if specified)              | Valid Until Date (YYYY-MM-DD) | Source(s) |
        |--------------------|-------------------------------------|-----------------------------------|-------------------------------|-----------|
        | ISO 9001:2015      | e.g., Certified [SSX]               | e.g., Manufacturing Ops [SSX]     | e.g., 2025-12-31 [SSX]        | [SSX]     |
        | ISO 27001:2022     | e.g., Certified [SSY]               | e.g., Cloud Platform Services [SSY]| e.g., 2026-06-30 [SSY]        | [SSY]     |
        | SOC 2 Type II      | e.g., Report Available [SSZ]        | e.g., Security, Availability [SSZ]| e.g., Report dated 2024-03-31[SSZ]| [SSZ]     |
        | ISO 14001:2015     | e.g., Certified [SSW]               | e.g., HQ Site [SSW]               | e.g., 2025-09-15 [SSW]        | [SSW]     |
        | ISO 45001:2018     | e.g., Compliant (Stated) [SSV]      | -                                 | -                             | [SSV]     |
        | {required_certs_focus or 'Industry Specific Cert'} | e.g., Not Mentioned [SSU]           | -                                 | -                             | [SSU]     |
        | CMMI Level X       | e.g., Level 3 Appraised [SST]       | e.g., Software Dev Unit [SST]     | e.g., 2024-11-01 [SST]        | [SST]     |
        | ...                | ...                                 | ...                               | ...                           |           |
    *   Discuss the significance or potential gaps based on the presence or absence of key certifications (especially {required_certs_focus or 'standard ones like ISO 9001/27001'}) [SSX, SSY, SSU].

### 5.2 Regulatory Compliance Statements
    *   **Data Privacy:** Summarize vendor's statements on compliance with major data privacy regulations (e.g., "States GDPR compliant processes [SSX]", "Mentions CCPA adherence [SSY]"). Note where data is processed/stored if mentioned [SSZ].
    *   **Environmental Regulations:** Mention adherence to specific environmental regulations if claimed (e.g., "RoHS compliant products [SSW]", "REACH declaration available [SSV]").
    *   **Industry-Specific Regulations:** Report compliance statements related to industry-specific regulations (e.g., "Adheres to HIPAA for healthcare data [SSU]", "Compliant with financial regulation XYZ [SST]"). {industry_focus_instruction}
    *   **Other Key Areas:** Note compliance statements regarding Anti-Bribery/Corruption policies [SSR], Export Controls [SSQ], etc.

### 5.3 Environmental, Social, Governance (ESG) Reporting
    *   Does Vendor '{identifier}' publish a dedicated ESG, Sustainability, or CSR report [SSX]? If yes, specify the latest year available and the reporting framework claimed (e.g., GRI Standards [SSY], SASB [SSZ], TCFD [SSW]).
    *   Highlight key ESG goals, targets, or achievements mentioned in the report relevant to compliance or risk (e.g., Carbon reduction target [SSV], Water usage reduction [SSU], Diversity & Inclusion metrics [SST]). Cite sources.
    *   Note any significant ESG-related controversies or poor ratings from reputable sources, if found and grounded [SSR].

### 5.4 Health & Safety (OHS) Approach
    *   Describe the vendor's stated approach to Occupational Health and Safety [SSX]. Is ISO 45001 or a similar framework mentioned [SSV]?
    *   Report any available OHS metrics (e.g., Lost Time Injury Rate - LTIR) if publicly disclosed [SSY]. Note trends if available.

### 5.5 Ethical Sourcing & Labor Practices
    *   Summarize the vendor's stated policies or commitments regarding ethical sourcing (e.g., conflict minerals policy [SSX]) and labor practices (e.g., adherence to ILO standards [SSY], supplier code of conduct addressing labor [SSZ]).
    *   Mention specific certifications like SA8000 if held [SSW].

{instructions['final_review']}
{instructions['final_source_list']}
"""
    return prompt

def get_vendor_management_strategy_prompt(identifier: str, language: str, context_company_name: str, **optional_inputs) -> str:
    """Generates the prompt for vendor management and strategy analysis."""
    instructions = _format_all_instructions(identifier, context_company_name)

    prompt = f"""
**CRITICAL FOCUS:** Research *exclusively* the specific vendor: **'{identifier}'**. Verify identity rigorously.

**Objective:** Understand the Vendor '{identifier}'s strategic direction, priorities, and management philosophy, focusing on aspects impacting long-term stability, reliability, quality focus, and innovation relevant to the products/services supplied to '{context_company_name}'.

**Target Audience:** {instructions['audience_reminder']} (Focus on long-term reliability, innovation pipeline)

**Output Language:** English

**Research Requirements:** Use vendor's Annual/Integrated Reports (CEO message, Strategy), Investor Relations materials (MTP), official website (About Us, Strategy), Press Releases. Ground every claim with [SSX].
{instructions['handling_missing']}
{instructions['research_depth']} # Focus on Strategy sections, IR materials
{instructions['specificity']} # Strategic goals, investment figures, timelines
{instructions['inline_citation']}
{instructions['analysis_synthesis']} # Implications of strategy for supplier reliability
{instructions['additional_refined']}

{instructions['base_formatting']}

## 6. Management & Strategy (Vendor: {identifier})

### 6.1 Overall Strategic Direction & Vision
    *   Summarize Vendor '{identifier}'s stated mission, vision, or core strategic pillars as they relate to its business operations and market positioning (e.g., "Focus on technology leadership in X [SSX]", "Aiming for operational excellence and cost efficiency [SSY]", "Strategy emphasizes long-term customer partnerships [SSZ]"). Cite sources.
    *   Comment on how this strategy potentially impacts their reliability or suitability as a supplier for '{context_company_name}'.

### 6.2 Mid-Term Plan (MTP) / Key Strategic Goals (if available)
    *   Identify key strategic goals or targets outlined in the vendor's recent Mid-Term Plan or strategic updates, focusing on areas relevant to supply (use bullet points) [SSX]. Include quantitative targets and timelines if stated:
        *   e.g., Invest $X million in expanding production capacity for Product Y by 2026 [SSY].
        *   e.g., Launch Z new products/features in the {optional_inputs.get('product_category', 'relevant')} category within 3 years [SSZ].
        *   e.g., Achieve X% improvement in quality metric (e.g., defect rate) by FY2025 [SSW].
        *   e.g., Increase R&D spending to Y% of revenue [SSV].
        *   e.g., Enhance supply chain resilience through supplier diversification initiative [SSU].
        *   e.g., Digital transformation project targeting Z% efficiency gain [SST].

### 6.3 Investment Priorities (CapEx & R&D)
    *   Detail stated areas of significant capital expenditure (CapEx) related to operations, capacity, or technology upgrades [SSX]. Include figures/timelines if available.
    *   Describe the vendor's stated Research & Development (R&D) focus areas, particularly those relevant to the products/services they offer [SSY]. How much do they state they invest in R&D (absolute value or % of revenue) [SSZ]?
    *   Analyze if investment levels appear adequate to support stated goals and maintain competitiveness [SSW].

### 6.4 Operational Philosophy & Improvement Initiatives
    *   Describe any stated operational philosophies or methodologies the vendor emphasizes (e.g., "Commitment to Lean manufacturing principles [SSX]", "Utilizes Agile development for software services [SSY]", "Focus on continuous improvement via Kaizen [SSZ]"). Cite sources.
    *   Report on specific, major operational improvement programs mentioned recently (e.g., "Ongoing Six Sigma quality program [SSW]", "Implementing new ERP system for efficiency [SSV]"). Cite sources.

### 6.5 Approach to Innovation
    *   How does Vendor '{identifier}' describe its innovation process or strategy for developing new products/services or improving existing ones [SSX]? Is it portrayed as customer-driven, technology-led, etc.?
    *   Mention any key partnerships or acquisitions aimed at boosting innovation capabilities [SSY].

### 6.6 Management Team & Stability
    *   List key executives (CEO, COO, CFO, Head of relevant Division if applicable) with their tenure if available [SSX].
    *   Note any significant changes in senior leadership (C-suite level) within the last 1-2 years, if verifiable from official sources [SSY]. Frequent turnover could indicate instability.

{instructions['final_review']}
{instructions['final_source_list']}
"""
    return prompt

def get_vendor_competitive_position_prompt(identifier: str, language: str, context_company_name: str, **optional_inputs) -> str:
    """Generates the prompt for analyzing vendor's competitive position."""
    instructions = _format_all_instructions(identifier, context_company_name)
    product_category = optional_inputs.get('product_category', 'their core offerings')

    prompt = f"""
**CRITICAL FOCUS:** Research *exclusively* the specific vendor: **'{identifier}'**. Verify identity rigorously.

**Objective:** Assess Vendor '{identifier}'s standing relative to other similar vendors in the specific market for **'{product_category}'**, understanding their strengths and weaknesses as a potential supplier to '{context_company_name}'.

**Target Audience:** {instructions['audience_reminder']} (Focus on supplier choice justification, differentiation)

**Output Language:** English

**Research Requirements:** Use vendor's materials, Annual Reports (competition section), grounded industry reports/news. Ground claims with [SSX]. Use **perfect Markdown tables** for competitors. Be cautious with competitor data unless grounded.
{instructions['handling_missing']}
{instructions['research_depth']} # Include industry reports if grounded
{instructions['specificity']} # Market segment, USPs
{instructions['inline_citation']}
{instructions['analysis_synthesis']} # Comparative analysis vs competitors
{instructions['additional_refined']}

{instructions['base_formatting']} # Enforces perfect tables

## 7. Competitive Positioning (as Vendor) (Vendor: {identifier})

### 7.1 Market Definition & Vendor's Role
    *   Briefly define the specific market segment where Vendor '{identifier}' primarily competes, especially concerning '{product_category}' [SSX].
    *   Describe the vendor's stated or perceived role within this market (e.g., "Positions itself as a premium provider [SSY]", "Focuses on the mid-market segment [SSZ]", "Known as an innovator in niche X [SSW]"). Cite sources.

### 7.2 Key Competitors / Alternative Suppliers
    *   Identify 2-4 key direct competitors offering similar products/services to Vendor '{identifier}' in the '{product_category}' space, based on vendor statements or grounded industry sources [SSX]. Use a **perfectly formatted Markdown table**.
        | Competitor Name        | Relevant Offering/Focus         | Stated/Perceived Positioning | Source(s) |
        |------------------------|---------------------------------|------------------------------|-----------|
        | e.g., Competitor Alpha | e.g., Similar Product Line Y    | e.g., Market Leader (Grounded)| [SSX, SSY]|
        | e.g., Competitor Beta  | e.g., Lower-cost alternative    | e.g., Focus on SMBs          | [SSZ]     |
        | e.g., Competitor Gamma | e.g., Stronger in Region Z      | e.g., Regional Specialist    | [SSW]     |
        | ...                    | ...                             | ...                          |           |

### 7.3 Market Share & Positioning (if available)
    *   Report any verifiable market share data for Vendor '{identifier}' in the defined market segment (e.g., "Holds X% market share in Segment Y according to Report Z [SSX]"). Specify source and date.
    *   Summarize qualitative positioning based on grounded third-party sources if available (e.g., "Ranked as a 'Leader' in Gartner MQ for X [SSY]", "Cited as 'Top 3 provider' by Industry Report ABC [SSZ]"). Specify source and date. Be precise about what is being ranked.

### 7.4 Vendor's Stated Strengths / USPs (as a Supplier)
    *   List the Unique Selling Propositions (USPs) or key strengths Vendor '{identifier}' emphasizes for its offerings or capabilities relevant to being a supplier (use bullet points) [SSX]:
        *   e.g., Superior product performance/quality metrics [SSY] (provide specific examples if cited).
        *   e.g., Proprietary technology or unique features [SSZ] (name them).
        *   e.g., Strong customer support / service levels [SSW].
        *   e.g., Customization capabilities [SSV].
        *   e.g., Reliability / proven track record [SSU].
        *   e.g., Competitive pricing (if explicitly claimed as a strength) [SST].
        *   e.g., Strong compliance / certifications portfolio [SSR].

### 7.5 Potential Weaknesses / Competitive Challenges (as a Supplier)
    *   Identify potential weaknesses or challenges for Vendor '{identifier}' compared to competitors, based on analysis or explicit statements in grounded sources (use bullet points) [SSX]:
        *   e.g., Smaller scale or more limited resources than key competitors [SSY].
        *   e.g., Geographic limitations in service or support coverage [SSZ].
        *   e.g., Perceived gaps in product portfolio compared to Competitor Alpha [SSW].
        *   e.g., Reliance on older technology stack in certain areas (if mentioned) [SSV].
        *   e.g., Higher price point than some alternatives [SSU].
        *   e.g., Less brand recognition than market leaders [SST].
        *   e.g., Known dependencies (e.g., single-source components, specific cloud provider) if mentioned as a risk [SSR].

### 7.6 Pricing Tier & Model (Inferred/Stated)
    *   Based on the vendor's positioning, features, target market, and competitive landscape, infer the likely pricing tier (e.g., Premium, Mid-Range, Value/Budget) [SSX]. State if this is inferred.
    *   Report the typical pricing models used by the vendor for relevant offerings, if stated (e.g., Subscription-based (SaaS) [SSY], Perpetual license + maintenance [SSZ], Usage-based [SSW], Per-unit hardware sales [SSV]). Cite sources.

{instructions['final_review']}
{instructions['final_source_list']}
"""
    return prompt

def get_vendor_digital_transformation_prompt(identifier: str, language: str, context_company_name: str, **optional_inputs) -> str:
    """Generates the prompt for analyzing vendor's digital capabilities and security."""
    instructions = _format_all_instructions(identifier, context_company_name)

    prompt = f"""
**CRITICAL FOCUS:** Research *exclusively* the specific vendor: **'{identifier}'**. Verify identity rigorously.

**Objective:** Understand how Vendor '{identifier}' utilizes digital technology internally for efficiency, quality, and security, and assess their cybersecurity posture, focusing on impacts to their capabilities and risk profile as a supplier to '{context_company_name}'.

**Target Audience:** {instructions['audience_reminder']} (Focus on supplier efficiency, security risks, integration capability)

**Output Language:** English

**Research Requirements:** Use vendor's website (Technology, Security, Trust Center), Annual Reports (IT strategy, risks), ESG reports, Press Releases on tech implementations. Ground claims with [SSX].
{instructions['handling_missing']}
{instructions['research_depth']} # Focus on Tech/Security/Trust sections
{instructions['specificity']} # Specific technologies, security frameworks
{instructions['inline_citation']}
{instructions['analysis_synthesis']} # Impact of DX, assessment of security posture
{instructions['additional_refined']} # Verify security claims, certifications

{instructions['base_formatting']}

## 8. Digital Capabilities & Security (Vendor: {identifier})

### 8.1 Internal Digital Transformation (DX) Initiatives
    *   Describe any stated initiatives focused on digitizing Vendor '{identifier}'s own operations (use bullet points) [SSX]:
        *   e.g., Implementation of a new ERP system (specify system and goal if mentioned, e.g., SAP S/4HANA for process integration) [SSY].
        *   e.g., Use of RPA/Automation for back-office processes (e.g., finance, HR) [SSZ].
        *   e.g., Development of 'Smart Factory' initiatives using IoT and analytics [SSW].
        *   e.g., Rollout of digital supply chain visibility platform [SSV].
    *   Analyze how these initiatives might enhance the vendor's efficiency, quality control, or responsiveness as a supplier [SSX, SSY, SSZ].

### 8.2 Technology in Core Operations
    *   Detail specific digital technologies Vendor '{identifier}' highlights using in its production, service delivery, or R&D processes (beyond general DX initiatives) [SSX]:
        *   e.g., Use of advanced analytics or AI/ML for quality control or predictive maintenance [SSY].
        *   e.g., Specific operational software platforms mentioned (e.g., MES, PLM systems) [SSZ].
        *   e.g., IoT sensors for monitoring equipment or environmental conditions [SSW].
        *   e.g., Cloud platforms utilized for service delivery (e.g., AWS, Azure, GCP) [SSV].

### 8.3 Cybersecurity Posture & Practices (Vendor-Side)
    *   Summarize Vendor '{identifier}'s stated approach to cybersecurity for its own internal systems and operations [SSX].
    *   Mention specific security frameworks or standards they claim to align with or follow internally (e.g., "Aligns with NIST Cybersecurity Framework [SSY]", "Internal processes follow ISO 27001 guidelines [SSZ]").
    *   Report on specific security practices mentioned (e.g., "Conducts regular vulnerability scanning [SSW]", "Employs multi-factor authentication (MFA) internally [SSV]", "Has an incident response plan [SSU]").
    *   Note if they mention regular third-party security audits or penetration tests of their own systems [SST].
    *   List relevant security certifications held (e.g., ISO 27001 - re-confirm from Sec 5) [SSY].

### 8.4 Data Handling & Privacy Practices (if Vendor Processes '{context_company_name}' Data)
    *   If Vendor '{identifier}' is a SaaS provider or processes sensitive data, describe their stated data protection measures (e.g., "Data encryption at rest and in transit [SSX]", "Access controls based on role [SSY]"). Cite sources.
    *   Report any statements regarding data residency or data processing locations [SSZ].
    *   Reiterate key data privacy compliance statements (e.g., GDPR, CCPA - confirm from Sec 5) [SSW].

### 8.5 System Integration Capabilities
    *   Comment on the vendor's apparent capability for technical integration with customer systems. Do they mention:
        *   Availability of APIs (Application Programming Interfaces) for their products/services [SSX]? Specify if standard (e.g., RESTful) or proprietary.
        *   Support for standard data exchange formats (e.g., EDI, XML, JSON) [SSY]?
        *   Partnerships with integration platform providers (e.g., MuleSoft, Boomi) [SSZ]?
    *   Assess the potential ease or difficulty of integrating with Vendor '{identifier}' based on these points [SSX, SSY, SSZ].

{instructions['final_review']}
{instructions['final_source_list']}
"""
    return prompt

def get_vendor_crisis_continuity_prompt(identifier: str, language: str, context_company_name: str, **optional_inputs) -> str:
    """Generates the prompt for analyzing vendor's operational resilience and continuity."""
    instructions = _format_all_instructions(identifier, context_company_name)

    prompt = f"""
**CRITICAL FOCUS:** Research *exclusively* the specific vendor: **'{identifier}'**. Verify identity rigorously.

**Objective:** Assess Vendor '{identifier}'s preparedness for and history of handling operational disruptions (e.g., system outages, physical disasters, supply chain issues, security incidents impacting operations) that could affect their ability to supply '{context_company_name}'.

**Target Audience:** {instructions['audience_reminder']} (Focus on supply continuity risk, vendor resilience)

**Output Language:** English

**Research Requirements:** Use vendor's website (BCP statements, Trust Center), Annual Reports (Risk Factors, Operations), Press Releases on incidents/recovery, grounded news reports. Ground claims with [SSX].
{instructions['handling_missing']}
{instructions['research_depth']} # Look for BCP/DR info, incident reports
{instructions['specificity']} # Incident dates, impact, RTO/RPO if stated
{instructions['inline_citation']}
{instructions['analysis_synthesis']} # Assessment of preparedness and track record
{instructions['additional_refined']} # Verify incident details

{instructions['base_formatting']}

## 9. Operational Resilience & Continuity (Vendor: {identifier})

### 9.1 Business Continuity Planning (BCP) Stance
    *   Does Vendor '{identifier}' publicly state that it maintains a Business Continuity Plan (BCP) [SSX]?
    *   Describe any key elements of their BCP approach mentioned (use bullet points if details are available):
        *   e.g., Regular BCP testing or drills mentioned [SSY]? Frequency?
        *   e.g., Stated Recovery Time Objectives (RTOs) for critical systems/services [SSZ]? Specify if possible.
        *   e.g., Stated Recovery Point Objectives (RPOs) for data [SSW]? Specify if possible.
        *   e.g., Use of alternative work sites or remote work capabilities for staff [SSV]?
        *   e.g., Existence of a crisis management team structure [SSU]?
    *   Assess the apparent maturity or comprehensiveness of their stated BCP based on available details [SSX, SSY, SSZ]. Lack of public detail can be a risk indicator.

### 9.2 Disaster Recovery (DR) Capabilities (IT Context)
    *   Describe any specific Disaster Recovery (DR) capabilities mentioned for IT systems or data [SSX].
    *   Is infrastructure redundancy mentioned (e.g., "Operates multiple data centers in different geographic regions [SSY]", "Utilizes cloud provider availability zones [SSZ]")?
    *   Are data backup strategies described (e.g., "Regular backups to offsite location [SSW]", "Point-in-time recovery capabilities [SSV]")?

### 9.3 History of Significant Operational Incidents (Last 3-5 Years)
    *   Detail any significant operational disruptions impacting Vendor '{identifier}' or its customers, based on verifiable sources (use bullet points per incident) [SSX]:
        *   **Incident Type & Date:** (e.g., Major Factory Fire [SSY], Prolonged Cloud Service Outage [SSZ], Ransomware Attack impacting Operations [SSW], Key Supplier Failure [SSV]) - Include approximate date (Month/Year or Quarter/Year).
        *   **Impact Description:** (e.g., Production halted for X weeks [SSY], Service unavailable for Y hours affecting Z customers [SSZ], Data access issues reported [SSW], Component shortage delayed product delivery [SSV]). Be specific about impact on supply if known.
        *   **Vendor Response/Recovery:** (e.g., Switched production to alternate site [SSY], Restored service after Y hours [SSZ], Worked with cybersecurity firm [SSW], Secured alternative supplier [SSV]). Mention recovery time if stated.
        *   **Stated Remediation/Lessons Learned:** (e.g., Implemented enhanced fire safety measures [SSY], Improved infrastructure monitoring [SSZ], Strengthened security controls [SSW], Diversified supplier base [SSV]).
    *   Analyze the vendor's apparent track record in handling and recovering from disruptions based on these incidents [SSX, SSY, SSZ, SSW, SSV].

### 9.4 Supply Chain Resilience (Vendor's Own Chain)
    *   Summarize any statements or initiatives Vendor '{identifier}' has mentioned regarding managing risks and resilience within its *own* upstream supply chain [SSX].
        *   e.g., Supplier diversification efforts [SSY].
        *   e.g., Geographic risk mitigation for sourcing [SSZ].
        *   e.g., Enhanced supplier monitoring or collaboration [SSW].
        *   e.g., Inventory strategies for critical components (e.g., safety stock) [SSV].
    *   Assess how proactive the vendor appears to be in managing its own supply chain risks based on these statements [SSX, SSY, SSZ].

### 9.5 Insurance Coverage (if mentioned)
    *   Note any mention of relevant insurance coverage held by the vendor, such as Business Interruption insurance [SSX] or Cyber Liability insurance [SSY]. (Acknowledge this is often not public).

{instructions['final_review']}
{instructions['final_source_list']}
"""
    return prompt

def get_vendor_risk_assessment_prompt(identifier: str, language: str, context_company_name: str, **optional_inputs) -> str:
    """Generates the prompt for a consolidated vendor risk assessment."""
    instructions = _format_all_instructions(identifier, context_company_name)
    required_certs = optional_inputs.get('required_certs', 'key requirements')

    prompt = f"""
**CRITICAL FOCUS:** Research *exclusively* the specific vendor: **'{identifier}'**. Verify identity rigorously.

**Objective:** Synthesize potential risks identified across previous sections (Financials, Operations, Compliance, Security, Resilience) for Vendor '{identifier}' into a consolidated overview, evaluating key threats relevant to '{context_company_name}'.

**Target Audience:** {instructions['audience_reminder']} (Focus on overall risk profile for decision making)

**Output Language:** English

**Research Requirements:** This section synthesizes findings from Sections 3, 4, 5, 8, 9. Ground every summarized risk factor by referencing the original finding with its citation (e.g., "High leverage [SSX from Sec3]"). Assign a risk level (Low, Moderate, High) to each category based *only* on the synthesized, grounded evidence.
{instructions['handling_missing']} # Applies to sourcing original findings
{instructions['research_depth']} # Relies on previous sections' depth
{instructions['specificity']} # Referencing specific issues
{instructions['inline_citation']} # Cite the source of the original finding
{instructions['analysis_synthesis']} # CRITICAL: Synthesize and assess risk levels
{instructions['additional_refined']}

{instructions['base_formatting']}

## 10. Consolidated Risk Assessment (Vendor: {identifier})

*This assessment synthesizes findings from previous sections. Citations may refer back to evidence presented earlier.*

### 10.1 Financial Risk Summary
    *   **Key Risk Factors:**
        *   e.g., High Debt-to-Equity ratio of X.Y in FYZZZZ [SSX from Sec3].
        *   e.g., Trend of declining Operating Margins over last 3 years [SSY from Sec3].
        *   e.g., Negative Net Cash from Operations reported in FYZZZZ [SSZ from Sec3].
        *   e.g., Recent credit rating downgrade by Agency ABC [SSW from Sec3].
        *   e.g., Dependence on a specific declining market segment mentioned in financials [SSV from Sec3].
    *   **Mitigating Factors:**
        *   e.g., Consistent revenue growth noted [SSU from Sec3].
        *   e.g., Strong Current Ratio above Z.0 [SST from Sec3].
    *   **Overall Financial Risk Assessment:** (Low / Moderate / High) - Justify based on the balance of factors above.

### 10.2 Operational Risk Summary
    *   **Key Risk Factors:**
        *   e.g., High geographic concentration with X% of production at single site in Location Y [SSX from Sec4].
        *   e.g., Stated capacity constraints for Product Z mentioned [SSY from Sec4].
        *   e.g., History of significant service disruptions in Year A and Year B [SSZ from Sec9].
        *   e.g., Limited public information available on BCP/DR testing procedures [SSW from Sec9].
        *   e.g., Mentioned reliance on single-source supplier for critical component ABC [SSV from Sec4].
    *   **Mitigating Factors:**
        *   e.g., Recent investment in new production facility announced [SSU from Sec4].
        *   e.g., ISO 9001 certification held [SST from Sec5].
        *   e.g., Stated dual-sourcing strategy for some materials [SSR from Sec4/Sec9].
    *   **Overall Operational Risk Assessment:** (Low / Moderate / High) - Justify based on the balance of factors above.

### 10.3 Compliance & Regulatory Risk Summary
    *   **Key Risk Factors:**
        *   e.g., Lacks required certification: '{required_certs}' [SSX from Sec5].
        *   e.g., Operates in jurisdictions known for high regulatory scrutiny (specify) [SSY from Sec1/Sec5].
        *   e.g., History of environmental fines in Year C [SSZ from Sec5/News].
        *   e.g., Vague statements regarding GDPR compliance [SSW from Sec5].
        *   e.g., Poor ESG rating from Source XYZ noted [SSV from Sec5].
    *   **Mitigating Factors:**
        *   e.g., Holds key certifications like ISO 9001, ISO 14001 [SSU from Sec5].
        *   e.g., Publishes detailed annual ESG report following GRI standards [SST from Sec5].
        *   e.g., Strong stated anti-bribery policies [SSR from Sec5].
    *   **Overall Compliance Risk Assessment:** (Low / Moderate / High) - Justify based on the balance of factors above.

### 10.4 Security Risk Summary (Especially for Tech/Data Vendors)
    *   **Key Risk Factors:**
        *   e.g., Does not hold ISO 27001 certification or provide SOC 2 report [SSX from Sec5/Sec8].
        *   e.g., Limited public information on internal security practices/audits [SSY from Sec8].
        *   e.g., Experienced a ransomware incident impacting operations in Year D [SSZ from Sec9].
        *   e.g., Vague statements on data encryption or access controls [SSW from Sec8].
    *   **Mitigating Factors:**
        *   e.g., States alignment with NIST CSF [SSV from Sec8].
        *   e.g., Mentions regular penetration testing [SSU from Sec8].
        *   e.g., Positive track record since last incident [SST from Sec9].
    *   **Overall Security Risk Assessment:** (Low / Moderate / High) - Justify based on the balance of factors above.

### 10.5 Reputational Risk Summary
    *   **Key Risk Factors:**
        *   e.g., Significant negative press coverage regarding labor practices in Year E [SSX from News/Sec5].
        *   e.g., Involvement in major product quality controversy [SSY from News/Sec4].
        *   e.g., Association with environmentally damaging activities [SSZ from News/Sec5].
    *   **Mitigating Factors:**
        *   e.g., Strong corporate social responsibility programs highlighted [SSW from Sec5].
        *   e.g., Positive brand perception generally noted [SSV from Sec7].
    *   **Overall Reputational Risk Assessment:** (Low / Moderate / High) - Justify based on the balance of factors above.

### 10.6 Overall Risk Profile Summary
    *   Concisely summarize the most significant risk areas for Vendor '{identifier}' based on the assessments above (e.g., "Overall risk profile appears Moderate, primarily driven by concerns regarding financial stability [cite Sec 10.1] and operational resilience due to past incidents [cite Sec 10.2], while compliance appears adequate [cite Sec 10.3].").

{instructions['final_review']}
{instructions['final_source_list']}
"""
    return prompt

def get_vendor_suitability_summary_prompt(identifier: str, language: str, context_company_name: str, **optional_inputs) -> str:
    """Generates the prompt for the final vendor suitability summary."""
    instructions = _format_all_instructions(identifier, context_company_name)
    product_category = optional_inputs.get('product_category', 'requirements')
    required_certs = optional_inputs.get('required_certs', 'required certifications')

    prompt = f"""
**CRITICAL FOCUS:** Research *exclusively* the specific vendor: **'{identifier}'**. Verify identity rigorously.

**Objective:** Provide a final, balanced assessment of Vendor '{identifier}'s overall suitability as a potential supplier/partner for '{context_company_name}', summarizing strengths, weaknesses, risks, and alignment with potential needs for '{product_category}'.

**Target Audience:** {instructions['audience_reminder']} (Provides final recommendation/next steps)

**Output Language:** English

**Research Requirements:** This section synthesizes findings from ALL previous sections (1-10). Ground summarized points by referencing the original findings/sections with citations (e.g., "Strong product fit [SSX from Sec2]", "Financial risks identified [SSY from Sec10]"). Base recommendations solely on the synthesized evidence.
{instructions['handling_missing']} # Applies to sourcing original findings
{instructions['research_depth']} # Relies on previous sections' depth
{instructions['specificity']} # Aligning with specific needs
{instructions['inline_citation']} # Cite the source of the original finding
{instructions['analysis_synthesis']} # CRITICAL: Balanced assessment and recommendation
{instructions['additional_refined']}

{instructions['base_formatting']}

## 11. Vendor Suitability Summary (Vendor: {identifier})

### 11.1 Overall Assessment
    *   Provide a 1-2 sentence summary judgment based on the entire research (e.g., "Vendor '{identifier}' appears to be a potentially strong candidate for supplying '{product_category}' to '{context_company_name}', demonstrating relevant capabilities but carrying moderate financial risk.", OR "Vendor '{identifier}' presents significant risks (Operational, Compliance) and may not be suitable without further mitigation.").

### 11.2 Key Strengths (as a Supplier for '{context_company_name}')
    *   Summarize the most compelling strengths based on previous sections (use bullet points):
        *   e.g., Strong alignment of Product/Service X with '{product_category}' requirements [SSX from Sec2].
        *   e.g., Proven operational capabilities and scale relevant to needs [SSY from Sec4].
        *   e.g., Solid financial performance and stability trend observed [SSZ from Sec3].
        *   e.g., Holds all '{required_certs}' and demonstrates strong compliance posture [SSW from Sec5].
        *   e.g., Positive track record of innovation in relevant areas [SSV from Sec2/Sec6].
        *   e.g., Favorable competitive positioning or unique technology [SSU from Sec7].
        *   e.g., Mature BCP/DR processes suggested [SST from Sec9].

### 11.3 Key Weaknesses / Concerns (as a Supplier for '{context_company_name}')
    *   Summarize the most significant weaknesses or concerns based on previous sections (use bullet points):
        *   e.g., Identified financial stability concerns (e.g., high debt, low liquidity) [SSX from Sec3/Sec10].
        *   e.g., Operational risks due to facility concentration or past disruptions [SSY from Sec4/Sec9/Sec10].
        *   e.g., Missing key certification '{required_certs}' or other compliance gaps [SSZ from Sec5/Sec10].
        *   e.g., Potential security vulnerabilities or lack of transparency [SSW from Sec8/Sec10].
        *   e.g., Limited evidence of robust BCP/DR planning or testing [SSV from Sec9/Sec10].
        *   e.g., Higher inferred price point compared to alternatives [SSU from Sec7].
        *   e.g., Concerns regarding management stability or strategic focus [SST from Sec6].
        *   e.g., Potential reputational risks identified [SSR from Sec10].

### 11.4 Alignment with '{context_company_name}' Needs
    *   Explicitly comment on the degree of alignment between Vendor '{identifier}'s offerings [Sec 2], capabilities [Sec 4], compliance status [Sec 5], and security posture [Sec 8] with the likely requirements of '{context_company_name}', specifically mentioning '{product_category}' and '{required_certs}'. Is there a good fit? Are there critical gaps?

### 11.5 Consolidated Risk View Recap
    *   Briefly reiterate the overall risk profile assessment from Section 10.6 (e.g., "Overall risk assessed as Moderate, primarily driven by operational factors.").

### 11.6 Recommendations / Next Steps (for '{context_company_name}')
    *   Based ONLY on the assessment above, suggest logical next steps for '{context_company_name}' regarding Vendor '{identifier}'. Be specific:
        *   e.g., "Recommend proceeding to Request for Information (RFI) / Request for Proposal (RFP)."
        *   e.g., "Recommend further due diligence focused specifically on [e.g., Financial Stability, BCP Validation, Security Audit results]."
        *   e.g., "Suggest engaging vendor in direct discussion regarding [e.g., specific compliance gaps, BCP details, pricing structure]."
        *   e.g., "Consider a limited pilot project or proof-of-concept to validate capabilities and integration."
        *   e.g., "Recommend exploring alternative vendors due to identified risks [specify key risks]."
        *   e.g., "Place vendor on 'Approved - Monitor Risks' list, conditional upon [e.g., providing missing certification]."
        *   e.g., "Recommend rejecting vendor based on significant misalignment or high unmitigated risks."

{instructions['final_review']}
{instructions['final_source_list']}
"""
    return prompt