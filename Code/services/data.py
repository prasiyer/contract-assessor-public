"""Data loading and embedding cache utilities for the Contract Assistant."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, List, Tuple

import gradio as gr
import pandas as pd

from config import (
    CONTRACT_CHUNK_EMBEDDINGS_FILE_PATH,
    LOGGER,
    VENDOR_NAME_EMBEDDINGS_FILE_PATH,
)

CONTRACT_CHUNK_SOURCE_DF: pd.DataFrame | None = None
CONTRACT_CHUNK_EMBEDDINGS_DF: pd.DataFrame | None = None
VENDOR_NAME_SOURCE_DF: pd.DataFrame | None = None
VENDOR_NAME_EMBEDDINGS_LIST: List[List[float]] | None = None

def parse_embedding(raw_embedding: Any) -> List[float]:
    """Convert a stored embedding representation into a list of floats."""

    if isinstance(raw_embedding, (list, tuple)):
        return [float(value) for value in raw_embedding]

    if not isinstance(raw_embedding, str):
        raise ValueError("Embedding value is not a recognised format.")

    try:
        parsed = ast.literal_eval(raw_embedding)
    except (ValueError, SyntaxError) as exc:
        raise ValueError("Failed to parse embedding string.") from exc

    if not isinstance(parsed, (list, tuple)):
        raise ValueError("Parsed embedding is not a sequence of floats.")

    return [float(value) for value in parsed]


def load_dataframe(csv_path: Path, description: str) -> pd.DataFrame:
    """Load a CSV file into a DataFrame with logging and friendly errors."""

    if not csv_path.exists():
        LOGGER.error("%s file not found at %s", description, csv_path)
        raise gr.Error(f"Required data file is missing: {description}.")

    try:
        dataframe = pd.read_csv(csv_path)
        LOGGER.info("Loaded %s from %s", description, csv_path)
        return dataframe
    except Exception as exc:  # pragma: no cover - pd read exceptions
        LOGGER.exception("Unable to load %s from %s", description, csv_path)
        raise gr.Error(
            f"Unable to load {description}. Please check the log for details."
        ) from exc


def _initialise_embedding_caches() -> None:
    """Load embedding CSVs and parse vectors once at startup."""

    global CONTRACT_CHUNK_SOURCE_DF
    global CONTRACT_CHUNK_EMBEDDINGS_DF
    global VENDOR_NAME_SOURCE_DF
    global VENDOR_NAME_EMBEDDINGS_LIST

    CONTRACT_CHUNK_SOURCE_DF = load_dataframe(
        CONTRACT_CHUNK_EMBEDDINGS_FILE_PATH,
        "contract chunk embeddings",
    )
    contract_embeddings_df = CONTRACT_CHUNK_SOURCE_DF.copy()
    contract_embeddings_df["parsed_embedding"] = contract_embeddings_df[
        "chunk_small3_embedding"
    ].apply(parse_embedding)
    CONTRACT_CHUNK_EMBEDDINGS_DF = contract_embeddings_df

    VENDOR_NAME_SOURCE_DF = load_dataframe(
        VENDOR_NAME_EMBEDDINGS_FILE_PATH,
        "vendor name embeddings",
    )
    vendor_embeddings_df = VENDOR_NAME_SOURCE_DF.copy()
    vendor_embeddings_df["parsed_embedding"] = vendor_embeddings_df[
        "vendor_small3_embedding"
    ].apply(parse_embedding)
    VENDOR_NAME_EMBEDDINGS_LIST = vendor_embeddings_df["parsed_embedding"].tolist()

    LOGGER.info(
        "Preloaded %d contract chunks and %d vendor embeddings",
        len(CONTRACT_CHUNK_SOURCE_DF),
        len(VENDOR_NAME_SOURCE_DF),
    )


def get_contract_chunk_df() -> pd.DataFrame:
    """Return the preloaded contract chunk embeddings DataFrame."""

    if CONTRACT_CHUNK_SOURCE_DF is None:
        raise gr.Error("Contract chunk embeddings are not loaded.")
    return CONTRACT_CHUNK_SOURCE_DF.copy()


def get_vendor_name_df() -> pd.DataFrame:
    """Return the preloaded vendor name embeddings DataFrame."""

    if VENDOR_NAME_SOURCE_DF is None:
        raise gr.Error("Vendor name embeddings are not loaded.")
    return VENDOR_NAME_SOURCE_DF.copy()


def get_contract_chunk_embeddings() -> pd.DataFrame:
    """Return contract chunk embeddings with parsed vectors from cache."""

    if CONTRACT_CHUNK_EMBEDDINGS_DF is None:
        raise gr.Error("Parsed contract embeddings are unavailable.")
    return CONTRACT_CHUNK_EMBEDDINGS_DF.copy()


def get_vendor_embeddings() -> Tuple[pd.DataFrame, List[List[float]]]:
    """Return vendor embeddings DataFrame and the parsed embeddings list."""

    if VENDOR_NAME_SOURCE_DF is None or VENDOR_NAME_EMBEDDINGS_LIST is None:
        raise gr.Error("Vendor embeddings are unavailable.")
    dataframe = VENDOR_NAME_SOURCE_DF.copy()
    embeddings_copy = [list(embedding) for embedding in VENDOR_NAME_EMBEDDINGS_LIST]
    return dataframe, embeddings_copy


_initialise_embedding_caches()
