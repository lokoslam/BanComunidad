"""
core/liquidity.py

Funciones puras de liquidez y capital invertible.
Espejo EXACTO de las fórmulas del sheet 'Riesgo' en BanComunidad_Modelo.xlsx.
Cada función referencia la celda de origen en su docstring.

Convención de inputs: pandas.DataFrame con columnas
['comunidad_id', 'fecha', 'saldo'] (== Saldos_Diarios cols A,B,C).
No leen archivos directamente — eso es trabajo de etl/.

IMPORTANTE — dos métricas distintas que NO deben confundirse:
  - "Piso por percentil" (P1/P5/P10): usado para CAPITAL INVERTIBLE (D14, D16, D36)
  - "Piso por mínimo histórico" (MIN): usado para el MÚLTIPLO DE DIVERSIFICACIÓN (D30-D33)
El workbook usa MIN para el insight de diversificación, no P5.
"""

from __future__ import annotations
import pandas as pd
import numpy as np


def saldo_diario_total(df: pd.DataFrame) -> pd.Series:
    """
    Suma el saldo de todas las comunidades por fecha.
    == Portafolio_Agregado!B (SUMIFS por fecha)
    """
    return df.groupby("fecha")["saldo"].sum().sort_index()


def saldo_promedio(df: pd.DataFrame) -> float:
    """== Riesgo!D6 = AVERAGE(Portafolio_Agregado!B2:B366)"""
    return saldo_diario_total(df).mean()


def saldo_minimo_agregado(df: pd.DataFrame) -> float:
    """== Riesgo!D7 = MIN(Portafolio_Agregado!B2:B366)  (también == D31)"""
    return saldo_diario_total(df).min()


def saldo_maximo_agregado(df: pd.DataFrame) -> float:
    """== Riesgo!D8 = MAX(Portafolio_Agregado!B2:B366)"""
    return saldo_diario_total(df).max()


def desviacion_estandar_agregada(df: pd.DataFrame) -> float:
    """== Riesgo!D9 = STDEV(Portafolio_Agregado!B2:B366)"""
    return saldo_diario_total(df).std()


def coeficiente_variacion(df: pd.DataFrame) -> float:
    """== Riesgo!D10 = D9/D6 (0 si D6=0)"""
    promedio = saldo_promedio(df)
    if promedio == 0:
        return 0.0
    return desviacion_estandar_agregada(df) / promedio


def percentil_agregado(df: pd.DataFrame, p: float) -> float:
    """
    Percentil del saldo TOTAL agregado por día.
    p en [0,1] (ej. 0.05 para P5), igual a Excel PERCENTILE.
    == Riesgo!D13 (p=0.01) / D14 (p=0.05) / D15 (p=0.10)
    """
    total = saldo_diario_total(df).dropna()
    return float(np.percentile(total, p * 100, method="linear"))


def pct_invertible_recomendado(df: pd.DataFrame) -> float:
    """
    P5 como % del promedio. Este es el % que alimenta MODELO_FINANCIERO.
    == Riesgo!D16 = D14/D6 ; también == D36 (veredicto final)
    """
    promedio = saldo_promedio(df)
    if promedio == 0:
        return 0.0
    return percentil_agregado(df, 0.05) / promedio


def capital_invertible_recomendado(df: pd.DataFrame) -> float:
    """
    Capital invertible en CLP = P5 del saldo agregado.
    Esta es la cifra ancla validada (~$885.7M).
    == Riesgo!D14 directamente (el "piso colocable" en pesos)
    """
    return percentil_agregado(df, 0.05)


def mayor_caida_diaria(df: pd.DataFrame) -> float:
    """== Riesgo!D19 = MIN(Portafolio_Agregado!E3:E366) (delta diario más negativo)"""
    total = saldo_diario_total(df)
    delta = total.diff().dropna()
    return float(delta.min())


def mayor_alza_diaria(df: pd.DataFrame) -> float:
    """== Riesgo!D20 = MAX(Portafolio_Agregado!E3:E366)"""
    total = saldo_diario_total(df)
    delta = total.diff().dropna()
    return float(delta.max())


def dias_bajo_umbral(df: pd.DataFrame, umbral: float) -> dict:
    """
    == Riesgo!D24 (umbral editable) / D25 (días bajo) / D26 (%) / D27 (días sobre)
    """
    total = saldo_diario_total(df)
    n = total.count()
    bajo = int((total < umbral).sum())
    return {
        "umbral": umbral,
        "dias_bajo_umbral": bajo,
        "pct_dias_bajo_umbral": bajo / n if n else 0.0,
        "dias_sobre_umbral": int(n - bajo),
    }


def minimo_por_comunidad(df: pd.DataFrame) -> pd.Series:
    """
    Saldo mínimo histórico por comunidad individual.
    == Analytics!E6:E61 = MINIFS(Saldos_Diarios!C, Saldos_Diarios!A, comunidad)
    """
    return df.groupby("comunidad_id")["saldo"].min()


def suma_minimos_individuales(df: pd.DataFrame) -> float:
    """
    Piso NAÏVE: suma de los mínimos de cada comunidad por separado.
    == Riesgo!D30 = SUM(Analytics!E6:E61)
    """
    return float(minimo_por_comunidad(df).sum())


def multiplo_diversificacion(df: pd.DataFrame) -> float:
    """
    Insight central del negocio: cuántas veces más alto es el piso REAL
    (mínimo del agregado) vs. el piso NAÏVE (suma de mínimos individuales).
    Validado en datos reales: ~1.32x.
    == Riesgo!D32 = D31/D30  (0 si D30=0)
    """
    naive = suma_minimos_individuales(df)
    if naive == 0:
        return 0.0
    return saldo_minimo_agregado(df) / naive


def capital_extra_por_diversificar(df: pd.DataFrame) -> float:
    """== Riesgo!D33 = D31 - D30 (float adicional que solo existe al agrupar)"""
    return saldo_minimo_agregado(df) - suma_minimos_individuales(df)


def saldo_invertible_dinamico(df_comunidad: pd.DataFrame) -> pd.Series:
    """
    Saldo invertible diario ajustado por proximidad al cierre de mes.
    - Últimos 5 días antes del fin de mes: usa P10 (más colchón de seguridad)
    - Resto del mes (6+ días antes): usa P2 (más capital liberado)
    Returns Series[fecha → monto_sugerido_invertible].
    """
    import calendar
    saldos = df_comunidad["saldo"].dropna()
    p2  = float(np.percentile(saldos, 2,  method="linear"))
    p10 = float(np.percentile(saldos, 10, method="linear"))

    df = df_comunidad[["fecha", "saldo"]].copy()
    df["dias_eom"] = df["fecha"].apply(
        lambda d: calendar.monthrange(d.year, d.month)[1] - d.day
    )
    df["invertible"] = df["dias_eom"].apply(lambda d: p10 if d <= 5 else p2)
    return df.set_index("fecha")["invertible"]


def resumen_riesgo(df: pd.DataFrame, umbral: float = 900_000_000) -> dict:
    """
    Resumen ejecutivo equivalente a leer el sheet Riesgo completo de un solo golpe.
    Pensado para alimentar Streamlit (Sprint 3) sin recalcular nada ahí.
    """
    umbral_info = dias_bajo_umbral(df, umbral)
    return {
        "saldo_promedio": saldo_promedio(df),
        "saldo_minimo_agregado": saldo_minimo_agregado(df),
        "saldo_maximo_agregado": saldo_maximo_agregado(df),
        "desviacion_estandar": desviacion_estandar_agregada(df),
        "coeficiente_variacion": coeficiente_variacion(df),
        "p1": percentil_agregado(df, 0.01),
        "p5": percentil_agregado(df, 0.05),
        "p10": percentil_agregado(df, 0.10),
        "pct_invertible_recomendado": pct_invertible_recomendado(df),
        "capital_invertible_recomendado": capital_invertible_recomendado(df),
        "mayor_caida_diaria": mayor_caida_diaria(df),
        "mayor_alza_diaria": mayor_alza_diaria(df),
        "suma_minimos_individuales": suma_minimos_individuales(df),
        "multiplo_diversificacion": multiplo_diversificacion(df),
        "capital_extra_por_diversificar": capital_extra_por_diversificar(df),
        **umbral_info,
        "n_comunidades": df["comunidad_id"].nunique(),
        "n_dias": df["fecha"].nunique(),
    }
