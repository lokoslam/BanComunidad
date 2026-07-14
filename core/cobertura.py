"""
core/cobertura.py

Funciones para responder: "¿qué datos tenemos vs qué deberíamos tener?"
Cruza la tabla `edificios` (metadata: banco, unidades, admin) con
`saldos_diarios` (los datos reales cargados).
"""

from __future__ import annotations
import pandas as pd


def comunidades_sin_datos(df_edificios: pd.DataFrame, df_saldos: pd.DataFrame) -> pd.DataFrame:
    """
    Comunidades que existen en la base de edificios pero NO tienen
    ninguna fila en saldos_diarios todavía. Esto es la lista de
    "cartolas pendientes de cargar".
    """
    con_datos = set(df_saldos["comunidad_id"].unique())
    faltantes = df_edificios[~df_edificios["comunidad_id"].isin(con_datos)]
    cols = ["comunidad_id", "banco", "unidades", "admin", "comuna"]
    return faltantes[cols].sort_values("comunidad_id").reset_index(drop=True)


def resumen_cobertura(df_edificios: pd.DataFrame, df_saldos: pd.DataFrame) -> dict:
    """
    KPIs de cobertura de datos: cuántos edificios totales, cuántos con
    datos, % de cobertura, y desglose de pendientes por banco.
    """
    total = df_edificios["comunidad_id"].nunique()
    con_datos = df_saldos["comunidad_id"].nunique()
    faltantes_df = comunidades_sin_datos(df_edificios, df_saldos)
    return {
        "total_edificios": total,
        "con_datos": con_datos,
        "pct_cobertura": con_datos / total if total else 0.0,
        "n_faltantes": len(faltantes_df),
        "faltantes_por_banco": faltantes_df["banco"].value_counts().to_dict(),
        "faltantes_detalle": faltantes_df,
    }


def cobertura_por_comunidad(df_saldos: pd.DataFrame) -> pd.DataFrame:
    """
    Para las comunidades QUE SÍ tienen datos: cuántos meses de cartola
    tienen realmente (días distintos / 30), útil para detectar meses
    sueltos faltantes dentro de una comunidad ya cargada.
    """
    g = df_saldos.groupby("comunidad_id")["fecha"].agg(
        primer_dia="min", ultimo_dia="max", n_dias="count"
    )
    g["meses_aprox"] = (g["n_dias"] / 30).round(1)
    rango_dias = (pd.to_datetime(g["ultimo_dia"]) - pd.to_datetime(g["primer_dia"])).dt.days + 1
    g["dias_esperados"] = rango_dias
    g["dias_faltantes"] = (g["dias_esperados"] - g["n_dias"]).clip(lower=0)
    return g.reset_index().sort_values("dias_faltantes", ascending=False)


def saldo_por_banco(df_edificios: pd.DataFrame, df_saldos: pd.DataFrame) -> pd.DataFrame:
    """
    Saldo promedio diario agregado por banco — solo para comunidades
    que tienen datos cargados.
    """
    merged = df_saldos.merge(
        df_edificios[["comunidad_id", "banco"]], on="comunidad_id", how="left"
    )
    return (
        merged.groupby(["banco", "fecha"])["saldo"]
        .sum()
        .groupby("banco")
        .mean()
        .sort_values(ascending=False)
        .reset_index(name="saldo_promedio_diario")
    )


def matriz_cobertura_mensual(df_saldos: pd.DataFrame, df_edificios: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Matriz Comunidad x Mes con estado de carga: 'Cargado', 'Parcial', 'Falta'.

    - 'Cargado': el mes tiene >= 90% de los días esperados con datos
    - 'Parcial': el mes tiene entre 1% y 90% de los días esperados
    - 'Falta': el mes no tiene ningún día cargado

    Si se pasa df_edificios, incluye también las comunidades que existen
    en la base pero no tienen NINGÚN dato (todas sus columnas = 'Falta').

    Returns: DataFrame con columnas ['comunidad_id', 'banco'(opcional), <mes1>, <mes2>, ...]
    en formato ancho (una columna por mes, ordenadas cronológicamente).
    """
    df = df_saldos.copy()
    df["mes"] = pd.to_datetime(df["fecha"]).dt.to_period("M")

    # días reales cargados por comunidad-mes
    conteo = df.groupby(["comunidad_id", "mes"])["fecha"].nunique().rename("dias_cargados")
    conteo = conteo.reset_index()

    # días esperados por mes calendario (días del mes)
    conteo["dias_esperados"] = conteo["mes"].apply(lambda p: p.days_in_month)
    conteo["pct"] = conteo["dias_cargados"] / conteo["dias_esperados"]

    def estado(pct: float) -> str:
        if pct >= 0.90:
            return "Cargado"
        elif pct > 0:
            return "Parcial"
        return "Falta"

    conteo["estado"] = conteo["pct"].apply(estado)

    tabla = conteo.pivot(index="comunidad_id", columns="mes", values="estado")
    tabla = tabla.reindex(sorted(tabla.columns), axis=1)  # orden cronológico
    tabla.columns = [str(c) for c in tabla.columns]  # ej. '2025-04'

    # comunidades sin NINGÚN dato (no aparecen en saldos_diarios en absoluto)
    if df_edificios is not None:
        todas = set(df_edificios["comunidad_id"].unique())
        con_datos = set(df["comunidad_id"].unique())
        sin_datos = todas - con_datos
        for com in sin_datos:
            tabla.loc[com] = "Falta"

    tabla = tabla.fillna("Falta").reset_index()

    if df_edificios is not None:
        tabla = tabla.merge(
            df_edificios[["comunidad_id", "banco"]].drop_duplicates("comunidad_id"),
            on="comunidad_id",
            how="left",
        )
        cols = ["comunidad_id", "banco"] + [c for c in tabla.columns if c not in ("comunidad_id", "banco")]
        tabla = tabla[cols]

    return tabla.sort_values("comunidad_id").reset_index(drop=True)


def saldo_por_tamano(df_edificios: pd.DataFrame, df_saldos: pd.DataFrame, n_bins: int = 4) -> pd.DataFrame:
    """
    Agrupa comunidades en buckets de tamaño (por n° de unidades) y
    calcula su saldo promedio.
    """
    saldo_prom = df_saldos.groupby("comunidad_id")["saldo"].mean().rename("saldo_promedio")
    merged = df_edificios.set_index("comunidad_id")[["unidades"]].join(saldo_prom).dropna()
    merged["bucket_unidades"] = pd.qcut(merged["unidades"], q=n_bins, duplicates="drop")
    return (
        merged.groupby("bucket_unidades")
        .agg(
            n_comunidades=("saldo_promedio", "count"),
            saldo_promedio=("saldo_promedio", "mean"),
            saldo_por_unidad=("saldo_promedio", "mean"),
        )
        .reset_index()
    )
