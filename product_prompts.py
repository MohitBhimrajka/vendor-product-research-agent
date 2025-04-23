# product_prompts.py

import textwrap
from typing import Optional, Dict, Any, List

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
    """Prompt to identify potential vendors for the product category."""
    region_focus = optional_inputs.get('region')
    focus_instruction = f"Consider vendors with a known presence or focus in: **'{region_focus}'** if possible, alongside global leaders." if region_focus else "Identify globally recognized and potentially significant regional vendors."

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
**CRITICAL FOCUS:** Identify vendors offering solutions in the product category: **'{identifier}'**.

**Objective:** Identify a list of significant vendors (aim for 5-10 if possible, but prioritize accuracy) that offer products or services within the '{identifier}' category, based on grounded sources. {focus_instruction}

**Target Audience:** {formatted_audience_reminder}

**Output Language:** English

**Research Requirements:** Use grounded sources like analyst reports (e.g., Gartner MQ, Forrester Wave vendor lists), reputable market share reports, industry directories, competitor lists mentioned by known players. Ground every identified vendor with [SSX]. Provide full official vendor names.
{formatted_handling_missing}
{formatted_research_depth}
{formatted_specificity}
{formatted_inline_citation}
{formatted_additional_instructions}

{formatted_base_formatting}

## 5. Preliminary Vendor Identification: {identifier}

### 5.1 Identified Vendors
    *   List the vendors identified as key players or significant providers in the '{identifier}' market. Present in a **perfectly formatted Markdown table**. Include Vendor Name, a brief note on their relevance/specialty within '{identifier}' if known, and the source(s) confirming their participation in this market.
        | Vendor Name                  | Relevance/Specialty in '{identifier}' (Brief Note) | Source(s) Identifying Vendor |
        |------------------------------|----------------------------------------------------|------------------------------|
        | [Vendor A Full Name]         | Market Leader / Broad Suite Provider               | [SSX], [SSY]                 |
        | [Vendor B Full Name]         | Specialist in Sub-Category X / Niche Player        | [SSZ]                        |
        | [Vendor C Full Name]         | Strong presence in '{region_focus or 'Region Y'}'          | [SSW]                        |
        | [Vendor D Full Name]         | Known for Innovation / Specific Technology         | [SSX], [SSV]                 |
        | ... (Aim for 5-10 verified)  | ...                                                | ...                          |
    *   Ensure vendor names are the official legal names where possible [SSX].

### 5.2 Notes on Vendor Landscape
    *   Briefly comment on the apparent concentration of the vendor landscape (e.g., dominated by a few large players, fragmented with many niche vendors) based on the findings [SSX].
    *   Mention any major vendor categories observed (e.g., large suite providers vs. best-of-breed specialists) [SSY].

{formatted_final_review}
{formatted_final_source_list}
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
4.  **Output Format:** Provide *only* the filtered list of vendor names, one name per line. Do NOT include any explanation, introductory text, or justifications. Just the names that remain after filtering. If no vendors seem like a strong match, output the text "NO_MATCHING_VENDORS".

**Filtered Vendor List (One vendor name per line):**
"""
    return prompt


# --- Prompts for Phase 4 onwards (Vendor Profiles, Comparison, Relevance etc.) ---
# --- These will be defined in Phase 4 ---

# Placeholder for profile prompt
def get_vendor_light_profiles_prompt(identifier: str, language: str, context_company_name: str, **optional_inputs) -> str:
     return f"Placeholder prompt for generating light profiles for vendors in category '{identifier}'."

# Placeholder for comparison prompt
def get_vendor_comparison_matrix_prompt(identifier: str, language: str, context_company_name: str, **optional_inputs) -> str:
     return f"Placeholder prompt for generating comparison matrix for vendors in category '{identifier}'."

# Placeholder for relevance prompt
def get_product_relevance_prompt(identifier: str, language: str, context_company_name: str, **optional_inputs) -> str:
     return f"Placeholder prompt for analyzing relevance of '{identifier}' for {context_company_name}."