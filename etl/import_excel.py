"""
etl/import_excel.py

Migra el sheet Saldos_Diarios de BanComunidad_Modelo.xlsx
a un formato normalizado (CSV o SQLite) que alimenta core/.

El Excel sigue siendo la fuente de carga manual de cartolas por ahora
(Sprint 1-2). Este script es el puente hasta que el ETL de IA reemplace
la carga manual.

Uso:
    python etl/import_excel.py /ruta/BanComunidad_Modelo.xlsx --to csv
    python etl/import_excel.py /ruta/BanComunidad_Modelo.xlsx --to sqlite
"""

from __future__ import annotations
import argparse
import sqlite3
from pathlib import Path

import pandas as pd

SHEET = "Saldos_Diarios"
COLS = ["comunidad_id", "fecha", "saldo"]


def leer_saldos_diarios(xlsx_path: str) -> pd.DataFrame:
    df = pd.read_excel(xlsx_path, sheet_name=SHEET, usecols="A:C", engine="openpyxl")
    df.columns = COLS
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["comunidad_id"] = df["comunidad_id"].astype(str).str.strip()
    df = df.dropna(subset=["comunidad_id", "fecha", "saldo"])
    return df.reset_index(drop=True)


def a_csv(df: pd.DataFrame, out_path: str) -> None:
    df.to_csv(out_path, index=False)


def a_sqlite(df: pd.DataFrame, out_path: str) -> None:
    con = sqlite3.connect(out_path)
    df.to_sql("saldos_diarios", con, if_exists="replace", index=False)
    con.execute("CREATE INDEX IF NOT EXISTS idx_comunidad ON saldos_diarios(comunidad_id)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_fecha ON saldos_diarios(fecha)")
    con.commit()
    con.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx_path", help="Ruta a BanComunidad_Modelo.xlsx")
    ap.add_argument("--to", choices=["csv", "sqlite"], default="sqlite")
    ap.add_argument(
        "--out",
        default=None,
        help="Ruta de salida. Default: data/raw/saldos_diarios.<csv|db>",
    )
    args = ap.parse_args()

    df = leer_saldos_diarios(args.xlsx_path)

    out_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    default_out = out_dir / f"saldos_diarios.{'csv' if args.to == 'csv' else 'db'}"
    out_path = args.out or str(default_out)

    if args.to == "csv":
        a_csv(df, out_path)
    else:
        a_sqlite(df, out_path)

    print(f"OK: {len(df)} filas, {df['comunidad_id'].nunique()} comunidades -> {out_path}")


if __name__ == "__main__":
    main()
