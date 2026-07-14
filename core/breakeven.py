"""
core/breakeven.py

Funciones puras de análisis de break-even para BanComunidad.
Todas las fórmulas son inversas del modelo financiero de Simulador.py.
"""

from __future__ import annotations


def ingreso_por_comunidad_mes(
    saldo_promedio: float,
    pct_invertible: float,
    tasa_anual: float,
    pct_banco: float,
) -> float:
    """
    Ingreso mensual que aporta UNA comunidad a BanComunidad.
    Fórmula: saldo_promedio * pct_invertible * (tasa_anual / 12) * pct_banco
    Retorna 0.0 si algún parámetro es 0 para evitar división por cero en callers.
    """
    return saldo_promedio * pct_invertible * (tasa_anual / 12) * pct_banco


def comunidades_breakeven(
    saldo_promedio: float,
    pct_invertible: float,
    tasa_anual: float,
    pct_banco: float,
    costo_fijo_mensual: float,
) -> float:
    """
    Número de comunidades necesarias para EBITDA = 0.
    Fórmula: N = costo_fijo_mensual / ingreso_por_comunidad_mes
    Retorna float('inf') si el ingreso por comunidad es 0.
    """
    ing = ingreso_por_comunidad_mes(saldo_promedio, pct_invertible, tasa_anual, pct_banco)
    if ing <= 0:
        return float("inf")
    return costo_fijo_mensual / ing


def tasa_breakeven(
    n_comunidades: int,
    saldo_promedio: float,
    pct_invertible: float,
    pct_banco: float,
    costo_fijo_mensual: float,
) -> float:
    """
    Tasa anual mínima para EBITDA = 0 con N comunidades fijas.
    Despejando tasa de: N * saldo * pct_inv * (tasa/12) * pct_banco = costo
    Retorna float('inf') si el denominador es 0.
    """
    denominador = n_comunidades * saldo_promedio * pct_invertible * pct_banco / 12
    if denominador <= 0:
        return float("inf")
    return costo_fijo_mensual / denominador


def costo_max_breakeven(
    n_comunidades: int,
    saldo_promedio: float,
    pct_invertible: float,
    tasa_anual: float,
    pct_banco: float,
) -> float:
    """
    Costo fijo mensual máximo sostenible con N comunidades y los parámetros dados.
    Equivale al ingreso total mensual de BanComunidad en ese escenario.
    """
    return n_comunidades * ingreso_por_comunidad_mes(
        saldo_promedio, pct_invertible, tasa_anual, pct_banco
    )

