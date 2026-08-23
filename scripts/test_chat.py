"""Suite de regresion del Asistente: 14 checks con respuesta esperada."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.chat.engine import ask

CHECKS = [
    ("Cuanto platano produjo Sevilla en 2025?", "81,630"),
    ("banano Sevilla 2025", "81,630"),
    ("platn en Sevilla 2025", "81,630"),
    ("Sevlla platano 2025", "81,630"),
    ("Quien es el #1 en naranja?", "Top 5"),
    ("Como va Alcala en el ranking departamental?", "#34"),
    ("Por que crecio el platano en Sevilla?", "intensificacion"),
    ("Que producira Alcala en 2027?", "39,19"),
    ("Hay municipios en declive?", "Declive"),
    ("Que zona produce mas sin cana?", "Centro"),
    ("El dato de EVA es confiable?", "0 anomalias"),
    ("Dame un resumen de Alcala", "#34"),
    ("Compara Sevilla vs Alcala", "Ratio"),
    ("Cuanto tomate produjo Alcala en 2021?", "4,7"),
]
ok = 0
for q, esp in CHECKS:
    r = ask(q)
    pasa = esp in r["texto"]
    ok += pasa
    print(("PASS" if pasa else "FAIL"), "|", q, "->", r["texto"][:80].replace("\n", " "))

r1 = ask("Cuanto platano produjo Sevilla en 2025?")
r2 = ask("y su rendimiento?", ctx=r1["ctx"])
pasa = "18.0" in r2["texto"]
ok += pasa
print(("PASS" if pasa else "FAIL"), "| contexto 'y su rendimiento?' ->", r2["texto"][:80])

print(f"\nRESULTADO: {ok}/{len(CHECKS) + 1} correctas")
