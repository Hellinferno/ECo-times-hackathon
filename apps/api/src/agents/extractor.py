"""Preparer agent for financial-data extraction.

Phase 2 upgrade: when a document has been ingested into the RAG vector store,
the extractor queries it for the most relevant chunks instead of passing the
full parsed_text. This reduces token usage by ~70-80% for large documents and
improves extraction quality by focusing the LLM on the relevant sections.

Fallback: if RAG retrieval is unavailable (ChromaDB not running, document not
yet ingested), the full document_context is used unchanged.
"""
import json
import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

from engine.llm import ask_llm
from engine.llm import resolve_llm_runtime_config
from agents.prompt_builder import PromptBuilder
from security.prompt_guard import guard_prompt_text

_EXTRACTION_QUERY = (
    "revenue EBITDA net profit borrowings debt cash equity shares outstanding "
    "historical financials balance sheet income statement"
)


def _resolve_context(
    document_id: Optional[str],
    deal_id: Optional[str],
    fallback: str,
    *,
    tenant_id: Optional[str],
    user_id: Optional[str],
) -> tuple[str, list[dict[str, Any]], str, list[dict[str, Any]]]:
    """Return sanitized RAG context when available, else sanitized fallback."""
    rag_chunks: list[dict[str, Any]] = []
    try:
        from rag.retriever import retrieve_chunk_records

        rag_chunks = (
            retrieve_chunk_records(
                _EXTRACTION_QUERY,
                document_id=document_id,
                deal_id=deal_id,
                top_k=10,
            )
            or []
        )
    except Exception as exc:
        logger.debug("[Preparer] RAG unavailable, using full text: %s", exc)

    if rag_chunks:
        retrieved = "\n\n---\n\n".join(chunk["text"] for chunk in rag_chunks)
        guarded = guard_prompt_text(
            retrieved,
            source="rag_context",
            tenant_id=tenant_id,
            user_id=user_id,
            resource_type="document",
            resource_id=document_id or deal_id,
            block_policy="sanitize",
        )
        return guarded.sanitized_text, rag_chunks, "rag", guarded.events

    guarded = guard_prompt_text(
        fallback,
        source="full_document_context",
        tenant_id=tenant_id,
        user_id=user_id,
        resource_type="deal",
        resource_id=deal_id or document_id,
        block_policy="sanitize",
    )
    return guarded.sanitized_text, [], "full_document", guarded.events


class PreparerAgent:
    @classmethod
    def extract(
        cls,
        system_prompt: str,
        document_context: str,
        params: dict,
        company_name: str = "",
        document_id: Optional[str] = None,
        deal_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        runtime_config = resolve_llm_runtime_config(
            purpose="modeling_extraction",
            tenant_id=tenant_id,
        )
        context, rag_chunks_used, context_source, guard_events = _resolve_context(
            document_id,
            deal_id,
            document_context,
            tenant_id=tenant_id,
            user_id=user_id,
        )
        prompt = PromptBuilder.build_preparer_prompt(params, context, company_name)

        try:
            raw_response = ask_llm(
                system_prompt,
                prompt,
                purpose="modeling_extraction",
                tenant_id=tenant_id,
            )
            parsed = cls._parse_preparer_response(raw_response)

            audit_trail = parsed.pop("audit_trail", [])
            reconciliation_log = parsed.pop("reconciliation_log", "")
            extraction_mode = parsed.pop("extraction_mode", "llm")

            extracted_data = {}
            for key, val in parsed.items():
                if isinstance(val, dict) and "value" in val:
                    extracted_data[key] = val["value"]
                    audit_trail.append(
                        {
                            "field": key,
                            "value": val["value"],
                            "confidence": val.get("confidence", 0.5),
                            "source_citation": val.get("source", "Not cited"),
                            "reasoning": val.get("reasoning", ""),
                        }
                    )
                else:
                    extracted_data[key] = val

            audit_fields = {entry["field"] for entry in audit_trail}
            for key, val in extracted_data.items():
                if key not in audit_fields and key not in {"currency", "extraction_mode", "fallback_profile"}:
                    audit_trail.append(
                        {
                            "field": key,
                            "value": val,
                            "confidence": 0.5 if val is not None else 0.0,
                            "source_citation": "Extracted without explicit citation",
                            "reasoning": "",
                        }
                    )

            return {
                "extracted_data": extracted_data,
                "audit_trail": audit_trail,
                "reconciliation_log": reconciliation_log,
                "extraction_mode": extraction_mode,
                "rag_chunks_used": rag_chunks_used,
                "guard_events": guard_events,
                "context_source": context_source,
                "registry_id": runtime_config.registry_id,
                "prompt_version": runtime_config.prompt_version,
                "model_runtime": {
                    "registry_id": runtime_config.registry_id,
                    "provider": runtime_config.provider,
                    "model_name": runtime_config.model_name,
                    "prompt_version": runtime_config.prompt_version,
                },
                "eval_status": (runtime_config.config or {}).get("eval_summary", {}).get("status", "pending"),
            }
        except Exception as exc:
            logger.exception("[Preparer] Extraction failed")
            return {
                "extracted_data": {},
                "audit_trail": [],
                "reconciliation_log": "Extraction failed. Check server logs.",
                "extraction_mode": "failed",
                "rag_chunks_used": rag_chunks_used,
                "guard_events": guard_events,
                "context_source": context_source,
                "registry_id": runtime_config.registry_id,
                "prompt_version": runtime_config.prompt_version,
                "model_runtime": {
                    "registry_id": runtime_config.registry_id,
                    "provider": runtime_config.provider,
                    "model_name": runtime_config.model_name,
                    "prompt_version": runtime_config.prompt_version,
                },
                "eval_status": (runtime_config.config or {}).get("eval_summary", {}).get("status", "pending"),
            }

    @staticmethod
    def _parse_preparer_response(raw: str) -> dict:
        text = raw.strip()
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        text = text.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(text[first_brace:last_brace + 1])
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Preparer: could not parse JSON (len={len(raw)})")
