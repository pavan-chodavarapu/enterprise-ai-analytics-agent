"""
LangChain agent wiring — Claude API + two tools + RLS enforcement.

Architecture:
  User question
    → get_business_context (RAG: fetch metric definitions first)
    → query_sales_data (Snowflake: RLS-enforced SELECT only)
    → formatted answer

The agent is cached at module level. build_agent() is only called once
per process — subsequent ask() calls reuse the same executor.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from agent.tools.snowflake_tool import execute_snowflake_query
from agent.tools.rag_tool import retrieve_business_context

load_dotenv()

SYSTEM_PROMPT = (Path(__file__).parent / "system_prompt.md").read_text()

# Module-level cache — one executor per process (thread-safe for Streamlit)
_executor: AgentExecutor | None = None


# ── Tool definitions ──────────────────────────────────────────────────────────
@tool
def get_business_context(question: str) -> str:
    """
    Retrieve metric definitions and business rules for this question.
    ALWAYS call this FIRST before writing any SQL.
    Returns the correct formula for metrics like YoY growth, ATV, net revenue,
    and business rules like region mappings, return handling, and date conventions.
    """
    return retrieve_business_context(question)


@tool
def query_sales_data(sql: str) -> str:
    """
    Execute a SELECT query against the enterprise sales data warehouse.
    Use this to answer questions about revenue, transactions, and store performance.

    Main table: ANALYTICS_DB.MARTS.FCT_DAILY_SALES
    Columns:
      sale_date (DATE), sale_year (INT), sale_month (1-12), sale_quarter (1-4),
      day_name (Monday-Sunday), store_key (INT), store_name (VARCHAR),
      city (VARCHAR), state (VARCHAR), region (VARCHAR),
      transaction_count (INT), units_sold (INT),
      net_revenue (FLOAT), net_profit (FLOAT), avg_transaction_value (FLOAT)

    Data range: years 1998-2002 (TPC-DS benchmark dataset).
    Row-level security is enforced automatically — results are pre-filtered
    to the current user's authorised regions. Do not add WHERE region = ... clauses.
    """
    user_id = os.environ.get("CURRENT_USER_ID", "alice")
    return execute_snowflake_query(sql, user_id)


# ── Agent builder ─────────────────────────────────────────────────────────────
def _build_executor() -> AgentExecutor:
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        api_key=os.environ["ANTHROPIC_API_KEY"],
        temperature=0,
        max_tokens=4096,
    )

    tools = [get_business_context, query_sales_data]

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=6)


def _get_executor() -> AgentExecutor:
    global _executor
    if _executor is None:
        _executor = _build_executor()
    return _executor


# ── Public interface ──────────────────────────────────────────────────────────
def _to_lc_messages(history: list) -> list:
    """Convert Streamlit-style [{"role": ..., "content": ...}] to LangChain messages."""
    result = []
    for msg in (history or []):
        if isinstance(msg, dict):
            if msg["role"] == "user":
                result.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                result.append(AIMessage(content=msg["content"]))
        else:
            result.append(msg)
    return result


def ask(question: str, chat_history: list = None) -> str:
    """Main entry point — ask the agent a question."""
    result = _get_executor().invoke({
        "input": question,
        "chat_history": _to_lc_messages(chat_history),
    })
    return result["output"]


if __name__ == "__main__":
    # Quick smoke test
    print(ask("What was total net revenue in 1999 by region?"))
