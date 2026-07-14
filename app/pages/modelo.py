"""
app/pages/modelo.py — Página "Modelo": qué datos tenemos y cómo se construyó.
Primera del menú. Orientada a mostrarle a un socio/inversionista el punto de partida.
"""

import os
import sqlite3
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from core.cobertura import resumen_cobertura, matriz_cobertura_mensual
from app.styles import ACCENT, CARD, BORDER, MUTED, TEXT, _SHADOW

DB_PATH  = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "saldos_diarios.db")
_PORTADA = os.path.join(os.path.dirname(__file__), "portada.py")

with st.sidebar:
    if st.button("← Portada", key="back_portada_mod"):
        st.switch_page(_PORTADA)

ESTADO_ICON  = {"Cargado": "✓", "Parcial": "⚠", "Falta": "✕"}
ESTADO_COLOR = {
    "Cargado": ("transparent",            "#C054BB"),
    "Parcial":  ("rgba(230,180,60,0.10)", "#E6B43C"),
    "Falta":    ("transparent",           "#555555"),
}


@st.cache_data
def cargar_datos():
    con = sqlite3.connect(DB_PATH)
    df_ed  = pd.read_sql("SELECT * FROM edificios", con)
    df_sal = pd.read_sql("SELECT * FROM saldos_diarios", con, parse_dates=["fecha"])
    con.close()
    return df_ed, df_sal


if not os.path.exists(DB_PATH):
    st.error("No se encontró la base de datos.")
    st.stop()

df_ed, df_sal = cargar_datos()
cob = resumen_cobertura(df_ed, df_sal)

# ── Encabezado ─────────────────────────────────────────────────────────────────
st.title(":material/grid_view: Modelo")
st.markdown(
    f"""
    <div style="background:{CARD};border:1px solid {BORDER};border-radius:12px;
                padding:24px 28px;margin-bottom:8px;box-shadow:{_SHADOW}">
      <div style="font-size:15px;color:{TEXT};line-height:1.8;max-width:720px">
        BanComunidad administra el <b>float de tesorería</b> de condominios urbanos —
        el saldo que permanece quieto en cuentas corrientes mientras las comunidades
        esperan pagar gastos comunes. Este modelo toma las <b>cartolas bancarias reales</b>
        de cada comunidad, extrae el saldo diario, y calcula cuánto capital es
        invertible de forma segura sin afectar la operación.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Mini-stats en fila de 4 bajo el texto descriptivo
_stats_data = [
    ("Comunidades",    cob["con_datos"],                       "con cartolas cargadas"),
    ("Bancos",         df_ed["banco"].nunique(),               "instituciones"),
    ("Administradores",df_ed["admin"].nunique(),               "empresas gestoras"),
    ("Unidades",       f"{int(df_ed['unidades'].sum()):,}",   "residenciales"),
]
_stat_html = "".join(
    f"""<div style="flex:1;min-width:120px;background:{CARD};border:1px solid {BORDER};
        border-radius:10px;padding:18px 14px;text-align:center;box-shadow:{_SHADOW}">
      <div style="font-size:10px;color:{MUTED};text-transform:uppercase;
                  letter-spacing:0.5px;margin-bottom:8px">{lbl}</div>
      <div style="font-size:30px;font-weight:700;color:{ACCENT};
                  letter-spacing:-0.5px;line-height:1">{val}</div>
      <div style="font-size:11px;color:{MUTED};margin-top:5px">{sub}</div>
    </div>"""
    for lbl, val, sub in _stats_data
)
st.markdown(
    f'<div style="display:flex;gap:12px;margin-top:12px;margin-bottom:4px">{_stat_html}</div>',
    unsafe_allow_html=True,
)

st.divider()

# ── KPIs de cobertura ──────────────────────────────────────────────────────────
# Calcular cobertura real a nivel de cartolas (celdas en la matriz)
# Se hace aquí arriba para usar el resultado en los KPIs antes de mostrar la grilla
@st.cache_data
def _cobertura_cartolas(_n_sal: int, _n_ed: int):
    mat = matriz_cobertura_mensual(df_sal, df_ed)
    mes_cols = [c for c in mat.columns if c not in ("comunidad_id", "banco")]
    celdas_posibles = len(mat) * len(mes_cols)
    celdas_cargadas = (mat[mes_cols] == "Cargado").values.sum()
    return int(celdas_cargadas), int(celdas_posibles)

celdas_cargadas, celdas_posibles = _cobertura_cartolas(len(df_sal), len(df_ed))
pct_cartolas = celdas_cargadas / celdas_posibles if celdas_posibles else 0.0

st.subheader("Cobertura de datos")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total edificios en cartera", cob["total_edificios"])
k2.metric(
    "Con cartolas cargadas",
    cob["con_datos"],
    help=f"{cob['pct_cobertura']*100:.1f}% de comunidades con al menos un mes cargado",
)
k3.metric("Pendientes de cargar", cob["n_faltantes"])
k4.metric(
    "Cobertura de cartolas",
    f"{pct_cartolas*100:.1f}%",
    help=(
        f"{celdas_cargadas} de {celdas_posibles} cartolas mensuales completas "
        f"({cob['total_edificios']} comunidades × {celdas_posibles // cob['total_edificios'] if cob['total_edificios'] else 0} meses). "
        "Mide completitud mes a mes, no solo comunidades iniciadas."
    ),
)

pct = pct_cartolas
st.markdown(
    f"""
    <div style="margin:12px 0 4px">
      <div style="font-size:10px;color:{MUTED};text-transform:uppercase;
                  letter-spacing:0.5px;margin-bottom:6px">
        Cartolas completas — {celdas_cargadas} de {celdas_posibles} posibles
      </div>
      <div style="background:{BORDER};border-radius:6px;height:8px;overflow:hidden">
        <div style="background:{ACCENT};width:{pct*100:.1f}%;height:100%;
                    border-radius:6px;transition:width 0.3s"></div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Badges por banco
faltantes_por_banco = cob["faltantes_por_banco"]
banco_badges = "  ".join(
    f'<span style="background:{CARD};border:1px solid {BORDER};border-radius:4px;'
    f'padding:2px 8px;font-size:11px;color:{MUTED}">{b}: {n}</span>'
    for b, n in faltantes_por_banco.items()
)
st.markdown(
    f'<div style="margin:14px 0 4px;font-size:11px;color:{MUTED};'
    f'text-transform:uppercase;letter-spacing:0.4px">Pendientes por banco</div>'
    f'<div style="margin-bottom:20px">{banco_badges}</div>',
    unsafe_allow_html=True,
)

st.divider()

# ── Grilla heatmap ─────────────────────────────────────────────────────────────
st.subheader("Cartolas cargadas por mes")
st.caption(
    "Una celda por comunidad × mes. "
    "✓ Cargado ≥ 90% de días · ⚠ Parcial 1–89% · ✕ Falta sin datos."
)

solo_incompletas = st.checkbox("Mostrar solo comunidades con meses incompletos o faltantes", value=False)

@st.cache_data
def calcular_matriz(solo_incompletas: bool, _n_sal: int, _n_ed: int):
    """_n_sal/_n_ed invalidan el cache automáticamente cuando cambia la BD."""
    mat = matriz_cobertura_mensual(df_sal, df_ed)
    mes_cols = [c for c in mat.columns if c not in ("comunidad_id", "banco")]
    if solo_incompletas:
        tiene_problema = mat[mes_cols].apply(
            lambda row: any(v != "Cargado" for v in row), axis=1
        )
        mat = mat[tiene_problema]
    return mat, mes_cols

mat, mes_cols = calcular_matriz(solo_incompletas, len(df_sal), len(df_ed))

# Formatear encabezados de mes: '2025-04' -> 'Abr-25'
_MESES_ES = {
    "01": "Ene", "02": "Feb", "03": "Mar", "04": "Abr",
    "05": "May", "06": "Jun", "07": "Jul", "08": "Ago",
    "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dic",
}
def _header(col: str) -> str:
    try:
        y, m = col.split("-")
        return f"{_MESES_ES.get(m, m)}-{y[2:]}"
    except Exception:
        return col

headers = [_header(c) for c in mes_cols]

# Construir HTML table
_BG    = "#141414"
_BORDER_C = "#2A2A2A"

rows_html = []
for _, row in mat.iterrows():
    cells = [
        f'<td style="padding:4px 10px;white-space:nowrap;font-weight:500;'
        f'color:{TEXT};border-right:1px solid {_BORDER_C}">{row["comunidad_id"]}</td>',
        f'<td style="padding:4px 10px;white-space:nowrap;color:{MUTED};'
        f'font-size:11px;border-right:1px solid {_BORDER_C}">{row.get("banco","")}</td>',
    ]
    for col in mes_cols:
        estado = row[col]
        bg, fg = ESTADO_COLOR.get(estado, ("transparent", "#555"))
        icon   = ESTADO_ICON.get(estado, "?")
        shadow = (
            f"text-shadow:0 0 6px {fg}88"
            if estado in ("Cargado", "Parcial")
            else ""
        )
        cells.append(
            f'<td style="text-align:center;background:{bg};color:{fg};'
            f'font-size:14px;font-weight:700;padding:5px 4px;{shadow};'
            f'border-right:1px solid {_BORDER_C}">{icon}</td>'
        )
    rows_html.append(f'<tr style="border-bottom:1px solid {_BORDER_C}">' + "".join(cells) + "</tr>")

header_cells = (
    f'<th style="padding:6px 10px;text-align:left;color:{MUTED};font-size:11px;'
    f'font-weight:600;text-transform:uppercase;letter-spacing:0.4px;'
    f'white-space:nowrap;border-right:1px solid {_BORDER_C}">Comunidad</th>'
    f'<th style="padding:6px 10px;text-align:left;color:{MUTED};font-size:11px;'
    f'font-weight:600;text-transform:uppercase;letter-spacing:0.4px;'
    f'white-space:nowrap;border-right:1px solid {_BORDER_C}">Banco</th>'
)
for h in headers:
    header_cells += (
        f'<th style="padding:6px 6px;text-align:center;color:{MUTED};font-size:11px;'
        f'font-weight:600;white-space:nowrap;border-right:1px solid {_BORDER_C}">{h}</th>'
    )

html = f"""
<div style="overflow-x:auto;border-radius:10px;border:1px solid {_BORDER_C};
            box-shadow:0 1px 3px rgba(0,0,0,0.5)">
  <table style="border-collapse:collapse;width:100%;background:{_BG};font-size:13px;
                font-family:inherit">
    <thead>
      <tr style="background:#1A1A1A;border-bottom:1px solid {_BORDER_C}">
        {header_cells}
      </tr>
    </thead>
    <tbody>
      {"".join(rows_html)}
    </tbody>
  </table>
</div>
"""

st.markdown(html, unsafe_allow_html=True)

# Leyenda
st.markdown(
    f"""
    <div style="margin-top:12px;display:flex;gap:20px;font-size:12px;color:{MUTED}">
      <span><b style="color:#C054BB">✓</b> Cargado (≥90% días del mes)</span>
      <span><b style="color:#E6B43C">⚠</b> Parcial (1–89%)</span>
      <span><b style="color:#555">✕</b> Sin datos</span>
    </div>
    """,
    unsafe_allow_html=True,
)

