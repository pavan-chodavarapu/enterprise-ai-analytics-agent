"""
RAG indexer: loads knowledge documents from markdown files and builds
a FAISS vector index for semantic search by the agent.

Run once before starting the agent:
    python rag/indexer.py

The index is saved locally and loaded by rag_tool.py at runtime.
No API calls needed — uses local sentence-transformers embeddings.
"""

import sys
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
INDEX_PATH = Path(__file__).parent / "faiss_index"


def load_knowledge_docs():
    from langchain.text_splitter import MarkdownTextSplitter
    from langchain.docstore.document import Document

    docs = []
    for md_file in sorted(KNOWLEDGE_DIR.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        splitter = MarkdownTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.create_documents([text])
        for chunk in chunks:
            chunk.metadata["source"] = md_file.name
        docs.extend(chunks)
        print(f"  Loaded {len(chunks)} chunks from {md_file.name}")
    return docs


def get_embeddings():
    from langchain_community.embeddings import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
    )


def build_index():
    from langchain_community.vectorstores import FAISS

    print("Loading knowledge documents...")
    docs = load_knowledge_docs()
    print(f"  Total: {len(docs)} chunks\n")

    print("Building FAISS index (local embeddings — no API call)...")
    embeddings = get_embeddings()
    index = FAISS.from_documents(docs, embeddings)
    index.save_local(str(INDEX_PATH))
    print(f"  Index saved → {INDEX_PATH}\n")
    print("Done. Run the agent with: streamlit run demo/app.py")


def load_index():
    """Load existing index — called by rag_tool.py at agent startup."""
    from langchain_community.vectorstores import FAISS

    if not INDEX_PATH.exists():
        raise FileNotFoundError(
            f"FAISS index not found at {INDEX_PATH}. "
            "Run 'python rag/indexer.py' first."
        )
    return FAISS.load_local(
        str(INDEX_PATH),
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )


def search(query: str, k: int = 3) -> list[str]:
    """Semantic search — returns top-k document chunks as plain text."""
    index = load_index()
    results = index.similarity_search(query, k=k)
    return [doc.page_content for doc in results]


if __name__ == "__main__":
    build_index()
