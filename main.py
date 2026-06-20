import threading
import time

def iniciar_monitor():
    from archivos.convertir import monitor_conversion
    while True:
        try:
            monitor_conversion()
        except Exception as e:
            print(f"[monitor] Error, reiniciando en 10s: {e}")
            time.sleep(10)

def iniciar_panel():
    import tkinter as tk
    from panel import PanelImpresiones
    root = tk.Tk()
    app  = PanelImpresiones(root)
    root.mainloop()

def iniciar_bot_con_reintentos():
    from bot import iniciar_bot
    while True:
        try:
            print("\n[main] Iniciando bot...")
            iniciar_bot()
        except Exception as e:
            print(f"[main] El bot fallo: {e}")
        print("[main] Reiniciando en 10 segundos...")
        time.sleep(10)

if __name__ == "__main__":
    # Monitor en hilo separado
    threading.Thread(target=iniciar_monitor, daemon=True).start()

    # Panel tkinter en hilo separado
    threading.Thread(target=iniciar_panel, daemon=True).start()

    # Bot en el hilo principal (Selenium funciona mejor aquí)
    iniciar_bot_con_reintentos()