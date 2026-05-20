from database import crear_pedido
from archivos.descargar import *

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
    
    # ✅ Inicializar usuario correctamente
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

    saludos = [
        "hola","hola!","buenas","buenos dias",
    ]

    # -----------------------
    # INICIO
    # -----------------------
    if mensaje in saludos:
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
            return "Opción inválida."
        
    # -----------------------
    # TIPO DOCUMENTO
    # -----------------------
    if estado == "TIPO_DOCUMENTO":

        if mensaje == "1":
            datos["color"] = "blanco_negro"
            datos["estado"] = "ESPERANDO_ARCHIVO"
            return """
            Impresion en blanco y negro seleccionada.
            Ahora envia tu archivo PDF o documento.
            """
        
        elif mensaje == "2":
            datos["color"] = "color"
            datos["estado"] = "ESPERANDO_ARCHIVO"
            return """
            Impresion a color seleccionada.
            Ahora envia tu archivo PDF o documento.
            """
        else:
            return "Opción inválida"
            
    # -----------------------
    # ESPERANDO ARCHIVO
    # -----------------------
    if estado == "ESPERANDO_ARCHIVO":

        datos["estado"] = "ESPERANDO_PAGINAS"
    
        return """
        Archivo recibido correctamente.
    
        Ahora escribe las paginas que deseas imprimir.
        Ejemplo: 1-5 o 2,4,6 o todo
        """

    # -----------------------
    # TIPO IMAGEN
    # -----------------------
    if estado == "TIPO_IMAGEN":

        if mensaje in ["1","2","3","4"]:
            datos["estado"] = "ESPERANDO_ARCHIVO"
            return """
            Formato seleccionado.
            Ahora envia la imagen que deseas imprimir.
            """

    # -----------------------
    # ESPERANDO PAGINAS
    # -----------------------
    if estado == "ESPERANDO_PAGINAS":

        archivo = datos.get("archivo")

        if not archivo:
            return "⚠️ Error: primero debes enviar un archivo."

        datos["paginas"] = mensaje
        datos["estado"] = "MENU"
        datos["pedido_estado"] = "PENDIENTE"

        crear_pedido(
            usuario,
            archivo["tipo"],
            archivo["nombre"],
            archivo["ruta"],
            datos["color"],
            datos["paginas"]
        )

        # ✅ limpiar datos
        datos["archivo"] = None
        datos["paginas"] = None
        datos["color"] = None
        datos["tipo_archivo"] = None

        return f"""
        Pedido confirmado ✅
        Archivo: {archivo['nombre']}
        Páginas: {mensaje}
        Color: {datos['color']}
        Estado: 🟡 PENDIENTE
        """

    return None


    # guardar SOLO si corresponde
    if estado_usuario[usuario]["estado"] == "ESPERANDO_ARCHIVO":
        estado_usuario[usuario]["archivo"] = {
            "nombre": nombre,
            "ruta": ruta,
            "tipo": tipo
    }
        
        print("Archivo guardado en memoria")
                
    else:
                print("Archivo ignorado (no estaba en flujo)")
        
