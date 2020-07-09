# instagram-scraper

Esta herramienta escrita en Python permite obtener métricas y  comentarios de uno o más posteos de Instagram.

Para obtener la del posteo, se hace una request HTTP con la librería `requests` de Python y se parsea el HTML recibido con la librería [`beautifulsoup4`](https://pypi.org/project/beautifulsoup4/).

Para obtener los comentarios es necesario emular un navegador web, y para ello se utiliza la librería [`selenium`](https://pypi.org/project/selenium/). Selenium utiliza un *webdriver* (una versión del navegador apta para ser controlada y automatizada mediante comandos) que puede ser el `chromedriver` (para utilizar Google Chrome) o el `geckodriver` (para utilizar Mozilla Firefox).  
Si el usuario ya tiene instalado uno de estos navegadores en su equipo puede optar por usar selenium con su perfil (ver [configuración de selenium](#sconfiguración-de-selenium)).

Para cargar los posteos automáticamente desde un archivo Excel de fanpage, se utilizan las librerías [`openpyxl`](https://pypi.org/project/openpyxl/) (para transformar los hipervínculos de los links en el contenido de la celda) y [`pandas`](https://pypi.org/project/pandas/), para leer el archivo y armar las listas con los posteos de cada usuario.

## Instalación
#### Instalación avanzada:
1.   
    ```bash
    git clone https://github.com/ivanlewin/instagram_scraper.git
    cd instagram_scraper
    pip install -r requirements.txt
    ```
1. [Descargar el driver](#descargar-el-driver).

#### Instalación detallada:

1. Descargar este proyecto [acá](https://github.com/ivanlewin/instagram-scraper/archive/master.zip) y extraer el archivo `.zip`.  

1. Descargar e instalar [Python](https://www.python.org/downloads/). Asegurarse de marcar la opción para 'Agregar Python al PATH'.
1. Instalar las librerías `beautifulsoup4`, `selenium`, `openpyxl` y `pandas`.
Se pueden instalar corriendo los siguientes comandos en una consola.  

    ```bash
    pip install beautifulsoup4
    ```

    ```bash
    pip install selenium
    ```

    ```bash
    pip install openpyxl
    ```

    ```bash
    pip install pandas
    ```

1. [Descargar el driver](#descargar-el-driver).

#### Descargar el driver
Descargar [`chromedriver`](https://chromedriver.chromium.org/downloads) o [`geckodriver`](https://github.com/mozilla/geckodriver/releases/tag/v0.26.0), extraer el archivo `.zip` y colocar el archivo (`chromedriver` o `geckodriver.exe`) dentro de la carpeta **scripts**.

## Agregar los posteos a scrapear:
#### Manualmente:

1. Crear un archivo txt para cada usuario cuyos posts se quieren scrapear en la carpeta **posts**. Colocar dentro de cada archivo los links de los posteos de ese usuario que se quieren scrapear (uno por línea).

    La carpeta del proyecto debería tener la siguiente estructura:

        instagram_scraper
        |
        |   .gitignore
        |   README.md
        |   requirements.txt
        |
        \---csv
        |       .gitkeep
        |
        \---excel
        |       .gitkeep
        |       archivo_ejemplo.xlsx
        |
        \---posts
        |       .gitkeep
        |
        \---scripts
                config.txt
                posts_from_xlsx.py
                scraper.py
                chromedriver (o geckodriver.exe)


    Archivo instagram.txt:  

    ![instagram.txt](https://i.imgur.com/gNpNjKC.png)


#### Desde un Excel de fanpage:

1. Bajar una base de fanpage y ponerla en la carpeta **excel**

1. Abrir el archivo [posts_from_xlsx.py](./scripts/posts_from_xlsx.py) de la carpeta **scripts** con un editor de texto (por ejemplo, Bloc de Notas) y hacer las siguientes modificaciones:
    * `archivo`: ingresar la ruta del archivo que se quiere leer (entre comillas).  
        Ejemplo:
        ```python
        archivo = "excel/archivo_ejemplo.xlsx"
        ```

    * `skip_row`: Número de filas a ignorar. Por lo general, la tabla de los posteos en los excels de fanpage comienzan en la fila 11, entonces hay que ignorar 10 filas.  
        Ejemplo:
        ```python
        skip_row = 10
        ```

    * `columna`: Número de la columna de los Links. Columna 'A' = 1, 'J' = 10.  
        Ejemplo:
        ```python
        columna = 1
        ```

    * Reemplazar nombres de las páginas por sus usuarios de ig (línea 25).  
        Ejemplo: 
        ```python
        posteos["Page"] = ["cristiano" if "Cristiano Ronaldo" in p else p for p in posteos["Page"]]
        ```
        Esto es para asignar el usuario 'cristiano' a las filas donde el nombre de la Página (columna 'Page') contenga 'Cristiano Ronaldo'.

1. Abrir una consola y navegar hasta la carpeta **instagram_scraper**. Esto se puede hacer con el comando `cd`.
1. Correr el archivo [posts_from_xlsx.py](./scripts/posts_from_xlsx.py). Esto se puede hacer con el comando `python ./scripts/posts_from_xlsx.py`.  

    Por ejemplo, si la carpeta con mi proyecto estuviera en el escritorio, la consola debería aparecer así:

        C:\Users\Ivan\Escritorio\instagram_scraper> python ./scripts/posts_from_xlsx.py


**Nota**: Si al correr el script ya existe un archivo con el nombre del usuario, los posteos del excel se agregarán al final del mismo.

## Correr el scraper


1. Modificar el archivo [config.txt](./scripts/config.txt) de la carpeta **scripts** de acuerdo a lo que se quiera scrapear. Los valores posibles son `True` o `False`.  
1. Correr el archivo [scraper.py](./scripts/scraper.py). Esto se puede hacer con el comando `python ./scripts/scraper.py`.  

    Por ejemplo, si la carpeta con mi proyecto estuviera en el escritorio, la consola debería aparecer así:

        C:\Users\Ivan\Escritorio\instagram_scraper> python ./scripts/scraper.py
  
El script leerá todos los archivos de texto en la carpeta **posts** y obtendrá la información de los posteos indicados dentro de cada archivo.

## Output
El scrapeo generará un archivo `.csv` por cada usuario, con la información de todos sus posteos.  
Todas las entradas (filas) poseen la [información del posteo](#datos-de-los-posteos). En caso haber scrapeado los comentarios, también estarán incluidas [esas columnas](#datos-de-los-comentarios).

#### Datos de los posteos 
```
Columna                 Tipo        Descripción
-------------------------------------------------
p_comments_count        (int)    -  Cantidad total de comentarios (incluye replies).
p_caption¹              (string) -  Descripción del posteo
p_ig_id                 (string) -  ID interno del posteo en Instagram
p_is_comment_enabled    (bool)   -  (True / False)
p_like_count            (int)    -  Cantidad de likes del posteo
p_media_type            (string) -  Tipo del posteo (IMAGE / CAROUSEL_ALBUM / VIDEO)
p_owner                 (string) -  ID del autor del posteo
p_shortcode³            (string) -  Código del posteo. Aparece en la URL.
p_timestamp²            (Date)   -  Fecha y/o hora de publicación del posteo
p_username              (string) -  Nombre de usuario del autor del posteo
p_views_count¹          (int)    -  Cantidad de vistas de los posteos de tipo 'VIDEO'
p_location¹             (string) -  Nombre de la ubicación del posteo
p_location_id¹          (string) -  ID de la ubicación del posteo
```

¹. Estos campos estarán vacíos si el posteo no posee esa información.  
². En algunos posteos el scraper no está pudiendo obtener esa información.  
³. Ejemplo: <code>www.instagram.com/p/**p_shortcode**</code>.


#### Datos de los comentarios
```
Columna                 Tipo        Descripción
-------------------------------------------------
c_username              (string) -  Nombre de usuario del autor del comentario
c_timestamp             (Date)   -  Fecha y hora de publicación del comentario
c_text                  (string) -  Texto del comentario
c_like_count            (int)    -  Cantidad de likes del comentario
c_id¹                   (string) -  ID del comentario (o del padre del hilo). Aparece en la URL.
c_reply_id²             (string) -  ID del comentario si es una reply. Aparece en la URL.
```
¹. Si es un comentario, será el ID. Si es una reply, será el ID del comentario padre del hilo.  
². Si es un comentario, estará vacío. Si es una reply, será el ID de la reply. Ejemplos:  
Comentario: <code>www.instagram.com/p/**p_shortcode**/c/**c_id**/</code>.  
Reply: <code>www.instagram.com/p/**p_shortcode**/c/**c_id**/r/**c_reply_id**</code>.  

<!-- #### Configuración de selenium -->

<!-- ¹²³⁴⁵⁶⁷⁸⁹⁰ -->