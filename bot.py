from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from menu import procesar_mensaje
from archivos.detectar import es_archivo
from archivos.descargar import descargar_archivo
from archivos.convertir import procesar_imagen, procesar_pdf, procesar_word, limpiar_archivos_viejos
from database import crear_pedido
import time
import os


def iniciar_bot():

    CARPETA_SESION = "C:/Users/ProManoloAlex/Documents/Ciber/SesionBot"

    if not os.path.exists(CARPETA_SESION):
        os.makedirs(CARPETA_SESION)

    chrome_options = Options()
    chrome_options.add_argument(f"user-data-dir={CARPETA_SESION}")

    driver = webdriver.Chrome(options=chrome_options)

    driver.get("https://web.whatsapp.com")

    print("Escanea el QR si es necesario...")

    # esperar a que cargue WhatsApp
    while True:
        try:
            driver.find_element(By.ID, "pane-side")
            limpiar_archivos_viejos()
            print("WhatsApp cargado correctamente")
            break
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

                print("Texto detectado:", texto)

                # verificar si es mensaje nuevo
                if texto != ultimo_mensaje:

                    ultimo_mensaje = texto

                    print("Nuevo mensaje detectado")

                    # -----------------------------
                    # DEPURACION
                    # -----------------------------
                    #print("HTML MENSAJE:")
                    #print(ultimo.get_attribute("outerHTML"))
                    #print("------------------")


                    # -----------------------------
                    # DETECTAR ARCHIVO
                    # -----------------------------
                    if es_archivo(ultimo):
                        print("ARCHIVO DETECTADO")
                                      
                        #Descargar archivos      
                        nombre, ruta = descargar_archivo(ultimo)
                        if nombre:
                            extension = nombre.split(".")[-1].lower()
                            
                          #Detecta que tipo de archivo y lo convierte en pdf-
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
                                 tipo = "documento"
                                 procesado = False
                                
                            
                            crear_pedido(
                                "cliente_whatsapp",
                                tipo,
                                nombre,
                                ruta
                            )
                            print("Pedido guardado en la base de datos")    
                        
                            if procesado:
                                print("Archivo convertido correctamente")
                            else:
                                print("Error al convertir archivo")
                    

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
                            print("Respuesta enviada")
                            time.sleep(1)

            time.sleep(2)

        except Exception as e:

            print("Error en el bucle:", e)
            time.sleep(5)