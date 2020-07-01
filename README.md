### instagram_scraper

Cómo correr:
1. Agregar los posteos en [/posts](./posts) con esta estructura:

        posts/
        |       facebook.txt
        |       google.txt
        |       twitter.txt
        |

    Donde cada archivo es una lista con los posteos que se quieren scrapear de ese usuario:
    
    por ej. [facebook.txt](./posts/facebook.txt):

        https://www.instagram.com/p/CCES9c2JLy5/
        https://www.instagram.com/p/CCBt76PpgVS/
        https://www.instagram.com/p/CB-6gugpfR8/

4. Modificar [config.txt](./scripts/config.txt)
5. Correr [scraper.py](./scripts/scraper.py)