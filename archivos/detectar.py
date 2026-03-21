from selenium.webdriver.common.by import By

def es_archivo(mensaje):
    try:
        # 📄 DOCUMENTOS (PDF, DOC, etc)
        # Detecta si hay texto tipo "PDF" o "páginas"
        if mensaje.find_elements(By.XPATH, ".//*[contains(text(), 'PDF')]"):
            return True

        if mensaje.find_elements(By.XPATH, ".//*[contains(text(), 'páginas')]"):
            return True

        # 🖼 IMÁGENES
        if mensaje.find_elements(By.TAG_NAME, "img"):
            return True

        # 🎥 VIDEOS
        if mensaje.find_elements(By.TAG_NAME, "video"):
            return True

        # 📎 BOTÓN DE DESCARGA (genérico)
        if mensaje.find_elements(By.XPATH, ".//span[contains(@data-icon,'download')]"):
            return True

        return False

    except Exception as e:
        print("Error en detección:", e)
        return False