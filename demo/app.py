import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Enterprise Sales Analytics Agent",
    page_icon="📊",
    layout="wide",
)

# ── Sidebar: user selection + RLS info ───────────────────────────────────────
with st.sidebar:
    st.title("🔒 Access Control Demo")
    st.markdown(
        "Select a user to see row-level security in action. "
        "The agent enforces data access automatically — it cannot be bypassed."
    )

    user = st.selectbox(
        "Login as:",
        options=["alice", "bob", "admin"],
        help="alice=East only | bob=West only | admin=All regions",
    )

    region_map = {
        "alice": ("East", "🟦"),
        "bob":   ("West", "🟩"),
        "admin": ("All regions", "🟨"),
    }
    region_label, icon = region_map[user]

    st.info(f"{icon} **{user}** has access to: **{region_label}**")
    st.caption("Queries are wrapped in an INNER JOIN on the security table — not a WHERE clause. The LLM cannot bypass it.")

    os.environ["CURRENT_USER_ID"] = user

    st.divider()
    st.markdown("**Sample questions:**")
    for q in [
        "What was total revenue in 1999?",
        "Which store had the highest sales in 2001?",
        "Show transaction count by day of week",
        "What is the ATV for my region?",
        "Compare revenue in 2001 vs 2000",
    ]:
        st.caption(f"• {q}")

    if st.button("🗑 Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── Main: chat interface ──────────────────────────────────────────────────────
st.title("📊 Enterprise Sales Analytics Agent")
st.caption(
    "Powered by Claude + LangChain + Snowflake. "
    "Ask questions in plain English — security enforced per user."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# New input
if prompt := st.chat_input("Ask about sales data..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Querying data warehouse..."):
            try:
                from agent.agent import ask
                # Pass prior messages as chat history for multi-turn context
                history = st.session_state.messages[:-1]   # exclude current message
                response = ask(prompt, chat_history=history)
            except Exception as e:
                response = f"❌ Agent error: {str(e)}"
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
