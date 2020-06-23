# Cargar links de posteos en un txt por usuario al master

import pandas as pd
from datetime import datetime

usuarios = ["banco_provincia", "banconacion","banco.ciudad"]

ts = datetime.timestamp(datetime.now())

for usuario in usuarios:
    with open(f"./txt/{usuario}.txt", "r") as f:
        lista_posts = f.read().splitlines()

    for post in lista_posts:
        post_id = post[-12 - 1]

        with open(r"./dictionaries/posts/master.csv", "a+") as f:
            print(f.write(f"{post_id},{usuario},{ts},{post[-1]}\n"))