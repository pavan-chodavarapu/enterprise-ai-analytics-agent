"""
Security isolation tests — the most important tests in the suite.

These prove that per-user row-level security works correctly.
Alice (East) must NEVER see West/South/Midwest data.
Bob (West) must NEVER see East/South/Midwest data.
Admin must see ALL regions.

Run: pytest tests/security/test_rls_isolation.py -v
"""
import os
import pytest
from dotenv import load_dotenv

load_dotenv()

# ── Helpers ───────────────────────────────────────────────────────────────────
def query_as_user(sql: str, user_id: str) -> str:
    os.environ["CURRENT_USER_ID"] = user_id
    from agent.tools.snowflake_tool import execute_snowflake_query
    return execute_snowflake_query(sql, user_id)


BASE_QUERY = """
    SELECT DISTINCT region
    FROM ANALYTICS_DB.MARTS.FCT_DAILY_SALES
    ORDER BY region
"""


# ── Alice: East only ──────────────────────────────────────────────────────────
class TestAliceEastOnly:

    def test_alice_sees_east(self):
        result = query_as_user(BASE_QUERY, "alice")
        assert "East" in result, "Alice should see East region data"

    def test_alice_cannot_see_west(self):
        result = query_as_user(BASE_QUERY, "alice")
        assert "West" not in result, "Alice must NOT see West region data"

    def test_alice_cannot_see_south(self):
        result = query_as_user(BASE_QUERY, "alice")
        assert "South" not in result, "Alice must NOT see South region data"

    def test_alice_cannot_see_midwest(self):
        result = query_as_user(BASE_QUERY, "alice")
        assert "Midwest" not in result, "Alice must NOT see Midwest region data"

    def test_alice_explicit_west_request_blocked(self):
        """Even if alice explicitly asks for West data, RLS blocks it."""
        west_query = """
            SELECT region, SUM(net_revenue) as revenue
            FROM ANALYTICS_DB.MARTS.FCT_DAILY_SALES
            WHERE region = 'West'
            GROUP BY region
        """
        result = query_as_user(west_query, "alice")
        # Result should be empty (INNER JOIN removes West rows)
        assert "West" not in result, "Explicit West query must return no data for alice"


# ── Bob: West only ────────────────────────────────────────────────────────────
class TestBobWestOnly:

    def test_bob_sees_west(self):
        result = query_as_user(BASE_QUERY, "bob")
        assert "West" in result, "Bob should see West region data"

    def test_bob_cannot_see_east(self):
        result = query_as_user(BASE_QUERY, "bob")
        assert "East" not in result, "Bob must NOT see East region data"

    def test_bob_cannot_see_alice_data(self):
        """Alice's East data must not appear in Bob's West query."""
        revenue_query = """
            SELECT state, SUM(net_revenue) as revenue
            FROM ANALYTICS_DB.MARTS.FCT_DAILY_SALES
            GROUP BY state ORDER BY revenue DESC
        """
        alice_result = query_as_user(revenue_query, "alice")
        bob_result   = query_as_user(revenue_query, "bob")

        # Extract states from each result — they must not overlap
        # (East states: NY, NJ, PA etc.; West states: CA, WA, OR etc.)
        east_states = ["NY", "NJ", "PA", "MA", "CT"]
        west_states = ["CA", "WA", "OR", "AZ", "CO"]

        for state in east_states:
            assert state not in bob_result, f"Bob must not see {state} (East state)"

        for state in west_states:
            assert state not in alice_result, f"Alice must not see {state} (West state)"


# ── Admin: sees all ───────────────────────────────────────────────────────────
class TestAdminSeesAll:

    def test_admin_sees_east(self):
        result = query_as_user(BASE_QUERY, "admin")
        assert "East" in result

    def test_admin_sees_west(self):
        result = query_as_user(BASE_QUERY, "admin")
        assert "West" in result

    def test_admin_row_count_exceeds_alice(self):
        """Admin must always see more rows than alice (who is East-only)."""
        count_query = "SELECT COUNT(*) as cnt FROM ANALYTICS_DB.MARTS.FCT_DAILY_SALES"
        alice_result = query_as_user(count_query, "alice")
        admin_result = query_as_user(count_query, "admin")

        # Extract numbers from result strings
        import re
        alice_count = int(re.search(r'\d+', alice_result).group())
        admin_count = int(re.search(r'\d+', admin_result).group())

        assert admin_count > alice_count, (
            f"Admin ({admin_count} rows) must see more than alice ({alice_count} rows)"
        )


# ── Write operation safety ────────────────────────────────────────────────────
class TestWriteOperationsBlocked:

    def test_delete_blocked(self):
        result = query_as_user("DELETE FROM ANALYTICS_DB.MARTS.FCT_DAILY_SALES", "alice")
        assert "blocked" in result.lower()

    def test_drop_blocked(self):
        result = query_as_user("DROP TABLE ANALYTICS_DB.MARTS.FCT_DAILY_SALES", "alice")
        assert "blocked" in result.lower()

    def test_insert_blocked(self):
        result = query_as_user(
            "INSERT INTO ANALYTICS_DB.MARTS.FCT_DAILY_SALES VALUES (1,2,3)", "alice"
        )
        assert "blocked" in result.lower()
