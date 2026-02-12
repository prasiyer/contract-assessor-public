"""Production-ready Gradio application for contract assessment and query assistance."""

from __future__ import annotations

from typing import Any, Dict, Tuple

import gradio as gr
import pandas as pd

from config import APP_TITLE, CHARTS_DIR_PATH, LOW_SCORE_COLUMNS
from services.assessment import process_contract_submission
from services.chat import clear_chat, handle_chat
##
from ui.layout import (
    ASSISTANT_SECTION_HEADER_HTML,
    CHART_SUMMARIES,
    DASHBOARD_HERO_COPY_HTML,
    DASHBOARD_HERO_METRICS_HTML,
    DASHBOARD_SECTION_HEADER_HTML,
    DRAFT_SECTION_HEADER_HTML,
    LANDING_HERO_COPY_HTML,
    LANDING_HERO_PANEL_HTML,
    LANDING_KEY_FEATURES_HTML,
    LANDING_PROCESS_HTML,
    LANDING_SECTION_VALUE_HTML,
)
from ui.styles import OVERVIEW_CSS


def show_processing_indicator() -> Dict[str, Any]:
    """Display a temporary processing message to the user."""

    return gr.update(
        value="⏳ Processing your contract. This may take a couple of minutes...",
        visible=True,
    )


def reset_textbox() -> str:
    """Return an empty string to reset a textbox component."""

    return ""


def navigate(
    page: str,
) -> Tuple[
    str,
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
]:
    """Return style and visibility updates for navigation buttons and page sections."""

    button_variants = {
        "landing": gr.update(variant="primary" if page == "landing" else "secondary"),
        "draft": gr.update(variant="primary" if page == "draft" else "secondary"),
        "assistant": gr.update(variant="primary" if page == "assistant" else "secondary"),
        "dashboard": gr.update(
            variant="primary" if page == "dashboard" else "secondary"
        ),
    }

    return (
        page,
        button_variants["landing"],
        button_variants["draft"],
        button_variants["assistant"],
        button_variants["dashboard"],
        gr.update(visible=page == "landing"),
        gr.update(visible=page == "draft"),
        gr.update(visible=page == "assistant"),
        gr.update(visible=page == "dashboard"),
    )


def build_app() -> gr.Blocks:
    """Create and configure the Gradio Blocks application."""

    with gr.Blocks(title=APP_TITLE, theme=gr.themes.Soft(), css=OVERVIEW_CSS) as demo:
        page_state = gr.State("landing")

        with gr.Row():
            nav_overview = gr.Button("Overview", variant="primary")
            nav_draft = gr.Button("Draft Reviewer", variant="secondary")
            nav_assistant = gr.Button("Query Assistant", variant="secondary")
            nav_dashboard = gr.Button("Metrics Dashboard", variant="secondary")

        landing_group = gr.Group(visible=True, elem_classes="landing-group")
        with landing_group:
            with gr.Column(elem_classes="landing-layout"):
                with gr.Row(elem_classes="landing-hero"):
                    with gr.Column(scale=6, elem_classes="landing-hero__copy"):
                        gr.HTML(LANDING_HERO_COPY_HTML)
                    with gr.Column(scale=6, elem_classes="landing-hero__panel"):
                        gr.HTML(LANDING_HERO_PANEL_HTML)

                gr.HTML(LANDING_SECTION_VALUE_HTML)
                gr.HTML(LANDING_PROCESS_HTML)
                gr.HTML(LANDING_KEY_FEATURES_HTML)

        draft_group = gr.Group(visible=False)
        with draft_group:
            with gr.Column(elem_classes="workspace-layout"):
                with gr.Column(elem_classes="workspace-section"):
                    gr.HTML(DRAFT_SECTION_HEADER_HTML)
                    with gr.Row(elem_classes="workspace-form__row"):
                        vendor_name = gr.Textbox(
                            label="Vendor Name",
                            placeholder="e.g., Giuliani SPA",
                        )
                        category_name = gr.Textbox(
                            label="Category Name",
                            placeholder="e.g., Fluid Conveyance & Cylinders",
                        )

                    upload = gr.File(
                        label="Draft Contract (PDF only)",
                        file_types=[".pdf"],
                        type="filepath",
                    )

                    submit_button = gr.Button("Run Analysis", variant="primary")

                    processing_status = gr.Markdown(visible=False)
                    metrics_output = gr.Markdown(visible=False)
                    summary_output = gr.Markdown(visible=False)
                    low_score_table = gr.Dataframe(
                        headers=LOW_SCORE_COLUMNS,
                        datatype=["str", "str", "str", "str", "float"],
                        interactive=False,
                        row_count=(0, "dynamic"),
                        col_count=(len(LOW_SCORE_COLUMNS), "fixed"),
                        visible=False,
                        label="Items Requiring Attention",
                        elem_classes="workspace-table",
                        value=pd.DataFrame(columns=LOW_SCORE_COLUMNS),
                    )

                back_from_draft = gr.Button(
                    "← Back to Overview",
                    variant="secondary",
                    elem_classes="workspace-back",
                )

        assistant_group = gr.Group(visible=False)
        with assistant_group:
            with gr.Column(elem_classes="workspace-layout"):
                with gr.Column(elem_classes="workspace-section"):
                    gr.HTML(ASSISTANT_SECTION_HEADER_HTML)
                    chatbot = gr.Chatbot(
                        label="Contract Q&A Assistant",
                        type="messages",
                        height=400,
                    )
                    message_input = gr.Textbox(
                        label="Your Question",
                        placeholder="e.g., What are the payment terms for Supplier ABC?",
                        lines=1,
                    )
                    with gr.Row(elem_classes="workspace-form__actions"):
                        send_button = gr.Button("Send", variant="primary")
                        clear_button = gr.Button("Clear Conversation")

                    ui_history_state = gr.State([])
                    llm_history_state = gr.State([])

                back_from_assistant = gr.Button(
                    "← Back to Overview",
                    variant="secondary",
                    elem_classes="workspace-back",
                )

        dashboard_group = gr.Group(visible=False)
        with dashboard_group:
            with gr.Column(elem_classes="workspace-layout"):
                with gr.Row(elem_classes="workspace-hero workspace-hero--dashboard"):
                    with gr.Column(scale=7, elem_classes="workspace-hero__copy"):
                        gr.HTML(DASHBOARD_HERO_COPY_HTML)
                    with gr.Column(scale=5, elem_classes="workspace-hero__metrics"):
                        gr.HTML(DASHBOARD_HERO_METRICS_HTML)

                with gr.Column(elem_classes="workspace-section"):
                    gr.HTML(DASHBOARD_SECTION_HEADER_HTML)

                    for chart in CHART_SUMMARIES:
                        image_path = CHARTS_DIR_PATH / chart["filename"]
                        with gr.Accordion(chart["title"], open=False):
                            if image_path.exists():
                                gr.Image(value=str(image_path), show_label=False)
                            else:
                                gr.Markdown(
                                    f"> ⚠️ Chart not found at `{image_path}`. Ensure the dashboard export is up to date."
                                )
                            gr.Markdown(chart["summary"])

                back_from_dashboard = gr.Button(
                    "← Back to Overview",
                    variant="secondary",
                    elem_classes="workspace-back",
                )

        navigation_outputs = [
            page_state,
            nav_overview,
            nav_draft,
            nav_assistant,
            nav_dashboard,
            landing_group,
            draft_group,
            assistant_group,
            dashboard_group,
        ]

        nav_overview.click(lambda: navigate("landing"), outputs=navigation_outputs)
        nav_draft.click(lambda: navigate("draft"), outputs=navigation_outputs)
        nav_assistant.click(lambda: navigate("assistant"), outputs=navigation_outputs)
        nav_dashboard.click(lambda: navigate("dashboard"), outputs=navigation_outputs)

        back_from_draft.click(lambda: navigate("landing"), outputs=navigation_outputs)
        back_from_assistant.click(lambda: navigate("landing"), outputs=navigation_outputs)
        back_from_dashboard.click(lambda: navigate("landing"), outputs=navigation_outputs)

        submit_button.click(
            fn=show_processing_indicator,
            outputs=processing_status,
            queue=False,
        ).then(
            fn=process_contract_submission,
            inputs=[vendor_name, category_name, upload],
            outputs=[processing_status, metrics_output, summary_output, low_score_table],
            api_name="run_review",
        )

        send_button.click(
            handle_chat,
            inputs=[message_input, ui_history_state, llm_history_state],
            outputs=[message_input, chatbot, ui_history_state, llm_history_state],
        )

        message_input.submit(
            handle_chat,
            inputs=[message_input, ui_history_state, llm_history_state],
            outputs=[message_input, chatbot, ui_history_state, llm_history_state],
        )

        clear_button.click(
            clear_chat,
            outputs=[chatbot, ui_history_state, llm_history_state],
        ).then(
            reset_textbox,
            outputs=message_input,
        )

        demo.queue()

    return demo


if __name__ == "__main__":
    APP = build_app()
    APP.launch()
