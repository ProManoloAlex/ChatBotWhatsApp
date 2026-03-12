import time
import os
from PIL import Image
import fitz
from docx2pdf import convert

from database import obtener_pedidos_pendientes, actualizar_estado


CARPETA_SALIDA = "C:/Users/ProManoloAlex/Documents/Ciber/Listos_Para_Imprimir/"

if not os.path.exists(CARPETA_SALIDA):
    os.makedirs(CARPETA_SALIDA)

# ===============================
# LIMPIEZA AUTOMATICA
# ===============================
def limpiar_archivos_viejos():
    ahora = time.time()
    limite = ahora - (24 * 3600)
    for archivo in os.listdir(CARPETA_SALIDA):
        ruta = os.path.join(CARPETA_SALIDA, archivo)
        if os.path.isfile(ruta) and os.path.getmtime(ruta) < limite:
            try:
                os.remove(ruta)
                print("Limpieza:", archivo, "eliminado")
            except:
                pass

# ===============================
# PROCESAR IMAGEN
# ===============================
def procesar_imagen(ruta, formato, id_p):
    try:
        foto = Image.open(ruta)
        hoja = Image.new("RGB", (2550, 3300), (255, 255, 255))
        if formato == "1-2":
            foto = foto.resize((2550, 1650), Image.Resampling.LANCZOS)
        elif formato == "1-4":
            foto = foto.resize((1275, 1650), Image.Resampling.LANCZOS)
        elif formato == "1-8":
            foto = foto.resize((1275, 825), Image.Resampling.LANCZOS)
        else:
            foto = foto.resize((2550, 3300), Image.Resampling.LANCZOS)
        hoja.paste(foto, (0, 0))
        ruta_final = os.path.join(CARPETA_SALIDA, f"pedido_{id_p}.jpg")

        hoja.save(ruta_final, quality=95)

        print("Imagen lista:", ruta_final)

        return True

    except Exception as e:

        print("Error procesando imagen:", e)

        return False


# ===============================
# PROCESAR PDF
# ===============================
def procesar_pdf(ruta, seleccion, id_p):
    try:
        doc = fitz.open(ruta)
        nuevo_doc = fitz.open()
        if not seleccion or str(seleccion).upper() == "TODO":
            indices = range(doc.page_count)
        else:
            indices = [int(p.strip()) - 1 for p in str(seleccion).split(",")]
        for i in indices:
            if 0 <= i < doc.page_count:
                nuevo_doc.insert_pdf(doc, from_page=i, to_page=i)
        ruta_final = os.path.join(CARPETA_SALIDA, f"pedido_{id_p}.pdf")
        nuevo_doc.save(ruta_final)
        print("PDF listo:", ruta_final)
        return True
    except Exception as e:
        print("Error procesando PDF:", e)
        return False


# ===============================
# PROCESAR WORD
# ===============================
def procesar_word(ruta, id_p):
    try:
        ruta_final = os.path.join(CARPETA_SALIDA, f"pedido_{id_p}.pdf")
        convert(ruta, ruta_final)
        print("Word convertido:", ruta_final)
        return True
    except Exception as e:
        print("Error procesando Word:", e)
        return False


# ===============================
# MONITOR DE CONVERSION
# ===============================
def monitor_conversion():
    print("Monitor de conversion iniciado")
    limpiar_archivos_viejos()
    while True:
        try:
            pedidos = obtener_pedidos_pendientes()
            for p in pedidos:
                id_p, ruta, formato, paginas, tipo = p
                print("Procesando pedido:", id_p)
                extension = ruta.lower().split(".")[-1]
                procesado = False
                if extension in ["jpg", "jpeg", "png"]:
                    procesado = procesar_imagen(ruta, formato, id_p)
                elif extension == "pdf":
                    procesado = procesar_pdf(ruta, paginas, id_p)
                elif extension in ["doc", "docx"]:
                    procesado = procesar_word(ruta, id_p)
                if procesado:
                    actualizar_estado(id_p, "PROCESANDO")
                else:
                    actualizar_estado(id_p, "ERROR")
        except Exception as e:
            print("Error general:", e)

        time.sleep(10)