import time
import os
from PIL import Image
import fitz
from docx2pdf import convert

from database import obtener_pedidos_pendientes, actualizar_estado, actualizar_monto, obtener_config

# ── RUTAS ────────────────────────────────────────────────────────────────────
# convertir.py está en Ciber/archivos/, subimos un nivel para llegar a Ciber/
DIRECTORIO_ACTUAL   = os.path.dirname(os.path.abspath(__file__))
RAIZ_PROYECTO       = os.path.dirname(DIRECTORIO_ACTUAL)          # Ciber/
CARPETA_SALIDA      = os.path.join(RAIZ_PROYECTO, "Listos_Para_Imprimir")

if not os.path.exists(CARPETA_SALIDA):
    os.makedirs(CARPETA_SALIDA)

# ─────────────────────────────────────────────────────────────────────────────
def limpiar_archivos_viejos():
    ahora  = time.time()
    limite = ahora - (24 * 3600)
    for archivo in os.listdir(CARPETA_SALIDA):
        ruta = os.path.join(CARPETA_SALIDA, archivo)
        if os.path.isfile(ruta) and os.path.getmtime(ruta) < limite:
            try:
                os.remove(ruta)
                print(f"[limpieza] Eliminado: {archivo}")
            except Exception as e:
                print(f"[limpieza] No se pudo eliminar {archivo}: {e}")

# ─────────────────────────────────────────────────────────────────────────────
def procesar_imagen(ruta, formato, id_p, copias=1, color="blanco_negro"):
    try:
        foto = Image.open(ruta).convert("RGB")
        ANCHO_CARTA, ALTO_CARTA = 2550, 3300
        tamaños = {
            "1-2": (ANCHO_CARTA,      ALTO_CARTA // 2),
            "1-4": (ANCHO_CARTA // 2, ALTO_CARTA // 2),
            "1-8": (ANCHO_CARTA // 2, ALTO_CARTA // 4),
        }
        w, h = tamaños.get(formato, (ANCHO_CARTA, ALTO_CARTA))
        foto = foto.resize((w, h), Image.Resampling.LANCZOS)

        if color == "blanco_negro":
            foto = foto.convert("L").convert("RGB")

        hoja = Image.new("RGB", (ANCHO_CARTA, ALTO_CARTA), (255, 255, 255))
        hoja.paste(foto, (0, 0))

        ruta_final = os.path.join(CARPETA_SALIDA, f"pedido_{id_p}.jpg")
        hoja.save(ruta_final, quality=95)
        print(f"[convertir] Imagen lista: {ruta_final}")
        return True, 1   # siempre 1 hoja por imagen

    except Exception as e:
        print(f"[convertir] Error procesando imagen: {e}")
        return False, 0

# ─────────────────────────────────────────────────────────────────────────────
def procesar_pdf(ruta, seleccion, id_p):
    try:
        doc       = fitz.open(ruta)
        nuevo_doc = fitz.open()

        if not seleccion or str(seleccion).strip().upper() == "TODO":
            indices = list(range(doc.page_count))
        else:
            indices = []
            for parte in str(seleccion).split(","):
                parte = parte.strip()
                if "-" in parte:
                    a, b = parte.split("-")
                    indices += list(range(int(a) - 1, int(b)))
                else:
                    indices.append(int(parte) - 1)

        for i in indices:
            if 0 <= i < doc.page_count:
                nuevo_doc.insert_pdf(doc, from_page=i, to_page=i)

        hojas = len(nuevo_doc)
        ruta_final = os.path.join(CARPETA_SALIDA, f"pedido_{id_p}.pdf")
        nuevo_doc.save(ruta_final)
        print(f"[convertir] PDF listo ({hojas} págs.): {ruta_final}")
        return True, hojas

    except Exception as e:
        print(f"[convertir] Error procesando PDF: {e}")
        return False, 0

# ─────────────────────────────────────────────────────────────────────────────
def procesar_word(ruta, id_p):
    try:
        ruta_final = os.path.join(CARPETA_SALIDA, f"pedido_{id_p}.pdf")
        convert(ruta, ruta_final)

        # Contar hojas del PDF generado
        doc   = fitz.open(ruta_final)
        hojas = doc.page_count
        doc.close()

        print(f"[convertir] Word convertido ({hojas} págs.): {ruta_final}")
        return True, hojas

    except Exception as e:
        print(f"[convertir] Error procesando Word: {e}")
        return False, 0

# ─────────────────────────────────────────────────────────────────────────────
def monitor_conversion():
    print("[monitor] Iniciado.")
    limpiar_archivos_viejos()

    while True:
        try:
            pedidos = obtener_pedidos_pendientes()
            for pedido in pedidos:
                id_p, ruta, formato, paginas, tipo, color, copias, hojas_bd, img_x_hoja = pedido
                print(f"[monitor] Procesando pedido #{id_p} — {tipo}")

                extension = ruta.lower().rsplit(".", 1)[-1]
                procesado  = False
                hojas_real = 0

                if extension in ("jpg", "jpeg", "png"):
                    procesado, hojas_real = procesar_imagen(ruta, formato, id_p, copias, color)

                elif extension == "pdf":
                    procesado, hojas_real = procesar_pdf(ruta, paginas, id_p)

                elif extension in ("doc", "docx"):
                    procesado, hojas_real = procesar_word(ruta, id_p)

                if procesado and hojas_real > 0:
                    # Calcular monto real ahora que conocemos las hojas
                    precio = float(
                        obtener_config("precio_color") if color == "color"
                        else obtener_config("precio_bn") or 1
                    )
                    monto = hojas_real * copias * precio
                    actualizar_monto(id_p, monto, hojas=hojas_real)  # ← guarda monto y hojas reales
                    actualizar_estado(id_p, "PROCESANDO")
                    print(f"[monitor] Pedido #{id_p} → {hojas_real} hojas × {copias} copias × ${precio} = ${monto}")
                elif not procesado:
                    actualizar_estado(id_p, "ERROR")

        except Exception as e:
            print(f"[monitor] Error general: {e}")

        time.sleep(10)