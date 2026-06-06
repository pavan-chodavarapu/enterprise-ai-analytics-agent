"""
RAG retrieval tool for the LangChain agent.

Uses FAISS vector search when the index exists (run rag/indexer.py first).
Falls back to keyword matching over raw markdown files if the index is absent.

This separation means the agent works out of the box without the index,
and upgrades silently to semantic search once it's built.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

_PROJECT_ROOT = Path(__file__).parent.parent.parent   # agent/tools/ → agent/ → project root
KNOWLEDGE_DIR = _PROJECT_ROOT / "rag" / "knowledge"
INDEX_PATH    = _PROJECT_ROOT / "rag" / "faiss_index"


# ── FAISS semantic search (preferred) ────────────────────────────────────────
def _faiss_search(question: str, k: int = 3) -> str | None:
    """Returns top-k chunks from the FAISS index, or None if unavailable."""
    if not INDEX_PATH.exists():
        return None
    try:
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
        )
        index = FAISS.load_local(
            str(INDEX_PATH), embeddings, allow_dangerous_deserialization=True
        )
        results = index.similarity_search(question, k=k)
        chunks = [doc.page_content for doc in results]
        return "📚 **Relevant business context (semantic search):**\n\n" + "\n\n---\n\n".join(chunks)
    except Exception:
        return None


# ── Keyword fallback ──────────────────────────────────────────────────────────
def _keyword_search(question: str) -> str:
    """Keyword overlap search over raw markdown files — always available."""
    question_lower = question.lower()
    results = []

    for doc_path in KNOWLEDGE_DIR.glob("*.md"):
        content = doc_path.read_text(encoding="utf-8")
        score = sum(
            1 for word in question_lower.split()
            if len(word) > 3 and word in content.lower()
        )
        if score > 0:
            results.append((score, doc_path.stem, content))

    if not results:
        return (
            "No specific business rules found for this question. "
            "Proceed with standard SQL patterns and the column list in your instructions."
        )

    results.sort(key=lambda x: -x[0])
    top = results[:2]
    output = "📚 **Relevant business context (keyword match):**\n\n"
    for _, name, content in top:
        output += f"### {name.replace('_', ' ').title()}\n{content}\n\n---\n\n"
    return output


# ── Public interface ──────────────────────────────────────────────────────────
def retrieve_business_context(question: str) -> str:
    """
    Retrieve metric definitions and business rules for a question.
    Called by the agent before generating SQL to ensure correct formulas.

    Tries FAISS semantic search first; falls back to keyword matching.
    """
    result = _faiss_search(question)
    if result:
        return result
    return _keyword_search(question)
