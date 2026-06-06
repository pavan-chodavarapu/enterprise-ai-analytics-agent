"""
Regression test runner — deployment gate.

Every prompt version change must pass this suite before deployment.
Exit 0 = safe to deploy. Exit 1 = CRITICAL failures detected = blocked.

Usage:
    python -m tests.regression.runner              # all tests
    python -m tests.regression.runner --critical   # CRITICAL only (fastest gate)
    python -m tests.regression.runner --dry-run    # validate structure, no API calls
    python -m tests.regression.runner --report     # save JSON + text report to disk
"""

import json
import sys
import os
import time
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

TEST_CASES_FILE  = Path(__file__).parent / "test_cases.json"
REPORTS_DIR      = Path(__file__).parent / "reports"

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
CATEGORY_ICONS = {
    "SECURITY":      "🔒",
    "SAFETY":        "🛡",
    "METRIC":        "📊",
    "HALLUCINATION": "👻",
    "AMBIGUITY":     "❓",
}


# ── Validation ────────────────────────────────────────────────────────────────
def validate_test_cases(cases: list) -> list[str]:
    """Validate test case structure — run in --dry-run mode."""
    errors = []
    required = {"id", "category", "severity", "input", "expected_behaviour", "rls_user"}
    valid_severities  = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
    valid_categories  = {"SECURITY", "SAFETY", "METRIC", "HALLUCINATION", "AMBIGUITY"}

    seen_ids = set()
    for case in cases:
        tc_id = case.get("id", "UNKNOWN")
        if tc_id in seen_ids:
            errors.append(f"{tc_id}: duplicate ID")
        seen_ids.add(tc_id)

        for field in required:
            if field not in case:
                errors.append(f"{tc_id}: missing required field '{field}'")

        if case.get("severity") not in valid_severities:
            errors.append(f"{tc_id}: invalid severity '{case.get('severity')}'")
        if case.get("category") not in valid_categories:
            errors.append(f"{tc_id}: invalid category '{case.get('category')}'")

        has_check = "must_contain" in case or "must_not_contain" in case
        if not has_check:
            errors.append(f"{tc_id}: no must_contain or must_not_contain — test cannot assert anything")

    return errors


# ── Runner ────────────────────────────────────────────────────────────────────
def run_tests(
    critical_only: bool = False,
    dry_run:       bool = False,
    save_report:   bool = False,
) -> int:
    cases = json.loads(TEST_CASES_FILE.read_text())

    # Dry run: validate structure only
    if dry_run:
        print(f"\n{'='*60}")
        print(f"  DRY RUN — validating {len(cases)} test cases")
        print(f"{'='*60}\n")
        errors = validate_test_cases(cases)
        if errors:
            print(f"❌ {len(errors)} validation error(s):\n")
            for e in errors:
                print(f"  • {e}")
            return 1
        print(f"✅ All {len(cases)} test cases are structurally valid\n")
        _print_coverage(cases)
        return 0

    if critical_only:
        cases = [c for c in cases if c["severity"] == "CRITICAL"]

    cases.sort(key=lambda c: SEVERITY_ORDER.get(c["severity"], 99))

    from agent.agent import ask

    passed, failed, errored = 0, 0, 0
    failures   = []
    timings    = []
    by_category = defaultdict(lambda: {"pass": 0, "fail": 0})

    print(f"\n{'='*60}")
    print(f"  REGRESSION SUITE — {len(cases)} cases{'  (CRITICAL only)' if critical_only else ''}")
    print(f"{'='*60}\n")

    for case in cases:
        tc_id    = case["id"]
        severity = case["severity"]
        category = case["category"]
        user_id  = case["rls_user"]
        icon     = CATEGORY_ICONS.get(category, "•")

        os.environ["CURRENT_USER_ID"] = user_id

        t0 = time.monotonic()
        try:
            response      = ask(case["input"])
            response_lower = response.lower()
            elapsed       = time.monotonic() - t0

            assertion_error = None
            for phrase in case.get("must_contain", []):
                if phrase.lower() not in response_lower:
                    assertion_error = f"Expected '{phrase}' not found in response"
                    break
            if not assertion_error:
                for phrase in case.get("must_not_contain", []):
                    if phrase.lower() in response_lower:
                        assertion_error = f"Forbidden term '{phrase}' found in response"
                        break

            if assertion_error:
                raise AssertionError(assertion_error)

            print(f"  ✅ {tc_id} [{severity:8}] {icon} {category:<14} ({elapsed:.1f}s)  user={user_id}")
            passed += 1
            by_category[category]["pass"] += 1
            timings.append((tc_id, elapsed, "PASS"))

        except AssertionError as e:
            elapsed = time.monotonic() - t0
            print(f"  ❌ {tc_id} [{severity:8}] {icon} {category:<14} ({elapsed:.1f}s)  FAIL: {e}")
            failed += 1
            by_category[category]["fail"] += 1
            failures.append({"id": tc_id, "severity": severity, "category": category, "reason": str(e)})
            timings.append((tc_id, elapsed, "FAIL"))

        except Exception as e:
            elapsed = time.monotonic() - t0
            print(f"  ⚠️  {tc_id} [{severity:8}] {icon} {category:<14} ({elapsed:.1f}s)  ERROR: {e}")
            errored += 1
            by_category[category]["fail"] += 1
            failures.append({"id": tc_id, "severity": severity, "category": category, "reason": f"ERROR: {e}"})
            timings.append((tc_id, elapsed, "ERROR"))

    # ── Summary ───────────────────────────────────────────────────────────────
    total_time = sum(t for _, t, _ in timings)
    print(f"\n{'='*60}")
    print(f"  Results: {passed} passed | {failed} failed | {errored} errors  ({total_time:.1f}s total)")
    print(f"{'='*60}\n")

    print("  By category:")
    for cat, counts in sorted(by_category.items()):
        icon   = CATEGORY_ICONS.get(cat, "•")
        status = "✅" if counts["fail"] == 0 else "❌"
        print(f"    {status} {icon} {cat:<14}  {counts['pass']} pass / {counts['fail']} fail")
    print()

    critical_failures = [f for f in failures if f["severity"] == "CRITICAL"]

    if save_report:
        _save_report(cases, failures, timings, passed, failed, errored)

    if critical_failures:
        print("🚨 CRITICAL FAILURES — deployment blocked:\n")
        for f in critical_failures:
            print(f"  {f['id']} [{f['category']}]: {f['reason']}")
        print()
        return 1

    if failed > 0:
        print(f"⚠️  {failed} non-critical failure(s) — review before deploying\n")
        return 0

    print("✅ All tests passed — safe to deploy\n")
    return 0


# ── Helpers ───────────────────────────────────────────────────────────────────
def _print_coverage(cases: list):
    by_cat = defaultdict(lambda: defaultdict(int))
    for c in cases:
        by_cat[c["category"]][c["severity"]] += 1

    print("  Coverage:")
    for cat in sorted(by_cat):
        icon = CATEGORY_ICONS.get(cat, "•")
        sev_counts = ", ".join(
            f"{sev}:{cnt}"
            for sev, cnt in sorted(by_cat[cat].items(), key=lambda x: SEVERITY_ORDER.get(x[0], 99))
        )
        print(f"    {icon} {cat:<14}  {sev_counts}")
    print()


def _save_report(cases, failures, timings, passed, failed, errored):
    REPORTS_DIR.mkdir(exist_ok=True)
    ts = int(time.time())

    report = {
        "timestamp": ts,
        "summary": {"passed": passed, "failed": failed, "errored": errored, "total": len(cases)},
        "failures": failures,
        "timings": [{"id": i, "seconds": round(t, 2), "result": r} for i, t, r in timings],
    }

    json_path = REPORTS_DIR / f"report_{ts}.json"
    json_path.write_text(json.dumps(report, indent=2))

    text_path = REPORTS_DIR / f"report_{ts}.txt"
    lines = [
        f"Regression Report — {ts}",
        f"Passed: {passed} | Failed: {failed} | Errors: {errored}",
        "",
        "Failures:",
    ]
    for f in failures:
        lines.append(f"  [{f['severity']}] {f['id']} ({f['category']}): {f['reason']}")

    text_path.write_text("\n".join(lines))
    print(f"  📄 Report saved → {json_path}\n")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sys.exit(run_tests(
        critical_only = "--critical"  in sys.argv,
        dry_run       = "--dry-run"   in sys.argv,
        save_report   = "--report"    in sys.argv,
    ))
