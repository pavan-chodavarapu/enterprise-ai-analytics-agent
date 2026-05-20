"""
Regression test runner — deployment gate.

Usage:
    python -m tests.regression.runner           # runs all tests
    python -m tests.regression.runner --critical # runs CRITICAL only

Exit 0 = all tests pass = safe to use.
Exit 1 = one or more CRITICAL failures = block deployment.
"""
import json
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TEST_CASES_FILE = Path(__file__).parent / "test_cases.json"


def run_tests(critical_only: bool = False) -> int:
    """Run regression tests. Returns exit code (0=pass, 1=fail)."""
    from agent.agent import ask

    cases = json.loads(TEST_CASES_FILE.read_text())
    if critical_only:
        cases = [c for c in cases if c["severity"] == "CRITICAL"]

    passed, failed, skipped = 0, 0, 0
    failures = []

    print(f"\n{'='*60}")
    print(f"  REGRESSION TEST SUITE — {len(cases)} cases")
    print(f"{'='*60}\n")

    for case in cases:
        tc_id    = case["id"]
        severity = case["severity"]
        user_id  = case["rls_user"]

        # Set the user context for this test
        os.environ["CURRENT_USER_ID"] = user_id

        try:
            response = ask(case["input"])
            response_lower = response.lower()

            # Check must_contain
            for phrase in case.get("must_contain", []):
                if phrase.lower() not in response_lower:
                    raise AssertionError(f"Expected '{phrase}' in response")

            # Check must_not_contain
            for phrase in case.get("must_not_contain", []):
                if phrase.lower() in response_lower:
                    raise AssertionError(f"Found forbidden term '{phrase}' in response")

            print(f"  ✅ {tc_id} [{severity}] PASS — {case['category']}")
            passed += 1

        except AssertionError as e:
            print(f"  ❌ {tc_id} [{severity}] FAIL — {e}")
            failed += 1
            failures.append((tc_id, severity, str(e)))

        except Exception as e:
            print(f"  ⚠️  {tc_id} [{severity}] ERROR — {e}")
            skipped += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"  Results: {passed} passed | {failed} failed | {skipped} errors")
    print(f"{'='*60}\n")

    critical_failures = [f for f in failures if f[1] == "CRITICAL"]
    if critical_failures:
        print("🚨 CRITICAL FAILURES — deployment blocked:\n")
        for tc_id, _, reason in critical_failures:
            print(f"  {tc_id}: {reason}")
        print()
        return 1

    if failed > 0:
        print(f"⚠️  {failed} non-critical failure(s) — review before deploying\n")
        return 0   # non-critical failures don't block

    print("✅ All tests passed — safe to deploy\n")
    return 0


if __name__ == "__main__":
    critical_only = "--critical" in sys.argv
    sys.exit(run_tests(critical_only=critical_only))
