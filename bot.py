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
#   2. Compara el HTML contra cada constante de abajo y actualiza la que
#      ya no coincida. No deberias necesitar tocar el resto del archivo.

# Contenedor de cada mensaje individual dentro del chat
# (confirmado 19/jun/2026)
SELECTOR_MENSAJE = "div[data-testid='msg-container']"

# Texto visible del mensaje
# (confirmado 19/jun/2026)
SELECTOR_TEXTO = "span[data-testid='selectable-text']"

# Colita del globo — solo aparece en el primer mensaje de una racha.
# Plan B para detectar entrante/saliente (Plan A es aria-label).
# (confirmado 19/jun/2026)
SELECTOR_TAIL_IN  = "span[data-testid='tail-in']"
SELECTOR_TAIL_OUT = "span[data-testid='tail-out']"

# Plan A para entrante/saliente: aria-label del remitente.
# En español dice "Tú:" para mensajes propios, "Nombre:" para ajenos.
# Si cambias el idioma de WhatsApp agrega la palabra en PALABRAS_YO.
# (confirmado 19/jun/2026)
SELECTOR_ARIA_REMITENTE = "span[aria-label]"
PALABRAS_YO = ["tú", "tu", "you"]

# ID unico de cada mensaje: fecha + hora + remitente en data-pre-plain-text
# Ejemplo: "[12:51 p.m., 19/6/2026] Manuel Alejandro: "
# (confirmado 19/jun/2026)
SELECTOR_ID_MENSAJE = "div.copyable-text[data-pre-plain-text]"

# Fila clickeable de cada chat en la barra lateral izquierda.
# (confirmado 19/jun/2026: WhatsApp ya no usa role='listitem' aqui)
SELECTOR_LISTA_CHATS = (
    "//div[@id='pane-side']"
    "//div[@data-testid='cell-frame-container']"
    "/ancestor::div[@tabindex][1]"
)

# Badge de mensajes no leidos en la lista de chats
# (confirmado 19/jun/2026)
SELECTOR_NO_LEIDOS = (
    "//div[@id='pane-side']"
    "//div[@data-testid='cell-frame-container']"
    "/ancestor::div[@tabindex][1]"
    "[.//*[@data-testid='icon-unread-count' or @aria-label[contains(.,'no leído') or contains(.,'unread')]]]"
)

# Caja de texto donde el bot escribe su respuesta
SELECTOR_CAJA_TEXTO = "//footer//div[@role='textbox']"

# ════════════════════════════════════════════════════════════════════════
# Vueltas seguidas sin detectar ningun mensaje antes de soltar alerta
LIMITE_ALERTA_SILENCIO = 30  # con sleep de 2s ≈ 1 minuto
# ════════════════════════════════════════════════════════════════════════


def _obtener_id(elemento, indice):
    # Siempre incluimos el indice de posicion en el ID para que dos
    # mensajes del mismo remitente dentro del mismo minuto no colisionen.
    # Sin el indice, "hola" y "1" mandados en el mismo minuto generaban
    # el mismo data-pre-plain-text y el bot descartaba el segundo.
    try:
        copyable = elemento.find_element(By.CSS_SELECTOR, SELECTOR_ID_MENSAJE)
        pre = copyable.get_attribute("data-pre-plain-text")
        if pre:
            return f"{indice}_{pre.strip()}"
    except:
        pass
    try:
        mid = elemento.get_attribute("data-id")
        if mid:
            return f"{indice}_{mid}"
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
    """True=entrante, False=saliente, None=no se pudo determinar."""
    # Plan A: aria-label con nombre del remitente o "Tú"
    try:
        span  = elemento.find_element(By.CSS_SELECTOR, SELECTOR_ARIA_REMITENTE)
        label = (span.get_attribute("aria-label") or "").strip().lower()
        if label:
            es_yo = any(label.startswith(p) for p in PALABRAS_YO)
            return not es_yo
    except:
        pass
    # Plan B: colita del globo
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
        print(f"[bot] Posible causa: cambio SELECTOR_CAJA_TEXTO en bot.py")
        return False


def _driver_vivo(driver):
    try:
        _ = driver.current_url
        return True
    except:
        return False


def _cerrar_popups(driver):
    """Cierra SOLO popups reales de Chrome — nunca toca el DOM de WhatsApp."""
    try:
        dialogos = driver.find_elements(
            By.XPATH, "//div[@role='alertdialog' or @role='dialog']"
        )
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


def _abrir_chat_con_no_leidos(driver):
    """Abre el primer chat que tenga mensajes sin leer.
    Devuelve True si encontro y abrio uno, False si no habia ninguno.
    Solo llama a esto cuando no hay un chat activo ya procesando."""
    try:
        chats = driver.find_elements(By.XPATH, SELECTOR_NO_LEIDOS)
        if chats:
            chats[0].click()
            time.sleep(1)
            return True
        return False
    except Exception as e:
        nombre = type(e).__name__
        if nombre not in ("StaleElementReferenceException",):
            print(f"[bot] Error al buscar chats no leidos: {nombre}")
        return False


def _abrir_primer_chat(driver):
    """Abre el primer chat de la lista (el mas reciente).
    Solo se usa al arrancar el bot por primera vez."""
    try:
        primer_chat = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, SELECTOR_LISTA_CHATS))
        )
        primer_chat.click()
        return True
    except Exception as e:
        nombre = type(e).__name__
        if nombre not in ("TimeoutException", "StaleElementReferenceException"):
            print(f"[bot] No se pudo abrir primer chat: {nombre}")
            print(f"[bot] Posible causa: cambio SELECTOR_LISTA_CHATS en bot.py")
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

    # Abrir el primer chat al arrancar para tener algo visible
    print("[bot] WhatsApp cargado, iniciando loop...")
    _abrir_primer_chat(driver)
    time.sleep(1)

    ultimo_msg_id          = ""
    procesando_ahora       = False
    contador_vacio         = 0
    alerta_disparada       = False
    ultimo_conteo_mensajes = -1
    ultimo_msg_id_visto    = None

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

            # ── Cambiar de chat SOLO si hay mensajes no leidos ────────────
            # Mientras estamos en medio de una conversacion activa NO
            # cambiamos de chat — eso rompia el flujo del menu porque
            # el bot perdia el hilo al saltar a otro chat entre mensajes.
            if not procesando_ahora:
                _abrir_chat_con_no_leidos(driver)

            # ── Leer mensajes del chat actualmente abierto ────────────────
            mensajes = driver.find_elements(By.CSS_SELECTOR, SELECTOR_MENSAJE)

            # Solo imprimimos cuando cambia la cantidad — evita spam
            if len(mensajes) != ultimo_conteo_mensajes:
                print(f"[DEBUG] mensajes detectados: {len(mensajes)}")
                ultimo_conteo_mensajes = len(mensajes)

            if not mensajes:
                contador_vacio += 1
                if contador_vacio == LIMITE_ALERTA_SILENCIO and not alerta_disparada:
                    alerta_disparada = True
                    print("=" * 60)
                    print("[bot] ALERTA: llevo muchas vueltas sin detectar NINGUN")
                    print("[bot] mensaje. Posible cambio de HTML en WhatsApp Web.")
                    print("[bot] Revisa SELECTOR_MENSAJE y SELECTOR_LISTA_CHATS")
                    print("[bot] en la ZONA DE SELECTORES al inicio de bot.py")
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
                print("[bot] es entrante o saliente. Revisa SELECTOR_ARIA_REMITENTE")
                print("[bot] / SELECTOR_TAIL_IN / SELECTOR_TAIL_OUT en bot.py")
                print("=" * 60)
                time.sleep(2)
                continue

            # Solo imprimimos cuando el msg_id cambia — evita spam
            if msg_id != ultimo_msg_id_visto:
                print(f"[DEBUG] msg_id={msg_id} | ultimo_id={ultimo_msg_id} | entrante={es_entrante}")
                ultimo_msg_id_visto = msg_id

            if msg_id == ultimo_msg_id or not es_entrante or procesando_ahora:
                time.sleep(2)
                continue

            # ── Mensaje nuevo entrante — procesar ─────────────────────────
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
                print(f"[bot] >>> Enviando respuesta...")
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