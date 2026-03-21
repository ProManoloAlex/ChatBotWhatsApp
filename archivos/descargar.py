import os
import time
import shutil
from selenium.webdriver.common.by import By


CARPETA_DESCARGAS = "C:/Users/ProManoloAlex/Downloads"
CARPETA_DESTINO = "C:/Users/ProManoloAlex/Documents/Ciber/archivos_recibidos"

if not os.path.exists(CARPETA_DESTINO):
    os.makedirs(CARPETA_DESTINO)

def descargar_archivo(mensaje):
    try:
        print("Buscando boton de descarga...")
        botones = mensaje.find_elements(By.CSS_SELECTOR, "span[data-icon]")
        boton_descarga = None
        for b in botones:
            icono = b.get_attribute("data-icon")
            if icono and "download" in icono:
                boton_descarga = b
                break

        if not boton_descarga:
            print("No se encontro boton de descarga")
            return None, None
        archivos_antes = set(os.listdir(CARPETA_DESCARGAS))
        boton_descarga.click()

        print("Descargando archivo...")
        for _ in range(30):
            time.sleep(1)
            archivos_despues = set(os.listdir(CARPETA_DESCARGAS))
            nuevos = archivos_despues - archivos_antes
            if nuevos:
                nombre = nuevos.pop()
                if nombre.endswith(".crdownload"):
                    continue
                ruta_descarga = os.path.join(CARPETA_DESCARGAS, nombre)
                ruta_destino = os.path.join(CARPETA_DESTINO, nombre)
                shutil.move(ruta_descarga, ruta_destino)
                print("Archivo guardado en:", ruta_destino)
                return nombre, ruta_destino

        print("La descarga no se detecto")
        return None, None

    except Exception as e:
        print("Error descargando archivo:", e)
        return None, None