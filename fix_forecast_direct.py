"""Reparacion directa de forecast.py: firma de _proyectar + integracion MLP."""
import re
from pathlib import Path

fp = Path("core/analytics/forecast.py")
content = fp.read_text(encoding="utf-8")

# 1) Reemplazar firma de _proyectar
content = re.sub(
    r'def _proyectar\(modelo: dict, n_steps: int\) -> np\.ndarray:',
    'def _proyectar(modelo: dict, n_steps: int, serie_original=None) -> np.ndarray:',
    content
)
print("[OK] Firma de _proyectar corregida")

# 2) Agregar caso MLP en la cadena if/elif/else
# Buscar el bloque de _proyectar y agregar antes del "else: # Holt"
pattern = r'(    elif nombre\.startswith\("Promedio movil"\):\n        return np\.full\(n_steps, modelo\["last_mean"\]\))'
replacement = r'\1\n    elif nombre == "MLP (5-8-4-1)":\n        return proyectar_mlp(modelo, n_steps, serie_original)'
content = re.sub(pattern, replacement, content)
print("[OK] Caso MLP agregado a _proyectar")

# 3) Corregir llamadas en backtest
content = content.replace(
    'pred = _proyectar(m, n_out)',
    'pred = _proyectar(m, n_out, serie)'
)
print("[OK] Llamadas en backtest corregidas")

# 4) Corregir llamada en proyectar_con_ic
content = content.replace(
    '_proyectar(res["modelo"], n_steps)',
    '_proyectar(res["modelo"], n_steps, serie)'
)
print("[OK] Llamada en proyectar_con_ic corregida")

# 5) Agregar caso MLP en elegir_mejor
pattern = r'(    elif nombre\.startswith\("Promedio movil"\):\n        modelo_full = modelo_promedio\(t_full, s_full, mejor\["modelo"\]\["ventana"\]\))\n    else:'
replacement = r'\1\n    elif nombre == "MLP (5-8-4-1)":\n        modelo_full = modelo_mlp(serie)\n    else:'
content = re.sub(pattern, replacement, content)
print("[OK] Caso MLP agregado a elegir_mejor")

fp.write_text(content, encoding="utf-8")
print("\n[OK] forecast.py reescrito completamente")

# Verificación
print("\n=== VERIFICACION ===")
print(f"¿Contiene 'serie_original'?: {content.count('serie_original')} veces")
print(f"¿Contiene 'MLP (5-8-4-1)'?: {'MLP (5-8-4-1)' in content}")
print(f"¿Contiene 'proyectar_mlp'?: {content.count('proyectar_mlp')} veces")