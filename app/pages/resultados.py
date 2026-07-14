"""
app/pages/resultados.py — Dashboard ejecutivo: waterfall, métricas y estadísticas.
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from core.liquidity import resumen_riesgo, saldo_diario_total
from core.formatting import fmt_clp, fmt_abr, fmt_pct
from app.styles import plotly_layout, PLT_LINE, PLT_ACCENT, PLT_MUTED, CARD, BORDER, MUTED, TEXT, ACCENT

DB_PATH  = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "saldos_diarios.db")
_PORTADA = os.path.join(os.path.dirname(__file__), "portada.py")

with st.sidebar:
    if st.button("← Portada", key="back_portada_res"):
        st.switch_page(_PORTADA)


@st.cache_data
def cargar_datos():
    con = sqlite3.connect(DB_PATH)
    df    = pd.read_sql("SELECT * FROM saldos_diarios", con, parse_dates=["fecha"])
    df_ed = pd.read_sql("SELECT * FROM edificios", con)
    con.close()
    return df, df_ed


def _md(s: str) -> str:
    return s.replace("$", r"\$")


if not os.path.exists(DB_PATH):
    st.error("No se encontró la base de datos.")
    st.stop()

df, df_ed = cargar_datos()
r = resumen_riesgo(df)

st.title(":material/bar_chart: Resultados")
st.caption(
    f"{r['n_comunidades']} comunidades · {r['n_dias']} días de datos · "
    "Saldos diarios reales (no proyectados)"
)

# ── KPIs con tooltips para inversionistas ────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "Capital administrado",
    fmt_abr(r["saldo_promedio"]),
    help=(
        f"Promedio del saldo diario total del portafolio entre "
        f"{df['fecha'].min().day} de {df['fecha'].min().strftime('%B')} de {df['fecha'].min().year} y "
        f"{df['fecha'].max().day} de {df['fecha'].max().strftime('%B')} de {df['fecha'].max().year} "
        f"({r['n_dias']} días). "
        f"Exacto: {fmt_clp(r['saldo_promedio'])}"
    ),
)
col2.metric(
    "Capital invertible (P5)",
    fmt_abr(r["capital_invertible_recomendado"]),
    help=(
        "Monto que el portafolio supera el 95% de los días — puede invertirse de "
        "forma segura sin afectar la operación de las comunidades. "
        f"Exacto: {fmt_clp(r['capital_invertible_recomendado'])}"
    ),
)
col3.metric(
    "% invertible",
    fmt_pct(r["pct_invertible_recomendado"]),
    help="Capital invertible como porcentaje del saldo promedio diario total.",
)
col4.metric(
    "Múltiplo diversificación",
    f"{r['multiplo_diversificacion']:.2f}x",
    help=(
        "Cuántas veces más alto es el piso del portafolio agregado vs la suma de los pisos "
        "individuales. Indica el beneficio de agrupar comunidades en lugar de invertir por separado."
    ),
)

st.divider()

# ── Waterfall — orden narrativo de menor a mayor ──────────────────────────────
st.subheader("De saldo administrado a capital invertible")
st.caption(
    "La diversificación entre comunidades genera más float invertible "
    "que la suma de lo que cada comunidad podría invertir por separado."
)

# Orden narrativo: peor caso → comparación naïve → piso recomendado → total
categorias = [
    "Mínimo histórico<br>agregado real",
    "Suma de mínimos<br>individuales (naïve)",
    "Percentil 5 (P5)<br>piso recomendado",
    "Saldo promedio<br>administrado",
]
valores = [
    r["saldo_minimo_agregado"],
    r["suma_minimos_individuales"],
    r["capital_invertible_recomendado"],
    r["saldo_promedio"],
]
colores = [PLT_MUTED, "rgba(150,130,80,0.85)", PLT_ACCENT, PLT_LINE]
captions = [
    "El día más bajo registrado en el período",
    "Si cada comunidad invirtiera su propio piso por separado",
    "Piso estadístico con margen de seguridad: el saldo supera este valor el 95% de los días",
    "Capital total bajo administración",
]

fig = go.Figure()
fig.add_trace(go.Bar(
    x=categorias, y=valores,
    marker=dict(color=colores),
    text=[fmt_abr(v) for v in valores],
    textposition="outside",
    textfont=dict(color=PLT_LINE, size=12),
    customdata=captions,
    hovertemplate="<b>%{x}</b><br>%{text}<br><i>%{customdata}</i><extra></extra>",
))
try:
    import plotly as _plt
    if tuple(int(x) for x in _plt.__version__.split(".")[:2]) >= (5, 12):
        fig.update_traces(marker_cornerradius=6)
except Exception:
    pass

fig.add_hline(
    y=r["capital_invertible_recomendado"],
    line_dash="dash", line_color=PLT_ACCENT, line_width=1.5,
    annotation_text=f"P5 — piso colocable: {fmt_abr(r['capital_invertible_recomendado'])}",
    annotation_position="top left",
    annotation_font_color=PLT_ACCENT, annotation_font_size=11,
)

# Anotaciones de caption debajo de cada barra
max_y = max(valores)
for i, (cat, cap) in enumerate(zip(categorias, captions)):
    fig.add_annotation(
        x=cat, y=-max_y * 0.03,
        text=f"<i>{cap}</i>",
        showarrow=False,
        font=dict(size=9, color="#666666"),
        xanchor="center", yanchor="top",
    )

layout_extra = plotly_layout(height=480, yaxis_title="CLP", showlegend=False)
layout_extra["margin"] = dict(t=40, b=100, l=10, r=10)
fig.update_layout(**layout_extra)
st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

# Insight central — narrativa actualizada
st.markdown(
    f"""<div style="border-left:4px solid {ACCENT};background:{CARD};
        padding:14px 20px;border-radius:0 8px 8px 0;margin:4px 0 0">
      <span style="color:{TEXT};font-size:14px;line-height:1.6">
        Partiendo del peor escenario histórico ({_md(fmt_clp(r['saldo_minimo_agregado']))}),
        la diversificación entre comunidades permite un piso
        <b style="color:{ACCENT}">{r['multiplo_diversificacion']:.2f}x</b>
        más alto que si cada una invirtiera sola
        ({_md(fmt_clp(r['suma_minimos_individuales']))}). Esto habilita
        <b>{_md(fmt_clp(r['capital_invertible_recomendado']))}</b> de capital invertible
        con margen de seguridad — sin afectar la operación de ninguna comunidad.
      </span>
    </div>""",
    unsafe_allow_html=True,
)

st.divider()

# ── Serie de tiempo con referencias y marcadores de fin de mes ────────────────
st.subheader("Evolución del saldo agregado diario")

total = saldo_diario_total(df).reset_index()
total.columns = ["fecha", "saldo"]
total["diff_label"] = (total["saldo"] - r["capital_invertible_recomendado"]).apply(
    lambda x: f"+{fmt_clp(x)}" if x >= 0 else fmt_clp(x)
)
total["cierre_label"] = total["fecha"].apply(
    lambda d: "📅 Cierre de mes" if (d + pd.Timedelta(days=1)).month != d.month else ""
)

saldo_min_ts = total["saldo"].min()
p5_val = r["capital_invertible_recomendado"]

fig2 = go.Figure()

# Traza base (nivel P5) — invisible, sirve de suelo para el relleno tonexty
fig2.add_trace(go.Scatter(
    x=total["fecha"],
    y=[p5_val] * len(total),
    mode="lines",
    line=dict(color="rgba(0,0,0,0)", width=0),
    showlegend=False, hoverinfo="skip", name="_p5_base",
))

# Curva principal del saldo — relleno entre la curva y el nivel P5
fig2.add_trace(go.Scatter(
    x=total["fecha"], y=total["saldo"],
    mode="lines",
    line=dict(color=PLT_LINE, width=1.5),
    fill="tonexty", fillcolor="rgba(192,84,187,0.08)",
    customdata=list(zip(total["diff_label"], total["cierre_label"])),
    hovertemplate=(
        "<b>%{x|%d %b %Y}</b><br>"
        "Saldo: $%{y:,.0f}<br>"
        "vs P5: %{customdata[0]}<br>"
        "%{customdata[1]}<extra></extra>"
    ),
    name="Saldo diario",
))

# Líneas de referencia con mayor contraste
fig2.add_hline(
    y=p5_val,
    line_dash="solid", line_color="#C054BB", line_width=2.5,
    annotation_text=f"Piso colocable P5: {fmt_abr(p5_val)}",
    annotation_position="top left",
    annotation_font_color="#C054BB", annotation_font_size=11,
)
fig2.add_hline(
    y=r["saldo_promedio"],
    line_dash="dot", line_color="#CCCCCC", line_width=1.5,
    annotation_text=f"Promedio: {fmt_abr(r['saldo_promedio'])}",
    annotation_position="bottom right",
    annotation_font_color="#CCCCCC", annotation_font_size=10,
)
fig2.add_hline(
    y=saldo_min_ts,
    line_dash="dot", line_color="#888888", line_width=1.5,
    annotation_text=f"Mín: {fmt_abr(saldo_min_ts)}",
    annotation_position="bottom left",
    annotation_font_color="#888888", annotation_font_size=10,
)

# Líneas verticales en fin de mes + anotación de patrón en primera ocurrencia
_MESES_ES = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
             7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}
try:
    mes_ends = total.set_index("fecha")["saldo"].resample("ME").last().index
    for d in mes_ends:
        fig2.add_vline(x=d, line_color="rgba(255,255,255,0.10)", line_width=1)
        fig2.add_annotation(
            x=d, y=1.02, yref="paper",
            text=_MESES_ES.get(d.month, ""),
            showarrow=False,
            font=dict(size=9, color="rgba(255,255,255,0.28)"),
            xanchor="center",
        )
except Exception:
    pass

fig2.update_layout(**plotly_layout(height=340, yaxis_title="CLP", showlegend=False))
st.plotly_chart(fig2, use_container_width=True, config={"scrollZoom": True})
st.markdown(
    f"""<div style="display:flex;gap:18px;flex-wrap:wrap;margin-top:4px;padding:2px 0">
      <span style="display:flex;align-items:center;gap:7px;font-size:12px;color:{MUTED}">
        <svg width="28" height="10"><line x1="0" y1="5" x2="28" y2="5"
          stroke="#C054BB" stroke-width="2.5"/></svg>
        Piso colocable (P5)
      </span>
      <span style="display:flex;align-items:center;gap:7px;font-size:12px;color:{MUTED}">
        <svg width="28" height="10"><line x1="0" y1="5" x2="28" y2="5"
          stroke="#CCCCCC" stroke-width="2" stroke-dasharray="3,3"/></svg>
        Promedio histórico
      </span>
      <span style="display:flex;align-items:center;gap:7px;font-size:12px;color:{MUTED}">
        <svg width="28" height="10"><line x1="0" y1="5" x2="28" y2="5"
          stroke="#888888" stroke-width="2" stroke-dasharray="3,3"/></svg>
        Mínimo absoluto
      </span>
      <span style="display:flex;align-items:center;gap:7px;font-size:12px;color:{MUTED}">
        <svg width="28" height="10"><line x1="14" y1="0" x2="14" y2="10"
          stroke="rgba(255,255,255,0.18)" stroke-width="1.5"/></svg>
        Fin de mes
      </span>
    </div>""",
    unsafe_allow_html=True,
)

st.divider()

# ── Estadísticas de la cartera ────────────────────────────────────────────────
st.subheader("Estadísticas de la cartera")


@st.cache_data
def stats_cartera(_n_rows, _n_ed):
    com_saldo = df.groupby("comunidad_id")["saldo"].mean()
    com_cv    = df.groupby("comunidad_id")["saldo"].apply(
        lambda x: x.std() / x.mean() if x.mean() > 0 else float("inf")
    )
    merged     = df.merge(df_ed[["comunidad_id", "banco"]], on="comunidad_id", how="left")
    bank_saldo = merged.groupby(["banco", "fecha"])["saldo"].sum().groupby("banco").mean()
    return {
        "n_registros":    len(df),
        "fecha_min":      df["fecha"].min(),
        "fecha_max":      df["fecha"].max(),
        "com_max":        com_saldo.idxmax(),
        "com_max_val":    com_saldo.max(),
        "com_estable":    com_cv.idxmin(),
        "com_estable_cv": com_cv.min(),
        "banco_top":      bank_saldo.idxmax(),
        "banco_top_val":  bank_saldo.max(),
    }


s = stats_cartera(len(df), len(df_ed))

sc1, sc2, sc3, sc4, sc5 = st.columns(5)
sc1.metric("Registros en BD", f"{s['n_registros']:,}")
sc2.metric(
    "Rango de datos",
    f"{s['fecha_min'].strftime('%b-%y')} → {s['fecha_max'].strftime('%b-%y')}",
    help=f"{s['fecha_min'].strftime('%d/%m/%Y')} al {s['fecha_max'].strftime('%d/%m/%Y')}",
)
sc3.metric("Mayor saldo promedio", s["com_max"], help=fmt_clp(s["com_max_val"]))
sc4.metric(
    "Más estable (menor CV)",
    s["com_estable"],
    help=f"Coeficiente de variación: {s['com_estable_cv']*100:.1f}%",
)
sc5.metric("Banco con más float", s["banco_top"], help=fmt_clp(s["banco_top_val"]))

st.divider()

# ── Riesgo y volatilidad ──────────────────────────────────────────────────────
st.subheader("Riesgo y volatilidad")
rcol1, rcol2, rcol3 = st.columns(3)
rcol1.metric("Mayor caída diaria",  fmt_abr(r["mayor_caida_diaria"]),
             help=fmt_clp(r["mayor_caida_diaria"]))
rcol2.metric("Mayor alza diaria",   fmt_abr(r["mayor_alza_diaria"]),
             help=fmt_clp(r["mayor_alza_diaria"]))
cv_pct = r["coeficiente_variacion"] * 100
rcol3.metric(
    "Coeficiente de variación",
    f"{r['coeficiente_variacion']:.3f}",
    help=(
        f"Qué tan parejo se mantiene el saldo día a día. Un valor de {cv_pct:.1f}% "
        f"significa que el saldo típicamente se aleja ±{cv_pct:.1f}% de su promedio. "
        "Menor valor = más estable y predecible."
    ),
)
st.caption(
    f"Días bajo el umbral de seguridad ({_md(fmt_clp(r['umbral']))}): "
    f"**{r['dias_bajo_umbral']}** de {r['n_dias']} "
    f"({fmt_pct(r['pct_dias_bajo_umbral'])} del período)."
)
