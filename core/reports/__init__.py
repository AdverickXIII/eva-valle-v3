"""Generacion de reportes por municipio (Excel y PDF)."""
from core.reports.excel_report import build_municipality_excel
from core.reports.pdf_report import build_municipality_pdf

__all__ = ["build_municipality_excel", "build_municipality_pdf"]
