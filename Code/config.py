"""Centralised configuration for the Contract Assistant application."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
##

APP_TITLE = "🤖 AI Contract Assistant"
APP_SUBTITLE = "Analyze, understand, and improve supplier contracts with AI-powered tools."

LOW_SCORE_COLUMNS = [
    "question_type",
    "question_text",
    "relevant_context",
    "answer_justification",
    "score",
]

APP_BASE_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = APP_BASE_DIR.parent

# DEFAULT_BASE_DIR = Path("/home/vp899/projects/contract_assessor")
# set variable VENDOR_MATCH_CONFIDENCE_THRESHOLD = 0.5
VENDOR_MATCH_CONFIDENCE_THRESHOLD = float(
    os.getenv("VENDOR_MATCH_CONFIDENCE_THRESHOLD", "0.5")
)
LOG_FILE_PATH = Path(
    os.getenv(
        "CONTRACT_ASSISTANT_LOG_PATH",
        str(PROJECT_ROOT / "Output" / "output_log.txt"),
    )
)
CONTRACT_CHUNK_EMBEDDINGS_FILE_PATH = Path(
    os.getenv(
        "CONTRACT_CHUNK_EMBEDDINGS_FILE_PATH",
        str(PROJECT_ROOT / "Output" / "contract_chunk_embeddings.csv"),
    )
)
VENDOR_NAME_EMBEDDINGS_FILE_PATH = Path(
    os.getenv(
        "VENDOR_NAME_EMBEDDINGS_FILE_PATH",
        str(PROJECT_ROOT / "Output" / "vendor_name_embeddings.csv"),
    )
)
CHARTS_DIR_PATH = Path(
    os.getenv(
        "CHARTS_DIR_PATH",
        str(PROJECT_ROOT / "Output" / "Charts"),
    )
)

TOKEN_USAGE_FILE_PATH = Path(
    os.getenv(
        "CONTRACT_ASSISTANT_TOKEN_USAGE_PATH",
        str(PROJECT_ROOT / "Output" / "oai_token_usage.csv"),
    )
)
CONTRACT_TEXT_WIP_FILE_PATH = Path(
    os.getenv(
        "CONTRACT_ASSISTANT_TEXT_WIP_PATH",
        str(PROJECT_ROOT / "Output" / "contract_text_WIP.md"),
    )
)
CONTRACT_QUESTION_FILE_PATH = Path(
    os.getenv(
        "CONTRACT_ASSISTANT_QUESTION_FILE_PATH",
        str(PROJECT_ROOT / "Input" / "Contract_Eval_Questions_v6.csv"),
    )
)
TEST_CONTRACT_FILE_PATH = Path(
    os.getenv(
        "CONTRACT_ASSISTANT_TEST_CONTRACT_PATH",
        str(PROJECT_ROOT / "Input" / "Wipro SSP MSA_output.md"),
    )
)
# create a variable ASSESSMENT_TEST_MODE and set it to boolean value of environment variable CONTRACT_ASSISTANT_ASSESSMENT_TEST_MODE AND DEFAULT VALUE OF FALSE
ASSESSMENT_TEST_MODE = (
    os.getenv("CONTRACT_ASSISTANT_ASSESSMENT_TEST_MODE", False)
)

DEFAULT_ASSESSOR_MODEL_ID = os.getenv("CONTRACT_ASSESSOR_MODEL_ID", "gpt-4.1-mini")
DOC_TO_IMAGE_CONVERTER = os.getenv("CONTRACT_DOC_TO_IMAGE_CONVERTER", "fitz")

CONTRACT_ASSISTANT_EMBEDDING_MODEL_ID = os.getenv(
    "CONTRACT_ASSISTANT_EMBEDDING_MODEL_ID", "text-embedding-3-small"
)
CONTRACT_ASSISTANT_COMPLETION_MODEL_ID = os.getenv(
    "CONTRACT_ASSISTANT_COMPLETION_MODEL_ID", "gpt-4.1-mini"
)

FILE_LOGGING_ENABLED = (
    os.getenv("CONTRACT_ASSISTANT_ENABLE_FILE_LOGGING", "1").strip().lower()
    not in {"0", "false", "no", "off"}
)

MAX_RELEVANT_CHUNKS = 5
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024


def setup_logging() -> logging.Logger:
    """Configure application logging with console and optional file handlers."""

    logger = logging.getLogger("contract_assessor.app")
    if logger.handlers:
        return logger

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(stream_handler)
    logger.propagate = False

    if FILE_LOGGING_ENABLED:
        try:
            log_dir = LOG_FILE_PATH.parent
            log_dir.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                LOG_FILE_PATH,
                maxBytes=2 * 1024 * 1024,
                backupCount=3,
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            logger.info("File logging enabled at %s", LOG_FILE_PATH)
        except OSError as exc:
            logger.warning(
                "File logging disabled; unable to access %s (%s)",
                LOG_FILE_PATH,
                exc,
            )
    else:
        logger.info("File logging disabled via CONTRACT_ASSISTANT_ENABLE_FILE_LOGGING")

    logger.info("Logging initialised.")
    return logger


LOGGER = setup_logging()
