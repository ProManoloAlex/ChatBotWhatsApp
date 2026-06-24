from selenium.webdriver.common.by import By
from selectores import (
    ARCHIVO_DOCUMENT_THUMB,
    ARCHIVO_TIPO,
    ARCHIVO_BOTON_DESCARGA,
    ARCHIVO_IMAGEN,
    ARCHIVO_VIDEO,
)


def es_archivo(mensaje):
    """Detecta si un mensaje contiene un archivo adjunto (documento, imagen o video)."""
    try:
        # ── DOCUMENTOS (PDF, DOCX, DOC) ───────────────────────────────
        # Plan A: contenedor del documento
        if mensaje.find_elements(By.CSS_SELECTOR, ARCHIVO_DOCUMENT_THUMB):
            return True
        # Plan B: etiqueta de tipo
        for t in mensaje.find_elements(By.CSS_SELECTOR, ARCHIVO_TIPO):
            if (t.text or "").strip().upper() in ("PDF", "DOCX", "DOC"):
                return True
        # Plan C: boton de descarga presente
        if mensaje.find_elements(By.CSS_SELECTOR, ARCHIVO_BOTON_DESCARGA):
            return True

        # ── IMAGENES ──────────────────────────────────────────────────
        if mensaje.find_elements(By.CSS_SELECTOR, ARCHIVO_IMAGEN):
            return True

        # ── VIDEOS ────────────────────────────────────────────────────
        if mensaje.find_elements(By.CSS_SELECTOR, ARCHIVO_VIDEO):
            return True

        return False

    except Exception as e:
        print(f"[detectar] Error: {e}")
        return False