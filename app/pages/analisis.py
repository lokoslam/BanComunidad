"""
app/pages/analisis.py — Análisis individual y comparativo de comunidades.
Incluye secciones de saldo por banco y por tamaño de edificio.
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
from core.cobertura import saldo_por_banco, saldo_por_tamano

# Paleta sobria por banco — definida aquí para evitar cache de módulo
_COLOR_BANCOS = {
    "Chile":     "#4A6FA5",
    "Itaú":      "#C9782E",
    "Scotia":    "#C98A3E",
    "Santander": "#B5484F",
    "BCI":       "#5B8C6E",
    "BICE":      "#4A9BA8",
    "Security":  "#7D5A94",
}

def banco_color(nombre: str) -> str:
    return _COLOR_BANCOS.get(nombre, "#6A6A6A")


def saldo_invertible_dinamico(df_comunidad):
    """
    Saldo invertible con transición sigmoide suave según proximidad a fin de mes.
    Cerca del cierre sube hacia P10 (más colchón); lejos baja a P2 (más capital libre).
    """
    import calendar, math
    saldos = df_comunidad["saldo"].dropna()
    p2  = float(np.percentile(saldos, 2,  method="linear"))
    p10 = float(np.percentile(saldos, 10, method="linear"))
    _df = df_comunidad[["fecha", "saldo"]].copy().sort_values("fecha")
    _df["dias_eom"] = _df["fecha"].apply(
        lambda d: calendar.monthrange(d.year, d.month)[1] - d.day
    )
    # Sigmoide: w→1 cerca del fin de mes, w→0 lejos → mezcla suave entre p2 y p10
    _df["invertible"] = _df["dias_eom"].apply(
        lambda d: p2 + (p10 - p2) / (1 + math.exp((d - 5) / 2))
    )
    return _df.set_index("fecha")["invertible"]
from app.styles import plotly_layout, PLT_LINE, PLT_ACCENT, PLT_MUTED

DB_PATH  = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "saldos_diarios.db")
_PORTADA = os.path.join(os.path.dirname(__file__), "portada.py")

with st.sidebar:
    if st.button("← Portada", key="back_portada_anal"):
        st.switch_page(_PORTADA)


def fmt_mm(n: float) -> str:
    return f"MM${n/1_000_000:.1f}"


if not os.path.exists(DB_PATH):
    st.error("No se encontró la base de datos.")
    st.stop()


@st.cache_data
def cargar_datos():
    con = sqlite3.connect(DB_PATH)
    df_sal = pd.read_sql("SELECT * FROM saldos_diarios", con, parse_dates=["fecha"])
    df_ed  = pd.read_sql("SELECT * FROM edificios", con)
    con.close()
    return df_sal, df_ed


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


def _corner_radius(fig, r=4):
    try:
        import plotly as _p
        if tuple(int(x) for x in _p.__version__.split(".")[:2]) >= (5, 12):
            fig.update_traces(marker_cornerradius=r)
    except Exception:
        pass


df, df_ed = cargar_datos()
resumen   = tabla_resumen(df)
comunidades = sorted(df["comunidad_id"].unique())

st.title(":material/search: Análisis por comunidad")

# ══ SECCIÓN 1: ANÁLISIS INDIVIDUAL ════════════════════════════════════════════
st.subheader("Comunidad individual")

_sel_col, _ = st.columns([2, 3])
with _sel_col:
    comunidad_sel = st.selectbox("Selecciona una comunidad", comunidades)
df_com    = df[df["comunidad_id"] == comunidad_sel].sort_values("fecha")
saldo_prom = df_com["saldo"].mean()
saldo_min  = df_com["saldo"].min()
saldo_p5   = float(np.percentile(df_com["saldo"].dropna(), 5, method="linear"))
cv         = df_com["saldo"].std() / saldo_prom if saldo_prom else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Saldo promedio",    fmt_abr(saldo_prom),  help=fmt_clp(saldo_prom))
k2.metric("Mínimo histórico",  fmt_abr(saldo_min),   help=fmt_clp(saldo_min))
k3.metric("P5 propio",         fmt_abr(saldo_p5),
          help=fmt_clp(saldo_p5) + " — piso colocable individual")
k4.metric("% invertible (P5)", f"{saldo_p5/saldo_prom*100:.1f}%" if saldo_prom else "—")
k5.metric("Volatilidad (CV)",  f"{cv*100:.1f}%",
          help="Desviación estándar / promedio. Menor = más estable.")

inv_din = saldo_invertible_dinamico(df_com.reset_index(drop=True))

fig = go.Figure()
# Base invisible en el nivel del saldo invertible dinámico — para fill tonexty
fig.add_trace(go.Scatter(
    x=inv_din.index, y=inv_din.values,
    mode="lines", line=dict(color="rgba(0,0,0,0)", width=0),
    showlegend=False, hoverinfo="skip", name="_inv_base",
))
# Curva principal del saldo con relleno entre saldo y línea dinámica
fig.add_trace(go.Scatter(
    x=df_com["fecha"], y=df_com["saldo"],
    mode="lines", name="Saldo diario",
    line=dict(color=PLT_LINE, width=1.5),
    fill="tonexty", fillcolor="rgba(192,84,187,0.08)",
    hovertemplate="<b>%{x|%d %b %Y}</b><br>Saldo: $%{y:,.0f}<extra></extra>",
))
# Línea dinámica de saldo invertible
fig.add_trace(go.Scatter(
    x=inv_din.index, y=inv_din.values,
    mode="lines", name="Saldo invertible (dinámico)",
    line=dict(color="#C054BB", width=2, dash="solid"),
    hovertemplate="<b>%{x|%d %b %Y}</b><br>Invertible: $%{y:,.0f}<extra></extra>",
))
# P5 estático como referencia en gris punteado
fig.add_trace(go.Scatter(
    x=df_com["fecha"], y=[saldo_p5] * len(df_com),
    mode="lines", name=f"P5 estático ({fmt_abr(saldo_p5)})",
    line=dict(color="#666666", width=1.2, dash="dot"),
    hoverinfo="skip",
))
fig.update_layout(**plotly_layout(
    title=dict(text=f"Saldo diario — {comunidad_sel}", font=dict(color="#F4F4F4", size=13)),
    height=320, yaxis_title="CLP", showlegend=True,
    legend=dict(orientation="h", y=-0.28, x=0, font=dict(color="#F4F4F4", size=10)),
    margin=dict(t=30, b=70, l=10, r=10),
))
st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})
st.caption(
    "El modelo dinámico ajusta el colchón de seguridad según la cercanía al pago de "
    "gastos comunes (fin de mes), liberando más capital invertible el resto del período."
)

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

with st.expander("¿Qué significa cada columna?"):
    st.markdown(
        "- **Saldo promedio**: Media del saldo diario de la comunidad en todo el período analizado.\n"
        "- **Mínimo histórico**: El día con el saldo más bajo — útil para conocer el peor caso real.\n"
        "- **P5 propio**: El saldo que esta comunidad supera el 95% de los días. Es el capital que "
        "podría invertir individualmente sin riesgo de quedarse corta.\n"
        "- **% invertible (P5)**: P5 propio como porcentaje del saldo promedio — cuánto del float "
        "está disponible para invertir de forma segura.\n"
        "- **Volatilidad (CV)**: Coeficiente de variación (desviación estándar / promedio). "
        "Menor % = saldo más estable y predecible, ideal para invertir.\n"
        "- **N° días**: Días con datos cargados en el período analizado."
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
    textposition="outside", textfont=dict(color=PLT_MUTED, size=10),
    name="Saldo promedio",
))
fig2.add_trace(go.Bar(
    x=top["Comunidad"], y=top["P5 propio"],
    marker=dict(color=PLT_ACCENT, opacity=0.9),
    name="P5 propio (invertible)",
))
_corner_radius(fig2)
fig2.update_layout(**plotly_layout(
    height=380, yaxis_title="CLP", barmode="overlay",
    margin=dict(t=20, b=130, l=10, r=10), xaxis_tickangle=-45,
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
))
st.plotly_chart(fig2, use_container_width=True, config={"scrollZoom": True})
st.caption("Barras claras: saldo promedio · Barras violeta: P5 propio (capital invertible individual)")

st.divider()

# ══ SECCIÓN 4: SALDO POR BANCO ════════════════════════════════════════════════
st.subheader("Saldo por banco")
st.caption(
    "Saldo promedio diario agregado por institución bancaria — solo comunidades con datos cargados. "
    "Permite ver qué bancos concentran más float administrado."
)

df_banco = saldo_por_banco(df_ed, df)

_bar_colors = [banco_color(b) for b in df_banco["banco"]]
_bar_lines  = ["rgba(0,0,0,0)" for _ in df_banco["banco"]]

fig3 = go.Figure()
fig3.add_trace(go.Bar(
    x=df_banco["saldo_promedio_diario"],
    y=df_banco["banco"],
    orientation="h",
    marker=dict(color=_bar_colors, line=dict(color=_bar_lines, width=1.5)),
    text=df_banco["saldo_promedio_diario"].apply(fmt_abr),
    textposition="outside",
    textfont=dict(color=PLT_LINE, size=11),
))
_corner_radius(fig3, r=5)
fig3.update_layout(**plotly_layout(
    height=max(220, len(df_banco) * 48),
    xaxis_title="Saldo promedio diario (CLP)",
    yaxis=dict(
        gridcolor="rgba(255,255,255,0.05)",
        linecolor="rgba(0,0,0,0)",
        tickcolor="rgba(0,0,0,0)",
        tickfont=dict(color="#F4F4F4", size=12),
        title_font=dict(color="#8A8A8A", size=11),
        autorange="reversed",
    ),
    xaxis=dict(
        gridcolor="rgba(255,255,255,0.05)",
        linecolor="rgba(0,0,0,0)",
        tickfont=dict(color="#8A8A8A", size=11),
        title_font=dict(color="#8A8A8A", size=11),
    ),
    showlegend=False,
    margin=dict(t=20, b=20, l=10, r=80),
))
st.plotly_chart(fig3, use_container_width=True, config={"scrollZoom": False})

# ── Pie chart: distribución del saldo por banco ────────────────────────────────
st.subheader("Distribución del saldo por banco")
st.caption("Participación porcentual de cada banco en el float total administrado.")

_pie_colors = [banco_color(b) for b in df_banco["banco"]]
_pie_lines  = ["#191919" for _ in df_banco["banco"]]

fig_pie = go.Figure(go.Pie(
    labels=df_banco["banco"],
    values=df_banco["saldo_promedio_diario"],
    marker=dict(colors=_pie_colors, line=dict(color=_pie_lines, width=2)),
    textfont=dict(color="#F4F4F4", size=12),
    hovertemplate="<b>%{label}</b><br>Saldo prom: %{value:,.0f}<br>%{percent}<extra></extra>",
    hole=0.38,
))
fig_pie.update_layout(**plotly_layout(
    height=320, showlegend=True,
    legend=dict(orientation="v", x=1.02, y=0.5, font=dict(color="#F4F4F4", size=11)),
    margin=dict(t=10, b=10, l=10, r=120),
))
st.plotly_chart(fig_pie, use_container_width=True, config={"scrollZoom": False})

# ── Gráfico de líneas: evolución del saldo por banco (mensual) ─────────────────
st.subheader("Evolución del saldo por banco (mensual)")
st.caption(
    "Saldo promedio mensual de las comunidades agrupadas por banco. "
    "Permite ver si algún banco superó a otro en algún período."
)


@st.cache_data
def evolucion_mensual_banco(df_hash):
    merged = df.merge(df_ed[["comunidad_id", "banco"]], on="comunidad_id", how="left")
    merged["mes"] = merged["fecha"].dt.to_period("M").dt.to_timestamp()
    # Paso 1: suma de todas las comunidades del banco por día
    diario_banco = merged.groupby(["banco", "fecha", "mes"])["saldo"].sum().reset_index()
    # Paso 2: promedio mensual de esos totales diarios (igual lógica que saldo_por_banco)
    return (
        diario_banco.groupby(["banco", "mes"])["saldo"]
        .mean()
        .reset_index()
        .rename(columns={"saldo": "saldo_prom_mes"})
    )


df_evol = evolucion_mensual_banco(len(df))
bancos_lista = df_evol["banco"].unique()

fig_lineas = go.Figure()
for banco in bancos_lista:
    d = df_evol[df_evol["banco"] == banco]
    color = banco_color(banco)
    fig_lineas.add_trace(go.Scatter(
        x=d["mes"], y=d["saldo_prom_mes"],
        mode="lines+markers",
        name=banco,
        line=dict(color=color, width=1.8),
        marker=dict(size=5, color=color),
        hovertemplate=f"<b>{banco}</b><br>%{{x|%b %Y}}<br>Saldo: $%{{y:,.0f}}<extra></extra>",
    ))

fig_lineas.update_layout(**plotly_layout(
    height=360, yaxis_title="Saldo promedio mensual (CLP)",
    legend=dict(orientation="h", y=-0.22, x=0, font=dict(color="#F4F4F4", size=11)),
    margin=dict(t=10, b=60, l=10, r=10),
))
st.plotly_chart(fig_lineas, use_container_width=True, config={"scrollZoom": True})

st.divider()

# ══ SECCIÓN 5: SALDO POR TAMAÑO DE EDIFICIO ═══════════════════════════════════
st.subheader("Saldo por tamaño de edificio")
st.caption(
    "¿Los edificios más grandes administran más float por comunidad? "
    "Comunidades agrupadas en cuartiles por número de unidades."
)

try:
    df_tam = saldo_por_tamano(df_ed, df, n_bins=4)
    df_tam["bucket_label"] = df_tam["bucket_unidades"].apply(
        lambda iv: f"{int(iv.left)+1}–{int(iv.right)} uds"
    )

    fig4 = go.Figure()
    fig4.add_trace(go.Bar(
        x=df_tam["bucket_label"],
        y=df_tam["saldo_promedio"],
        marker=dict(color=PLT_LINE, opacity=0.85),
        text=df_tam["saldo_promedio"].apply(fmt_abr),
        textposition="outside",
        textfont=dict(color=PLT_LINE, size=11),
        customdata=df_tam["n_comunidades"],
        hovertemplate="<b>%{x}</b><br>Saldo prom: %{text}<br>N° comunidades: %{customdata}<extra></extra>",
    ))
    _corner_radius(fig4)
    fig4.update_layout(**plotly_layout(
        height=320, yaxis_title="Saldo promedio por comunidad (CLP)", showlegend=False,
    ))
    st.plotly_chart(fig4, use_container_width=True, config={"scrollZoom": False})

    st.caption(
        "Cada barra agrupa comunidades con rangos similares de unidades. "
        "El tooltip muestra cuántas comunidades hay en cada bucket."
    )
except Exception as e:
    st.warning(f"No se pudo calcular saldo por tamaño: {e}")
