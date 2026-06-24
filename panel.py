import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import sqlite3

# ── RUTAS ─────────────────────────────────────────────────────────────────────
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
DB_NAME           = os.path.join(DIRECTORIO_ACTUAL, "automatizacion.db")
CARPETA_SALIDA    = os.path.join(DIRECTORIO_ACTUAL, "Listos_Para_Imprimir")
GHOSTSCRIPT_EXE   = os.path.join(DIRECTORIO_ACTUAL, "Impresora", "bin", "gswin64.exe")
NOMBRE_IMPRESORA  = "EPSON L1250 Series"

# ── COLORES POR ESTADO ────────────────────────────────────────────────────────
COLORES = {
    "PENDIENTE":          "#E3F2FD",  # azul claro
    "PROCESANDO":         "#FFF9C4",  # amarillo claro
    "LISTO_PARA_IMPRIMIR":"#FFE0B2",  # naranja claro  ← nuevo estado
    "IMPRESO":            "#C8E6C9",  # verde claro
    "CANCELADO":          "#FFCDD2",  # rojo claro
    "ERROR":              "#F8BBD0",  # rosa
}

# ── BASE DE DATOS ─────────────────────────────────────────────────────────────
def conectar():
    return sqlite3.connect(DB_NAME)

def obtener_pedidos():
    conn   = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, whatsapp, nombre_archivo, hojas_totales,
               monto_pago, color, formato, estado, fecha_registro
        FROM pedidos
        ORDER BY id DESC
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

def limpiar_pedidos_viejos():
    """Elimina permanentemente pedidos de mas de 1 dia."""
    conn   = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM pedidos
        WHERE datetime(fecha_registro) < datetime('now', '-1 day')
    """)
    eliminados = cursor.rowcount
    conn.commit()
    conn.close()
    return eliminados

# ── IMPRESIÓN ─────────────────────────────────────────────────────────────────
def imprimir_pedido(id_pedido):
    import subprocess

    # Buscar el archivo — puede ser PDF o JPG (imagenes)
    ruta_pdf = os.path.join(CARPETA_SALIDA, f"pedido_{id_pedido}.pdf")
    ruta_jpg = os.path.join(CARPETA_SALIDA, f"pedido_{id_pedido}.jpg")

    if os.path.exists(ruta_pdf):
        ruta_archivo = ruta_pdf
    elif os.path.exists(ruta_jpg):
        ruta_archivo = ruta_jpg
    else:
        messagebox.showerror("Error", f"No se encontro el archivo del pedido #{id_pedido}")
        return False

    if not os.path.exists(GHOSTSCRIPT_EXE):
        messagebox.showerror("Error", f"No se encontro Ghostscript:\n{GHOSTSCRIPT_EXE}")
        return False

    GS_LIB  = os.path.join(DIRECTORIO_ACTUAL, "Impresora", "lib")
    comando = [
        GHOSTSCRIPT_EXE,
        "-dPrinted", "-dBATCH", "-dNOPAUSE", "-dNOSAFER",
        "-dQueryUser=3",
        f"-I{GS_LIB}",
        "-sDEVICE=mswinpr2",
        f"-sPrinterName={NOMBRE_IMPRESORA}",
        ruta_archivo
    ]
    try:
        subprocess.run(comando, check=True, creationflags=0x08000000)
        return True
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error de impresion", str(e))
        return False
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return False

# ── PANEL PRINCIPAL ───────────────────────────────────────────────────────────
class PanelImpresiones:
    def __init__(self, root):
        self.root = root
        self.root.title("Panel de Impresiones")
        self.root.geometry("1100x640")
        self.root.configure(bg="#F5F5F5")

        self._construir_ui()
        self._actualizar_tabla()
        self._iniciar_auto_refresco()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _construir_ui(self):
        # Título
        tk.Label(
            self.root, text="Panel de Impresiones",
            font=("Helvetica", 16, "bold"),
            bg="#F5F5F5", fg="#333"
        ).pack(pady=(12, 4))

        # Contador
        self.lbl_contador = tk.Label(
            self.root, text="",
            font=("Helvetica", 10), bg="#F5F5F5", fg="#555"
        )
        self.lbl_contador.pack()

        # Botón refrescar
        tk.Button(
            self.root, text="Actualizar",
            command=self._actualizar_tabla,
            bg="#1976D2", fg="white",
            font=("Helvetica", 10), relief="flat", padx=10
        ).pack(pady=(4, 8))

        # Tabla
        frame_tabla = tk.Frame(self.root)
        frame_tabla.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        columnas = ("id", "whatsapp", "archivo", "hojas", "monto", "color", "formato", "estado", "fecha")
        self.tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=18)

        config_cols = [
            ("id",       "ID",         50),
            ("whatsapp", "WhatsApp",  130),
            ("archivo",  "Archivo",   200),
            ("hojas",    "Hojas",      60),
            ("monto",    "Monto",      70),
            ("color",    "Color",      90),
            ("formato",  "Formato",    90),
            ("estado",   "Estado",    130),
            ("fecha",    "Fecha",      140),
        ]
        for col, titulo, ancho in config_cols:
            self.tabla.heading(col, text=titulo)
            self.tabla.column(col, width=ancho, anchor="center")

        sb_y = ttk.Scrollbar(frame_tabla, orient="vertical",   command=self.tabla.yview)
        sb_x = ttk.Scrollbar(frame_tabla, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        sb_y.pack(side="right", fill="y")
        sb_x.pack(side="bottom", fill="x")
        self.tabla.pack(fill="both", expand=True)

        # Botones de acción
        frame_botones = tk.Frame(self.root, bg="#F5F5F5")
        frame_botones.pack(pady=(4, 4))

        tk.Button(
            frame_botones, text="🖨️  Imprimir seleccionado",
            command=self._imprimir_seleccionado,
            bg="#2E7D32", fg="white",
            font=("Helvetica", 11, "bold"), relief="flat", padx=16, pady=6
        ).pack(side="left", padx=8)

        tk.Button(
            frame_botones, text="❌  Cancelar seleccionado",
            command=self._cancelar_seleccionado,
            bg="#C62828", fg="white",
            font=("Helvetica", 11, "bold"), relief="flat", padx=16, pady=6
        ).pack(side="left", padx=8)

        tk.Button(
            frame_botones, text="🗑️  Limpiar pedidos (+1 día)",
            command=self._limpiar_pedidos,
            bg="#757575", fg="white",
            font=("Helvetica", 11, "bold"), relief="flat", padx=16, pady=6
        ).pack(side="left", padx=8)

        # Etiqueta de estado
        self.lbl_estado = tk.Label(
            self.root, text="",
            font=("Helvetica", 10), bg="#F5F5F5", fg="#2E7D32"
        )
        self.lbl_estado.pack(pady=(2, 8))

    # ── TABLA ─────────────────────────────────────────────────────────────────
    def _actualizar_tabla(self):
        seleccion = self.tabla.focus()
        id_sel    = None
        if seleccion:
            vals = self.tabla.item(seleccion, "values")
            if vals:
                id_sel = vals[0]

        for row in self.tabla.get_children():
            self.tabla.delete(row)

        pedidos        = obtener_pedidos()
        listos         = 0

        for p in pedidos:
            id_p, wa, archivo, hojas, monto, color, formato, estado, fecha = p
            monto_str   = f"${monto:.0f}" if monto else "$0"
            hojas_str   = str(hojas) if hojas else "0"
            fecha_corta = fecha[:16] if fecha else ""

            tag = estado or "PENDIENTE"
            iid = self.tabla.insert(
                "", "end",
                values=(id_p, wa, archivo, hojas_str, monto_str, color, formato, estado, fecha_corta),
                tags=(tag,)
            )
            if str(id_p) == str(id_sel):
                self.tabla.focus(iid)
                self.tabla.selection_set(iid)

            if estado == "LISTO_PARA_IMPRIMIR":
                listos += 1

        for estado, color in COLORES.items():
            self.tabla.tag_configure(estado, background=color)

        self.lbl_contador.config(
            text=f"{listos} pedido(s) listos para imprimir"
            if listos > 0 else "Sin pedidos pendientes de impresion"
        )

    # ── ACCIONES ──────────────────────────────────────────────────────────────
    def _obtener_id_seleccionado(self):
        seleccion = self.tabla.focus()
        if not seleccion:
            messagebox.showwarning("Aviso", "Selecciona un pedido de la tabla.")
            return None, None
        vals = self.tabla.item(seleccion, "values")
        return (vals[0], vals) if vals else (None, None)

    def _imprimir_seleccionado(self):
        id_p, vals = self._obtener_id_seleccionado()
        if not id_p:
            return

        pedidos = obtener_pedidos()
        pedido  = next((p for p in pedidos if str(p[0]) == str(id_p)), None)
        if not pedido:
            messagebox.showerror("Error", "Pedido no encontrado.")
            return

        estado_actual = pedido[7]
        if estado_actual != "LISTO_PARA_IMPRIMIR":
            messagebox.showwarning(
                "Aviso",
                f"Solo se pueden imprimir pedidos en estado LISTO_PARA_IMPRIMIR.\n"
                f"Este pedido esta en: {estado_actual}"
            )
            return

        monto = pedido[4] or 0
        confirmar = messagebox.askyesno(
            "Confirmar impresion",
            f"¿Imprimir pedido #{id_p}?\n"
            f"Archivo: {pedido[2]}\n"
            f"Hojas: {pedido[3]} — Monto: ${monto:.0f}"
        )
        if not confirmar:
            return

        self.lbl_estado.config(text="Enviando a impresora...", fg="#1976D2")
        self.root.update()

        def _hilo_imprimir():
            exito = imprimir_pedido(id_p)
            if exito:
                actualizar_estado(id_p, "IMPRESO")
                self.lbl_estado.config(
                    text=f"✅ Pedido #{id_p} impreso correctamente", fg="#2E7D32"
                )
            else:
                self.lbl_estado.config(
                    text=f"❌ Error al imprimir pedido #{id_p}", fg="#C62828"
                )
            self.root.after(0, self._actualizar_tabla)

        threading.Thread(target=_hilo_imprimir, daemon=True).start()

    def _cancelar_seleccionado(self):
        id_p, _ = self._obtener_id_seleccionado()
        if not id_p:
            return

        confirmar = messagebox.askyesno(
            "Confirmar cancelacion",
            f"¿Cancelar pedido #{id_p}?\nEsta accion no se puede deshacer."
        )
        if not confirmar:
            return

        actualizar_estado(id_p, "CANCELADO")
        self.lbl_estado.config(text=f"Pedido #{id_p} cancelado", fg="#C62828")
        self._actualizar_tabla()

    def _limpiar_pedidos(self):
        confirmar = messagebox.askyesno(
            "Limpiar pedidos",
            "Se eliminaran PERMANENTEMENTE todos los pedidos\n"
            "con mas de 1 dia de antiguedad.\n\n"
            "¿Continuar?"
        )
        if not confirmar:
            return

        eliminados = limpiar_pedidos_viejos()
        self.lbl_estado.config(
            text=f"🗑️ {eliminados} pedido(s) eliminado(s)", fg="#757575"
        )
        self._actualizar_tabla()

    # ── AUTO REFRESCO ─────────────────────────────────────────────────────────
    def _iniciar_auto_refresco(self):
        def _loop():
            while True:
                time.sleep(10)
                try:
                    self.root.after(0, self._actualizar_tabla)
                except:
                    break
        threading.Thread(target=_loop, daemon=True).start()


# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = PanelImpresiones(root)
    root.mainloop()