import sqlite3
con = sqlite3.connect('data/raw/saldos_diarios.db')
rows = con.execute("SELECT DISTINCT comunidad_id FROM saldos_diarios WHERE comunidad_id LIKE '%ptown%'").fetchall()
print(rows)
