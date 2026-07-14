"""
app/pages/inteligencia.py — Módulo de análisis IA con Claude.
Genera un análisis ejecutivo del portafolio en lenguaje natural.
"""
import os
import sqlite3
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from core.liquidity import resumen_riesgo
from core.formatting import fmt_clp, fmt_abr, fmt_pct
from app.styles import ACCENT, CARD, BORDER, MUTED, TEXT, _SHADOW

DB_PATH  = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "saldos_diarios.db")
_PORTADA = os.path.join(os.path.dirname(__file__), "portada.py")

with st.sidebar:
    if st.button("← Portada", key="back_portada_intel"):
        st.switch_page(_PORTADA)
    st.divider()
    st.caption("Modelo de IA")
    st.info("claude-sonnet-4-6", icon="🤖")

if not os.path.exists(DB_PATH):
    st.error("No se encontró la base de datos.")
    st.stop()


@st.cache_data
def cargar_resumen():
    con = sqlite3.connect(DB_PATH)
    df  = pd.read_sql("SELECT * FROM saldos_diarios", con, parse_dates=["fecha"])
    df_ed = pd.read_sql("SELECT * FROM edificios", con)
    con.close()
    r = resumen_riesgo(df)
    return r, df_ed


r, df_ed = cargar_resumen()

# ── Encabezado ─────────────────────────────────────────────────────────────────
st.title(":material/smart_toy: Inteligencia")
st.caption("Claude analiza el portafolio y entrega insights ejecutivos en lenguaje natural")

# ── Resumen de datos que se enviará a la IA ────────────────────────────────────
fecha_min = r.get("fecha_min", "—")
fecha_max = r.get("fecha_max", "—")

_PROMPT_DATOS = f"""
PORTAFOLIO — BanComunidad Intelligence

Período analizado: {r.get('n_dias', '—')} días de datos reales
Comunidades activas: {r['n_comunidades']}
Total edificios en cartera: {df_ed['comunidad_id'].nunique()}
Bancos representados: {df_ed['banco'].nunique()}
Administradores: {df_ed['admin'].nunique()}
Unidades residenciales totales: {int(df_ed['unidades'].sum()):,}

SALDOS
Saldo promedio diario (portafolio agregado): {fmt_clp(r['saldo_promedio'])}
Capital invertible recomendado (P5): {fmt_clp(r['capital_invertible_recomendado'])}
% invertible del saldo promedio: {fmt_pct(r['pct_invertible_recomendado'])}
Saldo mínimo histórico agregado: {fmt_clp(r['saldo_minimo_agregado'])}
Suma de mínimos individuales (sin diversificación): {fmt_clp(r['suma_minimos_individuales'])}
Capital extra generado por diversificación: {fmt_clp(r['capital_extra_por_diversificar'])}
Múltiplo de diversificación: {r['multiplo_diversificacion']:.2f}x

RIESGO
Mayor caída diaria observada: {fmt_clp(r['mayor_caida_diaria'])}
Mayor alza diaria observada: {fmt_clp(r['mayor_alza_diaria'])}
Coeficiente de variación del portafolio: {r['coeficiente_variacion']:.3f}
Días bajo umbral de seguridad: {r['dias_bajo_umbral']} de {r['n_dias']} ({fmt_pct(r['pct_dias_bajo_umbral'])})

CONTEXTO
Este negocio propone invertir el float de tesorería de comunidades residenciales
que permanece quieto en cuentas corrientes bancarias. BanComunidad actúa como
intermediario financiero, agrupa comunidades para potenciar el capital invertible
vía diversificación, y reparte los rendimientos entre la empresa y cada comunidad.
El mercado potencial chileno supera 50,000 comunidades administradas.
"""

_SYSTEM_PROMPT = """Eres un analista financiero senior especializado en fintechs y modelos de negocio
de intermediación financiera en Latinoamérica. Analizas portafolios de capital y
entregas insights accionables para inversionistas y equipos ejecutivos.

Tu análisis debe ser directo, sin jerga técnica innecesaria, orientado a decisiones.
Usa lenguaje claro que entienda un inversionista no técnico pero sofisticado.
Sé específico con los números — cita las cifras que respaldan cada conclusión.

Estructura tu respuesta EXACTAMENTE así (usa estos títulos con ##):

## Resumen ejecutivo
2-3 párrafos. ¿Qué es este negocio, qué tan grande es la oportunidad, qué muestran los datos?

## Los 5 insights clave
Lista numerada. Cada insight: una oración de título en negrita + 1-2 oraciones de explicación con el número que lo respalda.

## Riesgos principales
3-4 riesgos concretos e identificados en los datos (no genéricos).

## Recomendación del analista
1 párrafo directo: ¿invertirías o no? ¿por qué? ¿qué condición faltante cambiaría tu decisión?"""

# ── API Key ────────────────────────────────────────────────────────────────────
api_key = os.environ.get("ANTHROPIC_API_KEY", "")
if not api_key:
    with st.expander("🔑 Configurar API Key de Anthropic", expanded=True):
        api_key = st.text_input(
            "ANTHROPIC_API_KEY",
            type="password",
            placeholder="sk-ant-...",
            help="Obtén tu API key en console.anthropic.com",
        )

# ── Botón principal ────────────────────────────────────────────────────────────
st.divider()

col_btn, col_info = st.columns([2, 5])
with col_btn:
    generar = st.button(
        "🤖  Generar análisis",
        type="primary",
        use_container_width=True,
        disabled=not api_key,
    )
with col_info:
    st.markdown(
        f'<div style="padding:10px 0;font-size:12px;color:{MUTED}">'
        f'Analiza {r["n_comunidades"]} comunidades · {r["n_dias"]} días de datos · '
        f'{fmt_abr(r["saldo_promedio"])} en portafolio</div>',
        unsafe_allow_html=True,
    )

if not api_key:
    st.info("Ingresa tu API key de Anthropic arriba para activar el análisis.")
    st.stop()

# Guardar análisis en session state para persistencia
if "intel_resultado" not in st.session_state:
    st.session_state["intel_resultado"] = ""
if "intel_prompt_usado" not in st.session_state:
    st.session_state["intel_prompt_usado"] = ""

if generar:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        with st.spinner("Claude está analizando el portafolio..."):
            msg = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2000,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": _PROMPT_DATOS}],
            )
        st.session_state["intel_resultado"] = msg.content[0].text
        st.session_state["intel_prompt_usado"] = _PROMPT_DATOS

    except ImportError:
        st.error("Instala el paquete anthropic: `pip install anthropic`")
    except Exception as e:
        st.error(f"Error al llamar a la API: {e}")

# ── Mostrar resultado ──────────────────────────────────────────────────────────
if st.session_state.get("intel_resultado"):
    resultado = st.session_state["intel_resultado"]

    st.divider()

    st.markdown(
        f'<div style="background:{CARD};border:1px solid {BORDER};border-radius:14px;'
        f'padding:28px 32px;box-shadow:{_SHADOW}">',
        unsafe_allow_html=True,
    )
    st.markdown(resultado)
    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # Botón copiar
    col_copy, col_raw = st.columns([1, 4])
    with col_copy:
        st.download_button(
            "⬇ Descargar análisis",
            data=resultado,
            file_name="bancocomunidad_analisis_ia.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with st.expander("Ver datos enviados a Claude"):
        st.code(st.session_state.get("intel_prompt_usado", ""), language="text")

    st.caption(
        f"Análisis generado con claude-sonnet-4-6 · "
        f"Los datos son reales, el análisis es orientativo."
    )

elif not generar:
    # Estado vacío
    st.markdown(
        f"""<div style="background:{CARD};border:1px solid {BORDER};border-radius:14px;
            padding:48px;text-align:center;margin-top:16px">
          <div style="font-size:40px;margin-bottom:16px">🤖</div>
          <div style="font-size:16px;font-weight:600;color:{TEXT};margin-bottom:8px">
            Análisis ejecutivo con IA
          </div>
          <div style="font-size:13px;color:{MUTED};max-width:480px;margin:0 auto;line-height:1.6">
            Claude analiza los {r['n_comunidades']} comunidades, {r['n_dias']} días de datos
            y {fmt_abr(r['saldo_promedio'])} en portafolio para entregarte un
            resumen ejecutivo, insights clave y recomendación de inversión.
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

