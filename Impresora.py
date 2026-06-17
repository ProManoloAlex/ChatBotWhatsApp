import os
import subprocess
import win32print

# Obtener el nombre de las impresoras configuradas
printers = [printer[2] for printer in win32print.EnumPrinters(2)]
for p in printers:
    print(p)

# --- CONFIGURACIÓN DE RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Llamamos directamente al motor de Ghostscript (gswin64.exe)
GHOSTSCRIPT_EXE = os.path.join(BASE_DIR, 'Impresora', 'bin', 'gswin64.exe')
GS_LIB_PATH = os.path.join(BASE_DIR, 'Impresora', 'lib')

def imprimir_archivo_pdf(nombre_pdf):
    nombre_impresora = "EPSON L1250 Series"
    ruta_pdf = os.path.join(BASE_DIR, nombre_pdf)

    # --- VALIDACIONES ---
    if not os.path.exists(ruta_pdf):
        print(f"❌ Error: El archivo '{nombre_pdf}' no existe en {BASE_DIR}")
        return

    if not os.path.exists(GHOSTSCRIPT_EXE):
        print("❌ Error: No se encuentra gswin64.exe en /Impresora/bin")
        return

    # --- COMANDO DIRECTO A GHOSTSCRIPT ---
    #aaaa funciona
    comando = [
        GHOSTSCRIPT_EXE,
        "-dPrinted",                  # Indica que va a impresión física
        "-dBATCH",                    # Sale automáticamente al terminar
        "-dNOPAUSE",                  # No espera confirmación entre páginas
        "-dNOSAFER",                  # Permite acceder a los recursos del sistema
        "-dQueryUser=3",              # <--- ¡ESTA LÍNEA ES LA CLAVE! Desactiva el diálogo de Windows
        f"-I{GS_LIB_PATH}",           # Incluye la librería de fuentes/soporte
        "-sDEVICE=mswinpr2",          # Driver de impresión de Windows
        f"-sPrinterName={nombre_impresora}", # Nombre exacto de tu EPSON
        ruta_pdf                      # Ruta del archivo
    ]

    print(f"Enviando '{nombre_pdf}' directamente a la {nombre_impresora}...")

    try:
        # Ejecutamos de forma limpia ocultando ventanas molestas
        subprocess.run(comando, check=True, creationflags=0x08000000)
        
        print("-" * 30)
        print("✅ Enviado a la cola de la impresora con éxito")
        print("-" * 30)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Ghostscript devolvió un error: {e}")
    except Exception as e:
        print(f"❌ Hubo un fallo inesperado: {e}")

# --- EJECUCIÓN ---
if __name__ == "__main__":
    imprimir_archivo_pdf("Hola.pdf")