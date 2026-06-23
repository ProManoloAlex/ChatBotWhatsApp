import os
import time
import shutil
from selenium.webdriver.common.by import By

from database import crear_pedido, obtener_config, actualizar_monto

# ════════════════════════════════════════════════════════════════════════
# ZONA DE SELECTORES — SI WHATSAPP WEB CAMBIA SU HTML, EMPIEZA AQUI
# ════════════════════════════════════════════════════════════════════════
# (confirmado 22/jun/2026 inspeccionando mensaje con archivo .docx)

# Boton de descarga — data-testid es mas estable que data-icon
SEL_BOTON_DESCARGA    = "[data-testid='audio-download']"

# Fallback: buscar por data-icon si el testid cambia
SEL_BOTON_DESCARGA_ICON = "span[data-icon='audio-download']"

# Contenedor del documento — clic aqui si no hay boton de descarga visible
SEL_DOCUMENT_THUMB    = "[data-testid='document-thumb']"

# Nombre del archivo — span con dir="auto" dentro del thumb del documento
SEL_NOMBRE_ARCHIVO    = "[data-testid='document-thumb'] span[dir='auto']"

# Tipo de archivo (muestra "PDF", "DOCX", etc.)
SEL_TIPO_ARCHIVO      = "[data-testid='type']"
# ════════════════════════════════════════════════════════════════════════

# ── RUTAS ────────────────────────────────────────────────────────────────────
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RAIZ_PROYECTO     = os.path.dirname(DIRECTORIO_ACTUAL)
CARPETA_DESCARGAS = os.path.join(os.path.expanduser("~"), "Downloads")
CARPETA_DESTINO   = os.path.join(RAIZ_PROYECTO, "archivos_recibidos")

if not os.path.exists(CARPETA_DESTINO):
    os.makedirs(CARPETA_DESTINO)

EXTENSIONES_IMAGEN    = {"jpg", "jpeg", "png"}
EXTENSIONES_DOCUMENTO = {"pdf", "doc", "docx"}


def _esperar_descarga(archivos_antes: set, timeout: int = 30):
    for _ in range(timeout):
        time.sleep(1)
        nuevos = set(os.listdir(CARPETA_DESCARGAS)) - archivos_antes
        for nombre in nuevos:
            if not nombre.endswith(".crdownload"):
                return nombre
    return None


def descargar_archivo(mensaje):
    try:
        # ── Plan A: boton de descarga por data-testid ─────────────────
        boton = None
        elementos = mensaje.find_elements(By.CSS_SELECTOR, SEL_BOTON_DESCARGA)
        if elementos:
            boton = elementos[0]
            print("[descargar] Boton descarga encontrado por data-testid")

        # ── Plan B: boton por data-icon ───────────────────────────────
        if not boton:
            elementos = mensaje.find_elements(By.CSS_SELECTOR, SEL_BOTON_DESCARGA_ICON)
            if elementos:
                boton = elementos[0]
                print("[descargar] Boton descarga encontrado por data-icon")

        # ── Plan C: clic directo en el thumb del documento ────────────
        if not boton:
            thumbs = mensaje.find_elements(By.CSS_SELECTOR, SEL_DOCUMENT_THUMB)
            if thumbs:
                boton = thumbs[0]
                print("[descargar] Usando document-thumb como boton de descarga")

        if not boton:
            print("[descargar] No se encontro ningun boton de descarga.")
            print("[descargar] Revisa SEL_BOTON_DESCARGA en descargar.py")
            return None, None

        archivos_antes = set(os.listdir(CARPETA_DESCARGAS))
        boton.click()
        print("[descargar] Click realizado, esperando archivo...")

        nombre = _esperar_descarga(archivos_antes)
        if not nombre:
            print("[descargar] Tiempo de espera agotado — el archivo no llego a Downloads.")
            return None, None

        ruta_origen  = os.path.join(CARPETA_DESCARGAS, nombre)
        ruta_destino = os.path.join(CARPETA_DESTINO, nombre)
        shutil.move(ruta_origen, ruta_destino)
        print(f"[descargar] Archivo guardado: {ruta_destino}")
        return nombre, ruta_destino

    except Exception as e:
        print(f"[descargar] Error: {e}")
        return None, None


def registrar_pedido(whatsapp, nombre, ruta, estado_usuario: dict):
    extension = nombre.rsplit(".", 1)[-1].lower()

    if extension in EXTENSIONES_IMAGEN:
        tipo = "imagen"
    elif extension in EXTENSIONES_DOCUMENTO:
        tipo = "documento"
    else:
        print(f"[registrar_pedido] Extension no soportada: {extension}")
        return None

    color   = estado_usuario.get("color", "blanco_negro")
    formato = estado_usuario.get("formato_imagen") or estado_usuario.get("formato", "CARTA")
    paginas = estado_usuario.get("paginas") or "TODO"
    copias  = int(estado_usuario.get("copias", 1))

    if tipo == "imagen":
        mapa = {"1-2": 2, "1-4": 4, "1-8": 8}
        imagenes_por_hoja = mapa.get(formato, 1)
        hojas_totales = copias
    else:
        imagenes_por_hoja = 1
        hojas_totales = 0

    precio_unitario = float(
        obtener_config("precio_color") if color == "color"
        else obtener_config("precio_bn") or 1
    )
    monto_pago = hojas_totales * precio_unitario if tipo == "imagen" else 0.0

    id_pedido = crear_pedido(
        whatsapp              = whatsapp,
        tipo_archivo          = tipo,
        nombre_archivo        = nombre,
        ruta_local            = ruta,
        color                 = color,
        paginas_seleccionadas = paginas,
        formato               = formato,
        copias                = copias,
        hojas_totales         = hojas_totales,
        imagenes_por_hoja     = imagenes_por_hoja,
        monto_pago            = monto_pago,
    )

    print(f"[registrar_pedido] Pedido #{id_pedido} — {tipo} | {color} | {formato} | monto: ${monto_pago}")
    return id_pedido