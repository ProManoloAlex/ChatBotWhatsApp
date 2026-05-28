from database import crear_pedido
from archivos.descargar import *

estado_usuario = {}

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

def procesar_mensaje(mensaje, usuario="cliente"):
    mensaje = mensaje.strip().lower()

    if usuario not in estado_usuario:
        estado_usuario[usuario] = {
            "estado": "INICIO",
            "tipo_archivo": None,
            "color": None,
            "paginas": None,
            "archivo": None,
            "pedido_estado": None
        }

    datos = estado_usuario[usuario]
    estado = datos["estado"]
    
    # ✅ AGREGA ESTO
    print(f"[DEBUG] Mensaje: '{mensaje}' | Estado actual: '{estado}'")

    saludos = ["hola", "hola!", "buenas", "buenos dias"]

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
        if mensaje in ["1", "2", "3", "4"]:
            datos["estado"] = "ESPERANDO_ARCHIVO"
            return "Formato seleccionado.\nAhora envia la imagen que deseas imprimir."
        else:
            return "Opcion invalida.\n\n" + menu_imagen()

    # -----------------------
    # ESPERANDO ARCHIVO
    # (texto normal mientras espera archivo)
    # -----------------------
    if estado == "ESPERANDO_ARCHIVO":
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

        datos["paginas"] = mensaje
        datos["pedido_estado"] = "PENDIENTE"

        # ✅ Insertar en BD con todos los datos completos
        crear_pedido(
            usuario,
            archivo["tipo"],
            nombre_archivo,
            archivo["ruta"],
            color_usado,
            mensaje
        )

        # Limpiar datos temporales
        datos["archivo"] = None
        datos["paginas"] = None
        datos["color"] = None
        datos["tipo_archivo"] = None
        datos["estado"] = "MENU"

        return (
            f"Pedido confirmado ✅\n"
            f"Archivo: {nombre_archivo}\n"
            f"Paginas: {mensaje}\n"
            f"Color: {color_usado}\n"
            f"Estado: 🟡 PENDIENTE\n\n"
            + menu_principal()
        )

    return None


# -----------------------
# LLAMADO DESDE bot.py cuando llega un archivo
# -----------------------
def registrar_archivo(usuario, nombre, ruta, tipo):
    if usuario not in estado_usuario:
        return None

    if estado_usuario[usuario]["estado"] == "ESPERANDO_ARCHIVO":
        estado_usuario[usuario]["archivo"] = {
            "nombre": nombre,
            "ruta": ruta,
            "tipo": tipo
        }
        estado_usuario[usuario]["estado"] = "ESPERANDO_PAGINAS"
        print(f"Archivo guardado: {nombre}")
        return "Archivo recibido correctamente.\nEscribe las paginas que deseas imprimir.\nEjemplo: 1-5 o 2,4,6 o todo"
    else:
        print("Archivo ignorado (no estaba en flujo)")
        return None