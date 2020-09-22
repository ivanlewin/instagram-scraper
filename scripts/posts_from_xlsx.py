import pandas as pd
import openpyxl

archivo = ""
skip_row = 10
columna = 12

# Escribe el valor del hipervínculo en la celda
wb = openpyxl.load_workbook(archivo)
ws = wb['Top 10 Posts']
for row in ws.iter_rows(min_row=skip_row, min_col=columna, max_col=columna):
    for cell in row:
        try:
            cell.value = cell.hyperlink.target
        except AttributeError:
            pass
wb.save(archivo)

# Carga el archivo con pandas
posteos = pd.read_excel(archivo, skiprows=skip_row)
posteos = posteos.loc[posteos['Network'] == "INSTAGRAM"]
posteos = posteos.drop("Network", axis=1)
posteos = posteos[["Page", "Link"]]

# Reemplazar nombres de las páginas por sus usuarios de ig
posteos["Page"] = ["" if "" in p else p for p in posteos["Page"]]


# Genera los archivos txt con los posteos de cada usuario
for p in posteos["Page"]:
    links = posteos.loc[posteos["Page"] == p]["Link"].tolist()
    file = f"./posts/{p}.txt"
    with open(file, "w") as f:
        for link in links:
            f.write(f"{link}\n")
