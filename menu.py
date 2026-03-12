estado_usuario = {}

def menu_principal():
    return """
MENU DE IMPRESIONES

1 Imprimir documento
2 Imprimir imagen
3 Escanear documento
4 Ver pedido
5 Cancelar pedido

Escribe el numero de la opcion que deseas
"""

def menu_documento():
    return """
IMPRESION DE DOCUMENTO

Selecciona el tipo de impresion

1 Blanco y negro ($1 por hoja)
2 Color ($2 por hoja)
"""

def menu_imagen():
    return """
IMPRESION DE IMAGEN

1 Hoja completa
2 Media hoja (2 imagenes por hoja)
3 Cuarto de hoja (4 imagenes por hoja)
4 Octavo de hoja (8 imagenes por hoja)
"""

def pedido_recibido():
    return """
Tu pedido fue registrado correctamente.

Cuando tu impresion este lista te enviaremos una notificacion.
"""

def procesar_mensaje(mensaje, usuario="cliente"):
    mensaje = mensaje.strip().lower()
    estado = estado_usuario.get(usuario, "INICIO")

    saludos = [
        "hola","hola!","buenas","buenos dias",
        "buenas tardes","buenas noches","hey","menu"
    ]

    # -----------------------
    # INICIO
    # -----------------------
    if mensaje in saludos:
        estado_usuario[usuario] = "MENU"
        return menu_principal()


    # -----------------------
    # MENU PRINCIPAL
    # -----------------------
    if estado == "MENU":

        if mensaje == "1":
            estado_usuario[usuario] = "TIPO_DOCUMENTO"
            return menu_documento()

        elif mensaje == "2":
            estado_usuario[usuario] = "TIPO_IMAGEN"
            return menu_imagen()

        elif mensaje == "3":
            return "El servicio de escaneo cuesta $2 por hoja."

        elif mensaje == "4":
            return "Escribe el numero de tu pedido para consultarlo."

        elif mensaje == "5":
            return "Escribe el numero de pedido que deseas cancelar."


    # -----------------------
    # TIPO DOCUMENTO
    # -----------------------
    if estado == "TIPO_DOCUMENTO":

        if mensaje == "1":
            estado_usuario[usuario] = "ESPERANDO_ARCHIVO"
            return """
Impresion en blanco y negro seleccionada.

Ahora envia tu archivo PDF o documento.
"""

        elif mensaje == "2":
            estado_usuario[usuario] = "ESPERANDO_ARCHIVO"
            return """
Impresion a color seleccionada.

Ahora envia tu archivo PDF o documento.
"""


    # -----------------------
    # TIPO IMAGEN
    # -----------------------
    if estado == "TIPO_IMAGEN":

        if mensaje in ["1","2","3","4"]:
            estado_usuario[usuario] = "ESPERANDO_ARCHIVO"
            return """
Formato seleccionado.

Ahora envia la imagen que deseas imprimir.
"""


    # -----------------------
    # ESPERANDO PAGINAS
    # -----------------------
    if estado == "ESPERANDO_PAGINAS":

        estado_usuario[usuario] = "PEDIDO_CONFIRMADO"

        return f"""
Paginas seleccionadas: {mensaje}

{pedido_recibido()}
"""

    return None