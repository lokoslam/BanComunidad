"""
app/pages/carga.py — Carga de datos desde Excel.
Sube BanComunidad_Modelo.xlsx y actualiza la BD SQLite completa.
"""
import os
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from app.styles import ACCENT, CARD, BORDER, MUTED, TEXT, _SHADOW

DB_PATH  = Path(__file__).resolve().parents[2] / "data" / "raw" / "saldos_diarios.db"
_PORTADA = os.path.join(os.path.dirname(__file__), "portada.py")

SHEET = "Saldos_Diarios"
COLS  = ["comunidad_id", "fecha", "saldo"]

with st.sidebar:
    if st.button("← Portada", key="back_portada_carga"):
        st.switch_page(_PORTADA)
    st.divider()
    st.caption("Fuente de datos")
    st.info("Excel → SQLite (replace total)", icon="📋")

# ── Encabezado ─────────────────────────────────────────────────────────────────
st.title("Carga de datos")
st.caption("Sube el Excel maestro y el dashboard se actualiza solo.")

st.markdown(
    f"""<div style="background:{CARD};border:1px solid {BORDER};border-radius:12px;
        padding:20px 24px;margin-bottom:24px;box-shadow:{_SHADOW}">
      <div style="font-size:14px;color:{TEXT};line-height:1.7">
        <b>¿Cómo funciona?</b><br>
        1. El archivo debe ser <b>BanComunidad_Modelo.xlsx</b> con el sheet
           <code style="background:#2A2A2A;padding:1px 6px;border-radius:4px">Saldos_Diarios</code>
           en columnas A:C (comunidad · fecha · saldo).<br>
        2. Al cargar, la tabla SQLite se <b>reemplaza completamente</b> con los datos del Excel.<br>
        3. Todos los módulos del dashboard se actualizan en la misma sesión.
      </div>
    </div>""",
    unsafe_allow_html=True,
)

# ── Estado actual de la BD ────────────────────────────────────────────────────
if DB_PATH.exists():
    con = sqlite3.connect(DB_PATH)
    n_com  = con.execute("SELECT COUNT(DISTINCT comunidad_id) FROM saldos_diarios").fetchone()[0]
    n_rows = con.execute("SELECT COUNT(*) FROM saldos_diarios").fetchone()[0]
    f_min  = con.execute("SELECT MIN(fecha) FROM saldos_diarios").fetchone()[0]
    f_max  = con.execute("SELECT MAX(fecha) FROM saldos_diarios").fetchone()[0]
    con.close()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Comunidades en BD", n_com)
    c2.metric("Registros totales", f"{n_rows:,}".replace(",", "."))
    c3.metric("Desde", f_min[:7] if f_min else "—")
    c4.metric("Hasta", f_max[:7] if f_max else "—")
else:
    st.warning("No existe base de datos aún — la primera carga la creará.")

st.divider()

# ── Uploader ──────────────────────────────────────────────────────────────────
st.subheader("Subir nuevo Excel")

archivo = st.file_uploader(
    "Arrastra o selecciona BanComunidad_Modelo.xlsx",
    type=["xlsx"],
    label_visibility="collapsed",
)

if archivo:
    st.markdown(
        f'<div style="font-size:13px;color:{MUTED};margin:4px 0 12px">'
        f'📄 <b style="color:{TEXT}">{archivo.name}</b> · '
        f'{archivo.size / 1024:.1f} KB</div>',
        unsafe_allow_html=True,
    )

    # Preview antes de confirmar
    try:
        df_preview = pd.read_excel(archivo, sheet_name=SHEET, usecols="A:C", engine="openpyxl", nrows=5)
        df_preview.columns = COLS
        with st.expander("Vista previa (primeras 5 filas)"):
            st.dataframe(df_preview, hide_index=True, use_container_width=True)
        archivo.seek(0)  # reset para lectura completa
    except Exception as e:
        st.error(f"No se pudo leer el archivo: {e}")
        st.stop()

    st.warning(
        f"Esto reemplazará **toda** la tabla `saldos_diarios` en la BD. "
        f"El contenido actual ({n_com if DB_PATH.exists() else 0} comunidades) será sobrescrito.",
        icon="⚠️",
    )

    if st.button("✓  Cargar y actualizar BD", type="primary", use_container_width=False):
        try:
            with st.spinner("Leyendo Excel..."):
                df = pd.read_excel(archivo, sheet_name=SHEET, usecols="A:C", engine="openpyxl")
                df.columns = COLS
                df["fecha"] = pd.to_datetime(df["fecha"])
                df["comunidad_id"] = df["comunidad_id"].astype(str).str.strip()
                df = df.dropna(subset=["comunidad_id", "fecha", "saldo"])

            with st.spinner("Escribiendo en SQLite..."):
                DB_PATH.parent.mkdir(parents=True, exist_ok=True)
                con = sqlite3.connect(DB_PATH)
                df.to_sql("saldos_diarios", con, if_exists="replace", index=False)
                con.execute("CREATE INDEX IF NOT EXISTS idx_comunidad ON saldos_diarios(comunidad_id)")
                con.execute("CREATE INDEX IF NOT EXISTS idx_fecha ON saldos_diarios(fecha)")
                con.commit()
                con.close()

            # Limpiar caché para que todos los módulos recarguen
            st.cache_data.clear()

            n_new_com  = df["comunidad_id"].nunique()
            n_new_rows = len(df)
            f_new_min  = df["fecha"].min().strftime("%Y-%m")
            f_new_max  = df["fecha"].max().strftime("%Y-%m")

            st.success(
                f"✓ BD actualizada — **{n_new_com} comunidades**, "
                f"**{n_new_rows:,} registros** ({f_new_min} → {f_new_max})"
            )
            st.balloons()

        except Exception as e:
            st.error(f"Error durante la carga: {e}")
