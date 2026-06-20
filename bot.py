from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, InvalidSessionIdException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from menu import procesar_mensaje, estado_usuario
from archivos.convertir import limpiar_archivos_viejos
from archivos.detectar import es_archivo
from database import obtener_ultimo_pedido
import time
import os

# ════════════════════════════════════════════════════════════════════════
# ZONA DE SELECTORES — SI WHATSAPP WEB CAMBIA SU HTML, EMPIEZA AQUI
# ════════════════════════════════════════════════════════════════════════
# Cada vez que WhatsApp actualice su pagina, lo mas probable es que SOLO
# se rompan los valores de aqui abajo. Para diagnosticar:
#   1. Abre el chat en Chrome, clic derecho sobre un mensaje > Inspeccionar
#   2. Busca el contenedor del mensaje (div con data-testid="msg-container")
#   3. Compara contra los selectores de abajo y actualiza el que ya no
#      coincida. No deberias necesitar tocar el resto del archivo.
#
# Si tienes dudas, copia el HTML del mensaje inspeccionado y compáralo
# con la version que se documenta en cada constante.

# Contenedor de cada mensaje individual dentro del chat
# (confirmado 19/jun/2026: div[data-testid='msg-container'])
SELECTOR_MENSAJE = "div[data-testid='msg-container']"

# Texto visible del mensaje, dentro del contenedor anterior
# (confirmado 19/jun/2026: span[data-testid='selectable-text'])
SELECTOR_TEXTO = "span[data-testid='selectable-text']"

# "Colita" del globo que indica si un mensaje es entrante o saliente.
# Solo aparece en el primer mensaje de una racha del mismo remitente,
# por eso es solo el PLAN B (ver _es_entrante). Valores posibles:
# 'tail-in' = entrante, 'tail-out' = saliente
SELECTOR_TAIL_IN  = "span[data-testid='tail-in']"
SELECTOR_TAIL_OUT = "span[data-testid='tail-out']"

# Plan A para detectar entrante/saliente: aria-label del remitente.
# Aparece en CADA mensaje (agrupado o no). En español dice "Tú:" para
# mensajes propios y "Nombre del contacto:" para mensajes ajenos.
# OJO: si cambias el idioma de WhatsApp esto cambia tambien (ver lista
# PALABRAS_YO abajo para agregar otros idiomas si hace falta).
SELECTOR_ARIA_REMITENTE = "span[aria-label]"
PALABRAS_YO = ["tú", "tu", "you"]  # agrega aqui si usas otro idioma

# Identificador unico de cada mensaje: fecha + hora + remitente.
# Vive en el atributo data-pre-plain-text del div.copyable-text.
# Ejemplo real: "[12:51 p.m., 19/6/2026] Manuel Alejandro: "
SELECTOR_ID_MENSAJE = "div.copyable-text[data-pre-plain-text]"

# Lista de chats, en la barra lateral izquierda.
# (confirmado 19/jun/2026: WhatsApp ya NO usa role='listitem' aqui.
# El ancla estable ahora es data-testid='cell-frame-container', que
# vive en un div hijo de la fila clickeable real. Por eso navegamos al
# ancestro 'div[@tabindex]' que es el que realmente recibe el click.)
SELECTOR_LISTA_CHATS = "//div[@id='pane-side']//div[@data-testid='cell-frame-container']/ancestor::div[@tabindex][1]"

# Caja de texto donde el bot escribe su respuesta
SELECTOR_CAJA_TEXTO = "//footer//div[@role='textbox']"

# ════════════════════════════════════════════════════════════════════════
# Cuantas vueltas seguidas del loop sin detectar NINGUN mensaje antes de
# soltar una alerta fuerte en consola (posible cambio de HTML en WhatsApp)
LIMITE_ALERTA_SILENCIO = 30   # con sleep de 2s ≈ 1 minuto
# ════════════════════════════════════════════════════════════════════════


def _obtener_id(elemento, indice):
    """Identificador unico del mensaje: fecha+hora+remitente si se puede,
    si no, cae a un indice de respaldo."""
    try:
        copyable = elemento.find_element(By.CSS_SELECTOR, SELECTOR_ID_MENSAJE)
        pre = copyable.get_attribute("data-pre-plain-text")
        if pre:
            return pre.strip()
    except:
        pass
    # Plan B viejo, por si acaso
    try:
        mid = elemento.get_attribute("data-id")
        if mid:
            return mid
    except:
        pass
    try:
        hora = elemento.find_element(
            By.CSS_SELECTOR, "span[data-testid='msg-meta'] span"
        ).text.strip()
    except:
        hora = ""
    return f"idx{indice}_{hora}"


def _es_entrante(elemento):
    """Devuelve True si el mensaje es entrante, False si es saliente,
    None si no se pudo determinar con ningun metodo (esto deberia
    disparar una alerta arriba en el loop principal)."""

    # Plan A: aria-label con el nombre del remitente o "Tú"
    try:
        span  = elemento.find_element(By.CSS_SELECTOR, SELECTOR_ARIA_REMITENTE)
        label = (span.get_attribute("aria-label") or "").strip().lower()
        if label:
            es_yo = any(label.startswith(p) for p in PALABRAS_YO)
            return not es_yo
    except:
        pass

    # Plan B: la "colita" del globo (tail-in / tail-out)
    try:
        elemento.find_element(By.CSS_SELECTOR, SELECTOR_TAIL_IN)
        return True
    except:
        pass
    try:
        elemento.find_element(By.CSS_SELECTOR, SELECTOR_TAIL_OUT)
        return False
    except:
        pass

    # Ningun metodo funciono — probablemente cambio el HTML de WhatsApp
    return None


def _enviar_respuesta(driver, respuesta):
    try:
        caja = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, SELECTOR_CAJA_TEXTO))
        )
        caja.click()
        time.sleep(0.3)
        caja.send_keys(respuesta)
        caja.send_keys(Keys.ENTER)
        time.sleep(1)
        return True
    except (InvalidSessionIdException, WebDriverException):
        raise
    except Exception as e:
        print(f"[bot] Error al enviar respuesta: {e}")
        print(f"[bot] Posible causa: cambio el selector de la caja de texto "
              f"(SELECTOR_CAJA_TEXTO en bot.py). Revisa con Inspeccionar.")
        return False


def _driver_vivo(driver):
    try:
        _ = driver.current_url
        return True
    except:
        return False


def _cerrar_popups(driver):
    """Cierra SOLO popups reales de Chrome (ej. 'Restaurar páginas').

    OJO: antes este buscaba cualquier texto 'Cancel' o 'No' en TODA la
    pagina, lo cual tambien hacia match con el aviso normal de WhatsApp
    ('Usa WhatsApp en tu telefono...') y le daba clic sin necesidad,
    interfiriendo con el chat que ya estaba abierto. Por eso ahora se
    busca el boton SOLO dentro de un dialogo nativo de Chrome
    (role='alertdialog' o similar), nunca dentro del DOM de WhatsApp.
    """
    try:
        # Buscamos unicamente dentro de un dialogo de Chrome (no de WhatsApp)
        dialogos = driver.find_elements(By.XPATH, "//div[@role='alertdialog' or @role='dialog']")
        for dialogo in dialogos:
            for texto in ["No restaurar", "Cancelar", "Cancel", "No"]:
                try:
                    boton = dialogo.find_element(
                        By.XPATH, f".//*[contains(text(),'{texto}')]"
                    )
                    boton.click()
                    time.sleep(0.8)
                    print(f"[bot] Popup de Chrome cerrado: '{texto}'")
                    return
                except:
                    pass
    except:
        pass


def _abrir_primer_chat(driver):
    """Abre el chat hasta arriba de la lista (el de actividad mas
    reciente). Reemplaza la vieja logica de 'buscar no leidos' que
    dependia de un data-testid que WhatsApp dejo de usar.

    Usa element_to_be_clickable (no solo presence_of_element_located)
    para esperar a que el elemento sea realmente clickeable, evitando
    fallos cuando el DOM se reacomoda justo despues de cerrar un popup."""
    try:
        primer_chat = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, SELECTOR_LISTA_CHATS))
        )
        primer_chat.click()
        return True
    except Exception as e:
        nombre_error = type(e).__name__
        # Un clic interceptado momentaneamente (ej. el DOM se movio justo
        # despues de cerrar un popup) NO es un selector roto - es normal
        # y se resuelve solo en la siguiente vuelta del loop. Solo avisamos
        # fuerte si de verdad no se encuentra el elemento en absoluto.
        if "Intercepted" in nombre_error or "StaleElement" in nombre_error:
            return False
        print(f"[bot] No se pudo abrir el primer chat: {nombre_error}")
        print(f"[bot] Posible causa: cambio el selector de la lista de chats "
              f"(SELECTOR_LISTA_CHATS en bot.py). Revisa con Inspeccionar.")
        return False


def iniciar_bot():
    DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
    CARPETA_SESION    = os.path.join(DIRECTORIO_ACTUAL, "SesionBot")

    if not os.path.exists(CARPETA_SESION):
        os.makedirs(CARPETA_SESION)

    chrome_options = Options()
    chrome_options.add_argument(f"user-data-dir={CARPETA_SESION}")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--disable-session-crashed-bubble")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_experimental_option("prefs", {
        "profile.exit_type": "Normal"
    })

    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://web.whatsapp.com")
    except Exception as e:
        print(f"No se pudo iniciar el navegador: {e}")
        return

    time.sleep(2)
    _cerrar_popups(driver)

    while True:
        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.ID, "pane-side"))
            )
            limpiar_archivos_viejos()
            break
        except (InvalidSessionIdException, WebDriverException):
            print("\n[!] El navegador se cerró antes de cargar WhatsApp.")
            return
        except:
            _cerrar_popups(driver)
            time.sleep(2)

    print("[bot] WhatsApp cargado, iniciando loop...")
    ultimo_msg_id    = ""
    procesando_ahora = False
    contador_vacio   = 0
    alerta_disparada = False

    while True:
        try:
            if not _driver_vivo(driver):
                print("\n[bot] Driver no responde — saliendo.")
                break

            _cerrar_popups(driver)

            # ── Revisar si hay pedido listo para avisar ───────────────────
            for usr, datos in list(estado_usuario.items()):
                if datos.get("estado") == "ESPERANDO_AVISO":
                    pedido = obtener_ultimo_pedido(usr)
                    if pedido:
                        id_p, estado_p, hojas, monto = pedido
                        if estado_p == "IMPRESO":
                            aviso = (
                                f"Tus impresiones estan listas!\n"
                                f"Pedido #{id_p} — {hojas} hojas — ${monto:.0f} pesos.\n"
                                f"Pasa a recogerlas cuando gustes.\n\n"
                                f"Escribe hola si deseas hacer otro pedido."
                            )
                            _enviar_respuesta(driver, aviso)
                            datos["estado"] = "INICIO"
                            datos["pedido_estado"] = "LISTO"
                            print(f"[bot] Aviso enviado a {usr} — pedido #{id_p}")

            # ── Abrir siempre el primer chat (mas reciente) ────────────────
            _abrir_primer_chat(driver)
            time.sleep(1)

            # ── Buscar mensajes en el chat abierto ─────────────────────────
            mensajes = driver.find_elements(By.CSS_SELECTOR, SELECTOR_MENSAJE)
            print(f"[DEBUG] mensajes detectados: {len(mensajes)}")

            if not mensajes:
                contador_vacio += 1
                if contador_vacio == LIMITE_ALERTA_SILENCIO and not alerta_disparada:
                    alerta_disparada = True
                    print("=" * 60)
                    print("[bot] ALERTA: llevo muchas vueltas sin detectar NINGUN")
                    print("[bot] mensaje, ni siquiera viejos. Es muy probable que")
                    print("[bot] WhatsApp Web haya cambiado su estructura HTML.")
                    print("[bot] Revisa la 'ZONA DE SELECTORES' al inicio de bot.py")
                    print("[bot] y compara SELECTOR_MENSAJE / SELECTOR_LISTA_CHATS")
                    print("[bot] contra el HTML actual (clic derecho > Inspeccionar")
                    print("[bot] sobre un mensaje real en el chat).")
                    print("=" * 60)
                time.sleep(2)
                continue
            else:
                contador_vacio   = 0
                alerta_disparada = False

            ultimo      = mensajes[-1]
            indice      = len(mensajes)
            msg_id      = _obtener_id(ultimo, indice)
            es_entrante = _es_entrante(ultimo)

            if es_entrante is None:
                print("=" * 60)
                print("[bot] ALERTA: no se pudo determinar si el ultimo mensaje")
                print("[bot] es entrante o saliente (fallaron los 2 metodos).")
                print("[bot] Revisa SELECTOR_ARIA_REMITENTE / SELECTOR_TAIL_IN /")
                print("[bot] SELECTOR_TAIL_OUT en la 'ZONA DE SELECTORES' de bot.py")
                print("=" * 60)
                time.sleep(2)
                continue

            print(f"[DEBUG] msg_id={msg_id} | ultimo_id={ultimo_msg_id} | entrante={es_entrante}")

            if msg_id == ultimo_msg_id or not es_entrante or procesando_ahora:
                time.sleep(2)
                continue

            # ── Mensaje nuevo entrante ────────────────────────────────────
            ultimo_msg_id    = msg_id
            procesando_ahora = True
            usuario = "cliente"

            if usuario not in estado_usuario:
                estado_usuario[usuario] = {
                    "estado": "INICIO",
                    "tipo_archivo": None,
                    "color": None,
                    "paginas": None,
                    "archivo": None,
                    "pedido_estado": None,
                    "formato_imagen": None,
                    "copias": 1,
                    "hojas_reales": 0,
                    "monto_real": 0.0,
                }

            if es_archivo(ultimo):
                print(f"[bot] Archivo detectado — estado: {estado_usuario[usuario]['estado']}")
                respuesta = procesar_mensaje("__archivo__", usuario, elemento=ultimo)
            else:
                try:
                    span  = ultimo.find_element(By.CSS_SELECTOR, SELECTOR_TEXTO)
                    texto = span.text.strip()
                except:
                    texto = ultimo.text.strip()
                print(f"[bot] Texto: '{texto}' — estado: {estado_usuario[usuario]['estado']}")
                respuesta = procesar_mensaje(texto, usuario)

            if respuesta:
                print(f"[bot] >>> Respuesta a enviar: {repr(respuesta)}")
                _enviar_respuesta(driver, respuesta)
            else:
                print(f"[bot] >>> procesar_mensaje no devolvio nada (None)")

            procesando_ahora = False
            time.sleep(2)

        except (InvalidSessionIdException, WebDriverException) as e:
            if _driver_vivo(driver):
                print(f"[bot] Excepcion recuperable: {e} — reintentando...")
                procesando_ahora = False
                time.sleep(3)
                continue
            print("\n" + "="*40)
            print("AVISO: El navegador fue cerrado o se perdio la conexion.")
            print("Deteniendo el bot de forma segura...")
            print("="*40)
            break
        except Exception as e:
            print(f"[bot] Error inesperado: {e}")
            procesando_ahora = False
            time.sleep(5)