from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Folder names are intentionally vague to match the tool names students see.
# The imported function names are the underlying implementations (unchanged).
from .clarify.tool import ask_user
from .papers.tool import arxiv_search
from .paper_text.tool import get_arxiv_paper_text
from .timeline.tool import get_user_tweets
from .fetch.tool import read_url
from .format.tool import render_digest
from .policy.tool import search_company_policy
from .social_search.tool import search_tweets
from .send.tool import send_telegram
from .lookup.tool import web_search as lookup_search
from .web_search.tool import web_search
from .webpage_reader.tool import read_webpage
from .calculator.tool import calculate
from .unit_converter.tool import convert_unit
from .datetime_tool.tool import current_datetime
from .weather_lookup.tool import get_weather
from .currency_converter.tool import convert_currency
from .pdf_text_extractor.tool import extract_pdf_text
from .csv_summary.tool import summarize_csv
from .markdown_summarizer.tool import summarize_markdown


# NOTE (starter_v0): tool names here are intentionally vague. These keys are the
# names the model sees AND the names data/eval_base.json + data/eval_research_extension.json
# match against. If a team renames a tool, it MUST stay in sync across ALL of:
#   artifacts/tools.yaml  ->  this dict  ->  data/eval_base.json + data/eval_research_extension.json
# Otherwise the eval raises "not declared in tools.yaml" or scores every call as a name mismatch.
TOOL_FUNCTIONS = {
    "clarify": ask_user,
    "timeline": get_user_tweets,
    "social_search": search_tweets,
    "lookup": lookup_search,
    "web_search": web_search,
    "webpage_reader": read_webpage,
    "calculator": calculate,
    "unit_converter": convert_unit,
    "datetime_tool": current_datetime,
    "weather_lookup": get_weather,
    "currency_converter": convert_currency,
    "pdf_text_extractor": extract_pdf_text,
    "csv_summary": summarize_csv,
    "markdown_summarizer": summarize_markdown,
    "fetch": read_url,
    "format": render_digest,
    "send": send_telegram,
    "policy": search_company_policy,
    "papers": arxiv_search,
    "paper_text": get_arxiv_paper_text,
}


def load_tool_declarations(path: Path) -> list[dict[str, Any]]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))["tools"]


def to_openai_tools(declarations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "type": "function",
        "function": {
            "name": item["name"],
            "description": item.get("description", ""),
            "parameters": item.get("parameters", {"type": "object", "properties": {}}),
        },
    } for item in declarations]

