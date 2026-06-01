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
import time
import os

def _obtener_id(elemento, indice):
    try:
        mid = elemento.get_attribute("data-id")
        if mid:
            return mid
    except:
        pass
    for selector in ["[data-id]", "[data-key]"]:
        try:
            hijo = elemento.find_element(By.CSS_SELECTOR, selector)
            mid  = hijo.get_attribute("data-id") or hijo.get_attribute("data-key")
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

def _enviar_respuesta(driver, respuesta):
    """Envía un mensaje a la caja de texto. Retorna True si tuvo éxito."""
    try:
        caja = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//footer//div[@role='textbox']"))
        )
        caja.click()
        time.sleep(0.3)
        caja.send_keys(respuesta)
        caja.send_keys(Keys.ENTER)
        time.sleep(1)
        return True
    except (InvalidSessionIdException, WebDriverException):
        raise   # dejar que suba — el navegador se cerró
    except Exception as e:
        print(f"[bot] Error al enviar respuesta: {e}")
        return False

def _driver_vivo(driver):
    """Verifica si el driver sigue activo sin lanzar excepción."""
    try:
        _ = driver.current_url
        return True
    except:
        return False

def iniciar_bot():
    DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
    CARPETA_SESION    = os.path.join(DIRECTORIO_ACTUAL, "SesionBot")

    if not os.path.exists(CARPETA_SESION):
        os.makedirs(CARPETA_SESION)

    chrome_options = Options()
    chrome_options.add_argument(f"user-data-dir={CARPETA_SESION}")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://web.whatsapp.com")
    except Exception as e:
        print(f"No se pudo iniciar el navegador: {e}")
        return

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
            time.sleep(2)

    ultimo_msg_id    = ""
    procesando_ahora = False

    while True:
        try:
            # Si el driver murió de verdad, salir limpiamente
            if not _driver_vivo(driver):
                print("\n[bot] Driver no responde — saliendo.")
                break

            chats_sin_leer = driver.find_elements(
                By.XPATH, "//div[@id='pane-side']//span[@data-testid='icon-unread-count']/.."
            )
            if chats_sin_leer:
                chats_sin_leer[0].click()
                time.sleep(1)

            mensajes = driver.find_elements(By.CSS_SELECTOR, "div.message-in, div.message-out")
            if not mensajes:
                time.sleep(2)
                continue

            ultimo      = mensajes[-1]
            indice      = len(mensajes)
            msg_id      = _obtener_id(ultimo, indice)
            es_entrante = "message-in" in (ultimo.get_attribute("class") or "")

            if msg_id == ultimo_msg_id or not es_entrante or procesando_ahora:
                time.sleep(2)
                continue

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
                }

            if es_archivo(ultimo):
                print(f"[bot] Archivo detectado — estado: {estado_usuario[usuario]['estado']}")
                respuesta = procesar_mensaje("__archivo__", usuario, elemento=ultimo)
            else:
                try:
                    span  = ultimo.find_element(By.CSS_SELECTOR, "span[data-testid='selectable-text']")
                    texto = span.text.strip()
                except:
                    texto = ultimo.text.strip()
                print(f"[bot] Texto: '{texto}' — estado: {estado_usuario[usuario]['estado']}")
                respuesta = procesar_mensaje(texto, usuario)

            if respuesta:
                _enviar_respuesta(driver, respuesta)

            procesando_ahora = False
            time.sleep(2)

        except (InvalidSessionIdException, WebDriverException) as e:
            # Verificar si el driver sigue vivo antes de rendirse
            if _driver_vivo(driver):
                print(f"[bot] Excepción recuperable: {e} — reintentando...")
                procesando_ahora = False
                time.sleep(3)
                continue
            # Driver muerto de verdad
            print("\n" + "="*40)
            print("AVISO: El navegador fue cerrado o se perdió la conexión.")
            print("Deteniendo el bot de forma segura...")
            print("="*40)
            break
        except Exception as e:
            print(f"[bot] Error inesperado: {e}")
            procesando_ahora = False
            time.sleep(5)