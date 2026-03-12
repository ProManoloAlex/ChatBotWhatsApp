from selenium.webdriver.common.by import By


def es_archivo(mensaje):
    # documento (PDF, DOC, etc)
    try:
        mensaje.find_element(By.CSS_SELECTOR, "[data-icon='document']")
        return True
    except:
        pass
    # imagen
    try:
        mensaje.find_element(By.CSS_SELECTOR, "img")
        return True
    except:
        pass
    # video
    try:
        mensaje.find_element(By.CSS_SELECTOR, "video")
        return True
    except:
        pass
    # enlace de archivo
    try:
        mensaje.find_element(By.CSS_SELECTOR, "a[href*='blob']")
        return True
    except:
        pass
    return False