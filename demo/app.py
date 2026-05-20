import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Enterprise Sales Analytics Agent",
    page_icon="📊",
    layout="wide",
)

# ── Sidebar: user selection ───────────────────────────────────────────────────
with st.sidebar:
    st.title("🔒 Access Control Demo")
    st.markdown("Select a user to see how RLS filters data per identity.")

    user = st.selectbox(
        "Login as:",
        options=["alice", "bob", "admin"],
        help="alice=East only | bob=West only | admin=All regions",
    )

    st.markdown(f"""
    **Access for `{user}`:**
    - `alice` → East region only
    - `bob`   → West region only
    - `admin` → All regions
    """)

    os.environ["CURRENT_USER_ID"] = user
    st.divider()
    st.caption("Row-level security is enforced automatically — the agent cannot bypass it.")

# ── Main: chat interface ──────────────────────────────────────────────────────
st.title("📊 Enterprise Sales Analytics Agent")
st.caption("Ask questions about sales data in plain English. Security is enforced per user.")

# Sample questions
with st.expander("💡 Try these questions"):
    st.markdown("""
    - What was total revenue last month?
    - Which store had the highest sales this year?
    - Show me transaction count by day of week
    - What is the average transaction value for my region?
    - Compare this month's revenue to last year
    """)

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
if prompt := st.chat_input("Ask about sales data..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Querying data warehouse..."):
            from agent.agent import ask
            response = ask(prompt)
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
