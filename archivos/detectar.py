from selenium.webdriver.common.by import By

def es_archivo(mensaje):
    try:
        # 📄 DOCUMENTOS (PDF, DOC, DOCX)
        if mensaje.find_elements(By.XPATH, ".//*[contains(text(), 'PDF')]"):
            return True
        if mensaje.find_elements(By.XPATH, ".//*[contains(text(), 'páginas')]"):
            return True
        
        # ✅ WORD y otros documentos por icono o extension
        if mensaje.find_elements(By.XPATH, ".//*[contains(text(), 'DOCX')]"):
            return True
        if mensaje.find_elements(By.XPATH, ".//*[contains(text(), 'DOC')]"):
            return True
        if mensaje.find_elements(By.XPATH, ".//*[contains(text(), 'kB')]"):
            return True  # cualquier archivo tiene tamaño en kB o MB
        if mensaje.find_elements(By.XPATH, ".//*[contains(text(), 'MB')]"):
            return True

        # 🖼 IMÁGENES
        if mensaje.find_elements(By.TAG_NAME, "img"):
            return True
        # 🎥 VIDEOS
        if mensaje.find_elements(By.TAG_NAME, "video"):
            return True
        # 📎 BOTÓN DE DESCARGA
        if mensaje.find_elements(By.XPATH, ".//span[contains(@data-icon,'download')]"):
            return True

        return False
    except Exception as e:
        print("Error en detección:", e)
        return False