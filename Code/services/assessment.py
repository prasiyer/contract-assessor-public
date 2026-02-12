"""Assessment-related services for contract ingestion and scoring."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any, Tuple

import gradio as gr
import pandas as pd

from services import contract_assessor_script
from config import LOGGER, LOW_SCORE_COLUMNS, MAX_UPLOAD_SIZE_BYTES, ASSESSMENT_TEST_MODE

def resolve_uploaded_path(file_obj: Any) -> str | None:
    """Resolve the filesystem path from a Gradio file object or path-like value."""

    if file_obj is None:
        return None
    if isinstance(file_obj, (str, Path)):
        return str(file_obj)
    if isinstance(file_obj, dict) and "name" in file_obj:
        return file_obj["name"]
    return getattr(file_obj, "name", None)


def sanitize_vendor_name(raw_name: str) -> str:
    """Normalize vendor names and reject disallowed characters."""

    cleaned = re.sub(r"\s+", " ", raw_name.strip())
    if not cleaned:
        return ""

    if not re.fullmatch(r"[A-Za-z0-9\s\-_,.&/]+", cleaned):
        LOGGER.warning("Vendor name contains unsupported characters: %s", raw_name)
        raise gr.Error(
            "Vendor name contains unsupported characters. Use letters, numbers, spaces, and - _ , . & / only."
        )

    if cleaned != raw_name:
        LOGGER.info("Vendor name sanitized from '%s' to '%s'", raw_name, cleaned)

    return cleaned


def validate_contract_inputs(
    vendor_name: str,
    category_name: str,
    upload_file: Any,
) -> Tuple[str, str, Path]:
    """Validate user inputs for contract assessment and return canonical values."""

    vendor = sanitize_vendor_name(vendor_name or "")
    category = (category_name or "").strip()

    if not vendor:
        LOGGER.warning("Contract assessment attempted without vendor name.")
        raise gr.Error("Vendor name is required.")
    if not category:
        LOGGER.warning("Contract assessment attempted without category name.")
        raise gr.Error("Category name is required.")

    input_contract_path = resolve_uploaded_path(upload_file)
    if not input_contract_path:
        LOGGER.warning("Contract assessment attempted without a valid PDF upload.")
        raise gr.Error("Please upload a contract PDF before running the assessment.")

    contract_path = Path(input_contract_path)
    if not contract_path.exists():
        LOGGER.warning("Uploaded file path does not exist: %s", input_contract_path)
        raise gr.Error("The uploaded file could not be found on the server.")
    if contract_path.suffix.lower() != ".pdf":
        LOGGER.warning("Unsupported file type uploaded: %s", input_contract_path)
        raise gr.Error("The uploaded file must be a PDF.")

    try:
        file_size = contract_path.stat().st_size
    except OSError as exc:
        LOGGER.warning("Unable to read uploaded file size for %s: %s", contract_path, exc)
        raise gr.Error("Unable to read the uploaded file. Please try again.") from exc

    if file_size > MAX_UPLOAD_SIZE_BYTES:
        LOGGER.warning(
            "Uploaded file exceeds size limit: %s (%d bytes)",
            contract_path,
            file_size,
        )
        raise gr.Error("Uploaded file is larger than 10 MB. Please upload a smaller PDF.")

    return vendor, category, contract_path


def compliance_status_label(rate: float) -> str:
    """Return a textual status label for the compliance rate."""

    if rate >= 90.0:
        return "Excellent"
    if rate >= 75.0:
        return "Good"
    return "Needs Attention"


def format_metrics_markdown(
    compliance_rate: float,
    completeness_rate: float,
    total_parameters: int,
    non_compliant: int,
    complete_parameters: int,
) -> str:
    """Generate a markdown summary for contract metrics."""

    status = compliance_status_label(compliance_rate)
    return (
        "<h3>✅ Key Metrics</h3>"
        '<div class="metrics-tiles">'
        f"<article class=\"metrics-tile\"><h3>Compliance Rate</h3>"
        f"<span class=\"metrics-value\">{compliance_rate:.1f}%</span>"
        f"<span class=\"metrics-note\">{status}</span></article>"
        f"<article class=\"metrics-tile\"><h3>Completeness</h3>"
        f"<span class=\"metrics-value\">{completeness_rate:.1f}%</span>"
        f"<span class=\"metrics-note\">{complete_parameters} of {total_parameters} parameters specified</span></article>"
        f"<article class=\"metrics-tile\"><h3>Follow-ups</h3>"
        f"<span class=\"metrics-value\">{non_compliant}</span>"
        f"<span class=\"metrics-note\">Parameters requiring attention</span></article>"
        "</div>"
    )


def compute_metrics(df: pd.DataFrame) -> Tuple[str, float, float, int]:
    """Compute compliance and completeness metrics and return a markdown snippet."""

    if df is None or df.empty:
        message = "> ⚠️ No parameters were scored. Confirm that contract processing completed successfully."
        return message, 0.0, 0.0, 0

    total = len(df)
    compliant = int((df.get("score", pd.Series(dtype=float)) >= 2).sum()) if "score" in df else 0
    non_compliant = total - compliant

    answer_column = None
    if "structured_answer_revised" in df.columns:
        answer_column = "structured_answer_revised"
    elif "structured_answer" in df.columns:
        answer_column = "structured_answer"

    if answer_column:
        complete = int((df[answer_column].astype(str).str.upper() != "NOT_SPECIFIED").sum())
    else:
        complete = 0

    compliance_rate = compliant / total * 100.0 if total else 0.0
    completeness_rate = complete / total * 100.0 if total else 0.0

    metrics_markdown = format_metrics_markdown(
        compliance_rate=compliance_rate,
        completeness_rate=completeness_rate,
        total_parameters=total,
        non_compliant=non_compliant,
        complete_parameters=complete,
    )

    return metrics_markdown, compliance_rate, completeness_rate, total


def prepare_low_score_table(df: pd.DataFrame) -> pd.DataFrame:
    """Return a table containing only the low scoring parameters."""

    if df is None or df.empty:
        return pd.DataFrame(columns=LOW_SCORE_COLUMNS)

    prepared_df = df.copy()
    for column in LOW_SCORE_COLUMNS:
        if column not in prepared_df.columns:
            prepared_df[column] = ""

    if "score" in prepared_df.columns:
        prepared_df = prepared_df[prepared_df["score"] < 2]

    return prepared_df[LOW_SCORE_COLUMNS].reset_index(drop=True)


def format_summary_markdown(summary_text: str) -> str:
    """Generate a markdown block for the assessment summary."""

    if not summary_text:
        return "> ⚠️ No summary available for this contract."
    return f"### 📋 Executive Summary\n\n{summary_text}"


def run_contract_assessment(
    vendor: str,
    category: str,
    input_contract_path: Path,
) -> Tuple[pd.DataFrame, str, str]:
    """Execute the contract assessment pipeline and return results for the UI."""

    LOGGER.info("Starting contract assessment for vendor=%s category=%s", vendor, category)

    try:
        assessor = contract_assessor_script.ContractAssessor(
            input_contract_path=str(input_contract_path),
            use_test_file=ASSESSMENT_TEST_MODE,
        )
        assessor.process_pdf_contract()

        scores_df = getattr(assessor, "contract_parameter_scores_df", pd.DataFrame())
        summary_text = getattr(assessor, "contract_assessment_response_str", "")

        low_score_df = prepare_low_score_table(scores_df)
        metrics_markdown, _, _, _ = compute_metrics(scores_df)
        summary_markdown = format_summary_markdown(summary_text)

        LOGGER.info("Contract assessment completed successfully for vendor=%s", vendor)
        return low_score_df, metrics_markdown, summary_markdown

    except gr.Error:  # pragma: no cover - Gradio errors surface directly
        raise
    except Exception as exc:  # pragma: no cover - pipeline failures
        LOGGER.exception("Contract processing failed for vendor=%s", vendor)
        raise gr.Error("Contract processing failed. Please review the log for details.") from exc


async def process_contract_submission(
    vendor: str,
    category: str,
    uploaded_file: Any,
    progress: gr.Progress = gr.Progress(),
) -> Tuple[dict, dict, dict, dict]:
    """Run the contract assessment and prepare UI updates."""

    progress(0.1, desc="Validating inputs...")

    try:
        vendor_clean, category_clean, contract_path = validate_contract_inputs(
            vendor,
            category,
            uploaded_file,
        )
        progress(0.2, desc="Starting analysis...")
        low_score_df, metrics_markdown, summary_markdown = await asyncio.to_thread(
            run_contract_assessment,
            vendor_clean,
            category_clean,
            contract_path,
        )
        progress(0.9, desc="Preparing results...")

        return (
            gr.update(value="✅ Analysis complete.", visible=True),
            gr.update(value=metrics_markdown, visible=True),
            gr.update(value=summary_markdown, visible=True),
            gr.update(value=low_score_df, visible=True),
        )

    except gr.Error as exc:
        LOGGER.warning("Contract assessment failed: %s", exc)
        empty_table = pd.DataFrame(columns=LOW_SCORE_COLUMNS)
        return (
            gr.update(value=f"⚠️ {exc}", visible=True),
            gr.update(value="", visible=False),
            gr.update(value="", visible=False),
            gr.update(value=empty_table, visible=False),
        )

    except Exception as exc:  # pragma: no cover - unexpected failures
        LOGGER.exception("Unexpected error during contract assessment")
        empty_table = pd.DataFrame(columns=LOW_SCORE_COLUMNS)
        return (
            gr.update(value="⚠️ An unexpected error occurred during analysis.", visible=True),
            gr.update(value="", visible=False),
            gr.update(value="", visible=False),
            gr.update(value=empty_table, visible=False),
        )
