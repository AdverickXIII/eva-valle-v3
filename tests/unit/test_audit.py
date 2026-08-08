"""Tests de auditorias (funciones puras)."""
import pandas as pd

from core.audit.models import AuditFinding
from core.audit.nulls import audit_nulls
from core.audit.structure import audit_structure


def test_nulls_sin_nulos_retorna_info():
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    findings = audit_nulls(df)
    assert isinstance(findings, list)
    assert all(isinstance(f, AuditFinding) for f in findings)
    assert all(f.severidad == "INFO" for f in findings)


def test_nulls_detecta_nulos():
    df = pd.DataFrame({"a": [1, None], "b": ["x", "y"]})
    findings = audit_nulls(df)
    assert any(f.severidad in ("ADVERTENCIA", "ERROR") for f in findings)


def test_structure_detecta_columnas():
    df = pd.DataFrame({"a": [1], "b": [2]})
    findings = audit_structure(df)
    assert isinstance(findings, list) and len(findings) >= 1
