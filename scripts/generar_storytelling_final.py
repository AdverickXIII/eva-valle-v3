"""Genera el Informe Ejecutivo Narrativo completo (10 capitulos)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.reports.storytelling_report import main
main()