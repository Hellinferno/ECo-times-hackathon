"""DocumentParser — text extraction and metadata enrichment for workspace documents.

Handles plain-text formats (txt, md, json, csv, log) with UTF-8 decoding;
binary files (pdf, docx, xlsx) receive a placeholder preview until a real
extraction library is wired in.

Public API
----------
  ParsedDocument       — dataclass returned by all parser methods
  DocumentParser.parse(path, filename)  → ParsedDocument
"""
from __future__ import annotations

import io
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ParsedDocument:
    document_id: str
    filename: str
    file_type: str
    text_content: str
    metadata: dict[str, Any]
    pages: list[dict[str, Any]]
    tables: list[dict[str, Any]]
    entities: list[dict[str, Any]]


class DocumentParser:
    SUPPORTED_TYPES = {
        "pdf": "pdf",
        "docx": "docx",
        "doc": "doc",
        "txt": "text",
        "md": "text",
        "json": "json",
        "csv": "csv",
        "xlsx": "excel",
        "xls": "excel",
    }

    def __init__(self):
        self._text_extractors = {
            "text": self._extract_text_plain,
            "json": self._extract_text_json,
            "csv": self._extract_text_csv,
        }

    def parse(self, file_path: str | Path, content: bytes) -> ParsedDocument:
        file_path = Path(file_path)
        file_ext = file_path.suffix.lower().lstrip(".")
        parser_type = self.SUPPORTED_TYPES.get(file_ext, "binary")

        document_id = str(uuid.uuid4())
        text_content = ""
        pages = []
        tables = []
        entities = []
        metadata = {
            "filename": file_path.name,
            "file_type": parser_type,
            "file_size_bytes": len(content),
            "parsed_at": datetime.utcnow().isoformat(),
        }

        if parser_type in self._text_extractors:
            text_content, pages, tables, entities = self._text_extractors[parser_type](content, metadata)
        else:
            text_content = f"[Binary file: {file_path.name}]"
            metadata["parse_status"] = "skipped"

        return ParsedDocument(
            document_id=document_id,
            filename=file_path.name,
            file_type=parser_type,
            text_content=text_content,
            metadata=metadata,
            pages=pages,
            tables=tables,
            entities=entities,
        )

    def _extract_text_plain(self, content: bytes, metadata: dict[str, Any]) -> tuple[str, list, list, list]:
        try:
            text = content.decode("utf-8", errors="ignore")
        except Exception:
            text = content.decode("latin-1", errors="ignore")

        metadata["parse_status"] = "parsed"
        metadata["char_count"] = len(text)
        metadata["line_count"] = text.count("\n") + 1

        pages = self._split_into_pages(text)
        entities = self._extract_entities(text)

        return text, pages, [], entities

    def _extract_text_json(self, content: bytes, metadata: dict[str, Any]) -> tuple[str, list, list, list]:
        try:
            data = json.loads(content)
            text = json.dumps(data, indent=2)
        except Exception:
            text = content.decode("utf-8", errors="ignore")

        metadata["parse_status"] = "parsed"
        metadata["char_count"] = len(text)
        metadata["json_valid"] = True

        entities = self._extract_entities(text)
        tables = self._extract_tables_from_json(data)

        return text, [], tables, entities

    def _extract_text_csv(self, content: bytes, metadata: dict[str, Any]) -> tuple[str, list, list, list]:
        try:
            text = content.decode("utf-8", errors="ignore")
        except Exception:
            text = content.decode("latin-1", errors="ignore")

        metadata["parse_status"] = "parsed"
        tables = self._extract_tables_from_csv(text)

        lines = text.split("\n")
        headers = lines[0].split(",") if lines else []
        metadata["columns"] = len(headers)
        metadata["rows"] = len([l for l in lines if l.strip()])

        entities = self._extract_entities(text)

        return text, [], tables, entities

    def _split_into_pages(self, text: str, chars_per_page: int = 3000) -> list[dict[str, Any]]:
        pages = []
        lines = text.split("\n")
        current_page = []
        current_chars = 0

        for line in lines:
            line_chars = len(line)
            if current_chars + line_chars > chars_per_page and current_page:
                pages.append({
                    "page_number": len(pages) + 1,
                    "content": "\n".join(current_page),
                    "char_count": current_chars,
                })
                current_page = []
                current_chars = 0
            current_page.append(line)
            current_chars += line_chars

        if current_page:
            pages.append({
                "page_number": len(pages) + 1,
                "content": "\n".join(current_page),
                "char_count": current_chars,
            })

        return pages

    def _extract_entities(self, text: str) -> list[dict[str, Any]]:
        entities = []

        money_patterns = [
            r"₹\s*[\d,]+\.?\d*\s*(?:crore|lac|lakh|million|billion|bn)?",
            r"Rs\.?\s*[\d,]+\.?\d*\s*(?:crore|lac|lakh|million|billion|bn)?",
            r"\$\s*[\d,]+\.?\d*\s*(?:million|billion|mn|bn)?",
            r"INR\s*[\d,]+\.?\d*\s*(?:crore|lac|lakh|million|billion|bn)?",
        ]
        for pattern in money_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches[:10]:
                entities.append({
                    "type": "money",
                    "value": match.strip(),
                    "context": text[max(0, text.find(match) - 50):text.find(match) + 100],
                })

        percent_patterns = [
            r"[\d,]+\.?\d*\s*%",
            r"(?:growth|increase|decrease|margin|rate)\s*(?:of)?\s*[\d,]+\.?\d*\s*%",
        ]
        for pattern in percent_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches[:10]:
                entities.append({
                    "type": "percentage",
                    "value": match.strip(),
                    "context": text[max(0, text.find(match) - 30):text.find(match) + 70],
                })

        date_patterns = [
            r"(?:FY\d{2,4}|FY\s*\d{2,4})",
            r"(?:Q[1-4]\s*\d{2,4})",
            r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches[:10]:
                entities.append({
                    "type": "date_period",
                    "value": match.strip(),
                    "context": text[max(0, text.find(match) - 30):text.find(match) + 50],
                })

        return entities

    def _extract_tables_from_json(self, data: Any) -> list[dict[str, Any]]:
        tables = []

        def flatten(obj: Any, prefix: str = "") -> list[dict[str, Any]]:
            result = []
            if isinstance(obj, dict):
                for key, value in obj.items():
                    result.extend(flatten(value, f"{prefix}.{key}" if prefix else key))
            elif isinstance(obj, list) and obj and isinstance(obj[0], dict):
                result.append(obj)
            return result

        flattened = flatten(data)
        for idx, table in enumerate(flattened[:5]):
            if isinstance(table, list) and table:
                tables.append({
                    "table_id": f"json_table_{idx}",
                    "row_count": len(table),
                    "columns": list(table[0].keys()) if isinstance(table[0], dict) else [],
                    "source": "json",
                })

        return tables

    def _extract_tables_from_csv(self, text: str) -> list[dict[str, Any]]:
        tables = []
        lines = [l for l in text.split("\n") if l.strip()]

        if len(lines) > 1:
            tables.append({
                "table_id": "csv_table_0",
                "row_count": len(lines) - 1,
                "columns": lines[0].split(","),
                "source": "csv",
            })

        return tables


document_parser = DocumentParser()
