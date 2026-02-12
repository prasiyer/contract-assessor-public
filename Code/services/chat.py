"""Chat and retrieval services for the Contract Assistant."""

from __future__ import annotations

import asyncio
import json
from functools import lru_cache
from typing import Any, Dict, List, Tuple

import gradio as gr
from sklearn.metrics.pairwise import cosine_similarity

from static_assets import contract_evaluation_prompts
from services import oai_client
from config import (
    CONTRACT_ASSISTANT_COMPLETION_MODEL_ID,
    CONTRACT_ASSISTANT_EMBEDDING_MODEL_ID,
    LOGGER,
    MAX_RELEVANT_CHUNKS,
    VENDOR_MATCH_CONFIDENCE_THRESHOLD,
)

from services.data import get_contract_chunk_embeddings, get_vendor_embeddings

SYSTEM_PROMPT = contract_evaluation_prompts.system_prompt_contract_assistant_v1


def base_llm_history() -> List[Dict[str, str]]:
    """Return a fresh base conversation history containing the system prompt."""

    return [{"role": "system", "content": SYSTEM_PROMPT}]


@lru_cache(maxsize=1)
def get_embedding_client():
    """Instantiate and cache the embedding client."""

    LOGGER.info(
        "Initialising embedding client with model %s",
        CONTRACT_ASSISTANT_EMBEDDING_MODEL_ID,
    )
    return oai_client.oai_client(model_id=CONTRACT_ASSISTANT_EMBEDDING_MODEL_ID)


@lru_cache(maxsize=1)
def get_contract_client():
    """Instantiate and cache the contract assistant client."""

    LOGGER.info(
        "Initialising contract assistant client with model %s",
        CONTRACT_ASSISTANT_COMPLETION_MODEL_ID,
    )
    return oai_client.oai_client(model_id=CONTRACT_ASSISTANT_COMPLETION_MODEL_ID)


def get_single_embedding(text: str) -> List[float]:
    """Fetch a single embedding vector for the supplied text."""

    client = get_embedding_client()
    try:
        response = client.get_embedding(input_text=[text])
    except TypeError:
        response = client.get_embedding([text])
    return response.data[0].embedding  # type: ignore[attr-defined]


def find_closest_vendor_names(input_vendor_names: List[str]) -> List[str]:
    """Return the closest known vendor names for the supplied list."""
    
    if not input_vendor_names:
        return []

    vendor_df, vendor_embeddings = get_vendor_embeddings()
    if not vendor_embeddings:
        LOGGER.warning("Vendor embeddings are empty.")
        print("Vendor embeddings are empty.")
        return []

    matches: List[str] = []
    
    LOGGER.info("Finding closest vendor names for input: %s", input_vendor_names)
    for raw_name in input_vendor_names:
        name = raw_name.strip()
        if not name:
            continue

        try:
            query_embedding = get_single_embedding(name)
            similarities = cosine_similarity([query_embedding], vendor_embeddings)[0]
            closest_index = int(similarities.argmax())
            matched_name = vendor_df.iloc[closest_index]["vendor_name"]
            vendor_match_confidence = similarities[closest_index]
            LOGGER.info("Matched vendor query '%s' to '%s' with confidence %.4f", name, matched_name, vendor_match_confidence)
            if vendor_match_confidence < VENDOR_MATCH_CONFIDENCE_THRESHOLD:
                LOGGER.warning("Low confidence (%.4f) matching vendor name '%s' to '%s'", vendor_match_confidence, name, matched_name)
            else:
                matches.append(str(matched_name))
        except Exception as exc:  # pragma: no cover - embedding failure
            LOGGER.exception("Failed to match vendor name '%s'", name)
            raise gr.Error("Unable to match vendor names for retrieval.") from exc

    return matches


def get_relevant_contract_chunks(matched_vendor_names: List[str], query: str) -> str:
    """Return the most relevant contract chunks for the query and vendor names."""

    if not query.strip() or not matched_vendor_names:
        return f"<query>{query}</query>"

    chunk_df = get_contract_chunk_embeddings()

    try:
        query_embedding = get_single_embedding(query)
    except Exception as exc:  # pragma: no cover - embedding failure
        LOGGER.exception("Failed to embed query for contract chunks")
        raise gr.Error("Unable to embed query for retrieving contract chunks.") from exc

    all_vendor_chunks: List[str] = []

    for vendor_name in matched_vendor_names:
        vendor_chunks = chunk_df[chunk_df["vendor_name"] == vendor_name]
        if vendor_chunks.empty:
            LOGGER.info("No contract chunks found for vendor '%s'", vendor_name)
            continue

        chunk_embeddings = vendor_chunks["parsed_embedding"].tolist()
        similarities = cosine_similarity([query_embedding], chunk_embeddings)[0]
        top_indices = similarities.argsort()[-MAX_RELEVANT_CHUNKS:][::-1]

        vendor_chunk_entries: List[str] = []
        for idx in top_indices:
            chunk_text = vendor_chunks.iloc[idx]["chunk_text"]
            vendor_chunk_entries.append(f"<chunk>{chunk_text}</chunk>")

        if vendor_chunk_entries:
            all_vendor_chunks.append(
                f"<vendor name='{vendor_name}'>\n"
                + "\n".join(vendor_chunk_entries)
                + "\n</vendor>"
            )

    vendor_chunk_text = "\n".join(all_vendor_chunks)
    return f"<query>{query}\n{vendor_chunk_text}</query>"


CONTRACT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "find_closest_vendor_names",
            "description": "Find the closest vendor names in the database for each input vendor name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_vendor_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of vendor names mentioned in the user's query.",
                    }
                },
                "required": ["input_vendor_names"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_relevant_contract_chunks",
            "description": "Retrieve contract chunks relevant to the user's query for the specified vendor names.",
            "parameters": {
                "type": "object",
                "properties": {
                    "matched_vendor_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of matched vendor names to retrieve chunks for.",
                    },
                    "query": {
                        "type": "string",
                        "description": "Rewritten user query that includes vendor context.",
                    },
                },
                "required": ["matched_vendor_names", "query"],
            },
        },
    },
]


def agent_step(
    message_history: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """Execute the agent decision loop and return updated history plus assistant message."""

    history = list(message_history)
    client = get_contract_client()

    while True:
        response_content, token_usage, response_tool_calls = client.get_response_with_token_tracking(
            oai_prompt=history,
            operation="contract_query_assistant",
            tools=CONTRACT_TOOLS,
        )

        LOGGER.info("LLM response content received.")

        if not response_tool_calls:
            assistant_message = {"role": "assistant", "content": response_content}
            history.append(assistant_message)
            return history, assistant_message

        LOGGER.info("Processing %d tool call(s)", len(response_tool_calls))

        for tool_call in response_tool_calls:
            function_name = getattr(tool_call.function, "name", "")
            arguments_raw = getattr(tool_call.function, "arguments", "{}")
            LOGGER.info("Tool call to function: %s", function_name)
            
            try:
                function_args = json.loads(arguments_raw)
            except json.JSONDecodeError as exc:
                LOGGER.exception("Failed to decode tool arguments for %s", function_name)
                raise gr.Error("Unable to interpret tool arguments from model response.") from exc

            if function_name == "find_closest_vendor_names":
                LOGGER.info("Matched Tool call to function: %s", function_name)
                matched_names = find_closest_vendor_names(
                    function_args.get("input_vendor_names", [])
                )
                
                LOGGER.info("Matched vendor names returned: %s", matched_names)
                tool_response = {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": "find_closest_vendor_names",
                    "content": json.dumps({"matched_vendor_names": matched_names}),
                }
            elif function_name == "get_relevant_contract_chunks":
                LOGGER.info("Matched Tool call to function: %s", function_name)
                matched_vendor_names = function_args.get("matched_vendor_names", [])
                query = function_args.get("query", "")
                chunks = get_relevant_contract_chunks(matched_vendor_names, query)
                tool_response = {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": "get_relevant_contract_chunks",
                    "content": json.dumps({"relevant_chunks": chunks}),
                }
            else:
                LOGGER.warning("Received unsupported tool call: %s", function_name)
                continue

            tool_call_message = {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": function_name,
                            "arguments": json.dumps(function_args),
                        },
                    }
                ],
            }

            history.append(tool_call_message)
            history.append(tool_response)


def clear_chat() -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, Any]]]:
    """Clear the chat history and reset underlying state."""

    LOGGER.info("Clearing chat history.")
    return [], [], []


async def handle_chat(
    message: str,
    ui_history: List[Dict[str, str]] | None,
    llm_history: List[Dict[str, Any]] | None,
) -> Tuple[str, List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, Any]]]:
    """Process chat interactions for the contract query assistant."""

    current_ui_history: List[Dict[str, str]] = list(ui_history or [])
    current_llm_history: List[Dict[str, Any]] = list(llm_history or base_llm_history())

    if not message.strip():
        return "", current_ui_history, current_ui_history, current_llm_history

    LOGGER.info("Received chat question: %s", message)

    user_message = {"role": "user", "content": message}
    current_ui_history.append(user_message)
    current_llm_history.append(user_message)

    try:
        updated_history, assistant_message = await asyncio.to_thread(
            agent_step,
            current_llm_history,
        )
        current_llm_history = updated_history
        current_ui_history.append(assistant_message)

    except gr.Error:  # pragma: no cover - Gradio-surfaced errors
        raise
    except Exception as exc:  # pragma: no cover - unexpected chat failure
        LOGGER.exception("Chat processing failed")
        error_message = {
            "role": "assistant",
            "content": "Sorry, I ran into an issue while answering that question. Please try again.",
        }
        current_ui_history.append(error_message)
        current_llm_history.append(error_message)
        return "", current_ui_history, current_ui_history, current_llm_history

    return "", current_ui_history, current_ui_history, current_llm_history
