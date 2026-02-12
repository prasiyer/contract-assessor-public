"""HTML layout snippets and UI content constants."""

from __future__ import annotations

LANDING_HERO_COPY_HTML = """
<h1 class="landing-hero__title">Contracts, clarified in minutes.</h1>
<p class="landing-hero__subtitle">
    Bring every supplier agreement into a guided workspace that answers queries, shows quantitative metrics and evaluates a draft.
</p>
<ul class="landing-hero__highlights">
    <li><strong>Automated scoring</strong></li>
    <li><strong>Retrieval-augmented answers</strong></li>
    <li><strong>Portfolio metrics</strong></li>
</ul>
"""


LANDING_HERO_PANEL_HTML = """
<div class="landing-hero__panel-card">
    <h4>Review throughput</h4>
    <strong>45 parameters</strong>
    <p>Scored per draft with remediation guidance aligned to your sourcing rubric.</p>
</div>
<div class="landing-hero__panel-card">
    <h4>Grounded answers</h4>
    <strong>Top 5 relevant paragraphs</strong>
    <p>Retrieved per query so every recommendation is backed by contract precedent.</p>
</div>
<div class="landing-hero__panel-card">
    <h4>Contracts Scope</h4>
    <strong>104 vendors</strong>
    <p>Tracked across 12 categories with export-ready dashboard summaries.</p>
</div>
"""

LANDING_SECTION_VALUE_HTML = """
<section class="landing-section">
    <div class="landing-section__header">
        <h2>Enable contract review</h2>
        <p>Draft review and contract analytics in a single tool.</p>
    </div>
    <div class="landing-value-grid">
        <article class="landing-value-card">
            <h3>📝 Draft Reviewer</h3>
            <p>Upload a supplier draft to receive calibrated scoring, AI summaries, and remediation notes in minutes.</p>
            <ul>
                <li>Highlights parameters that fall below compliance targets.</li>
                <li>Generates an executive-friendly summary for quick sign-off.</li>
            </ul>
        </article>
        <article class="landing-value-card">
            <h3>💬 Query Assistant</h3>
            <p>Ask natural-language questions across executed agreements and get grounded answers instantly.</p>
            <ul>
                <li>Retrieval-augmented responses cite the most relevant contract excerpts.</li>
                <li>Vendor name matching keeps each answer anchored to the right counterparty.</li>
            </ul>
        </article>
        <article class="landing-value-card">
            <h3>📊 Metrics Dashboard</h3>
            <p>Explore trends by category, supplier, or parameter to understand risk and opportunity at a glance.</p>
            <ul>
                <li>Portfolio summaries reveal where negotiation leverage is strongest.</li>
                <li>Category deep-dives highlight systemic gaps before renewal season.</li>
            </ul>
        </article>
    </div>
</section>
"""

LANDING_PROCESS_HTML = """
<section class="landing-section landing-process">
    <div class="landing-process__header">
        <h2>The journey from upload to insight</h2>
        <p>Four guided steps bring transparency to every supplier contract.</p>
    </div>
    <ol class="landing-process__timeline">
        <li>
            <strong>Import a contract</strong>
            <span>Select a PDF draft, provide the vendor and category, and the workspace validates your inputs in seconds.</span>
        </li>
        <li>
            <strong>Process & score</strong>
            <span>The Draft Reviewer extracts clauses, scores 45 parameters, and prepares a remediation plan automatically.</span>
        </li>
        <li>
            <strong>Q&A Assistant</strong>
            <span>Use the Query Assistant to find answers to specific questions about contracts.</span>
        </li>
        <li>
            <strong>Review contract analytics</strong>
            <span>Dive into the Metrics Dashboard to see objective insights acrosscd C categories, vendors, and clauses.</span>
        </li>
    </ol>
</section>
"""

LANDING_KEY_FEATURES_HTML = """
<section class="landing-section">
    <div class="landing-section__header">
        <h2>Key features</h2>
        <p>Efficient retrieval of relevant information.</p>
    </div>
    <div class="landing-behind">
        <article class="landing-behind__card">
            <h4>Cached intelligence</h4>
            <p>Contract embeddings and supplier vectors are cached for fast retrieval, even across large portfolios.</p>
        </article>
        <article class="landing-behind__card">
            <h4>Process logs</h4>
            <p>All processing is logged to <code>Output/output_log.txt</code> with timestamps for compliance reviews.</p>
        </article>
        <article class="landing-behind__card">
            <h4>Configurable parameters</h4>
            <p>Model selections, file paths, and chart sources follow user settings.</p>
        </article>
    </div>
</section>
"""

DRAFT_SECTION_HEADER_HTML = """
<div class="workspace-section__header">
    <h2>Run a draft evaluation</h2>
    <p>Upload the supplier PDF to receive parameter scores, remediation guidance, and grounded summaries.</p>
</div>
"""

ASSISTANT_SECTION_HEADER_HTML = """
<div class="workspace-section__header">
    <h2>Chat with the contract assistant</h2>
    <p>Ask natural-language questions and receive cited answers drawn from executed agreements.</p>
</div>
"""

DASHBOARD_HERO_COPY_HTML = """
<h2 class="workspace-hero__title">Review Contracts</h2>
<p class="workspace-hero__subtitle">
    Investigate category, supplier, and parameter trends from a single set of visuals.
</p>
<ul class="workspace-hero__highlights">
    <li><strong>Summarized metrics </strong></li>
    <li><strong>Key strengths</strong></li>
    <li><strong>Negotiation opportunities</strong></li>
</ul>
"""

DASHBOARD_HERO_METRICS_HTML = """
<div class="landing-hero__panel-card">
    <h4>Portfolio width</h4>
    <strong>104 vendors</strong>
    <p>Aggregated across 12 sourcing categories with score distribution overlays.</p>
</div>
<div class="landing-hero__panel-card">
    <h4>Parameters tracked</h4>
    <strong>45 custom parameters</strong>
    <p>Compare compliance and completeness to focus negotiation prep.</p>
</div>
<div class="landing-hero__panel-card">
    <h4>Charts available</h4>
    <strong>6 views</strong>
    <p>Drill into categories, suppliers, sections, and improvement opportunities.</p>
</div>
"""

DASHBOARD_SECTION_HEADER_HTML = """
<div class="workspace-section__header">
    <h2>Explore contract visualisations</h2>
    <p>Open each snapshot to inspect category performance, supplier standings, and parameter insights.</p>
</div>
"""

CHART_SUMMARIES = [
    {
        "title": "📋 Contract Portfolio Summary",
        "filename": "1.Contract_Portfolio_Summary.png",
        "summary": (
            "- **Portfolio Coverage:** Comprehensive view across all active contracts.\n"
            "- **Risk Hotspots:** Quickly locate categories requiring focused review.\n"
            "- **Trend Tracking:** Monitor how overall compliance evolves over time."
        ),
    },
    {
        "title": "📂 Category Insights",
        "filename": "2.Category_Insights.png",
        "summary": (
            "- **Highest Risk Category:** Plastics with 24.7% risk exposure.\n"
            "- **Top Performer:** FCC category averaging a score of 2.62.\n"
            "- **Category Champion:** Jiangsu H H C delivering the strongest results in FCC."
        ),
    },
    {
        "title": "📑 Section-Level Insights",
        "filename": "3.Section_level.png",
        "summary": (
            "- **Weakest Section:** Pricing Adjustment (score 1.99).\n"
            "- **Strongest Section:** Term provisions (score 2.96).\n"
            "- **Variability Watch:** Pricing Adjustment shows the widest score spread."
        ),
    },
    {
        "title": "🔍 Parameter-Level Insights",
        "filename": "4.Parameter_level.png",
        "summary": (
            "- **Parameters Reviewed:** 45 total with 11 below target.\n"
            "- **Top Parameter:** RM index band at 2.15.\n"
            "- **Highest Risk Parameter:** Currency index band at 1.15."
        ),
    },
    {
        "title": "🏆 Supplier Performance Insights",
        "filename": "5.Supplier_level.png",
        "summary": (
            "- **Best Performer:** Jiangsu H H C (score 2.80).\n"
            "- **Highest Risk:** Nuova S S (score 1.96).\n"
            "- **Consistency Leader:** Jiangsu H H C with lowest score variance."
        ),
    },
    {
        "title": "📈 Improvement Opportunities",
        "filename": "6.Neg_Opps.png",
        "summary": (
            "- **Vendors Analysed:** 104 with 20 showing improvement potential.\n"
            "- **Largest Opportunity:** Qingte G C L at 43.2%.\n"
            "- **Average Gap:** 35.2% across flagged parameters."
        ),
    },
]
