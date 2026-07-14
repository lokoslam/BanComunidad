"""
app/pages/mi_comunidad.py — Vista del administrador de edificio.
Muestra el saldo actual, flujo de saldos y rentabilidad estimada.
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
from app.styles import (
    plotly_layout, PLT_LINE, PLT_ACCENT, PLT_MUTED,
    ACCENT, CARD, BORDER, MUTED, TEXT, _SHADOW,
)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "saldos_diarios.db")
_PORTADA = os.path.join(os.path.dirname(__file__), "portada.py")

with st.sidebar:
    if st.button("← Portada", key="back_portada_mc"):
        st.switch_page(_PORTADA)

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


df_sal, df_ed = cargar_datos()
comunidades = sorted(df_sal["comunidad_id"].unique())

# ── Header: selector de comunidad ─────────────────────────────────────────────
st.title(":material/apartment: Mi Comunidad")
st.caption("Vista del administrador — saldo, flujo y rentabilidad estimada")

_mc_sel_col, _ = st.columns([2, 3])
with _mc_sel_col:
    comunidad = st.selectbox("Selecciona tu comunidad", comunidades, key="mc_sel")

df_com = df_sal[df_sal["comunidad_id"] == comunidad].sort_values("fecha").reset_index(drop=True)
ed_info = df_ed[df_ed["comunidad_id"] == comunidad]

if df_com.empty:
    st.warning("Esta comunidad no tiene datos cargados.")
    st.stop()

# ── Cálculos base ──────────────────────────────────────────────────────────────
ultimo     = df_com.iloc[-1]
penultimo  = df_com.iloc[-2] if len(df_com) >= 2 else ultimo
saldo_hoy  = ultimo["saldo"]
saldo_ayer = penultimo["saldo"]
delta_dia  = saldo_hoy - saldo_ayer

mes_actual = ultimo["fecha"].month
anio_actual = ultimo["fecha"].year
df_mes     = df_com[(df_com["fecha"].dt.month == mes_actual) & (df_com["fecha"].dt.year == anio_actual)]
prom_mes   = df_mes["saldo"].mean()
delta_mes  = saldo_hoy - prom_mes

saldo_p5   = float(np.percentile(df_com["saldo"].dropna(), 5, method="linear"))
saldo_prom = df_com["saldo"].mean()
cv         = df_com["saldo"].std() / saldo_prom if saldo_prom else 0

# Rentabilidad estimada con BanComunidad (tasa 5% anual, 50% reparto)
TASA_ANUAL = 0.05
PCT_COM    = 0.50
rent_mes   = saldo_p5 * TASA_ANUAL / 12 * PCT_COM
rent_anual = rent_mes * 12

# ── Info del edificio ──────────────────────────────────────────────────────────
if not ed_info.empty:
    ei = ed_info.iloc[0]
    banco   = ei.get("banco", "—")
    unidades = int(ei.get("unidades", 0)) if pd.notna(ei.get("unidades")) else "—"
    admin   = ei.get("admin", "—")
    comuna  = ei.get("comuna", "—")
else:
    banco = unidades = admin = comuna = "—"

st.markdown(
    f"""<div style="background:{CARD};border:1px solid {BORDER};border-radius:10px;
        padding:14px 20px;margin-bottom:8px;display:flex;gap:32px;
        flex-wrap:wrap;box-shadow:{_SHADOW}">
      <span style="font-size:12px;color:{MUTED}">🏦 <b style="color:{TEXT}">{banco}</b></span>
      <span style="font-size:12px;color:{MUTED}">🏢 <b style="color:{TEXT}">{unidades} unidades</b></span>
      <span style="font-size:12px;color:{MUTED}">👤 Admin: <b style="color:{TEXT}">{admin}</b></span>
      <span style="font-size:12px;color:{MUTED}">📍 <b style="color:{TEXT}">{comuna}</b></span>
      <span style="font-size:12px;color:{MUTED}">📅 Último dato: <b style="color:{TEXT}">{ultimo['fecha'].strftime('%d/%m/%Y')}</b></span>
    </div>""",
    unsafe_allow_html=True,
)

st.divider()

# ══ SECCIÓN 1: SALDO HOY ══════════════════════════════════════════════════════
st.subheader("Saldo hoy")

# Número grande central
delta_dia_sign  = "+" if delta_dia >= 0 else ""
delta_dia_color = "#4CAF80" if delta_dia >= 0 else "#E05555"
delta_mes_sign  = "+" if delta_mes >= 0 else ""
delta_mes_color = "#4CAF80" if delta_mes >= 0 else "#E05555"

st.markdown(
    f"""<div style="background:{CARD};border:1px solid {BORDER};border-radius:14px;
        padding:32px 40px;text-align:center;box-shadow:{_SHADOW};margin-bottom:16px">
      <div style="font-size:12px;color:{MUTED};text-transform:uppercase;letter-spacing:0.6px;margin-bottom:8px">
        Saldo en cuenta — {ultimo['fecha'].strftime('%d de %B de %Y')}
      </div>
      <div style="font-size:52px;font-weight:800;color:{TEXT};letter-spacing:-1px;line-height:1.1">
        {fmt_abr(saldo_hoy)}
      </div>
      <div style="font-size:12px;color:{MUTED};margin-top:4px">{fmt_clp(saldo_hoy)}</div>
      <div style="display:flex;justify-content:center;gap:40px;margin-top:20px">
        <div style="text-align:center">
          <div style="font-size:11px;color:{MUTED};margin-bottom:4px">vs día anterior</div>
          <div style="font-size:18px;font-weight:700;color:{delta_dia_color}">
            {delta_dia_sign}{fmt_abr(delta_dia)}
          </div>
        </div>
        <div style="text-align:center">
          <div style="font-size:11px;color:{MUTED};margin-bottom:4px">vs promedio del mes</div>
          <div style="font-size:18px;font-weight:700;color:{delta_mes_color}">
            {delta_mes_sign}{fmt_abr(delta_mes)}
          </div>
        </div>
        <div style="text-align:center">
          <div style="font-size:11px;color:{MUTED};margin-bottom:4px">promedio histórico</div>
          <div style="font-size:18px;font-weight:700;color:{TEXT}">{fmt_abr(saldo_prom)}</div>
        </div>
      </div>
    </div>""",
    unsafe_allow_html=True,
)

st.divider()

# ══ SECCIÓN 2: Tu rendimiento con BanComunidad ══════════════════════════════
st.subheader("Tu rendimiento con BanComunidad")

r1, r2, r3 = st.columns(3)
r1.metric(
    "Capital invertible (P5)",
    fmt_abr(saldo_p5),
    help=f"Monto que tu comunidad supera el 95% de los días. Exacto: {fmt_clp(saldo_p5)}",
)
r2.metric(
    "Rentabilidad estimada / mes",
    fmt_abr(rent_mes),
    help=f"P5 × 5% anual × 50% reparto. Exacto: {fmt_clp(rent_mes)}",
)
r3.metric(
    "Acumulado estimado / año",
    fmt_abr(rent_anual),
    help=f"Proyección anual. Exacto: {fmt_clp(rent_anual)}",
)

st.markdown(
    f"""<div style="background:rgba(192,84,187,0.07);border:1px solid rgba(192,84,187,0.25);
        border-left:4px solid {ACCENT};border-radius:0 10px 10px 0;
        padding:16px 20px;margin:8px 0 0">
      <span style="color:{TEXT};font-size:14px">
        Con BanComunidad, <b>{comunidad}</b> podría generar
        <b style="color:{ACCENT}">{fmt_abr(rent_anual)} al año</b>
        sin cambiar nada en su operación — simplemente invirtiendo
        el float que hoy duerme en la cuenta corriente.
      </span>
    </div>""",
    unsafe_allow_html=True,
)

st.divider()

# ══ SECCIÓN 3: FLUJO DE SALDOS (últimos 90 días) ══════════════════════════════
st.subheader("Flujo de saldos — últimos 90 días")

df_90 = df_com.tail(90).copy()

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_90["fecha"], y=df_90["saldo"],
    mode="lines",
    line=dict(color=PLT_LINE, width=1.8),
    fill="tozeroy", fillcolor="rgba(244,244,244,0.04)",
    hovertemplate="<b>%{x|%d %b %Y}</b><br>Saldo: $%{y:,.0f}<extra></extra>",
))
fig.add_hline(
    y=saldo_p5, line_dash="dash", line_color=PLT_ACCENT, line_width=1.5,
    annotation_text=f"P5: {fmt_abr(saldo_p5)}", annotation_position="top left",
    annotation_font_color=PLT_ACCENT, annotation_font_size=11,
)
fig.add_hline(
    y=saldo_prom, line_dash="dot", line_color="rgba(244,244,244,0.25)", line_width=1,
    annotation_text=f"Prom: {fmt_abr(saldo_prom)}", annotation_position="bottom right",
    annotation_font_color="rgba(244,244,244,0.4)", annotation_font_size=10,
)
fig.update_layout(**plotly_layout(
    height=310, yaxis_title="CLP", showlegend=False,
    margin=dict(t=10, b=10, l=10, r=10),
))
st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

st.divider()

# ══ SECCIÓN 4: ÚLTIMOS 30 MOVIMIENTOS ═════════════════════════════════════════
st.subheader("Últimos 30 días")

df_30 = df_com.tail(30).copy().reset_index(drop=True)
df_30["variación"] = df_30["saldo"].diff()
df_30 = df_30.sort_values("fecha", ascending=False)

df_display = df_30[["fecha", "saldo", "variación"]].copy()
df_display["fecha"]     = df_display["fecha"].dt.strftime("%d/%m/%Y")
df_display["saldo"]     = df_display["saldo"].apply(fmt_clp)
df_display["variación"] = df_display["variación"].apply(
    lambda x: f"+{fmt_clp(x)}" if pd.notna(x) and x >= 0
    else (fmt_clp(x) if pd.notna(x) else "—")
)
df_display.columns = ["Fecha", "Saldo", "Variación día"]

st.dataframe(df_display, use_container_width=True, hide_index=True)

# Resumen de volatilidad
st.caption(
    f"Volatilidad (CV): **{cv*100:.1f}%** · "
    f"Mín histórico: **{fmt_abr(df_com['saldo'].min())}** · "
    f"Máx histórico: **{fmt_abr(df_com['saldo'].max())}**"
)

