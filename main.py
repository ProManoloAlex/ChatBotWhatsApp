import threading
from bot import iniciar_bot
from archivos.convertir import monitor_conversion

if __name__ == "__main__":
    # El monitor corre en paralelo para no bloquear el bot
    hilo_monitor = threading.Thread(target=monitor_conversion, daemon=True)
    hilo_monitor.start()

    iniciar_bot()