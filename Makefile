.PHONY: setup run test test-security test-regression dry-run demo-gif clean

# ── Setup ─────────────────────────────────────────────────────────────────────
setup: rag-index
	@echo "✅ Setup complete. Run 'make run' to start the demo."

rag-index:
	@echo "Building RAG index..."
	python rag/indexer.py

# ── Run ───────────────────────────────────────────────────────────────────────
run:
	streamlit run demo/app.py

# ── Tests ─────────────────────────────────────────────────────────────────────
test: test-security test-regression

test-security:
	@echo "\n🔒 Running security isolation tests..."
	pytest tests/security/ -v

test-regression:
	@echo "\n📋 Running regression suite (CRITICAL only)..."
	python -m tests.regression.runner --critical

test-full:
	@echo "\n📋 Running full regression suite..."
	python -m tests.regression.runner --report

dry-run:
	@echo "\n🔍 Validating test case structure..."
	python -m tests.regression.runner --dry-run

# ── dbt ───────────────────────────────────────────────────────────────────────
dbt-run:
	cd dbt && dbt run

dbt-test:
	cd dbt && dbt test

dbt-all: dbt-run dbt-test

# ── Demo GIF ──────────────────────────────────────────────────────────────────
demo-gif:
	@echo "To capture a demo GIF:"
	@echo "  1. Run: make run"
	@echo "  2. Use Kap (macOS) or peek (Linux) to record demo/screenshots/"
	@echo "  3. Ask: 'What was total revenue in 1999?'"
	@echo "  4. Switch user to bob, ask the same question"
	@echo "  5. Save as demo/screenshots/demo.gif"
	@echo "  6. Update README.md: uncomment the ![Demo] line"

# ── Clean ─────────────────────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf rag/faiss_index
	@echo "Cleaned cache files. Run 'make rag-index' to rebuild the RAG index."
