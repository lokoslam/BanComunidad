"""
app/styles.py

Paleta, CSS global y helpers de presentación compartidos entre todas las páginas.
Inyectar al inicio de cada página con: inject_css()
"""

from __future__ import annotations
import streamlit as st

# ── Paleta ────────────────────────────────────────────────────────────────────
BG       = "#191919"
CARD     = "#1F1F1F"
CARD_ALT = "#232323"
BORDER   = "#2A2A2A"
BORDER2  = "#333333"
TEXT     = "#F4F4F4"
MUTED    = "#8A8A8A"
ACCENT   = "#C054BB"
ACCENT_T = "rgba(192,84,187,0.08)"   # tinte positivo muy sutil

# Colores Plotly
PLT_LINE   = "#E8E8E8"               # barra / línea principal
PLT_ACCENT = "#C054BB"               # P5, capital invertible, referencias
PLT_MUTED  = "#555555"               # barras secundarias / naïve
PLT_GRID   = "rgba(255,255,255,0.05)"# grilla muy tenue

_SHADOW = "0 1px 3px rgba(0,0,0,0.5), 0 1px 2px rgba(0,0,0,0.7)"


_CSS = f"""
<style>

/* ── App shell ──────────────────────────────────────────────────────────────── */
.stApp {{ background-color: {BG}; }}
.block-container {{ padding-top: 2rem !important; }}

/* ── Sidebar shell ──────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {{
    background-color: {CARD} !important;
    border-right: 1px solid {BORDER} !important;
}}
[data-testid="stSidebar"] > div:first-child {{
    padding-top: 1rem !important;
}}

/* ── Sidebar nav items ──────────────────────────────────────────────────────── */
[data-testid="stSidebarNavLink"] {{
    padding: 9px 14px !important;
    margin: 2px 8px !important;
    border-radius: 7px !important;
    color: {MUTED} !important;
    font-size: 13px !important;
    border-left: 3px solid transparent !important;
    transition: color 0.15s, border-color 0.15s;
}}
/* Hover: sólo el ícono se ilumina magenta — sin relleno de fondo */
[data-testid="stSidebarNavLink"]:hover {{
    background: transparent !important;
    color: {TEXT} !important;
    border-left-color: rgba(192,84,187,0.35) !important;
}}
[data-testid="stSidebarNavLink"]:hover [data-testid="stIconMaterial"] {{
    color: {ACCENT} !important;
}}
/* Ítem activo */
[data-testid="stSidebarNavLink"][aria-current="page"] {{
    background: {CARD_ALT} !important;
    border-left: 3px solid {ACCENT} !important;
    color: {TEXT} !important;
    font-weight: 600 !important;
}}
[data-testid="stSidebarNavLink"][aria-current="page"] [data-testid="stIconMaterial"] {{
    color: {ACCENT} !important;
}}

/* ── Metric cards ───────────────────────────────────────────────────────────── */
[data-testid="metric-container"] {{
    background: {CARD};
    border: 1px solid {BORDER} !important;
    border-radius: 12px !important;
    padding: 18px 22px 16px !important;
    box-shadow: {_SHADOW};
}}
[data-testid="stMetricLabel"] > div {{
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    color: {MUTED} !important;
    font-weight: 500 !important;
    margin-bottom: 6px !important;
}}
[data-testid="stMetricValue"] > div {{
    font-size: 36px !important;
    font-weight: 700 !important;
    color: {TEXT} !important;
    line-height: 1.1 !important;
    letter-spacing: -0.5px !important;
}}
[data-testid="stMetricDelta"] {{
    color: {MUTED} !important;
    font-size: 12px !important;
}}

/* ── Expander ──────────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {{
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 12px !important;
    box-shadow: {_SHADOW};
}}
[data-testid="stExpander"] summary {{
    color: {MUTED} !important;
    font-size: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}}

/* ── Divider ────────────────────────────────────────────────────────────────── */
hr {{
    border: none !important;
    border-top: 1px solid {BORDER} !important;
    opacity: 1 !important;
    margin: 1.5rem 0 !important;
}}

/* ── Captions ───────────────────────────────────────────────────────────────── */
.stCaption p, [data-testid="stCaptionContainer"] p {{
    color: {MUTED} !important;
    font-size: 12px !important;
    line-height: 1.5 !important;
}}

/* ── Info / Alert boxes ─────────────────────────────────────────────────────── */
[data-testid="stAlert"] {{
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
    border-left: 4px solid {ACCENT} !important;
    border-radius: 12px !important;
    box-shadow: {_SHADOW};
}}
[data-testid="stAlert"] p {{ color: {TEXT} !important; }}

/* ── Buttons ────────────────────────────────────────────────────────────────── */
.stButton > button {{
    background: transparent !important;
    border: 1px solid {BORDER2} !important;
    color: {TEXT} !important;
    border-radius: 7px !important;
    font-size: 13px !important;
    padding: 6px 14px !important;
    transition: border-color 0.12s, color 0.12s, background 0.12s;
}}
.stButton > button:hover {{
    border-color: {ACCENT} !important;
    color: {ACCENT} !important;
    background: rgba(192,84,187,0.06) !important;
}}
.stButton > button:active, .stButton > button:focus:not(:focus-visible) {{
    background: {ACCENT} !important;
    color: {BG} !important;
    border-color: {ACCENT} !important;
}}

/* ── Dataframe ──────────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {{
    border: 1px solid {BORDER} !important;
    border-radius: 12px !important;
    box-shadow: {_SHADOW};
    overflow: hidden;
}}

/* ── Widget labels ──────────────────────────────────────────────────────────── */
[data-testid="stWidgetLabel"] p {{
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    color: {MUTED} !important;
}}

/* ── Number input ───────────────────────────────────────────────────────────── */
[data-testid="stNumberInput"] input {{
    background: {CARD_ALT} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 7px !important;
    color: {TEXT} !important;
}}

/* ── Select ─────────────────────────────────────────────────────────────────── */
[data-testid="stSelectbox"] > div > div {{
    background: {CARD_ALT} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 7px !important;
}}

/* ── Headers ────────────────────────────────────────────────────────────────── */
h1 {{ color: {TEXT} !important; font-weight: 700 !important; letter-spacing: -0.5px; }}
h2 {{ color: {TEXT} !important; letter-spacing: -0.3px; font-size: 20px !important; }}
h3 {{ color: {TEXT} !important; letter-spacing: -0.2px; }}

/* ── Plotly chart container ─────────────────────────────────────────────────── */
[data-testid="stPlotlyChart"] {{
    border-radius: 12px !important;
    overflow: hidden;
}}

</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def sidebar_header() -> None:
    """Header del proyecto en el sidebar — llamar dentro de `with st.sidebar:`."""
    st.markdown(
        f"""
        <div style="padding:18px 16px 10px">
          <div style="display:flex;align-items:center;gap:9px">
            <div style="width:3px;height:22px;background:{ACCENT};
                        border-radius:2px;flex-shrink:0"></div>
            <div style="font-size:16px;font-weight:800;color:{TEXT};
                        letter-spacing:-0.4px;line-height:1.1">BanComunidad</div>
          </div>
          <div style="font-size:8.5px;color:{ACCENT};letter-spacing:3px;
                      text-transform:uppercase;font-weight:700;
                      margin-top:3px;margin-left:12px">INTELLIGENCE</div>
        </div>
        <div style="height:1px;background:{BORDER};margin:0 16px 12px"></div>
        """,
        unsafe_allow_html=True,
    )


def plotly_layout(**kwargs) -> dict:
    """Base layout para todos los gráficos Plotly."""
    base = dict(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, family="sans-serif", size=12),
        xaxis=dict(
            gridcolor=PLT_GRID,
            linecolor="rgba(0,0,0,0)",
            tickcolor="rgba(0,0,0,0)",
            tickfont=dict(color=MUTED, size=11),
            title_font=dict(color=MUTED, size=11),
        ),
        yaxis=dict(
            gridcolor=PLT_GRID,
            linecolor="rgba(0,0,0,0)",
            tickcolor="rgba(0,0,0,0)",
            tickfont=dict(color=MUTED, size=11),
            title_font=dict(color=MUTED, size=11),
            showgrid=True,
        ),
        margin=dict(t=40, b=20, l=10, r=10),
        legend=dict(
            font=dict(color=MUTED, size=11),
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
        ),
    )
    base.update(kwargs)
    return base


def bar_marker(color: str, opacity: float = 1.0) -> dict:
    """Marker dict para barras Plotly con corner radius si está soportado."""
    m: dict = dict(color=color, opacity=opacity)
    try:
        import plotly
        major, minor = (int(x) for x in plotly.__version__.split(".")[:2])
        if (major, minor) >= (5, 12):
            m["cornerradius"] = 6
    except Exception:
        pass
    return m


def banner(
    title: str,
    subtitle: str,
    positive: bool,
    extra_lines: list[str] | None = None,
) -> None:
    """
    Banner de estado. Positivo: tinte ACCENT sutil + borde magenta.
    Negativo: fondo neutro + borde magenta. Diferencia vía ✓/✕ y signo.
    """
    symbol = "✓" if positive else "✕"
    bg_color = ACCENT_T if positive else "rgba(0,0,0,0)"
    extra_html = ""
    if extra_lines:
        items = "".join(f"&nbsp;• {l}<br>" for l in extra_lines)
        extra_html = (
            f'<div style="font-size:12px;color:{MUTED};margin-top:12px;'
            f'line-height:1.9;border-top:1px solid {BORDER};padding-top:10px">'
            f"Para equilibrarse con estos parámetros, una de:<br>{items}</div>"
        )
    st.markdown(
        f"""
        <div style="background:linear-gradient({bg_color},{bg_color}),{CARD};
                    border:1px solid {BORDER};border-left:5px solid {ACCENT};
                    padding:22px 28px;border-radius:12px;margin-bottom:8px;
                    box-shadow:{_SHADOW}">
          <div style="font-size:10px;color:{MUTED};letter-spacing:0.6px;
                      text-transform:uppercase;margin-bottom:8px">Estado del escenario</div>
          <div style="font-size:28px;font-weight:700;color:{TEXT};letter-spacing:-0.3px">
            {symbol}&nbsp;{title}
          </div>
          <div style="font-size:13px;color:{MUTED};margin-top:6px">{subtitle}</div>
          {extra_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def ebitda_box(value: float, value_anual: float, positive: bool, fmt_fn) -> None:
    """Box EBITDA — acento violeta si positivo, blanco si negativo."""
    signo = "+" if positive else ""
    color = ACCENT if positive else TEXT
    st.markdown(
        f"""
        <div style="padding:4px 0">
          <div style="font-size:10px;color:{MUTED};text-transform:uppercase;
                      letter-spacing:0.5px;margin-bottom:8px">EBITDA neto / mes</div>
          <div style="font-size:34px;font-weight:700;color:{color};letter-spacing:-0.5px">
            {signo}{fmt_fn(value)}
          </div>
          <div style="font-size:12px;color:{MUTED};margin-top:6px">
            Anual: {signo}{fmt_fn(value_anual)}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

