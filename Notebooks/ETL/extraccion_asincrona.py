import asyncio
import aiohttp
import pandas as pd
import re
from bs4 import BeautifulSoup
from psycopg2 import OperationalError
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

usuario=os.getenv("SUPA_USER")
contrasenia=os.getenv("SUPA_PASSWORD")
serv=os.getenv("SUPA_HOST")
puerto=os.getenv("SUPA_PORT")
db=os.getenv("SUPA_DB")

def crear_conexion():
    
    try:
        conn = psycopg2.connect(
            
        user=usuario,
        password=contrasenia,
        host=serv,
        port=puerto,
        dbname=db

    )
        print("Conexión creada con éxito")


    except OperationalError:
         conn = None
         print("la contraseña es errónea")

    return conn 


def limpiar_texto(text):
    # Limpieza de texto
    text = text.lower()  # Convertir a mayus
    text = re.sub(r'[^\w\s]', ' ', text)  # Eliminar puntuación
    text = re.sub(r'\s+', ' ', text)  # Reemplazar múltiples espacios o saltss de línea por un espacio
    text = re.sub(r'\u0302', '', text)
    text = text.strip()  # Quitar espacios en blanco al inicio y al final
    text = text.replace(" ","_") #Reemplazar espacios por guiones bajos
    text = text.capitalize()

    return text

# Crear conexión a PostgreSQL
conn = crear_conexion()
cur = conn.cursor()

BASE_URL = "https://www.km77.com/buscador/informaciones?grouped=0&order=date-desc&markets[]=current&markets[]=discontinued"

async def obtener_total_paginas():
    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL) as response:
            if response.status != 200:
                print("Error al obtener el total de páginas")
                return 0
            sopa = BeautifulSoup(await response.text(), "html.parser")
            pags_totales = sopa.find("div", class_="d-inline font-weight-normal font-size-2xl").text.strip()
            total_resultados = int(re.findall(r"\d+", pags_totales)[0])
            return (total_resultados // 20) + 1  # Cálculo de páginas

import aiohttp
import asyncio
from bs4 import BeautifulSoup
import time

BASE_URL = "https://www.km77.com/buscador/informaciones?grouped=0&order=date-desc&markets[]=current&markets[]=discontinued"

# Función para obtener los links de una página con estrategia de reintentos
async def obtener_links_pagina(session, numero_pagina, max_intentos=3, espera=50):
    url_review = f"{BASE_URL}&page={numero_pagina}"
    intentos = 0
    
    while intentos < max_intentos:
        try:
            async with session.get(url_review, timeout=10) as response:
                if response.status == 200:
                    sopa_review = BeautifulSoup(await response.text(), "html.parser")
                    titulo = sopa_review.find("div", class_="d-inline font-weight-normal font-size-2xl")
                    
                    if titulo and titulo.text == '(0 resultados)':
                        return []

                    links = {link["href"] for link in sopa_review.findAll("a", class_="font-size-sm", href=True)}
                    return links
                elif response.status == 504:
                    print(f"Error 504 en la página {numero_pagina}, reintentando ({intentos + 1}/{max_intentos})...")
                    await asyncio.sleep(espera)
                else:
                    print(f"Error en la página {numero_pagina}, código de estado: {response.status}")
                    return []
        except Exception as e:
            print(f"Excepción al obtener la página {numero_pagina}: {e}")
        
        intentos += 1
        await asyncio.sleep(espera)
    
    print(f"No se pudo obtener los links de la página {numero_pagina} tras {max_intentos} intentos.")
    return []



async def procesar_link(enlace):
    if len(enlace.split("/")) == 7:
        dic_coche = {
            "marca": enlace.split("/")[2],
            "modelo": enlace.split("/")[3],
            "anio": enlace.split("/")[4],
            "tipo_carroceria": enlace.split("/")[5],
            "link": enlace
        }
    elif len(enlace.split("/")) == 8:
        dic_coche = {
            "marca": enlace.split("/")[2],
            "modelo": f"{enlace.split('/')[3]} {enlace.split('/')[6]}",
            "anio": enlace.split("/")[4],
            "tipo_carroceria": enlace.split("/")[5],
            "link": enlace
        }
    else:
        return None

    # Limpiar texto
    for key in ["marca", "modelo", "anio", "tipo_carroceria"]:
        dic_coche[key] = limpiar_texto(dic_coche[key])

    return dic_coche

async def insertar_en_bd(datos):
    if not datos:
        return
    insert_query = """
        INSERT INTO modelos (marca, modelo, anio, tipo_carroceria, link)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (marca, modelo, anio)
        DO UPDATE SET tipo_carroceria = EXCLUDED.tipo_carroceria, link = EXCLUDED.link;
    """
    cur.executemany(insert_query, [(d["marca"], d["modelo"], d["anio"], d["tipo_carroceria"], d["link"]) for d in datos])
    conn.commit()

async def main():
    total_paginas = await obtener_total_paginas()
    print(f"Total de páginas a procesar: {total_paginas}")

    async with aiohttp.ClientSession() as session:
        tasks = [obtener_links_pagina(session, num) for num in range(1, total_paginas + 1)]
        resultados = await asyncio.gather(*tasks)

        enlaces = set(link for lista in resultados for link in lista)
        print(f"Total de enlaces obtenidos: {len(enlaces)}")

        # Procesar enlaces en paralelo
        coches_procesados = await asyncio.gather(*[procesar_link(link) for link in enlaces])
        coches_procesados = [c for c in coches_procesados if c is not None]

        # Insertar en base de datos
        await insertar_en_bd(coches_procesados)
        print("Inserción completada.")

if __name__ == "__main__":
    asyncio.run(main())

conn.close()
cur.close()
