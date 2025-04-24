# Vendor & Product Research AI Agent

This Streamlit application leverages Google's Gemini API to perform two distinct types of research:
1.  **Deep Vendor Research:** Generates a comprehensive analysis of a specific vendor, focusing on their capabilities, financial stability, operational resilience, compliance posture, and overall suitability as a supplier or partner.
2.  **Product & Market Landscape Research:** Analyzes a specified product category, identifies leading vendors, allows interactive filtering based on user needs, generates comparative vendor profiles, and assesses market relevance. Optionally performs deep dives on selected vendors.

The agent uses grounding via Google Search to enhance factual accuracy and provides citations for generated claims. Reports are generated in Markdown and compiled into a professional PDF format.

## Features

*   **Dual Research Modes:**
    *   **Vendor Mode:** In-depth analysis of a single vendor.
    *   **Product Mode:** Market analysis, vendor identification, interactive filtering, comparison, and optional deep dives.
*   **Enhanced UI/UX:** Modern, intuitive interface with visual cards, progress indicators, and clear navigation.
*   **Comprehensive Sections:** Covers aspects like basic info, product details, financials (stability focus), operations, compliance, risk, strategy, competitive positioning, and suitability.
*   **Interactive Filtering (Product Mode):** Uses LLM-generated questions and natural language understanding to refine vendor lists based on user criteria.
*   **Grounded Information:** Utilizes Google Search grounding for enhanced factuality.
*   **Inline Citations:** Provides citations (`[SSX]`) linked to a final Sources list using Vertex AI Search grounding URLs.
*   **Structured Output:** Generates organized Markdown files for each section.
*   **Professional PDF Reports:** Compiles findings into a styled PDF with cover page, table of contents, and section covers.
*   **Dashboard Summary:** Visual dashboard with key metrics and insights extracted from the report.
*   **Real-time Status Tracking:** Detailed progress indicators showing completion status of each section.
*   **Multi-phase Workflow:** Interactive wizard-like interface guiding users through the entire research process.
*   **Parallel Processing:** Generates report sections concurrently for faster results.

## Project Structure

```
└── vendor-product-research-agent/
    ├── app.py                      # Main Streamlit application
    ├── report_orchestrator.py      # Handles LLM calls, workflow logic, parallel execution
    ├── config.py                   # Configuration (LLM, sections, PDF)
    ├── vendor_prompts.py           # Prompts & base instructions for Vendor Mode
    ├── product_prompts.py          # Prompts & base instructions for Product Mode
    ├── pdf_generator.py            # Core PDF generation logic (Markdown -> HTML -> PDF)
    ├── requirements.txt            # Python dependencies
    ├── .env.example                # Example environment variables file
    ├── render.yaml                 # Deployment configuration for Render.com
    ├── ui/                         # UI components and helper functions
    │   ├── forms.py                # Input forms for vendor and product research
    │   ├── helpers.py              # UI helper functions and components
    │   └── states.py               # Application state management
    ├── services/                   # Service layer
    │   ├── vendor.py               # Vendor research service
    │   └── product.py              # Product research service
    └── templates/
        ├── enhanced_report_template.html # Jinja2/HTML template for PDF
        └── assets/                  # Logo, favicon images
    └── static/                     # Static assets like logos
    └── output/                     # Default directory for generated reports (created on run)
```

## Setup

1.  **Clone Repository:**
    ```bash
    git clone <your-repository-url>
    cd vendor-product-research-agent
    ```
2.  **Create Virtual Environment:**
    ```bash
    python -m venv venv
    # On Windows: .\venv\Scripts\activate
    # On macOS/Linux: source venv/bin/activate
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Environment Variables:**
    *   Copy `.env.example` to `.env`.
    *   Edit `.env` and add your `GEMINI_API_KEY`.
    *   Optionally, uncomment and set `LLM_MODEL` or `LLM_TEMPERATURE` to override defaults in `config.py`.

## Usage

1.  **Run the Streamlit App:**
    ```bash
    streamlit run app.py
    ```
2.  **Open in Browser:** The application should open automatically, or navigate to the URL provided (usually `http://localhost:8501`).
3.  **Configure Research:**
    *   Select the **Research Mode** ("Vendor Research" or "Product Research").
    *   Enter **Your Company Name (Context)**.
    *   Enter the required **Vendor Name** or **Product/Service Category**.
    *   Fill in any **Optional Filters** (e.g., Required Certs, Region).
4.  **Start Research:** Click the appropriate button to begin the research process.
5.  **Interactive Wizard:** Follow the step-by-step guide through the research phases.
    * **Vendor Research:** Watch the status indicators as the report is generated.
    * **Product Research:** 
        1. Initial analysis with status indicators
        2. Answer filtering questions to narrow down vendor selection
        3. Choose comparison criteria for selected vendors
        4. Optionally select vendors for deep dive analysis
        5. Generate the final comprehensive report
6.  **View Results:**
    *   Dashboard with key metrics and insights
    *   Tabbed report sections for easy navigation
    *   PDF download option for all reports
    *   Detailed statistics on token usage and processing time

## Output Structure

Generated reports are saved in the `output/` directory.

**Vendor Mode:**
```
output/
└── vendor_VENDORNAME_YYYYMMDD_HHMMSS/
    ├── markdown/                # Individual markdown files for each section
    │   ├── vendor_basic.md
    │   ├── vendor_financial_stability.md
    │   └── ...
    ├── pdf/                     # Generated PDF report
    │   └── VENDORNAME_VendorReport.pdf
    └── misc/                    # Metadata and summaries
        ├── generation_config.yaml
        ├── generation_summary.json
        └── dashboard_data.json
```

**Product Mode:**
```
output/
└── product_PRODUCTCATEGORY_YYYYMMDD_HHMMSS/
    ├── markdown/                # Markdown files for initial analysis, profiles, comparison etc.
    │   ├── product_definition.md
    │   ├── product_market_overview.md
    │   ├── ...
    │   ├── profile_VENDORA.md   # Example light profile
    │   ├── comparison_matrix.md
    │   └── ...
    ├── pdf/                     # Generated PDF report(s)
    │   └── PRODUCTCATEGORY_ProductReportFull.pdf # Example final combined PDF
    ├── misc/                    # Metadata and summaries
    │   ├── generation_config.yaml
    │   ├── generation_summary.json # Summary for initial run
    │   ├── generation_summary_phase2.json # Summary for profile/comparison run
    │   ├── filtered_vendors.txt    # List saved after filtering
    │   └── dashboard_data.json     # Final dashboard data
    └── deep_dives/              # Optional: Contains outputs from deep dive runs
        └── vendor_DEEPDIVEVENDOR_YYYYMMDD_HHMMSS/ # Separate full vendor report structure
            ├── markdown/
            ├── pdf/
            └── misc/
```

## Customization

*   **Prompts:** Modify prompt logic and instructions in `vendor_prompts.py` and `product_prompts.py`.
*   **Sections:** Adjust section lists and order in `config.py` (`VENDOR_SECTION_ORDER`, `PRODUCT_INITIAL_SECTION_ORDER`, `PRODUCT_FULL_SECTION_ORDER`). Ensure corresponding prompt functions exist and are mapped.
*   **PDF Styling:** Edit the CSS within `templates/enhanced_report_template.html`.
*   **UI Components:** Modify UI elements in the `ui/` directory files.
*   **LLM Parameters:** Change `LLM_MODEL` and `LLM_TEMPERATURE` in `config.py` or via the `.env` file.

## Deployment on Render

This project includes a `render.yaml` configuration for easy deployment on Render.com:

1. **Create a Render Account:**
   * Sign up at [render.com](https://render.com) if you don't have an account.

2. **Fork or Push the Repository:**
   * Ensure your code is in a Git repository (GitHub, GitLab, etc.).

3. **Create a New Web Service on Render:**
   * From the Render dashboard, click "New +" and select "Blueprint."
   * Connect your repository and select it.
   * Render will automatically detect the `render.yaml` configuration.

4. **Configure Environment Variables:**
   * Add your `GEMINI_API_KEY` as an environment variable.
   * Add any other custom environment variables if needed.

5. **Deploy the Service:**
   * Click "Create Blueprint" and wait for the deployment to complete.
   * Render will automatically build and deploy your application.

6. **Access Your Application:**
   * Once deployed, Render will provide a URL to access your application.
   * You can configure a custom domain in the Render dashboard if desired.

## Troubleshooting Render Deployment

* **Memory Issues:** If you encounter memory errors, you may need to upgrade your Render plan or optimize your application.
* **API Key Issues:** Ensure your `GEMINI_API_KEY` is correctly set in the environment variables.
* **Deployment Failures:** Check the build logs for errors. Common issues include missing dependencies or syntax errors.
* **Timeout Errors:** Long-running operations might exceed Render's timeout limits. Consider optimizing your code or upgrading your plan.

## License

Proprietary and confidential. Please do not distribute.