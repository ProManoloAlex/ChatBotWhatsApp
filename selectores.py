# ════════════════════════════════════════════════════════════════════════
# SELECTORES.PY — ARCHIVO CENTRAL DE SELECTORES DE WHATSAPP WEB
# ════════════════════════════════════════════════════════════════════════
# Cuando WhatsApp actualice su HTML y algo deje de funcionar:
#   1. Abre el chat en Chrome
#   2. Clic derecho sobre el elemento roto > Inspeccionar
#   3. Busca el selector correcto en el HTML
#   4. Actualiza SOLO la constante correspondiente aqui abajo
#   5. Todos los archivos (bot.py, detectar.py, descargar.py) lo
#      recogen automaticamente sin tocar nada mas.
#
# Fecha de ultima verificacion: 22/jun/2026
# ════════════════════════════════════════════════════════════════════════


# ── MENSAJES ─────────────────────────────────────────────────────────────────

# Contenedor de cada mensaje individual dentro del chat abierto
MSG_CONTENEDOR = "div[data-testid='msg-container']"

# Texto visible del mensaje
MSG_TEXTO = "span[data-testid='selectable-text']"

# Identificador unico del mensaje: fecha+hora+remitente
# Ejemplo del atributo: "[12:51 p.m., 19/6/2026] Manuel Alejandro: "
MSG_ID = "div.copyable-text[data-pre-plain-text]"

# Remitente del mensaje para detectar si es entrante o saliente.
# En español dice "Tú:" para mensajes propios, "Nombre:" para ajenos.
# Si cambias el idioma de WhatsApp, agrega la palabra en PALABRAS_YO.
MSG_ARIA_REMITENTE = "span[aria-label]"
PALABRAS_YO = ["tú", "tu", "you"]

# Colita del globo — Plan B para entrante/saliente.
# Solo aparece en el primer mensaje de una racha del mismo remitente.
MSG_TAIL_IN  = "span[data-testid='tail-in']"
MSG_TAIL_OUT = "span[data-testid='tail-out']"


# ── LISTA DE CHATS (barra lateral izquierda) ──────────────────────────────────

# Fila clickeable de cada chat
# (WhatsApp ya no usa role='listitem' — ahora se llega por el ancestro tabindex)
CHAT_FILA = (
    "//div[@id='pane-side']"
    "//div[@data-testid='cell-frame-container']"
    "/ancestor::div[@tabindex][1]"
)

# Fila de chat que ademas tiene mensajes no leidos
CHAT_NO_LEIDOS = (
    "//div[@id='pane-side']"
    "//div[@data-testid='cell-frame-container']"
    "/ancestor::div[@tabindex][1]"
    "[.//*[@data-testid='icon-unread-count' "
    "or @aria-label[contains(.,'no leído') "
    "or contains(.,'unread')]]]"
)


# ── CAJA DE TEXTO PARA ENVIAR MENSAJES ───────────────────────────────────────

# Cuadro de texto en el footer donde el bot escribe su respuesta
ENVIO_CAJA_TEXTO = "//footer//div[@role='textbox']"


# ── ARCHIVOS ADJUNTOS ─────────────────────────────────────────────────────────

# Contenedor clickeable del documento (PDF, DOCX, DOC)
ARCHIVO_DOCUMENT_THUMB = "[data-testid='document-thumb']"

# Etiqueta con el tipo de archivo ("PDF", "DOCX", "DOC", etc.)
ARCHIVO_TIPO = "[data-testid='type']"

# Boton de descarga — WhatsApp usa audio-download para documentos tambien
ARCHIVO_BOTON_DESCARGA      = "[data-testid='audio-download']"
ARCHIVO_BOTON_DESCARGA_ICON = "span[data-icon='audio-download']"

# Nombre del archivo dentro del thumb del documento
ARCHIVO_NOMBRE = "[data-testid='document-thumb'] span[dir='auto']"

# Imagen adjunta real (foto enviada como mensaje)
ARCHIVO_IMAGEN = "[data-testid='media-url-provider'], [data-testid='image-thumb']"

# Video adjunto
ARCHIVO_VIDEO = "[data-testid='video-thumb']"