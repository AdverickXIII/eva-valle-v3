"""Genera CHANGELOG.md y CONTRIBUTING.md."""
from pathlib import Path

CHANGELOG = '''# Changelog

## [3.0.0] - 2026-08-08

### Added
- Dashboard Streamlit con 8 paginas.
- Pagina Cultivos con 3 tablas.
- Arquitectura Hexagonal Modular.
- Pipeline CLI (Pasos 0-7).
- 15 tests unitarios (100% passed).
- Cache de analisis pesados.
- Manejo de errores global y logging.
- Persistencia de modelos con joblib.
- Documentacion completa.

### Fixed
- Gini negativo (ahora 0.979).
- Data leakage en target encoding.

### Changed
- 7 notebooks migrados a 87 modulos Python.
- matplotlib reemplazado por Plotly.

## [2.x] - 2026-07
- Serie de 7 notebooks Jupyter.

## [1.x] - 2026-07
- Prototipo inicial.
'''

CONTRIBUTING = '''# Guia de Contribucion

## Principios de Arquitectura
1. core/ es puro: sin I/O, sin imports de adapters/ ni ui/.
2. core/ports/ define contratos (inbound/outbound).
3. adapters/ implementa puertos (I/O real).
4. ui/ solo orquesta y renderiza.

## Flujo de Trabajo
1. Crea una rama: git checkout -b feature/mi-mejora
2. Cambios pequenos y enfocados.
3. Tests: python -m pytest tests/unit -v
4. Formato: ruff check core/ adapters/ ui/
5. Tipos: mypy core/ adapters/
6. Abre un Pull Request.

## Convenciones
- Type hints en funciones publicas.
- Docstrings estilo Google.
- Funciones puras en core/.
- Sin print(): usar core.logging.get_logger().
- Sin variables globales mutables.
- snake_case / PascalCase.

## Anadir un Test
1. Crea tests/unit/test_modulo.py.
2. Datos sinteticos pequenos y deterministas.
3. Aserciones con mensaje de error.
4. Ejecuta pytest y verifica.
'''

Path("CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
Path("CONTRIBUTING.md").write_text(CONTRIBUTING, encoding="utf-8")
print("[OK] CHANGELOG.md")
print("[OK] CONTRIBUTING.md")