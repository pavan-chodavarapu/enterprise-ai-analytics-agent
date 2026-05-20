import os
from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from pathlib import Path
from dotenv import load_dotenv

from agent.tools.snowflake_tool import execute_snowflake_query
from agent.tools.rag_tool import retrieve_business_context

load_dotenv()

# ── Load system prompt ────────────────────────────────────────────────────────
SYSTEM_PROMPT = (Path(__file__).parent / "system_prompt.md").read_text()

# ── Define LangChain tools ────────────────────────────────────────────────────
@tool
def query_sales_data(sql: str) -> str:
    """
    Execute a SELECT query against the enterprise sales data warehouse.
    Use this to answer questions about revenue, transactions, store performance,
    and regional sales metrics. Always write valid Snowflake SQL.
    The main table is: ANALYTICS_DB.MARTS.FCT_DAILY_SALES
    Columns: sale_date, sale_year, sale_month, sale_quarter, day_name,
             store_key, store_name, city, state, region,
             transaction_count, units_sold, net_revenue, net_profit, avg_transaction_value
    Row-level security is automatically enforced — you will only see data
    for regions your user is authorised to access.
    """
    user_id = os.environ.get("CURRENT_USER_ID", "alice")
    return execute_snowflake_query(sql, user_id)


@tool
def get_business_context(question: str) -> str:
    """
    Retrieve metric definitions and business rules relevant to the question.
    ALWAYS call this FIRST before writing SQL for any metric or calculation.
    Returns definitions for metrics like YoY growth, ATV, sell-through,
    and business rules like region mappings and date handling conventions.
    """
    return retrieve_business_context(question)


# ── Build agent ───────────────────────────────────────────────────────────────
def build_agent() -> AgentExecutor:
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        api_key=os.environ["ANTHROPIC_API_KEY"],
        temperature=0,
    )

    tools = [get_business_context, query_sales_data]

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=5)


def ask(question: str, chat_history: list = None) -> str:
    """Main entry point: ask the agent a question."""
    agent_executor = build_agent()
    result = agent_executor.invoke({
        "input": question,
        "chat_history": chat_history or [],
    })
    return result["output"]


if __name__ == "__main__":
    print(ask("What was total revenue last month by region?"))
