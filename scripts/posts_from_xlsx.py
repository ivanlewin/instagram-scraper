import pandas as pd
import openpyxl

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

# Abrir archivo en pandas, y seleccionar los posteos de instagram de cada usuario
posteos = pd.read_excel(archivo, skiprows=10)
posteos = posteos.loc[posteos['Network'] == "INSTAGRAM"]
posteos = posteos.drop("Network", axis=1)
posteos = posteos[["Page", "Link"]]

# Reemplazar nombres de las páginas por sus usuarios de ig
# posteos["Page"] = ["googlemaps" if "Google Maps" in p else p for p in posteos["Page"]]


# Archivos txt
for p in posteos["Page"]:
    links = posteos.loc[posteos["Page"] == p]["Link"].tolist()
    file = f"./posts/{p}.txt"
    with open(file, "w+") as f:
        for link in links:
            f.write(f"{link}\n")