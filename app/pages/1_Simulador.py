"""
app/pages/1_Simulador.py

Simulador financiero — controles en sidebar, resultados en 3 secciones jerárquicas.
"""

import os
import sqlite3
import sys
import math

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from core.liquidity import resumen_riesgo
from core.breakeven import comunidades_breakeven, tasa_breakeven, costo_max_breakeven
from core.formatting import fmt_clp, fmt_abr
from app.styles import inject_css, sidebar_header, banner, ebitda_box, ACCENT, CARD, BORDER, MUTED, TEXT

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "saldos_diarios.db")

st.set_page_config(page_title="Simulador — BanComunidad", layout="wide")
inject_css()

with st.sidebar:
    sidebar_header()


def fmt(n: float) -> str:
    return fmt_clp(n)


def _md(s: str) -> str:
    return s.replace("$", r"\$")


@st.cache_data
def cargar_real():
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM saldos_diarios", con, parse_dates=["fecha"])
    con.close()
    return resumen_riesgo(df)


tiene_datos = os.path.exists(DB_PATH)

if tiene_datos:
    r = cargar_real()
    real_n           = int(r["n_comunidades"])
    real_saldo       = r["saldo_promedio"]
    real_pct         = r["pct_invertible_recomendado"]
    real_multiplo    = r["multiplo_diversificacion"]
    real_saldo_x_com = real_saldo / real_n / 1_000_000
else:
    real_n, real_saldo, real_pct, real_multiplo, real_saldo_x_com = 43, 1_022_713_404, 0.866, 1.32, 23.8
    r = {"capital_invertible_recomendado": 885_693_901}

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Parámetros")

    # Inicializar session state
    if "n_com" not in st.session_state:
        st.session_state["n_com"] = real_n
    if "saldo_mm" not in st.session_state:
        st.session_state["saldo_mm"] = max(1, min(200, int(round(real_saldo_x_com))))

    # Leer valores actuales de los sliders para calcular break-even dinámico
    # (se necesitan antes de renderizar los botones)
    _saldo_actual   = st.session_state.get("saldo_mm", int(round(real_saldo_x_com))) * 1_000_000
    _pct_actual     = st.session_state.get("pct_inv_val", int(real_pct * 100)) / 100
    _tasa_actual    = st.session_state.get("tasa_val", 5.0) / 100
    _pct_bc_actual  = st.session_state.get("pct_bc_val", 50) / 100
    _costo_actual   = st.session_state.get("costo_val", 3_260_000)

    _be_n = comunidades_breakeven(_saldo_actual, _pct_actual, _tasa_actual, _pct_bc_actual, _costo_actual)
    _be_label = f"Break-even ({math.ceil(_be_n) if math.isfinite(_be_n) else '∞'})"

    st.caption("Escenarios rápidos")
    e1, e2 = st.columns(2)
    if e1.button("Actual"):
        st.session_state["n_com"]    = real_n
        st.session_state["saldo_mm"] = max(1, min(200, int(round(real_saldo_x_com))))
    if e2.button(_be_label):
        if math.isfinite(_be_n):
            st.session_state["n_com"] = math.ceil(_be_n)
    e3, e4 = st.columns(2)
    if e3.button("100"):
        st.session_state["n_com"] = 100
    if e4.button("500"):
        st.session_state["n_com"] = 500

    st.divider()

    n_comunidades = st.number_input(
        "N° de comunidades",
        min_value=1, max_value=50_000, step=1, key="n_com",
    )
    saldo_promedio_por_comunidad = st.slider(
        "Saldo promedio / comunidad (MM$)",
        min_value=1, max_value=200, step=1, key="saldo_mm",
    ) * 1_000_000
    st.caption(f"Actual en cartera: **MM\\${real_saldo_x_com:.1f}**")

    pct_invertible = st.slider(
        "% invertido",
        min_value=10, max_value=90,
        value=int(real_pct * 100),
        step=5, format="%d%%", key="pct_inv_val",
        help=f"Real actual (P5): {real_pct*100:.1f}% · Múltiplo diversificación: {real_multiplo:.2f}x",
    ) / 100

    tasa_anual = st.slider(
        "Tasa anual (%)",
        min_value=1.0, max_value=12.0, value=5.0, step=0.25,
        format="%.2f%%", key="tasa_val",
    ) / 100

    st.divider()
    pct_bancocomunidad = st.slider(
        "% BanComunidad",
        min_value=10, max_value=90, value=50, step=5,
        format="%d%%", key="pct_bc_val",
        help="Porcentaje de los intereses que retiene BanComunidad.",
    ) / 100
    pct_comunidades = 1 - pct_bancocomunidad
    st.caption(f"BC **{pct_bancocomunidad*100:.0f}%** · Comunidades **{pct_comunidades*100:.0f}%**")

    st.divider()
    with st.expander("Ver desglose de costos"):
        st.caption("Ingresa los costos fijos mensuales estimados por categoría.")
        c_sueldos  = st.number_input("Sueldos y honorarios",   min_value=0, value=2_000_000, step=100_000, format="%d")
        c_tech     = st.number_input("Tecnología / software",  min_value=0, value=500_000,   step=50_000,  format="%d")
        c_oficina  = st.number_input("Oficina / arriendo",     min_value=0, value=400_000,   step=50_000,  format="%d")
        c_otros    = st.number_input("Otros gastos",           min_value=0, value=360_000,   step=50_000,  format="%d")
        costos_mensual = c_sueldos + c_tech + c_oficina + c_otros
        st.caption(f"**Total: {_md(fmt(costos_mensual))}/mes**")
        st.session_state["costo_val"] = costos_mensual

    costos_anual = costos_mensual * 12

# ── CÁLCULOS ───────────────────────────────────────────────────────────────────
saldo_total        = saldo_promedio_por_comunidad * n_comunidades
capital_invertido  = saldo_total * pct_invertible
interes_anual      = capital_invertido * tasa_anual
interes_mensual    = interes_anual / 12
utilidad_bc_anual  = interes_anual * pct_bancocomunidad
utilidad_bc_mes    = utilidad_bc_anual / 12
utilidad_com_anual = interes_anual * pct_comunidades
utilidad_com_mes   = utilidad_com_anual / 12
ebitda_mensual     = utilidad_bc_mes - costos_mensual
ebitda_anual       = ebitda_mensual * 12
sobre_breakeven    = ebitda_mensual >= 0

be_n    = comunidades_breakeven(saldo_promedio_por_comunidad, pct_invertible, tasa_anual, pct_bancocomunidad, costos_mensual)
be_tasa = tasa_breakeven(int(n_comunidades), saldo_promedio_por_comunidad, pct_invertible, pct_bancocomunidad, costos_mensual)
be_costo_max = costo_max_breakeven(int(n_comunidades), saldo_promedio_por_comunidad, pct_invertible, tasa_anual, pct_bancocomunidad)

# ── ÁREA PRINCIPAL ─────────────────────────────────────────────────────────────
st.title("Simulador financiero")

with st.expander("Situación actual — datos reales", expanded=True):
    ra, rb, rc, rd, re = st.columns(5)
    ra.metric("Comunidades activas", real_n)
    rb.metric("Saldo total administrado", fmt_abr(real_saldo), help=fmt_clp(real_saldo))
    rc.metric("Saldo / comunidad", f"MM${real_saldo_x_com:.1f}")
    rd.metric("% invertible (P5)", f"{real_pct*100:.1f}%")
    re.metric("Múltiplo diversificación", f"{real_multiplo:.2f}x")

st.divider()

# ══ SECCIÓN 1: BANNER BREAK-EVEN ══════════════════════════════════════════════
if sobre_breakeven:
    banner(
        title=f"Rentable — EBITDA +{fmt(ebitda_mensual)}/mes",
        subtitle=f"Con {int(n_comunidades):,} comunidades · +{fmt(ebitda_anual)}/año",
        positive=True,
    )
else:
    deficit     = abs(ebitda_mensual)
    be_n_ceil   = math.ceil(be_n) if math.isfinite(be_n) else "∞"
    be_tasa_pct = f"{be_tasa*100:.2f}%" if math.isfinite(be_tasa) else "∞"
    faltantes   = (be_n_ceil - int(n_comunidades)) if math.isfinite(be_n) else "∞"
    banner(
        title=f"Bajo break-even — déficit {fmt(deficit)}/mes",
        subtitle=f"Con {int(n_comunidades):,} comunidades · déficit anual {fmt(abs(ebitda_anual))}",
        positive=False,
        extra_lines=[
            f"<b>{be_n_ceil} comunidades</b> (faltan {faltantes})",
            f"Tasa anual mínima <b>{be_tasa_pct}</b> (hoy: {tasa_anual*100:.2f}%)",
            f"Reducir costos a máx. <b>{fmt(be_costo_max)}/mes</b> (hoy: {fmt(costos_mensual)}/mes)",
        ],
    )

st.divider()

# ══ SECCIÓN 2: ¿CUÁNTO SE GENERA? ═════════════════════════════════════════════
st.subheader("¿Cuánto se genera?")

c1, arr1, c2, arr2, c3 = st.columns([3, 1, 3, 1, 4])

with c1:
    st.metric(
        "Capital invertido",
        fmt_abr(capital_invertido),
        delta=fmt_abr(capital_invertido - r["capital_invertible_recomendado"]) if tiene_datos else None,
        help=fmt_clp(capital_invertido),
    )
    st.caption(
        f"{pct_invertible*100:.0f}% del saldo total "
        f"({fmt_abr(saldo_total)}) · percentil P5"
    )

with arr1:
    st.markdown(f"<div style='text-align:center;font-size:26px;padding-top:22px;color:#555'>→</div>",
                unsafe_allow_html=True)

with c2:
    st.metric("Intereses / mes", fmt_abr(interes_mensual), help=fmt_clp(interes_mensual))
    st.caption(f"Tasa {tasa_anual*100:.2f}% anual · {fmt_abr(interes_anual)}/año")

with arr2:
    st.markdown(f"<div style='text-align:center;font-size:26px;padding-top:22px;color:#555'>→</div>",
                unsafe_allow_html=True)

with c3:
    sc3a, sc3b = st.columns(2)
    with sc3a:
        st.metric(f"BanComunidad ({pct_bancocomunidad*100:.0f}%)", fmt_abr(utilidad_bc_mes),
                  help=fmt_clp(utilidad_bc_mes))
        st.caption(f"{fmt_abr(utilidad_bc_anual)}/año")
    with sc3b:
        st.metric(f"Comunidades ({pct_comunidades*100:.0f}%)", fmt_abr(utilidad_com_mes),
                  help=fmt_clp(utilidad_com_mes))
        st.caption(f"{fmt_abr(utilidad_com_anual)}/año")

st.divider()

# ══ SECCIÓN 3: RESULTADO DEL NEGOCIO (EBITDA) ═════════════════════════════════
st.subheader("Resultado del negocio (EBITDA)")

d1, op1, d2, op2, d3 = st.columns([3, 1, 3, 1, 3])

with d1:
    st.metric("Ingreso bruto BC / mes", fmt_abr(utilidad_bc_mes), help=fmt_clp(utilidad_bc_mes))
    st.caption(
        f"{pct_bancocomunidad*100:.0f}% de los {fmt_abr(interes_mensual)} "
        f"de intereses mensuales generados"
    )

with op1:
    st.markdown(f"<div style='text-align:center;font-size:28px;padding-top:22px;color:#555'>−</div>",
                unsafe_allow_html=True)

with d2:
    st.metric("Costos operativos / mes", fmt_abr(costos_mensual), help=fmt_clp(costos_mensual))
    st.caption(f"Fijos estimados · {fmt_abr(costos_anual)}/año")

with op2:
    st.markdown("<div style='text-align:center;font-size:28px;padding-top:18px;color:#aaa'>=</div>",
                unsafe_allow_html=True)

with d3:
    ebitda_box(ebitda_mensual, ebitda_anual, sobre_breakeven, fmt_abr)

st.divider()

ec1, ec2, ec3 = st.columns(3)
ec1.metric(
    "Retorno total comunidades / año",
    fmt_abr(utilidad_com_anual),
    help=f"{pct_comunidades*100:.0f}% de los intereses generados · exacto: {fmt_clp(utilidad_com_anual)}",
)
ec2.metric(
    "Retorno por comunidad / año",
    fmt_abr(utilidad_com_anual / n_comunidades) if n_comunidades else "$0",
    help=(
        f"Total que reciben las comunidades ({fmt_clp(utilidad_com_anual)}) "
        f"÷ {int(n_comunidades):,} comunidades simuladas"
    ),
)
ec3.metric(
    "Retorno por comunidad / mes",
    fmt_abr(utilidad_com_mes / n_comunidades) if n_comunidades else "$0",
)
