"""
app/Home.py — Punto de entrada. Define la navegación con st.navigation()
para controlar el orden y los labels del menú independientemente de los
nombres de archivo.

Lanzar con: streamlit run app/Home.py
"""

import sys
import os

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.styles import inject_css, sidebar_header

st.set_page_config(
    page_title="BanComunidad Intelligence",
    page_icon="🏦",
    layout="wide",
)
inject_css()

_DIR = os.path.dirname(__file__)

pg = st.navigation([
    st.Page(os.path.join(_DIR, "pages", "portada.py"),      title="Portada",               icon=":material/home:"),
    st.Page(os.path.join(_DIR, "pages", "modelo.py"),       title="Modelo",                icon=":material/grid_view:"),
    st.Page(os.path.join(_DIR, "pages", "resultados.py"),   title="Resultados",            icon=":material/bar_chart:"),
    st.Page(os.path.join(_DIR, "pages", "simulador.py"),    title="Simulador",             icon=":material/tune:"),
    st.Page(os.path.join(_DIR, "pages", "analisis.py"),     title="Análisis por comunidad",icon=":material/search:"),
    st.Page(os.path.join(_DIR, "pages", "mi_comunidad.py"), title="Mi Comunidad",          icon=":material/apartment:"),
    st.Page(os.path.join(_DIR, "pages", "inteligencia.py"), title="Inteligencia",          icon=":material/smart_toy:"),
    st.Page(os.path.join(_DIR, "pages", "carga.py"),        title="Carga de datos",        icon=":material/upload_file:"),
])

with st.sidebar:
    sidebar_header()

pg.run()

