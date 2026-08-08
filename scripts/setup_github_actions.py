"""Crea .github/workflows/tests.yml para CI/CD."""
from pathlib import Path

WORKFLOW = '''name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.14
        uses: actions/setup-python@v5
        with:
          python-version: "3.14"

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt

      - name: Run tests
        run: |
          python -m pytest tests/unit -v --tb=short

      - name: Test coverage
        run: |
          python -m pytest tests/unit --cov=core --cov-report=term-missing
        continue-on-error: true
'''

README_BADGE = '''[![Tests](https://github.com/AdverickXIII/eva-valle-v3/actions/workflows/tests.yml/badge.svg)](https://github.com/AdverickXIII/eva-valle-v3/actions)
'''

if __name__ == "__main__":
    # 1. Crear workflow
    workflow_path = Path(".github/workflows/tests.yml")
    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(WORKFLOW, encoding="utf-8")
    print(f"[OK] {workflow_path}")

    # 2. Agregar badge al README si no existe
    readme = Path("README.md")
    if readme.exists():
        content = readme.read_text(encoding="utf-8")
        if "actions/workflows/tests.yml/badge.svg" not in content:
            # Insertar badge después del primer título
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("# "):
                    lines.insert(i + 2, README_BADGE.strip())
                    break
            readme.write_text("\n".join(lines), encoding="utf-8")
            print("[OK] README.md (badge de CI agregado)")
        else:
            print("[INFO] README.md ya tiene el badge")

    print("\nListo. Haz commit y push para activar CI:")
    print("  git add .")
    print("  git commit -m 'Add CI/CD with GitHub Actions'")
    print("  git push")
    print("\nLuego ve a: https://github.com/AdverickXIII/eva-valle-v3/actions")