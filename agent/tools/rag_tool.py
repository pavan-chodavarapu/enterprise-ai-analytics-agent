import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Simple file-based RAG (no vector DB needed for v1) ───────────────────────
# Reads knowledge markdown files and returns the most relevant one
# based on keyword matching. Replace with FAISS or Cortex Search in v2.

KNOWLEDGE_DIR = Path(__file__).parent.parent / "rag" / "knowledge"


def retrieve_business_context(question: str) -> str:
    """
    Retrieves relevant business context for the question from knowledge docs.
    Used by the agent before generating SQL to ensure correct metric definitions.

    v1: Keyword matching over markdown files.
    v2: Replace with FAISS embeddings or Snowflake Cortex Search.
    """
    question_lower = question.lower()
    results = []

    for doc_path in KNOWLEDGE_DIR.glob("*.md"):
        content = doc_path.read_text()
        # Score by keyword overlap
        keywords_found = sum(
            1 for word in question_lower.split()
            if len(word) > 3 and word in content.lower()
        )
        if keywords_found > 0:
            results.append((keywords_found, doc_path.stem, content))

    if not results:
        return "No specific business rules found for this question. Proceed with standard SQL patterns."

    # Return top-2 most relevant docs
    results.sort(key=lambda x: -x[0])
    top_docs = results[:2]

    output = "📚 **Relevant business context retrieved:**\n\n"
    for _, name, content in top_docs:
        output += f"### {name.replace('_', ' ').title()}\n{content}\n\n---\n\n"

    return output
