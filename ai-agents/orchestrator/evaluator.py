"""
Evaluator — Self-Improvement Layer, Level 1 (Shield EPC HSE pipeline)

Only job: read existing pipeline outputs and score/flag them.
Does NOT call any AI provider. Does NOT change safety rules or
pipeline behavior. Deterministic checks only (no AI-based checks yet).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from logger import log_run

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def load_json(filename):
    path = PROJECT_ROOT / filename
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def evaluate():
    stage2 = load_json("stage2_validated.json")
    report = load_json("Verification_Report.json")

    findings = []
    score = 1.0

    if stage2 is None:
        findings.append("stage2_validated.json not found")
        score -= 0.5
    else:
        checks = stage2.get("checks", {})
        if not checks.get("envelope_schema_valid", False):
            findings.append("schema invalid")
            score -= 0.3
        if not checks.get("human_in_the_loop_respected", False):
            findings.append("human-in-the-loop not respected")
            score -= 0.5
        bypass_detected = checks.get("architecture_bypass_detected", None)
        if bypass_detected is None:
            findings.append("architecture_bypass_detected missing in stage2 checks")
            score -= 0.2

        if report is None:
            findings.append("Verification_Report.json not found")
            score -= 0.3
        else:
            s2 = PROJECT_ROOT / "stage2_validated.json"
            rp = PROJECT_ROOT / "Verification_Report.json"
            if rp.stat().st_mtime < s2.stat().st_mtime:
                findings.append(
                    "Verification_Report.json is older than stage2_validated.json (possibly stale)"
                )
                score -= 0.3

        if report is not None:
            recommendations = report.get("recommendations", [])

            if not isinstance(recommendations, list):
                recommendations = [recommendations]

            def flatten_text(value):
                if isinstance(value, list):
                    return " ".join(flatten_text(item) for item in value)
                if isinstance(value, dict):
                    return " ".join(
                        flatten_text(item) for item in value.values()
                    )
                return str(value)

            report_text = flatten_text(recommendations) + " " + str(
                report.get("note", "")
            )

            report_lower = report_text.lower()

            actionable_bypass_phrases = (
                "fix architecture bypass",
                "implement architecture bypass mitigation",
                "bypass mitigation missing",
                "architecture bypass detected",
                "architecture bypass violation",
                "bypass the frozen architecture",
            )

            mentions_bypass_issue = any(
                phrase in report_lower
                for phrase in actionable_bypass_phrases
            )

            if bypass_detected is False and mentions_bypass_issue:
                findings.append(
                    "INCONSISTENCY: stage2 says architecture_bypass_detected=false, "
                    "but Verification_Report.json still recommends bypass mitigation"
                )
                score -= 0.4

    score = max(0.0, round(score, 2))
    status = "pass" if score >= 0.7 and not findings else "flagged"

    record = log_run(
        stage="evaluator",
        provider=None,
        status=status,
        input_file="stage2_validated.json + Verification_Report.json",
        notes="; ".join(findings) if findings else "no issues found",
    )
    record["score"] = score
    record["findings"] = findings

    output_path = PROJECT_ROOT / "audit" / "learning" / "evaluation_result.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(record, f, indent=2)

    print(json.dumps(record, indent=2))
    print(f"Evaluation result written to: {output_path}")

    return record


if __name__ == "__main__":
    result = evaluate()
    # exit 0 = pass, 2 = flagged (distinct from crash = 1)
    sys.exit(2 if result["findings"] or result["score"] < 0.7 else 0)
