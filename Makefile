.PHONY: install run test smoke lint lint-strict

install:
	pip install -r requirements-dev.txt

run:
	streamlit run app.py --server.port=8501

test:
	pytest tests/ -v --cov=core

# Prueba de humo: ejecuta app.py y cada pagina como un admin logueado.
smoke:
	pytest tests/smoke -v

# Mismo comando y reglas que el CI (ver ruff.toml: solo errores reales).
lint:
	ruff check app.py core/ adapters/ ui/ config/ tests/

# Conjunto amplio de reglas de ruff (ignora ruff.toml): estilo, limpieza, etc.
# No bloquea el CI; sirve para ir reduciendo la deuda tecnica.
lint-strict:
	ruff check --isolated core/ adapters/ ui/ config/
