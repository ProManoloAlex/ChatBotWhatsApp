from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, InvalidSessionIdException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from menu import procesar_mensaje, estado_usuario
from archivos.convertir import limpiar_archivos_viejos
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
        
    #print("Escanea el QR si es necesario...")

    # esperar a que cargue WhatsApp
    while True:
        try:
            WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "pane-side")))
            limpiar_archivos_viejos()
            #print("WhatsApp cargado correctamente")
            break
        except (InvalidSessionIdException, WebDriverException):
            print("\n[!] El navegador se cerró antes de cargar WhatsApp.")
            return # Salimos de la función
        except:
            time.sleep(2)
            
    ultimo_mensaje = ""

    while True:
        try:
            # obtener todos los mensajes
            mensajes = driver.find_elements(By.CSS_SELECTOR, "div.message-in, div.message-out")
            if mensajes:
                ultimo = mensajes[-1]
                texto = ""

                # intentar obtener texto
                try:
                    span = ultimo.find_element(By.CSS_SELECTOR, "span[data-testid='selectable-text']")
                    texto = span.text.strip()
                except:
                    pass

                if not texto:
                    texto = ultimo.text.strip()

                #print("Texto detectado:", texto)

                # verificar si es mensaje nuevo
                if texto != ultimo_mensaje:

                    ultimo_mensaje = texto

                    #print("Nuevo mensaje detectado")

                    # -----------------------------
                    # DEPURACION
                    # -----------------------------
                    #print("HTML MENSAJE:")
                    #print(ultimo.get_attribute("outerHTML"))
                    #print("------------------")
                            
                    usuario = "cliente"

                    # inicializar si no existe
                    if usuario not in estado_usuario:
                        estado_usuario[usuario] = {
                                    "estado": "INICIO",
                                    "tipo_archivo": None,
                                    "color": None,
                                    "paginas": None,
                                    "archivo": None,
                                    "pedido_estado": None
                                }

                    # -----------------------------
                    # PROCESAR MENSAJE
                    # -----------------------------
                    if texto:
                        respuesta = procesar_mensaje(texto)
                        if respuesta:
                            caja = driver.find_element(
                                By.XPATH, "//footer//div[@role='textbox']"
                                )

                            caja.send_keys(respuesta)
                            caja.send_keys(Keys.ENTER)
                            #print("Respuesta enviada")
                            time.sleep(1)

            time.sleep(2)

        # CAPTURA DE CIERRE DE VENTANA
        except (InvalidSessionIdException, WebDriverException):
            print("\n" + "="*40)
            print("AVISO: El navegador fue cerrado o se perdió la conexión.")
            print("Deteniendo el bot de forma segura...")
            print("="*40)
            break # Rompe el bucle principal y termina el script
        except Exception as e:
                print(f"Error inesperado en el bucle: {e}")
                time.sleep(5)
                