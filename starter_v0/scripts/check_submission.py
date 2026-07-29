from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import TOOL_FUNCTIONS
failures: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def latest_run(version: str, suite: str) -> Path | None:
    files = sorted((ROOT / "runs").glob(f"{version}_B_{suite}_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def main() -> int:
    declarations = yaml.safe_load((ROOT / "artifacts/tools.yaml").read_text(encoding="utf-8"))["tools"]
    names = [item["name"] for item in declarations]
    require(len(names) >= 5, "tools.yaml must declare at least 5 tools")
    require(len(names) == len(set(names)), "tools.yaml contains duplicate tool names")
    require(set(names) == set(TOOL_FUNCTIONS), "tools.yaml and TOOL_FUNCTIONS registry are out of sync")
    require((ROOT / "tools/source_quality/TOOL.md").exists(), "new tool is missing TOOL.md")
    require((ROOT / "tools/source_quality/tool.py").exists(), "new tool is missing implementation")

    group = read_json(ROOT / "data/eval_group.json")
    cases = group.get("cases", [])
    require(len(cases) == 10, "eval_group.json must contain exactly 10 cases")
    require(sum("query" in case for case in cases) == 5, "eval_group.json must contain exactly 5 single-turn cases")
    require(sum("turns" in case for case in cases) == 5, "eval_group.json must contain exactly 5 multi-turn cases")
    allowed = set(group.get("allowed_failure_types", []))
    for case in cases:
        require(case.get("phase") == "B", f"{case.get('id')} phase must be B")
        require(case.get("failure_type") in allowed, f"{case.get('id')} has invalid failure_type")
        require(bool(case.get("metadata", {}).get("what_it_tests")), f"{case.get('id')} missing metadata.what_it_tests")
        if "turns" in case:
            require(bool(case["turns"]) and case["turns"][-1].get("role") == "user", f"{case.get('id')} must end in a user turn")

    with (ROOT / "artifacts/version_log.csv").open(encoding="utf-8", newline="") as file:
        version_rows = list(csv.DictReader(file))
    require({row.get("version") for row in version_rows} >= {"v0", "v1", "v2", "v3"}, "version_log.csv must contain v0-v3")

    for version in ("v0", "v1", "v2", "v3"):
        path = latest_run(version, "base")
        require(path is not None, f"missing base run for {version}")
        if path:
            run = read_json(path)
            summary = run.get("summary", {})
            require(summary.get("provider_error_cases") == 0, f"{path.name} has provider errors")
            require(summary.get("measured_cases") == summary.get("total_cases"), f"{path.name} has unmeasured cases")
            require(run.get("prompt_hash") and run.get("tools_hash"), f"{path.name} missing hashes")

    group_run = latest_run("v3", "group")
    require(group_run is not None, "missing v3 group run")
    if group_run:
        summary = read_json(group_run).get("summary", {})
        require(summary.get("total_cases") == 10, "group run must contain 10 cases")
        require(summary.get("passed_cases") == 10, "group run must pass all 10 cases")
        require(summary.get("provider_error_cases") == 0, "group run has provider errors")

    require((ROOT / "app.py").exists(), "missing UI entrypoint app.py")
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    for required_text in ("run_model_tool_loop", "tool_events", "write_transcript", "artifact_version"):
        require(required_text in app, f"app.py missing UI contract field: {required_text}")
    require(any(line.lower().startswith("streamlit>=1.30.0") for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()), "requirements.txt missing streamlit>=1.30.0")

    transcript_files = list((ROOT / "transcripts").glob("*.transcript.json"))
    require(bool(transcript_files), "missing transcript evidence")
    if transcript_files:
        transcript = read_json(sorted(transcript_files, key=lambda p: p.stat().st_mtime, reverse=True)[0])
        require(len(transcript.get("turns", [])) >= 3, "live transcript must contain at least 3 turns")
        require("artifact_version" in transcript and "transcript_id" in transcript, "transcript missing artifact metadata")

    if failures:
        print("SUBMISSION CHECK: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("SUBMISSION CHECK: PASS")
    print(f"tools={len(names)} group_cases={len(cases)} base_versions=4 transcripts={len(transcript_files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
