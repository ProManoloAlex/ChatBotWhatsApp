from selenium.webdriver.common.by import By

def es_archivo(mensaje):
    """
    Detecta si un mensaje de WhatsApp contiene un archivo adjunto.
    Evita falsos positivos con imágenes de perfil o miniaturas del DOM.
    """
    try:
        # ── DOCUMENTOS: PDF, DOCX, DOC ────────────────────────────────
        for texto in ["PDF", "DOCX", "DOC"]:
            if mensaje.find_elements(By.XPATH, f".//*[contains(text(), '{texto}')]"):
                return True

        # ── TAMAÑO DE ARCHIVO (kB / MB) ────────────────────────────────
        # Buscamos específicamente dentro de burbujas de documento,
        # no en cualquier parte del DOM
        contenedor_doc = mensaje.find_elements(
            By.XPATH,
            ".//*[contains(@class,'document') or contains(@class,'media-caption') "
            "or contains(@class,'audio') or contains(@data-testid,'document')]"
        )
        if contenedor_doc:
            for c in contenedor_doc:
                t = c.text
                if "kB" in t or "MB" in t or "páginas" in t:
                    return True

        # ── IMÁGENES REALES (burbuja de imagen de WhatsApp) ───────────
        # WhatsApp usa data-testid="media-url-provider" para imágenes adjuntas
        if mensaje.find_elements(By.XPATH,
                ".//*[@data-testid='media-url-provider' or "
                "@data-testid='image-thumb']"):
            return True

        # ── VIDEOS ────────────────────────────────────────────────────
        if mensaje.find_elements(By.XPATH,
                ".//*[@data-testid='video-thumb' or "
                "@data-testid='media-container']//video"):
            return True

        # ── BOTÓN DE DESCARGA ─────────────────────────────────────────
        if mensaje.find_elements(By.XPATH,
                ".//span[contains(@data-icon,'download')]"):
            return True

        return False

    except Exception as e:
        print(f"[detectar] Error: {e}")
        return False