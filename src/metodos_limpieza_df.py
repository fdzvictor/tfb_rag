import pandas as pd
import numpy as np
import re
import unicodedata
import unidecode
import sys

# import soporte_sql as s_sql

def valores_precio(df,columna:str):
    try: 
        return df[columna].str.replace(".","").astype(int) 
    except ValueError: 
        return None
    
def buscar_palabra (lista, palabra:str):
    for indice, i in enumerate(lista):
        if re.search(palabra,i):
            return(indice)
        
def normalizar_columnas_caracteristicas(df_info_carro):
        
    df_info_carro = df_info_carro.reset_index(drop = True)
    df_info_carro["Fecha_inicio"] = pd.to_datetime(df_info_carro["Fecha_inicio"],errors = "coerce")
    df_info_carro["Fecha_fin"] = pd.to_datetime(df_info_carro["Fecha_fin"], errors="coerce")
    df_info_carro["Longitud"] = df_info_carro["Longitud"].apply(lambda x: [float(i.replace(",", ".")) for i in x] if isinstance(x, list) else [])
    df_info_carro["Volumen_maletero"] = df_info_carro["Volumen_maletero"].apply(lambda x: [int(i.replace(",", ".")) for i in x] if isinstance(x, list) else [])
    df_info_carro["Precio_base"] = valores_precio(df_info_carro,"Precio_base")
    df_info_carro["Precio_max"] = valores_precio(df_info_carro,"Precio_max")
    df_info_carro["Caja_cambios"] = df_info_carro["Caja_cambios"].astype(str)
    df_info_carro["Combustible"] = df_info_carro["Combustible"].astype(str)

    return df_info_carro

def expandir_columnas_caracteristicas(df_resultado):
    #Expandimos las columnas con listas en el df
    lista_longitud = df_resultado["Longitud"].apply(sorted).to_list()
    df_longitud = pd.DataFrame(lista_longitud, columns = [f"Lon_{i}" for i in range(len(lista_longitud[0]))]) 

    lista_maletero = df_resultado["Volumen_maletero"].apply(sorted).to_list()     
    df_maletero = pd.DataFrame(lista_maletero, columns = [f"Maletero_{i}" for i in range(len(lista_maletero[0]))]) 
    
    df_cambios = df_resultado["Caja_cambios"].str.strip("[]").str.split(",").apply(sorted)
    df_cambios = df_cambios.to_frame(name="Tipo_cambio")
    df_cambios.reset_index(drop=True)
    df_cambios = df_cambios.explode("Tipo_cambio")
    df_cambios = pd.crosstab(df_cambios.index,df_cambios["Tipo_cambio"])

    df_combustible = df_resultado["Combustible"].str.strip("[]").str.split(",").apply(sorted)
    df_combustible = df_combustible.to_frame(name="Tipo_combustible")
    df_combustible.reset_index(drop=True)
    df_combustible = df_combustible.explode("Tipo_combustible")
    df_combustible = pd.crosstab(df_combustible.index,df_combustible["Tipo_combustible"])


    df_tr = (df_resultado["Tipo_traccion"].str.split("/").apply(sorted))
    df_tr = df_tr.to_frame(name="Traccion")
    df_tr.reset_index(drop=True)
    df_tr = df_tr.explode("Traccion")
    df_tr = pd.crosstab(df_tr.index,df_tr["Traccion"])


    df_res = df_resultado.join(df_longitud)
    df_res = df_res.join(df_maletero)
    df_res = df_res.join(df_cambios)
    df_res = df_res.join(df_tr)
    df_res = df_res.join(df_combustible)


    df_res = df_res.drop(columns = ["Longitud","Volumen_maletero","Tipo_traccion","Caja_cambios","Combustible"])
    
    return df_res

def estandarizar_df_caracteristicas(df):
    df.rename(columns=lambda x: x.replace('"', '').replace("'", "").replace(" ",""), inplace=True)
    df = df.loc[:, ~df.columns.duplicated()]

    df = df.reindex(columns=["marca","modelo","anio","Precio_base","Precio_max","Fecha_inicio","Fecha_fin","Potencia_minima","Potencia_maxima","Lon_0","Lon_1","Maletero_0","Maletero_1","Man","Aut","Del","4x4","Tras","D","G","Híbrido/Eléctrico"])

    df.rename(columns = {"4x4":"Tracc_total","Híbrido/Eléctrico":"Electrificado","Man":"Cambio_man","Aut":"Cambio_aut","Del":"Tracc_del","Tras":"Tracc_tras","D":"Diesel","G":"Gasolina"},inplace = True)

    return df

def limpiar_texto(text):
    # Limpieza de texto
    text = text.lower()  # Convertir a mayus
    text = re.sub(r'[^\w\s]', ' ', text)  # Eliminar puntuación
    text = re.sub(r'\s+', ' ', text)  # Reemplazar múltiples espacios o saltss de línea por un espacio
    text = unicodedata.normalize('NFD', text)
    text = re.sub(r'\u0302', '', text)
    text = text.strip()  # Quitar espacios en blanco al inicio y al final
    text = text.replace(" ","_") #Reemplazar espacios por guiones bajos
    text = text.capitalize()

    return text

def limpiar_descripciones(lista_textos):
    
    text = lista_textos.lower()  # Convertir a mayus
    text = re.sub(r'[^\w\s]', ' ', text)  # Eliminar puntuación
    text = re.sub(r'\s+', ' ', text)  # Reemplazar múltiples espacios o saltss de línea por un espacio
    text = unidecode(text)
    text = re.sub(r'\u0302', '', text)
    text = text.strip()  # Quitar espacios en blanco al inicio y al final

    return text

def procesar_link(enlace):
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

def insertar_en_bd(datos):
    conn = s_sql.crear_conexion()
    cur = conn.cursor()

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

    conn.close()
    cur.close()

def limpiar_valores_diccionario(diccionario):
    resultado = {}
    for clave, valor in diccionario.items():
        # Buscar números, decimales o separados por comas/puntos
        numeros = re.findall(r'[\d.,]+', valor)
        if numeros:
            # Tomamos el primer número encontrado como valor limpio
            try:
                num_limpio = numeros[0].replace(".", "").replace(",", ".")
                resultado[clave] = num_limpio
                
            except clave.contains("Tarifa de"):
                pass

        else:
            # Si no hay números, dejamos el valor original
            resultado[clave] = valor
    return resultado
