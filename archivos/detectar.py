from selenium.webdriver.common.by import By

# ════════════════════════════════════════════════════════════════════════
# ZONA DE SELECTORES — SI WHATSAPP WEB CAMBIA SU HTML, EMPIEZA AQUI
# ════════════════════════════════════════════════════════════════════════
# (confirmado 22/jun/2026 inspeccionando mensaje con archivo .docx)

# Contenedor clickeable del documento (PDF, DOCX, DOC)
# Tiene el titulo con el nombre del archivo y el boton de descarga adentro
SEL_DOCUMENT_THUMB = "[data-testid='document-thumb']"

# Etiqueta con el tipo de archivo (muestra "PDF", "DOCX", "DOC", etc.)
SEL_TIPO_ARCHIVO = "[data-testid='type']"

# Boton de descarga — WhatsApp usa data-icon="audio-download" para documentos
# y data-testid="audio-download" como ancla estable
SEL_BOTON_DESCARGA = "[data-testid='audio-download']"

# Imagen adjunta real (foto enviada como mensaje, no miniatura de perfil)
SEL_IMAGEN_ADJUNTA = "[data-testid='media-url-provider'], [data-testid='image-thumb']"

# Video adjunto
SEL_VIDEO_ADJUNTO = "[data-testid='video-thumb']"
# ════════════════════════════════════════════════════════════════════════


def es_archivo(mensaje):
    """
    Detecta si un mensaje de WhatsApp contiene un archivo adjunto.
    Retorna True si encuentra documento, imagen o video.
    """
    try:
        # ── DOCUMENTOS (PDF, DOCX, DOC) ───────────────────────────────
        # Plan A: data-testid='document-thumb' — ancla mas estable
        if mensaje.find_elements(By.CSS_SELECTOR, SEL_DOCUMENT_THUMB):
            return True

        # Plan B: data-testid='type' con texto PDF/DOCX/DOC
        tipos = mensaje.find_elements(By.CSS_SELECTOR, SEL_TIPO_ARCHIVO)
        for t in tipos:
            texto = (t.text or "").strip().upper()
            if texto in ("PDF", "DOCX", "DOC"):
                return True

        # Plan C: boton de descarga presente
        if mensaje.find_elements(By.CSS_SELECTOR, SEL_BOTON_DESCARGA):
            return True

        # ── IMAGENES REALES ───────────────────────────────────────────
        if mensaje.find_elements(By.CSS_SELECTOR, SEL_IMAGEN_ADJUNTA):
            return True

        # ── VIDEOS ────────────────────────────────────────────────────
        if mensaje.find_elements(By.CSS_SELECTOR, SEL_VIDEO_ADJUNTO):
            return True

        return False

    except Exception as e:
        print(f"[detectar] Error: {e}")
        return False