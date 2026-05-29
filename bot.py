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

def iniciar_bot():

    DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
    CARPETA_SESION = os.path.join(DIRECTORIO_ACTUAL, "SesionBot")

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
            WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "pane-side")))
            limpiar_archivos_viejos()
            break
        except (InvalidSessionIdException, WebDriverException):
            print("\n[!] El navegador se cerró antes de cargar WhatsApp.")
            return
        except:
            time.sleep(2)

    ultimo_msg_id = ""

    while True:
        try:
            chats_sin_leer = driver.find_elements(
                By.XPATH, "//div[@id='pane-side']//span[@data-testid='icon-unread-count']/.."
            )
            if chats_sin_leer:
                chats_sin_leer[0].click()
                time.sleep(1)

            mensajes = driver.find_elements(By.CSS_SELECTOR, "div.message-in, div.message-out")
            if mensajes:
                ultimo = mensajes[-1]
                texto = ""

                try:
                    span = ultimo.find_element(By.CSS_SELECTOR, "span[data-testid='selectable-text']")
                    texto = span.text.strip()
                except:
                    pass

                if not texto:
                    texto = ultimo.text.strip()

                es_mensaje_entrante = "message-in" in ultimo.get_attribute("class")

                try:
                    msg_id = ultimo.find_element(By.CSS_SELECTOR, "[data-id]").get_attribute("data-id")
                except:
                    msg_id = None

                if not msg_id:
                    msg_id = f"{len(mensajes)}_{texto}"

                # DEBUG
                print(f"[DEBUG] es_archivo: {es_archivo(ultimo)}")

                if msg_id != ultimo_msg_id and es_mensaje_entrante:
                    ultimo_msg_id = msg_id
                    usuario = "cliente"

                    if usuario not in estado_usuario:
                        estado_usuario[usuario] = {
                            "estado": "INICIO",
                            "tipo_archivo": None,
                            "color": None,
                            "paginas": None,
                            "archivo": None,
                            "pedido_estado": None,
                            "formato_imagen": None
                        }

                    # ✅ señal en minúsculas para que coincida con el .lower() de menu.py
                    if es_archivo(ultimo):
                        respuesta = procesar_mensaje("__archivo__", usuario, elemento=ultimo)
                    else:
                        respuesta = procesar_mensaje(texto, usuario)

                    if respuesta:
                        caja = driver.find_element(By.XPATH, "//footer//div[@role='textbox']")
                        caja.send_keys(respuesta)
                        caja.send_keys(Keys.ENTER)
                        time.sleep(1)

            time.sleep(2)

        except (InvalidSessionIdException, WebDriverException):
            print("\n" + "="*40)
            print("AVISO: El navegador fue cerrado o se perdió la conexión.")
            print("Deteniendo el bot de forma segura...")
            print("="*40)
            break
        except Exception as e:
            print(f"Error inesperado en el bucle: {e}")
            time.sleep(5)