import os
import time
import shutil
from selenium.webdriver.common.by import By
from archivos.detectar import es_archivo
from archivos.convertir import procesar_imagen, procesar_pdf, procesar_word

# --- CONFIGURACIÓN DE RUTAS DINÁMICAS ---
# Detecta la carpeta del script actual (Ciber/archivos) y sube un nivel a la raíz (Ciber)
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RAIZ_PROYECTO = os.path.dirname(DIRECTORIO_ACTUAL)

CARPETA_DESCARGAS = os.path.join(os.path.expanduser("~"), "Downloads")
CARPETA_DESTINO = os.path.join(RAIZ_PROYECTO, "archivos_recibidos")
# ----------------------------------------

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
    
    
def procesar_archivo_detectado(ultimo):
    """
    Detecta, descarga y procesa un archivo según su extensión.
    Retorna el tipo de archivo y el resultado del procesamiento.
    """
    if es_archivo(ultimo):
        # Descargar archivos      
        nombre, ruta = descargar_archivo(ultimo)
        
        if nombre:
            extension = nombre.split(".")[-1].lower()
            procesado = False
            tipo = "documento" # Valor por defecto
            
            # Detecta qué tipo de archivo y lo procesa
            if extension in ["jpg", "jpeg", "png"]:
                tipo = "imagen"
                procesado = procesar_imagen(ruta, "1", 0)  # formato default
            
            elif extension == "pdf":
                tipo = "documento"
                procesado = procesar_pdf(ruta, "TODO", 0)
            
            elif extension in ["doc", "docx"]:
                tipo = "documento"
                procesado = procesar_word(ruta, 0)
            
            else:
                # Si la extensión no es conocida
                tipo = "desconocido"
                procesado = False
                
            return tipo, procesado, nombre, ruta
            
    return None, None, None, None

