.PHONY: install run test lint

install:
	pip install -r requirements-dev.txt

run:
	streamlit run app.py --server.port=8501

test:
	pytest tests/ -v --cov=core

lint:
	ruff check core/ adapters/ ui/ config/
