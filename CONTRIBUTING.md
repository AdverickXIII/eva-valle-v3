# Guia de Contribucion

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
