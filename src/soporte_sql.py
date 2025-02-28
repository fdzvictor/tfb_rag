import pandas as pd
import numpy as np
import re
import psycopg2
from psycopg2 import OperationalError
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

