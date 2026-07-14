"""
etl/import_base_edificios.py

Carga la metadata de edificios (Base_edificios.xlsx) a SQLite:
banco, unidades, administrador, fecha de contrato, comuna, etc.

Esta tabla se usa para:
  - Cruzar saldos por banco
  - Cruzar saldos por tamaño (n° unidades)
  - Detectar qué comunidades de la base aún no tienen cartolas cargadas
    en saldos_diarios (módulo "Cobertura de datos")

Uso:
    python etl/import_base_edificios.py /ruta/Base_edificios.xlsx
"""

from __future__ import annotations
import argparse
import sqlite3
from pathlib import Path

import pandas as pd

SHEET = "Base"
COLNAMES = [
    "id_interno", "comunidad_id", "rut", "direccion", "comuna", "pisos",
    "unidades", "colabs", "calderas", "admin", "fecha_contrato", "banco",
    "cuenta", "razon_social", "anio_edificio", "software", "ticket",
    "fondo_reserva",
]


def leer_base_edificios(xlsx_path: str) -> pd.DataFrame:
    df = pd.read_excel(xlsx_path, sheet_name=SHEET, usecols="A:R", engine="openpyxl")
    df.columns = COLNAMES
    df["comunidad_id"] = df["comunidad_id"].astype(str).str.strip()
    df = df.dropna(subset=["comunidad_id"])
    df["fecha_contrato"] = pd.to_datetime(df["fecha_contrato"], errors="coerce")
    return df.reset_index(drop=True)


def a_sqlite(df: pd.DataFrame, db_path: str) -> None:
    con = sqlite3.connect(db_path)
    df.to_sql("edificios", con, if_exists="replace", index=False)
    con.execute("CREATE INDEX IF NOT EXISTS idx_edif_comunidad ON edificios(comunidad_id)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_edif_banco ON edificios(banco)")
    con.commit()
    con.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx_path", help="Ruta a Base_edificios.xlsx")
    ap.add_argument(
        "--out",
        default=None,
        help="Ruta de salida SQLite. Default: data/raw/saldos_diarios.db (misma BD, tabla nueva)",
    )
    args = ap.parse_args()

    df = leer_base_edificios(args.xlsx_path)

    default_out = Path(__file__).resolve().parent.parent / "data" / "raw" / "saldos_diarios.db"
    out_path = args.out or str(default_out)

    a_sqlite(df, out_path)
    print(f"OK: {len(df)} edificios cargados -> tabla 'edificios' en {out_path}")
    print(f"   Bancos: {df['banco'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
