import pandas as pd
import openpyxl
from datetime import datetime

# Archivo de fanpage con las publicaciones del mes
archivo  = r"./excel/Junio 2020.xlsx"

# Hardcodear el valor del hipervínculo en la celda
wb = openpyxl.load_workbook(archivo)
ws = wb['Top 10 Posts']
for row in ws.iter_rows(min_row=10, min_col=12, max_col=12):
    for cell in row:
        try:
            cell.value = cell.hyperlink.target
        except AttributeError:
            pass
wb.save(archivo)

# Abrir archivo en pandas, y agarrar las cosas que importan
posteos = pd.read_excel(archivo, skiprows=10)
posteos = posteos[["Date", "Network", "Page", "Link"]]
posteos = posteos.loc[posteos['Network'] == "INSTAGRAM"]
posteos = posteos.drop("Network", axis=1)

# Nombre del banco -> usuario de ig
posteos = posteos.replace("Banco Provincia", "banco_provincia")
posteos = posteos.replace("Banco Ciudad", "banco.ciudad")
posteos = posteos.replace("Banco Nación", "banconacion")

# Transformar date en timestamp y agregar columna de id
posteos["Date"] = posteos["Date"].apply(lambda x: datetime.timestamp(x))
posteos["p_id"] = posteos["Link"].apply(lambda x: x[-12:-1])

# Renombrar y reordenar columnas
posteos = posteos.rename(columns={"Page": "p_author", "Link": "p_link", "Date": "p_date"})
posteos = posteos[["p_id", "p_author", "p_date", "p_link"]]

master_path = r"./dictionaries/posts/master.csv"
master = pd.read_csv(master_path)
concat = pd.concat([master, posteos])
concat.to_csv(master_path, index=False)