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

usuario_local=os.getenv("LOCAL_USER")
contrasenia_local=os.getenv("LOCAL_PW")
serv_local=os.getenv("LOCAL_HOST")
puerto_local=os.getenv("LOCAL_PORT")
db_local=os.getenv("LOCAL_DB")

def crear_conexion(bdd_local=True):
    
    if bdd_local == False:
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
    
    else:
        try:
            conn = psycopg2.connect(
                
            user=usuario_local,
            password=contrasenia_local,
            host=serv_local,
            port=puerto_local,
            dbname=db_local

        )
            print("Conexión creada con éxito")


        except OperationalError as e:
            conn = None
            print("la contraseña es errónea")

        return conn 

