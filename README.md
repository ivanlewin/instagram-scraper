### instagram_scraper

Cómo agregar los posteos desde el xlsx:
1. Bajar una base de fanpage y ponerla en la carpeta "excel"
2. Abrir [posts_from_xlsx.py](./scripts/posts_from_xlsx.py) y modificar

    1. *'archivo'*.
    2. *'skip_row'* y *'columna'*.
    3. Hacer los reemplazos de los nombres de las páginas por los usuarios de ig (line 30)

3. Correr posts_from_xlsx.py
4. Modificar [config.txt](./scripts/config.txt)
5. Correr [scraper.py](./scripts/scraper.py)