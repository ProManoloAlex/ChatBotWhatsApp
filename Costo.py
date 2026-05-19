import fitz  # PyMuPDF

# 📌 Obtener número de páginas
def contar_paginas(ruta_pdf):
    try:
        doc = fitz.open(ruta_pdf)
        total = doc.page_count
        doc.close()
        return total
    except:
        return 0

# 📌 Interpretar selección del usuario
def procesar_seleccion(entrada, total_paginas):
    # Convertimos a minúsculas y quitamos espacios para evitar errores de escritura
    entrada = entrada.lower().strip().replace(" ", "")

    # Ahora no importa si el usuario escribe "Todo", "TODO" o "todo"
    if entrada == "todo":
        return list(range(1, total_paginas + 1))

    paginas = set()
    partes = entrada.split(",")

    for parte in partes:
        if "-" in parte:
            try:
                inicio_str, fin_str = parte.split("-")
                inicio = int(inicio_str)
                fin = int(fin_str)
                # Aseguramos que el rango sea válido (ej. 5-1 en lugar de 1-5)
                rango_inicio = min(inicio, fin)
                rango_fin = max(inicio, fin)

                for i in range(rango_inicio, rango_fin + 1):
                    if 1 <= i <= total_paginas:
                        paginas.add(i)
            except ValueError:
                continue
        else:
            try:
                num = int(parte)
                if 1 <= num <= total_paginas:
                    paginas.add(num)
            except ValueError:
                continue

    return sorted(list(paginas))

# 📌 Calcular costo
def calcular_costo(paginas, precio=1):
    return len(paginas) * precio

# ----------------------------
# 🚀 PRUEBA
# ----------------------------
"""
# Cambia esto por un PDF real que tengas en tu carpeta
ruta_pdf = "Informe.pdf" 

total_paginas = contar_paginas(ruta_pdf)

if total_paginas == 0:
    print("❌ No se pudo abrir el archivo PDF.")
else:
    print(f"✅ El PDF tiene {total_paginas} páginas.")
    
    entrada = input("¿Qué páginas quieres imprimir? (ej: 1,2,5 | 1-5 | Todo): ")

    paginas_seleccionadas = procesar_seleccion(entrada, total_paginas)

    if not paginas_seleccionadas:
        print("❌ No seleccionaste páginas válidas.")
    else:
        costo = calcular_costo(paginas_seleccionadas)
        print(f"📄 Páginas a procesar: {paginas_seleccionadas}")
        print(f"🧾 Total hojas: {len(paginas_seleccionadas)}")
        print(f"💰 Costo total: ${costo} pesos")
   """