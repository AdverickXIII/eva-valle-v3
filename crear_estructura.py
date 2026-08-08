from pathlib import Path

carpetas = [
    ".streamlit",
    "config",
    "core/ports/in", "core/ports/out", "core/entities",
    "core/analytics", "core/diagnostics", "core/ml",
    "core/audit", "core/modeling",
    "adapters/downloader", "adapters/storage",
    "adapters/ml_registry", "adapters/logging",
    "ui/pages", "ui/components", "ui/charts",
    "ui/assets/css", "ui/assets/icons", "ui/assets/images",
    "data/raw/upra", "data/processed/01_clean",
    "data/processed/02_modelo", "data/external",
    "outputs/tables", "outputs/figures", "outputs/reports",
    "models", "logs",
    "tests/unit", "tests/integration",
    "docs", "scripts",
    ".github/workflows",
    ".vscode",
]

for c in carpetas:
    Path(c).mkdir(parents=True, exist_ok=True)

paquetes = [
    "config", "core", "core/ports", "core/ports/in", "core/ports/out",
    "core/entities", "core/analytics", "core/diagnostics", "core/ml",
    "core/audit", "core/modeling",
    "adapters", "adapters/downloader", "adapters/storage",
    "adapters/ml_registry", "adapters/logging",
    "ui", "ui/pages", "ui/components", "ui/charts",
    "tests", "tests/unit", "tests/integration",
]

for p in paquetes:
    (Path(p) / "__init__.py").touch()

gitkeep_dirs = [
    "data/raw/upra", "data/processed/01_clean", "data/processed/02_modelo",
    "data/external", "outputs/tables", "outputs/figures",
    "outputs/reports", "models", "logs",
]

for d in gitkeep_dirs:
    (Path(d) / ".gitkeep").touch()

print("Estructura de carpetas creada exitosamente.")
print(f"Carpetas: {len(carpetas)}")
print(f"Paquetes Python (__init__.py): {len(paquetes)}")
print(f".gitkeep: {len(gitkeep_dirs)}")