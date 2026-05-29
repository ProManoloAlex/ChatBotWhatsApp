from database import crear_pedido
import os

estado_usuario = {}

# ===============================
# RUTAS
# ===============================
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
CARPETA_RECIBIDOS = os.path.join(DIRECTORIO_ACTUAL, "archivos_recibidos")
CARPETA_LISTOS = os.path.join(DIRECTORIO_ACTUAL, "Listos_Para_Imprimir")

for carpeta in [CARPETA_RECIBIDOS, CARPETA_LISTOS]:
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)

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
            "formato_imagen": None
        }

    datos = estado_usuario[usuario]
    estado = datos["estado"]

    print(f"[DEBUG] Mensaje: '{mensaje}' | Estado: '{estado}'")

    saludos = ["hola", "hola!", "buenas", "buenos dias"]

    # -----------------------
    # ARCHIVO FUERA DE FLUJO
    # -----------------------
    if mensaje == "__archivo__" and estado != "ESPERANDO_ARCHIVO":
        return "Para enviar un archivo primero selecciona una opcion del menu."

    # -----------------------
    # SALUDO
    # -----------------------
    if mensaje in saludos:
        datos["estado"] = "MENU"
        return menu_principal()

    # -----------------------
    # INICIO sin saludo
    # -----------------------
    if estado == "INICIO":
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
            from archivos.descargar import descargar_archivo

            print("[DEBUG] Intentando descargar archivo...")
            print("[DEBUG] HTML elemento:", elemento.get_attribute("outerHTML")[:400])

            nombre, ruta = descargar_archivo(elemento)
            print(f"[DEBUG] Resultado descarga: nombre={nombre} | ruta={ruta}")

            if not nombre or not ruta:
                return "No se pudo descargar el archivo. Intenta de nuevo."

            extension = nombre.split(".")[-1].lower()

            if extension in ["jpg", "jpeg", "png"]:
                tipo = "imagen"
            elif extension in ["pdf", "doc", "docx"]:
                tipo = "documento"
            else:
                return "Formato no compatible.\nEnvia PDF, Word o imagen JPG/PNG."

            datos["archivo"] = {
                "nombre": nombre,
                "ruta": ruta,
                "tipo": tipo
            }
            datos["estado"] = "ESPERANDO_PAGINAS"
            print(f"[DEBUG] Archivo guardado: {nombre} | Ruta: {ruta}")

            return (
                "Archivo recibido correctamente ✅\n"
                "Escribe las paginas que deseas imprimir.\n"
                "Ejemplo: 1-5 o 2,4,6 o todo"
            )

        else:
            return "Por favor envia el archivo (PDF o imagen)."

    # -----------------------
    # ESPERANDO PAGINAS
    # -----------------------
    if estado == "ESPERANDO_PAGINAS":
        archivo = datos.get("archivo")

        if not archivo:
            return "Error: primero debes enviar un archivo."

        color_usado = datos["color"]
        nombre_archivo = archivo["nombre"]

        if archivo["tipo"] == "imagen":
            formato = datos.get("formato_imagen", "CARTA")
        else:
            formato = "CARTA"

        crear_pedido(
            usuario,
            archivo["tipo"],
            nombre_archivo,
            archivo["ruta"],
            color_usado,
            mensaje,
            formato
        )

        datos["pedido_estado"] = "PENDIENTE"
        datos["archivo"] = None
        datos["paginas"] = None
        datos["color"] = None
        datos["tipo_archivo"] = None
        datos["formato_imagen"] = None
        datos["estado"] = "MENU"

        return (
            f"Pedido confirmado ✅\n"
            f"Archivo: {nombre_archivo}\n"
            f"Paginas: {mensaje}\n"
            f"Color: {color_usado}\n"
            f"Formato: {formato}\n"
            f"Estado: 🟡 PENDIENTE\n\n"
            + menu_principal()
        )

    return None