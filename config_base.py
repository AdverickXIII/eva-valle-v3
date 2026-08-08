from pathlib import Path

# --- .env ---
env = (
    "EVA_PROJECT_NAME=eva-valle-v3.0\n"
    "EVA_ENV=development\n"
    "EVA_DATA_RAW_PATH=data/raw/upra\n"
    "EVA_DATA_PROCESSED_PATH=data/processed\n"
    "EVA_OUTPUTS_PATH=outputs\n"
    "EVA_UPRA_BASE_URL=https://upra.gov.co/es-co/eva/eva-2024\n"
    "EVA_DOWNLOAD_TIMEOUT=60\n"
    "EVA_DOWNLOAD_RETRIES=3\n"
    "EVA_HEADLESS=true\n"
    "EVA_ST_THEME=dark\n"
    "EVA_ST_PAGE_WIDTH=wide\n"
    "EVA_LOG_LEVEL=INFO\n"
    "EVA_LOG_FILE=logs/eva_valle.log\n"
    "EVA_ML_RANDOM_STATE=42\n"
    "EVA_ML_TEST_SIZE=0.2\n"
    "EVA_ML_MODELS_PATH=models\n"
)
Path(".env").write_text(env, encoding="utf-8")
Path(".env.example").write_text("# Copiar a .env y ajustar\n" + env, encoding="utf-8")
print("[OK] .env y .env.example")

# --- .gitignore ---
gi = (
    ".venv/\nvenv/\n__pycache__/\n*.py[cod]\n*.so\n"
    "data/raw/\ndata/processed/\noutputs/\nmodels/\nlogs/\n"
    ".env\n.env.local\n"
    ".streamlit/secrets.toml\n"
    ".DS_Store\nThumbs.db\n"
    ".coverage\nhtmlcov/\n.pytest_cache/\n.mypy_cache/\n.ruff_cache/\n"
    "config_base.py\nconfig_app.py\ncrear_estructura.py\n"
)
Path(".gitignore").write_text(gi, encoding="utf-8")
print("[OK] .gitignore")

# --- .streamlit/config.toml ---
st_cfg = (
    '[theme]\n'
    'primaryColor = "#2E8B57"\n'
    'backgroundColor = "#0E1117"\n'
    'secondaryBackgroundColor = "#1A1F2E"\n'
    'textColor = "#FAFAFA"\n'
    'font = "sans serif"\n\n'
    '[server]\nheadless = true\nport = 8501\n'
    'enableCORS = false\nmaxUploadSize = 200\n\n'
    '[browser]\ngatherUsageStats = false\n\n'
    '[client]\nshowErrorDetails = false\ntoolbarMode = "minimal"\n'
)
Path(".streamlit/config.toml").write_text(st_cfg, encoding="utf-8")
print("[OK] .streamlit/config.toml")

# --- requirements-dev.txt ---
req_dev = (
    "-r requirements.txt\n\n"
    "pytest>=7.4.0\n"
    "pytest-cov>=4.1.0\n"
    "ruff>=0.1.0\n"
    "mypy>=1.7.0\n"
    "pre-commit>=3.5.0\n"
)
Path("requirements-dev.txt").write_text(req_dev, encoding="utf-8")
print("[OK] requirements-dev.txt")

print("\n4 archivos creados. Ahora ejecuta: pip install -r requirements-dev.txt")