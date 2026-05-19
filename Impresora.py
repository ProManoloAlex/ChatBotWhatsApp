#import os
#import win32api
import win32print

#Obtener el nombre de las impresoras que tienes
printers =[printer[2] for printer in win32print.EnumPrinters(2)]
for p in printers:
    print (p)
"""
# --- CONFIGURACIÓN DE RUTAS ---
# Obtenemos la ruta base (donde está tu script)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Rutas exactas según tu estructura de carpetas
GSPRINT_PATH = os.path.join(BASE_DIR, 'Impresora', 'gsview', 'gsprint.exe')
GHOSTSCRIPT_EXE = os.path.join(BASE_DIR, 'Impresora', 'bin', 'gswin64.exe')
GS_LIB_PATH = os.path.join(BASE_DIR, 'Impresora', 'lib')

def imprimir_archivo_pdf(nombre_pdf):
    # 1. Definir impresora (Cámbiala por la física cuando estés con tu amigo)
    nombre_impresora = "Microsoft Print to PDF"
    
    # 2. Ruta completa al archivo PDF que quieres imprimir
    ruta_pdf = os.path.join(BASE_DIR, nombre_pdf)

    # --- VALIDACIONES ---
    if not os.path.exists(ruta_pdf):
        print(f"❌ Error: El archivo '{nombre_pdf}' no existe en {BASE_DIR}")
        return

    if not os.path.exists(GSPRINT_PATH) or not os.path.exists(GHOSTSCRIPT_EXE):
        print("❌ Error: Los ejecutables de Ghostscript/GSprint no se encuentran en /Impresora")
        return

    # 3. Construcción del comando (Formato robusto para evitar errores de comillas)
    # Importante: No dejar espacios extra entre los flags y las comillas
    argumentos = (
        f'-ghostscript "{GHOSTSCRIPT_EXE}" '
        f'-I "{GS_LIB_PATH}" '
        f'-printer "{nombre_impresora}" '
        f'"{ruta_pdf}"'
    )

    print(f"Enviando '{nombre_pdf}' a la cola de impresión...")

    try:
        # Ejecutamos el comando
        # Usamos None en lugar de 'open' para que Windows use el ejecutable directamente
        win32api.ShellExecute(0, None, GSPRINT_PATH, argumentos, ".", 0)
        
        print("-" * 30)
        print("✅ Impreso correctamente")
        print("-" * 30)
        
    except Exception as e:
        print(f"❌ Hubo un fallo al intentar imprimir: {e}")

# --- EJECUCIÓN ---
if __name__ == "__main__":
    # Asegúrate de que el archivo se llame exactamente así en tu carpeta
    imprimir_archivo_pdf("Informe.pdf")
"""