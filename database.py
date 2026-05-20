import sqlite3
import os

# 1. Obtiene la ruta de la carpeta donde está tu script de Python
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))

# 2. Une esa ruta con el nombre del archivo de la base de datos
DB_NAME = os.path.join(DIRECTORIO_ACTUAL, "automatizacion.db")

def conectar():
    return sqlite3.connect(DB_NAME)

# ---------------------------------
# CREAR PEDIDO (cuando llega archivo)
# ---------------------------------
def crear_pedido(whatsapp, tipo_archivo, nombre_archivo, ruta_local, color):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO pedidos
        (whatsapp, tipo_archivo, nombre_archivo, ruta_local, color, estado)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (whatsapp, tipo_archivo, nombre_archivo, ruta_local, color, "PENDIENTE"))

    conn.commit()
    conn.close()

# ---------------------------------
# OBTENER PEDIDOS PENDIENTES
# ---------------------------------
def obtener_pedidos_pendientes():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, ruta_local, formato, paginas_seleccionadas, tipo_archivo
        FROM pedidos
        WHERE estado = 'PENDIENTE'
    """)
    pedidos = cursor.fetchall()
    conn.close()
    return pedidos

# ---------------------------------
# ACTUALIZAR ESTADO
# ---------------------------------
def actualizar_estado(id_pedido, estado):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE pedidos SET estado = ? WHERE id = ?",
        (estado, id_pedido)
    )
    conn.commit()
    conn.close()