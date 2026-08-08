from pathlib import Path
import json

# --- app.py ---
app = '''"""EVA Valle v3.0 - Dashboard Analitico."""
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="EVA Valle del Cauca",
    page_icon="\\U0001F33E",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("\\U0001F33E EVA Agricola 2019-2024 - Valle del Cauca")
st.markdown("---")
st.info(
    "**Estado:** En construccion (Fase 3).\\n"
    "Las paginas estaran disponibles tras la Fase 4 (migracion)."
)
st.markdown("### Paginas del Dashboard")
st.markdown(
    "- Dashboard\\n- Descriptivo\\n- Diagnostico\\n"
    "- Predictivo\\n- Auditoria\\n- Configuracion"
)
st.markdown("---")
st.caption("EVA Valle v3.0 - Arquitectura Hexagonal - UPRA")
'''
Path("app.py").write_text(app, encoding="utf-8")
print("[OK] app.py")

# --- .vscode/settings.json ---
vs_settings = {
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
    "python.terminal.activateEnvironment": True,
    "editor.formatOnSave": True,
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.codeActionsOnSave": {"source.organizeImports": "explicit"}
    },
    "files.exclude": {
        "**/__pycache__": True,
        "**/.pytest_cache": True,
        "**/.mypy_cache": True,
        "**/.ruff_cache": True
    },
    "editor.tabSize": 4,
    "editor.rulers": [100],
    "files.encoding": "utf8"
}
Path(".vscode/settings.json").write_text(
    json.dumps(vs_settings, indent=4), encoding="utf-8"
)
print("[OK] .vscode/settings.json")

# --- .vscode/launch.json ---
vs_launch = {
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Streamlit App",
            "type": "debugpy",
            "request": "launch",
            "module": "streamlit",
            "args": ["run", "${workspaceFolder}/app.py", "--server.port=8501"],
            "console": "integratedTerminal",
            "justMyCode": False
        },
        {
            "name": "Script Actual",
            "type": "debugpy",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": False
        },
        {
            "name": "pytest",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/", "-v"],
            "console": "integratedTerminal",
            "justMyCode": False
        }
    ]
}
Path(".vscode/launch.json").write_text(
    json.dumps(vs_launch, indent=4), encoding="utf-8"
)
print("[OK] .vscode/launch.json")

# --- .vscode/tasks.json ---
vs_tasks = {
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Run Streamlit",
            "type": "shell",
            "command": "${workspaceFolder}/.venv/Scripts/python.exe",
            "args": ["-m", "streamlit", "run", "app.py"],
            "group": "build",
            "presentation": {"reveal": "always", "panel": "dedicated"}
        },
        {
            "label": "Run Tests",
            "type": "shell",
            "command": "${workspaceFolder}/.venv/Scripts/python.exe",
            "args": ["-m", "pytest", "tests/", "-v", "--cov=core"],
            "group": "test",
            "presentation": {"reveal": "always", "panel": "dedicated"}
        },
        {
            "label": "Lint Code",
            "type": "shell",
            "command": "${workspaceFolder}/.venv/Scripts/python.exe",
            "args": ["-m", "ruff", "check", "core/", "adapters/", "ui/", "config/"]
        }
    ]
}
Path(".vscode/tasks.json").write_text(
    json.dumps(vs_tasks, indent=4), encoding="utf-8"
)
print("[OK] .vscode/tasks.json")

# --- Makefile ---
makefile = (
    ".PHONY: install run test lint\n\n"
    "install:\n\tpip install -r requirements-dev.txt\n\n"
    "run:\n\tstreamlit run app.py --server.port=8501\n\n"
    "test:\n\tpytest tests/ -v --cov=core\n\n"
    "lint:\n\truff check core/ adapters/ ui/ config/\n"
)
Path("Makefile").write_text(makefile, encoding="utf-8")
print("[OK] Makefile")

# --- README.md ---
readme = (
    "# EVA Valle v3.0\n\n"
    "Dashboard analitico de produccion agricola del Valle del Cauca (UPRA).\n\n"
    "## Quick Start\n\n"
    "    .venv\\Scripts\\activate.bat\n"
    "    pip install -r requirements-dev.txt\n"
    "    streamlit run app.py\n\n"
    "## Arquitectura\n\n"
    "Hexagonal Modular (Ports & Adapters).\n\n"
    "- core/ - Nucleo de dominio\n"
    "- adapters/ - Infraestructura\n"
    "- ui/ - Interfaz Streamlit\n"
    "- config/ - Configuracion\n"
)
Path("README.md").write_text(readme, encoding="utf-8")
print("[OK] README.md")

print("\n6 archivos creados. Ahora ejecuta: streamlit run app.py")