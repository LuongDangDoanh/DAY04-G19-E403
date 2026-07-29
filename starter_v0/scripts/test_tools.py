from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import TOOL_FUNCTIONS as T


class DeterministicToolTests(unittest.TestCase):
    def test_clarify_text_waits(self) -> None:
        result = T["clarify"]("Which account?", response_type="text")
        self.assertTrue(result["awaiting_user"])
        self.assertEqual(result["response_type"], "text")

    def test_clarify_yes_no_boundary(self) -> None:
        result = T["send"]("do not send", confirmed=False)
        self.assertEqual(result["status"], "needs_confirmation")

    def test_calculator_valid_and_unsafe(self) -> None:
        self.assertEqual(T["calculator"]("2 + 3 * 4")["result"], 14.0)
        self.assertEqual(T["calculator"]("__import__('os').getcwd").get("error"), "ValueError")

    def test_unit_converter_valid_and_invalid(self) -> None:
        self.assertEqual(T["unit_converter"](1, "km", "m")["result"], 1000.0)
        self.assertEqual(T["unit_converter"](1, "foo", "bar").get("error"), "ValueError")

    def test_source_quality_primary_and_invalid_url(self) -> None:
        result = T["source_quality"]("https://openai.com/research/example")
        self.assertIsNone(result.get("error"))
        self.assertEqual(result["tier"], "primary")
        self.assertEqual(T["source_quality"]("not-a-url").get("error"), "ValueError")

    def test_format_empty_and_items(self) -> None:
        self.assertEqual(T["format"]([])["item_count"], 0)
        result = T["format"]([{"title": "A", "url": "https://example.com", "summary": "Summary"}], template="brief")
        self.assertEqual(result["item_count"], 1)
        self.assertIn("example.com", result["markdown"])

    def test_missing_input_contracts(self) -> None:
        self.assertEqual(T["markdown_summarizer"]().get("error"), "ValueError")
        self.assertEqual(T["csv_summary"]().get("error"), "ValueError")
        self.assertEqual(T["pdf_text_extractor"]().get("error"), "ValueError")

    def test_datetime_contract(self) -> None:
        result = T["datetime_tool"](utc=True)
        self.assertEqual(result["utc"], True)
        self.assertTrue(result["value"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
