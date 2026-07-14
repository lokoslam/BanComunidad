"""
app/pages/2_Analisis_Comunidades.py — Análisis individual y comparativo de comunidades.
"""

import os
import sqlite3
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from core.formatting import fmt_clp, fmt_abr
from app.styles import inject_css, sidebar_header, plotly_layout, PLT_LINE, PLT_ACCENT, PLT_MUTED

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "saldos_diarios.db")

st.set_page_config(page_title="Análisis comunidades — BanComunidad", layout="wide")
inject_css()

with st.sidebar:
    sidebar_header()

st.title("Análisis por comunidad")


def fmt_mm(n: float) -> str:
    return f"MM${n/1_000_000:.1f}"


if not os.path.exists(DB_PATH):
    st.error("No se encontró la base de datos.")
    st.stop()


@st.cache_data
def cargar_df() -> pd.DataFrame:
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM saldos_diarios", con, parse_dates=["fecha"])
    con.close()
    return df


@st.cache_data
def tabla_resumen(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for com, g in df.groupby("comunidad_id"):
        promedio = g["saldo"].mean()
        minimo   = g["saldo"].min()
        p5       = float(np.percentile(g["saldo"].dropna(), 5, method="linear"))
        std      = g["saldo"].std()
        cv       = std / promedio if promedio else 0
        rows.append({
            "Comunidad":         com,
            "Saldo promedio":    promedio,
            "Mínimo histórico":  minimo,
            "P5 propio":         p5,
            "% invertible (P5)": p5 / promedio if promedio else 0,
            "Volatilidad (CV)":  cv,
            "N° días":           len(g),
        })
    return (
        pd.DataFrame(rows)
        .sort_values("Saldo promedio", ascending=False)
        .reset_index(drop=True)
    )


df      = cargar_df()
resumen = tabla_resumen(df)
comunidades = sorted(df["comunidad_id"].unique())

# ══ SECCIÓN 1: ANÁLISIS INDIVIDUAL ════════════════════════════════════════════
st.subheader("Comunidad individual")

comunidad_sel = st.selectbox("Selecciona una comunidad", comunidades)
df_com    = df[df["comunidad_id"] == comunidad_sel].sort_values("fecha")
saldo_prom = df_com["saldo"].mean()
saldo_min  = df_com["saldo"].min()
saldo_p5   = float(np.percentile(df_com["saldo"].dropna(), 5, method="linear"))
cv         = df_com["saldo"].std() / saldo_prom if saldo_prom else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Saldo promedio",    fmt_abr(saldo_prom),  help=fmt_clp(saldo_prom))
k2.metric("Mínimo histórico",  fmt_abr(saldo_min),   help=fmt_clp(saldo_min))
k3.metric("P5 propio",         fmt_abr(saldo_p5),    help=fmt_clp(saldo_p5) +
          " — piso colocable individual")
k4.metric("% invertible (P5)", f"{saldo_p5/saldo_prom*100:.1f}%" if saldo_prom else "—")
k5.metric("Volatilidad (CV)",  f"{cv*100:.1f}%",
          help="Desviación estándar / promedio. Menor = más estable.")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_com["fecha"], y=df_com["saldo"],
    mode="lines",
    line=dict(color=PLT_LINE, width=1.5),
    fill="tozeroy",
    fillcolor="rgba(244,244,244,0.04)",
    name="Saldo diario",
))
fig.add_hline(
    y=saldo_p5, line_dash="dash", line_color=PLT_ACCENT, line_width=1.5,
    annotation_text=f"P5: {fmt_abr(saldo_p5)}",
    annotation_position="top left",
    annotation_font_color=PLT_ACCENT, annotation_font_size=11,
)
fig.add_hline(
    y=saldo_min, line_dash="dot", line_color=PLT_MUTED, line_width=1,
    annotation_text=f"Mín: {fmt_abr(saldo_min)}",
    annotation_position="bottom left",
    annotation_font_color=PLT_MUTED, annotation_font_size=11,
)
fig.update_layout(**plotly_layout(
    title=dict(text=f"Saldo diario — {comunidad_sel}", font=dict(color="#F4F4F4", size=13)),
    height=320, yaxis_title="CLP", showlegend=False,
))
st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

st.divider()

# ══ SECCIÓN 2: TABLA COMPARATIVA ══════════════════════════════════════════════
st.subheader("Comparativa de todas las comunidades")
st.caption("Ordenadas por saldo promedio descendente.")

tabla_display = resumen.copy()
tabla_display["Saldo promedio"]    = tabla_display["Saldo promedio"].apply(fmt_clp)
tabla_display["Mínimo histórico"]  = tabla_display["Mínimo histórico"].apply(fmt_clp)
tabla_display["P5 propio"]         = tabla_display["P5 propio"].apply(fmt_clp)
tabla_display["% invertible (P5)"] = tabla_display["% invertible (P5)"].apply(lambda x: f"{x*100:.1f}%")
tabla_display["Volatilidad (CV)"]  = tabla_display["Volatilidad (CV)"].apply(lambda x: f"{x*100:.1f}%")

st.dataframe(
    tabla_display[["Comunidad", "Saldo promedio", "Mínimo histórico", "P5 propio",
                   "% invertible (P5)", "Volatilidad (CV)", "N° días"]],
    use_container_width=True, hide_index=True,
)

st.divider()

# ══ SECCIÓN 3: COMPARATIVA VISUAL ═════════════════════════════════════════════
st.subheader("Saldo promedio por comunidad")

top_n = st.slider("Top N comunidades", min_value=5, max_value=len(resumen), value=20, step=5)
top   = resumen.head(top_n)

fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=top["Comunidad"], y=top["Saldo promedio"],
    marker=dict(color=PLT_LINE, opacity=0.8),
    text=top["Saldo promedio"].apply(fmt_mm),
    textposition="outside",
    textfont=dict(color=PLT_MUTED, size=10),
    name="Saldo promedio",
))
fig2.add_trace(go.Bar(
    x=top["Comunidad"], y=top["P5 propio"],
    marker=dict(color=PLT_ACCENT, opacity=0.9),
    name="P5 propio (invertible)",
))

try:
    import plotly
    major, minor = (int(x) for x in plotly.__version__.split(".")[:2])
    if (major, minor) >= (5, 12):
        fig2.update_traces(marker_cornerradius=4)
except Exception:
    pass

fig2.update_layout(**plotly_layout(
    height=400, yaxis_title="CLP", barmode="overlay",
    margin=dict(t=20, b=130, l=10, r=10), xaxis_tickangle=-45,
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
))
st.plotly_chart(fig2, use_container_width=True, config={"scrollZoom": True})
st.caption(
    "Barras claras: saldo promedio · Barras violeta: P5 propio (capital invertible individual)"
)
