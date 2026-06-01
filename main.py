import threading
import time
from archivos.convertir import monitor_conversion

def iniciar_monitor():
    while True:
        try:
            monitor_conversion()
        except Exception as e:
            print(f"[monitor] Error inesperado, reiniciando en 10s: {e}")
            time.sleep(10)

def iniciar_bot_con_reintentos():
    from bot import iniciar_bot
    while True:
        try:
            print("\n[main] Iniciando bot...")
            iniciar_bot()
        except Exception as e:
            print(f"[main] El bot falló: {e}")
        print("[main] El navegador se cerró. Reiniciando en 10 segundos...")
        print("[main] Cierra esta ventana si quieres detener el programa.")
        time.sleep(10)

if __name__ == "__main__":
    # Monitor en hilo separado, se reinicia solo si falla
    hilo_monitor = threading.Thread(target=iniciar_monitor, daemon=True)
    hilo_monitor.start()

    # Bot en el hilo principal, se reinicia si el navegador se cierra
    iniciar_bot_con_reintentos()