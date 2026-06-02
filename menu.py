from archivos.descargar import descargar_archivo, registrar_pedido
from archivos.convertir import procesar_pdf, procesar_word, CARPETA_SALIDA
from database import obtener_config, actualizar_estado
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
            "hojas_reales": 0,
            "monto_real": 0.0,
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
    # Tambien reactiva el menu si el usuario ya estaba esperando aviso
    # -----------------------
    if mensaje in saludos or estado in ("INICIO", "ESPERANDO_AVISO"):
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
            return "Tu pedido fue cancelado"
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

            if tipo == "imagen":
                color   = datos.get("color", "blanco_negro")
                formato = datos.get("formato_imagen", "CARTA")
                copias  = int(datos.get("copias", 1))
                precio  = float(obtener_config("precio_color") if color == "color" else obtener_config("precio_bn") or 1)
                hojas   = copias
                monto   = hojas * precio

                datos["hojas_reales"] = hojas
                datos["monto_real"]   = monto
                datos["estado"]       = "CONFIRMANDO_PEDIDO"

                return (
                    f"Imagen recibida\n"
                    f"Formato: {formato}\n"
                    f"Color: {color}\n"
                    f"Hojas: {hojas}\n"
                    f"Total: ${monto:.0f} pesos\n\n"
                    f"Confirmas la impresion?\n"
                    f"Responde si o no"
                )

            # Documento → pedir paginas
            datos["estado"] = "ESPERANDO_PAGINAS"
            return (
                "Archivo recibido\n"
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

        datos["paginas"] = mensaje
        ruta      = archivo["ruta"]
        extension = ruta.rsplit(".", 1)[-1].lower()
        color     = datos.get("color", "blanco_negro")
        copias    = int(datos.get("copias", 1))
        precio    = float(obtener_config("precio_color") if color == "color" else obtener_config("precio_bn") or 1)

        # Convertir con id temporal 0 → genera pedido_0.pdf en Listos_Para_Imprimir
        if extension == "pdf":
            procesado, hojas = procesar_pdf(ruta, mensaje, 0)
        elif extension in ("doc", "docx"):
            procesado, hojas = procesar_word(ruta, 0)
        else:
            procesado, hojas = False, 0

        if not procesado or hojas == 0:
            return "Hubo un error al procesar el archivo. Intenta de nuevo."

        hojas_total = hojas * copias
        monto       = hojas_total * precio

        datos["hojas_reales"] = hojas_total
        datos["monto_real"]   = monto
        datos["estado"]       = "CONFIRMANDO_PEDIDO"

        return (
            f"Resumen de tu pedido:\n"
            f"Archivo: {archivo['nombre']}\n"
            f"Paginas: {mensaje}\n"
            f"Hojas: {hojas_total}\n"
            f"Color: {color}\n"
            f"Precio por hoja: ${precio:.0f}\n"
            f"Total: ${monto:.0f} pesos\n\n"
            f"Confirmas la impresion?\n"
            f"Responde si o no"
        )

    # -----------------------
    # CONFIRMANDO PEDIDO
    # -----------------------
    if estado == "CONFIRMANDO_PEDIDO":
        archivo = datos.get("archivo")
        if not archivo:
            return "Error: no hay pedido pendiente."

        if mensaje in ["si", "si", "s", "yes"]:
            id_pedido = registrar_pedido(usuario, archivo["nombre"], archivo["ruta"], datos)
            if not id_pedido:
                return "Error al registrar el pedido. Intenta de nuevo."

            # Renombrar pedido_0.pdf → pedido_{id_real}.pdf
            extension  = archivo["ruta"].rsplit(".", 1)[-1].lower()
            ext_salida = "jpg" if extension in ("jpg", "jpeg", "png") else "pdf"
            ruta_temp  = os.path.join(CARPETA_SALIDA, f"pedido_0.{ext_salida}")
            ruta_final = os.path.join(CARPETA_SALIDA, f"pedido_{id_pedido}.{ext_salida}")

            if os.path.exists(ruta_temp):
                os.rename(ruta_temp, ruta_final)
                print(f"[menu] Renombrado: pedido_0.{ext_salida} -> pedido_{id_pedido}.{ext_salida}")
                actualizar_estado(id_pedido, "PROCESANDO")
            else:
                print(f"[menu] Advertencia: no se encontro {ruta_temp}")

            datos["pedido_estado"] = "PENDIENTE"
            _limpiar_datos(datos)
            datos["estado"] = "ESPERANDO_AVISO"

            return (
                "Pedido confirmado\n"
                "Te avisaremos cuando tus impresiones esten listas."
            )

        elif mensaje in ["no", "n", "cancelar"]:
            # Limpiar archivo temporal si existe
            extension  = archivo["ruta"].rsplit(".", 1)[-1].lower()
            ext_salida = "jpg" if extension in ("jpg", "jpeg", "png") else "pdf"
            ruta_temp  = os.path.join(CARPETA_SALIDA, f"pedido_0.{ext_salida}")
            if os.path.exists(ruta_temp):
                os.remove(ruta_temp)
                print(f"[menu] Archivo temporal eliminado: pedido_0.{ext_salida}")

            _limpiar_datos(datos)
            datos["estado"] = "MENU"
            return (
                "Pedido cancelado\n"
                "Puedes iniciar de nuevo cuando quieras.\n\n"
                + menu_principal()
            )

        else:
            return "Por favor responde si para confirmar o no para cancelar."

    return None

# ─────────────────────────────────────────────────────────────────────────────
def _limpiar_datos(datos):
    datos["archivo"]        = None
    datos["paginas"]        = None
    datos["color"]          = None
    datos["tipo_archivo"]   = None
    datos["formato_imagen"] = None
    datos["copias"]         = 1
    datos["hojas_reales"]   = 0
    datos["monto_real"]     = 0.0