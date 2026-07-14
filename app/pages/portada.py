"""
app/pages/portada.py — Landing page del dashboard. Primera pantalla.
"""
import math
import os
import sqlite3
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from core.liquidity import resumen_riesgo
from core.formatting import fmt_abr
from app.styles import ACCENT, CARD, BORDER, MUTED, TEXT, _SHADOW

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "saldos_diarios.db")
_PAGES  = os.path.dirname(__file__)


@st.cache_data
def _kpis():
    if not os.path.exists(DB_PATH):
        return 1_022_000_000, 43, 365
    con = sqlite3.connect(DB_PATH)
    df  = pd.read_sql("SELECT comunidad_id, fecha, saldo FROM saldos_diarios", con, parse_dates=["fecha"])
    con.close()
    r = resumen_riesgo(df)
    return r["saldo_promedio"], int(r["n_comunidades"]), int(r["n_dias"])


saldo_total, n_com, n_dias = _kpis()
kpi_line = f"{fmt_abr(saldo_total)} administrados · {n_com} comunidades · {n_dias} días de datos"

# ── SVG vault (bóveda arquitectónica vista desde abajo) ────────────────────────
_cx, _cy = 600, 88
_ribs = []
for i in range(28):
    angle = 2 * math.pi * i / 28
    x2 = _cx + 950 * math.cos(angle)
    y2 = _cy + 950 * math.sin(angle)
    _ribs.append(f'<line x1="{_cx}" y1="{_cy}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="#1E1E1E" stroke-width="1.2"/>')

_arches = []
for i, (rx, ry) in enumerate([(46,32),(96,66),(158,107),(232,152),(318,203),(420,258)]):
    stroke = "#C054BB" if i < 2 else "#282828"
    sw     = "1.1"    if i < 2 else "0.7"
    op     = round(max(0.12, 0.78 - i * 0.12), 2)
    _arches.append(
        f'<ellipse cx="{_cx}" cy="{_cy}" rx="{rx}" ry="{ry}" fill="none" '
        f'stroke="{stroke}" stroke-width="{sw}" opacity="{op}"/>'
    )

_SVG = f"""<svg viewBox="0 0 1200 320" xmlns="http://www.w3.org/2000/svg" style="width:100%;display:block">
  <defs>
    <radialGradient id="vg" cx="50%" cy="27.5%" r="52%">
      <stop offset="0%"   stop-color="#C054BB" stop-opacity="0.44"/>
      <stop offset="38%"  stop-color="#7B2D7B" stop-opacity="0.11"/>
      <stop offset="100%" stop-color="#191919" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="cg" cx="50%" cy="27.5%" r="6%">
      <stop offset="0%"   stop-color="#E888E0" stop-opacity="1"/>
      <stop offset="100%" stop-color="#C054BB" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="fg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="52%" stop-color="#191919" stop-opacity="0"/>
      <stop offset="100%" stop-color="#191919" stop-opacity="1"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="320" fill="#191919"/>
  {"".join(_ribs)}
  {"".join(_arches)}
  <rect width="1200" height="320" fill="url(#vg)"/>
  <circle cx="{_cx}" cy="{_cy}" r="14" fill="url(#cg)"/>
  <rect width="1200" height="320" fill="url(#fg)"/>
  <text x="600" y="180" text-anchor="middle" font-size="38" font-weight="700"
        fill="#F4F4F4" font-family="sans-serif" letter-spacing="-0.5">BanComunidad Intelligence</text>
  <text x="600" y="216" text-anchor="middle" font-size="14" fill="#8A8A8A"
        font-family="sans-serif">Análisis financiero del float de comunidades residenciales</text>
  <text x="600" y="252" text-anchor="middle" font-size="12" fill="#C054BB"
        font-family="sans-serif" letter-spacing="0.8">{kpi_line}</text>
</svg>"""

st.markdown(
    f'<div style="border-radius:16px;overflow:hidden;border:1px solid {BORDER};'
    f'box-shadow:{_SHADOW};margin-bottom:28px">{_SVG}</div>',
    unsafe_allow_html=True,
)

# ── Cards de módulos ──────────────────────────────────────────────────────────
# Fuente Material Symbols outline (mismos íconos que el sidebar, pero en HTML → tamaño controlable)
st.markdown(
    f"""
    <link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@40,300,0,0"/>
    <style>
    /* Columna como contexto de posicionamiento para el overlay */
    section[data-testid="stMain"] [data-testid="stColumn"] {{
        position: relative !important;
        overflow: visible !important;
    }}
    /* El <button> se posiciona absoluto respecto a la columna,
       cubriendo exactamente los 170px de la card visual */
    section[data-testid="stMain"] [data-testid="stColumn"] [data-testid="stButton"] button {{
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 170px !important;
        min-height: unset !important;
        opacity: 0 !important;
        cursor: pointer !important;
        z-index: 20 !important;
        border-radius: 12px !important;
        padding: 0 !important;
        margin: 0 !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}
    /* Hover en columna → ilumina la card y el ícono debajo */
    section[data-testid="stMain"] [data-testid="stColumn"]:hover .mod-card {{
        border-color: #C054BB !important;
        box-shadow: 0 4px 24px rgba(192,84,187,0.22) !important;
    }}
    section[data-testid="stMain"] [data-testid="stColumn"]:hover .mod-icon {{
        color: #C054BB !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

MODULES = [
    ("grid_view",  "Modelo",       "Cobertura de datos: qué cartolas tenemos y cuáles faltan",    "modelo.py"),
    ("bar_chart",  "Resultados",   "Capital administrado, invertible y evolución del portafolio",  "resultados.py"),
    ("tune",       "Simulador",    "Proyecta escenarios de rentabilidad y punto de break-even",   "simulador.py"),
    ("search",     "Análisis",     "Comparativa por comunidad, banco y tamaño de edificio",       "analisis.py"),
    ("apartment",  "Mi Comunidad", "Vista del administrador: saldo actual, flujo y rentabilidad", "mi_comunidad.py"),
    ("smart_toy",  "Inteligencia", "Análisis ejecutivo e insights generados por IA (Claude)",     "inteligencia.py"),
]

c1, c2, c3, c4 = st.columns(4)
_g1, c5, c6, _g2 = st.columns([1, 2, 2, 1])

for col, (icon, title, desc, page_file) in zip([c1, c2, c3, c4, c5, c6], MODULES):
    page_path = os.path.join(_PAGES, page_file)
    with col:
        st.markdown(
            f"""<div class="mod-card" style="
                background:{CARD};border:1px solid {BORDER};border-radius:12px;
                padding:28px 16px 22px;text-align:center;box-shadow:{_SHADOW};
                min-height:170px;display:flex;flex-direction:column;
                justify-content:center;align-items:center;gap:10px;
                transition:border-color 0.18s,box-shadow 0.18s">
              <span class="material-symbols-outlined mod-icon" style="
                font-size:40px;color:{MUTED};transition:color 0.18s;
                font-variation-settings:'FILL' 0,'wght' 300,'GRAD' 0,'opsz' 40;
                user-select:none">{icon}</span>
              <div style="font-size:17px;font-weight:700;color:{TEXT};line-height:1.2;margin:0">{title}</div>
              <div style="font-size:12px;color:{MUTED};line-height:1.55;max-width:190px;margin:0">{desc}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        if st.button("", key=f"go_{title}", use_container_width=True):
            st.switch_page(page_path)

