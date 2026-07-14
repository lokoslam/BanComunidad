import sqlite3
import pandas as pd

con = sqlite3.connect('data/raw/saldos_diarios.db')
df = pd.read_sql("SELECT * FROM saldos_diarios WHERE comunidad_id = 'Uptown'", con)
print("Filas:", len(df))
print(df.head(10))
print(df.dtypes)
print("Fechas min/max:", df['fecha'].min(), df['fecha'].max())