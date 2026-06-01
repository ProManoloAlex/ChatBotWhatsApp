from archivos.descargar import descargar_archivo, registrar_pedido
import os

estado_usuario = {}

# ===============================
# MENUS
# ===============================
def menu_principal():
    return (
        "MENU DE IMPRESIONES\n"
        "1 Imprimir documento\n"
        "2 Imprimir imagen\n"
        "3 Escanear documento\n"
        "4 Ver pedido\n"
        "5 Cancelar pedido\n"
        "Escribe el numero de la opcion que deseas"
    )

def menu_documento():
    return (
        "IMPRESION DE DOCUMENTO\n"
        "Selecciona el tipo de impresion\n"
        "1 Blanco y negro ($1 por hoja)\n"
        "2 Color ($2 por hoja)"
    )

def menu_imagen():
    return (
        "IMPRESION DE IMAGEN\n"
        "1 Hoja completa\n"
        "2 Media hoja (2 imagenes por hoja)\n"
        "3 Cuarto de hoja (4 imagenes por hoja)\n"
        "4 Octavo de hoja (8 imagenes por hoja)"
    )

# ===============================
# PROCESAR MENSAJE
# ===============================
def procesar_mensaje(mensaje, usuario="cliente", elemento=None):
    mensaje = mensaje.strip().lower()

    if usuario not in estado_usuario:
        estado_usuario[usuario] = {
            "estado": "INICIO",
            "tipo_archivo": None,
            "color": None,
            "paginas": None,
            "archivo": None,
            "pedido_estado": None,
            "formato_imagen": None,
            "copias": 1,
        }

    datos  = estado_usuario[usuario]
    estado = datos["estado"]

    print(f"[DEBUG] Mensaje: '{mensaje}' | Estado: '{estado}'")

    saludos = ["hola", "hola!", "buenas", "buenos dias"]

    # -----------------------
    # ARCHIVO FUERA DE FLUJO
    # -----------------------
    if mensaje == "__archivo__" and estado != "ESPERANDO_ARCHIVO":
        return "Para enviar un archivo primero selecciona una opcion del menu."

    # -----------------------
    # SALUDO / INICIO
    # -----------------------
    if mensaje in saludos or estado == "INICIO":
        datos["estado"] = "MENU"
        return menu_principal()

    # -----------------------
    # MENU PRINCIPAL
    # -----------------------
    if estado == "MENU":
        if mensaje == "1":
            datos["tipo_archivo"] = "documento"
            datos["estado"] = "TIPO_DOCUMENTO"
            return menu_documento()
        elif mensaje == "2":
            datos["tipo_archivo"] = "imagen"
            datos["estado"] = "TIPO_IMAGEN"
            return menu_imagen()
        elif mensaje == "3":
            return "El servicio de escaneo cuesta $2 por hoja."
        elif mensaje == "4":
            if datos["pedido_estado"]:
                return f"Estado de tu pedido: {datos['pedido_estado']}"
            return "No tienes pedidos registrados."
        elif mensaje == "5":
            datos["pedido_estado"] = "CANCELADO"
            return "Tu pedido fue cancelado ❌"
        else:
            return "Opcion invalida.\n\n" + menu_principal()

    # -----------------------
    # TIPO DOCUMENTO
    # -----------------------
    if estado == "TIPO_DOCUMENTO":
        if mensaje == "1":
            datos["color"] = "blanco_negro"
            datos["estado"] = "ESPERANDO_ARCHIVO"
            return "Impresion en blanco y negro seleccionada.\nAhora envia tu archivo PDF o documento."
        elif mensaje == "2":
            datos["color"] = "color"
            datos["estado"] = "ESPERANDO_ARCHIVO"
            return "Impresion a color seleccionada.\nAhora envia tu archivo PDF o documento."
        else:
            return "Opcion invalida.\n\n" + menu_documento()

    # -----------------------
    # TIPO IMAGEN
    # -----------------------
    if estado == "TIPO_IMAGEN":
        formatos = {"1": "CARTA", "2": "1-2", "3": "1-4", "4": "1-8"}
        if mensaje in formatos:
            datos["formato_imagen"] = formatos[mensaje]
            datos["estado"] = "ESPERANDO_ARCHIVO"
            return "Formato seleccionado.\nAhora envia la imagen que deseas imprimir."
        else:
            return "Opcion invalida.\n\n" + menu_imagen()

    # -----------------------
    # ESPERANDO ARCHIVO
    # -----------------------
    if estado == "ESPERANDO_ARCHIVO":
        if mensaje == "__archivo__" and elemento is not None:
            print("[DEBUG] Intentando descargar archivo...")

            nombre, ruta = descargar_archivo(elemento)
            print(f"[DEBUG] Resultado descarga: nombre={nombre} | ruta={ruta}")

            if not nombre or not ruta:
                return "No se pudo descargar el archivo. Intenta de nuevo."

            extension = nombre.rsplit(".", 1)[-1].lower()
            if extension in ["jpg", "jpeg", "png"]:
                tipo = "imagen"
            elif extension in ["pdf", "doc", "docx"]:
                tipo = "documento"
            else:
                return "Formato no compatible.\nEnvia PDF, Word o imagen JPG/PNG."

            datos["archivo"] = {"nombre": nombre, "ruta": ruta, "tipo": tipo}

            # Imágenes no necesitan selección de páginas → registrar directo
            if tipo == "imagen":
                id_pedido = registrar_pedido(usuario, nombre, ruta, datos)
                if not id_pedido:
                    return "Error al registrar el pedido. Intenta de nuevo."
                datos["pedido_estado"] = "PENDIENTE"
                datos["estado"] = "MENU"
                _limpiar_datos(datos)
                return (
                    f"Pedido confirmado ✅\n"
                    f"Archivo: {nombre}\n"
                    f"Color: {datos.get('color','blanco_negro')}\n"
                    f"Formato: {datos.get('formato_imagen','CARTA')}\n"
                    f"Estado: 🟡 PENDIENTE\n\n"
                    + menu_principal()
                )

            # Documentos → preguntar páginas
            datos["estado"] = "ESPERANDO_PAGINAS"
            print(f"[DEBUG] Archivo guardado: {nombre} | Ruta: {ruta}")
            return (
                "Archivo recibido ✅\n"
                "Escribe las paginas que deseas imprimir.\n"
                "Ejemplo: 1-5 | 2,4,6 | todo"
            )

        else:
            return "Por favor envia el archivo (PDF, Word o imagen)."

    # -----------------------
    # ESPERANDO PAGINAS
    # -----------------------
    if estado == "ESPERANDO_PAGINAS":
        archivo = datos.get("archivo")
        if not archivo:
            return "Error: primero debes enviar un archivo."

        # Guardar páginas en estado para que registrar_pedido las tome
        datos["paginas"] = mensaje

        id_pedido = registrar_pedido(usuario, archivo["nombre"], archivo["ruta"], datos)
        if not id_pedido:
            return "Error al registrar el pedido. Intenta de nuevo."

        color  = datos.get("color", "blanco_negro")
        formato = datos.get("formato_imagen") or "CARTA"
        nombre  = archivo["nombre"]

        datos["pedido_estado"] = "PENDIENTE"
        _limpiar_datos(datos)
        datos["estado"] = "MENU"

        return (
            f"Pedido confirmado ✅\n"
            f"Archivo: {nombre}\n"
            f"Paginas: {mensaje}\n"
            f"Color: {color}\n"
            f"Formato: {formato}\n"
            f"Estado: 🟡 PENDIENTE\n\n"
            + menu_principal()
        )

    return None

# ─────────────────────────────────────────────────────────────────────────────
def _limpiar_datos(datos):
    """Resetea los datos del pedido sin tocar el estado ni pedido_estado."""
    datos["archivo"]       = None
    datos["paginas"]       = None
    datos["color"]         = None
    datos["tipo_archivo"]  = None
    datos["formato_imagen"]= None
    datos["copias"]        = 1