import sqlite3

DB_NAME = "C:/Users/ProManoloAlex/Documents/Ciber/automatizacion.db"

def conectar():
    return sqlite3.connect(DB_NAME)

# ---------------------------------
# CREAR PEDIDO (cuando llega archivo)
# ---------------------------------
def crear_pedido(whatsapp, tipo_archivo, nombre_archivo, ruta_local):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO pedidos
        (whatsapp, tipo_archivo, nombre_archivo, ruta_local)
        VALUES (?, ?, ?, ?)
    """, (whatsapp, tipo_archivo, nombre_archivo, ruta_local))
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