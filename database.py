import sqlite3
import os

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(DIRECTORIO_ACTUAL, "automatizacion.db")

def conectar():
    return sqlite3.connect(DB_NAME)

def crear_pedido(whatsapp, tipo_archivo, nombre_archivo, ruta_local,
                 color, paginas_seleccionadas, formato="CARTA", copias=1,
                 hojas_totales=0, imagenes_por_hoja=1, monto_pago=0.0):
    conn   = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO pedidos
        (whatsapp, tipo_archivo, nombre_archivo, ruta_local,
         color, paginas_seleccionadas, formato, copias,
         hojas_totales, imagenes_por_hoja, estado, monto_pago)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDIENTE', ?)
    """, (whatsapp, tipo_archivo, nombre_archivo, ruta_local,
          color, paginas_seleccionadas, formato, copias,
          hojas_totales, imagenes_por_hoja, monto_pago))
    conn.commit()
    id_pedido = cursor.lastrowid
    conn.close()
    return id_pedido

def obtener_pedidos_pendientes():
    conn   = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, ruta_local, formato, paginas_seleccionadas,
               tipo_archivo, color, copias, hojas_totales, imagenes_por_hoja
        FROM pedidos
        WHERE estado = 'PENDIENTE'
    """)
    pedidos = cursor.fetchall()
    conn.close()
    return pedidos

def actualizar_estado(id_pedido, estado):
    conn   = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE pedidos SET estado = ? WHERE id = ?", (estado, id_pedido))
    conn.commit()
    conn.close()

def actualizar_monto(id_pedido, monto, hojas=None):
    """Actualiza monto_pago y opcionalmente hojas_totales."""
    conn   = conectar()
    cursor = conn.cursor()
    if hojas is not None:
        cursor.execute(
            "UPDATE pedidos SET monto_pago = ?, hojas_totales = ? WHERE id = ?",
            (monto, hojas, id_pedido)
        )
    else:
        cursor.execute(
            "UPDATE pedidos SET monto_pago = ? WHERE id = ?",
            (monto, id_pedido)
        )
    conn.commit()
    conn.close()

def obtener_config(parametro):
    conn   = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM configuracion WHERE parametro = ?", (parametro,))
    fila = cursor.fetchone()
    conn.close()
    return fila[0] if fila else None