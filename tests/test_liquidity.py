"""
tests/test_liquidity.py

Valida core/liquidity.py contra los números REALES del workbook
(43 comunidades, 365 días, ya validados manualmente en Riesgo!D14, D32, D36).

No es un test sintético: lee del SQLite generado por etl/import_excel.py,
es decir, prueba la cadena completa Excel -> SQLite -> core.

Correr con: pytest tests/test_liquidity.py -v
"""
import sqlite3
import sys
import os

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.liquidity import resumen_riesgo

DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "raw", "saldos_diarios.db"
)


@pytest.fixture(scope="module")
def df():
    if not os.path.exists(DB_PATH):
        pytest.skip(
            "No existe data/raw/saldos_diarios.db. "
            "Correr antes: python etl/import_excel.py <ruta_xlsx> --to sqlite"
        )
    con = sqlite3.connect(DB_PATH)
    data = pd.read_sql("SELECT * FROM saldos_diarios", con, parse_dates=["fecha"])
    con.close()
    return data


@pytest.fixture(scope="module")
def resumen(df):
    return resumen_riesgo(df)


def test_cobertura_datos(resumen):
    # Ancla: 43 comunidades, 365 días (abril 2025 - marzo 2026)
    assert resumen["n_comunidades"] == 43
    assert resumen["n_dias"] == 365


def test_saldo_promedio_administrado(resumen):
    # Ancla validada: ~$1.02B CLP
    assert resumen["saldo_promedio"] == pytest.approx(1_022_713_404, rel=0.01)


def test_capital_invertible_p5(resumen):
    # Ancla validada: ~$885.7M CLP (Riesgo!D14)
    assert resumen["capital_invertible_recomendado"] == pytest.approx(
        885_693_901, rel=0.001
    )


def test_pct_invertible_recomendado(resumen):
    # Ancla validada: 86.6% del promedio (Riesgo!D16 / D36)
    assert resumen["pct_invertible_recomendado"] == pytest.approx(0.866, abs=0.001)


def test_multiplo_diversificacion(resumen):
    # EL NUMERO CLAVE DEL NEGOCIO. Ancla validada: 1.32x (Riesgo!D32)
    assert resumen["multiplo_diversificacion"] == pytest.approx(1.32, abs=0.005)
    # y debe ser > 1.0 siempre: la tesis central es que diversificar ayuda
    assert resumen["multiplo_diversificacion"] > 1.0


def test_suma_minimos_individuales_menor_que_minimo_agregado(resumen):
    # El piso naive (suma de mínimos por comunidad) debe ser MENOR
    # al mínimo real del agregado -- por eso existe el múltiplo > 1
    assert resumen["suma_minimos_individuales"] < resumen["saldo_minimo_agregado"]
