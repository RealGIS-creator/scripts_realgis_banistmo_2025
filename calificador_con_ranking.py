import pandas as pd
import re
import os

# --- 0. Configuración Inicial ---
ARCHIVO_EXCEL_ENTRADA = r"C:\Users\ACER\Documents\JUANTORRES\BANITSMO\DATA_BANISTMO\SCRIPTS\entrega_3_prueba_09072025.xlsx"
COLUMNA_DIRECCIONES_ENTRADA = "direcciones"
COLUMNA_ID = "direccion_id"
COLUMNA_ACREDITADO_ID = "acreditado_id"
NOMBRE_ARCHIVO_SALIDA_CSV = r"C:\Users\ACER\Documents\JUANTORRES\BANITSMO\DATA_BANISTMO\SCRIPTS\entrega_3_prueba_09072025_calificadas.csv"


def calificar_estructura_direccion_panama(direccion_texto):
    if not isinstance(direccion_texto, str) or not direccion_texto.strip():
        return 0, "Dirección vacía o inválida"

    score = 0
    detalles_calificacion = []
    direccion_lower = direccion_texto.lower().strip()
    palabras = [p.strip(".,") for p in direccion_lower.split()]
    num_palabras = len(palabras)

    tipos_via = ["calle", "cll", "avenida", "av", "ave", "vía", "via", "transversal", "trans",
                 "carrera", "diag", "diagonal", "boulevard", "blvd", "paseo", "carretera", "camino"]
    if any(tv in palabras for tv in tipos_via):
        score += 5
        detalles_calificacion.append("Tipo de vía detectado")

    if re.search(r'\d', direccion_texto):
        score += 3
        detalles_calificacion.append("Número detectado")
        if re.search(r'(nro|no|#)\s*\d+|\b\d+[a-zA-Z]?\b', direccion_lower):
            score += 2
            detalles_calificacion.append("Posible número de casa/edificio")

    keywords_especificidad = {
        "edificio": 3, "edif": 3, "torre": 3, "apartamento": 2, "apto": 2, "piso": 2,
        "local": 2, "oficina": 2, "casa": 3, "residencia": 3, "residencial": 3, "res": 3,
        "urbanización": 3, "urb": 3, "barriada": 2, "complejo": 2,
        "sector": 2, "área": 1, "zona": 1, "corregimiento": 3, "distrito": 1,
        "barrio": 2, "manzana": 1, "mz": 1, "lote": 1, "parcela": 1, "etapa": 1,
        "centro comercial": 2, "c.c.": 2, "plaza": 2, "parque": 1
    }
    for keyword, puntos in keywords_especificidad.items():
        if keyword in direccion_lower:
            score += puntos
            detalles_calificacion.append(f"Keyword: {keyword} (+{puntos})")

    nombres_propios_count = 0
    palabras_originales = [p.strip(".,") for p in direccion_texto.split()]
    if len(palabras_originales) > 1:
        posibles_nombres = False
        for palabra_orig in palabras_originales:
            if palabra_orig.lower() in tipos_via or palabra_orig.lower() in ["de", "del", "la", "el", "los", "las", "con", "y"]:
                posibles_nombres = True
                continue
            if posibles_nombres and palabra_orig.istitle() and len(palabra_orig) > 2 and palabra_orig.upper() != palabra_orig:
                if palabra_orig.lower() not in tipos_via and palabra_orig.lower() not in keywords_especificidad:
                    nombres_propios_count += 1

    if nombres_propios_count > 0:
        score += min(nombres_propios_count * 1, 3)
        detalles_calificacion.append(
            f"Posibles nombres propios: {nombres_propios_count}")

    if num_palabras > 4:
        score += 1
    if num_palabras > 7:
        score += 2
    if num_palabras > 10:
        score += 1
    if num_palabras > 0:
        detalles_calificacion.append(f"Longitud: {num_palabras} palabras")

    if num_palabras <= 1:
        score -= 10
        detalles_calificacion.append("Muy corta (<=1 palabra)")
    elif num_palabras <= 3:
        es_generica_panama = (
            ("panamá" in direccion_lower or "panama" in direccion_lower) and
            not any(kw in direccion_lower for kw in tipos_via + list(keywords_especificidad.keys())) and
            not re.search(r'\d', direccion_texto)
        )
        if es_generica_panama:
            score -= 7
            detalles_calificacion.append(
                "Parece genérica (ej. solo ciudad/provincia)")
        else:
            score -= 2
            detalles_calificacion.append("Corta (2-3 palabras)")

    ciudades_provincias_panama = ["panamá", "panama", "colón", "colon", "chiriquí", "david", "veraguas", "santiago",
                                  "coclé", "penonomé", "herrera", "chitré", "los santos", "las tablas",
                                  "bocas del toro", "darién"]

    menciones_geo = sum(
        1 for geo_term in ciudades_provincias_panama if geo_term in direccion_lower)
    if menciones_geo > 0 and num_palabras > (menciones_geo + 2) and score > 5:
        score += 1
        detalles_calificacion.append(
            "Contexto geográfico presente con otros detalles")
    elif menciones_geo > 1 and num_palabras <= (menciones_geo + 1):
        score -= 3
        detalles_calificacion.append(
            "Múltiples menciones geográficas sin suficiente detalle adicional")

    final_score = max(0, score)
    return final_score, "; ".join(detalles_calificacion)


# --- 2. Carga de Direcciones desde Excel ---
print(f"--- Cargando Direcciones desde '{ARCHIVO_EXCEL_ENTRADA}' ---")

if not os.path.exists(ARCHIVO_EXCEL_ENTRADA):
    print(f"Error: El archivo '{ARCHIVO_EXCEL_ENTRADA}' no fue encontrado.")
    exit()

try:
    df_excel_input = pd.read_excel(ARCHIVO_EXCEL_ENTRADA)
    columnas_necesarias = [COLUMNA_ID,
                           COLUMNA_ACREDITADO_ID, COLUMNA_DIRECCIONES_ENTRADA]
    if not all(col in df_excel_input.columns for col in columnas_necesarias):
        print("Error: Faltan columnas necesarias.")
        print(f"Columnas disponibles: {df_excel_input.columns.tolist()}")
        exit()

    direcciones_a_calificar = df_excel_input[columnas_necesarias].dropna().astype(
        str)
    if direcciones_a_calificar.empty:
        print("No se encontraron direcciones válidas.")
        exit()
    print(
        f"Se cargaron {len(direcciones_a_calificar)} direcciones para calificar.")

except Exception as e:
    print(f"Error al procesar el archivo: {e}")
    exit()

# --- 3. Calificación ---
print(f"\n--- Calificando {len(direcciones_a_calificar)} Direcciones ---")
resultados_calificacion = []

for i, fila in direcciones_a_calificar.iterrows():
    direccion_id = fila[COLUMNA_ID]
    acreditado_id = fila[COLUMNA_ACREDITADO_ID]
    direccion_actual = fila[COLUMNA_DIRECCIONES_ENTRADA]

    puntaje, detalle_puntaje = calificar_estructura_direccion_panama(
        direccion_actual)

    resultados_calificacion.append({
        "acreditado_id": acreditado_id,
        "direccion_id": direccion_id,
        "direccion_original": direccion_actual,
        "puntaje_calidad_estructura": puntaje,
        "detalle_calificacion": detalle_puntaje
    })

print("Calificación completada.")

# --- 4. Guardar con Ranking ---
print(f"\n--- Guardando Resultados de Calificación ---")
df_resultados_finales = pd.DataFrame(resultados_calificacion)

# Agregar ranking por acreditado_id
df_resultados_finales["ranking"] = df_resultados_finales.groupby("acreditado_id")[
    "puntaje_calidad_estructura"]    .rank(method="first", ascending=False).astype(int)

try:
    df_resultados_finales.to_csv(
        NOMBRE_ARCHIVO_SALIDA_CSV, index=False, sep=';', encoding='utf-8-sig')
    print(f"Resultados guardados en: '{NOMBRE_ARCHIVO_SALIDA_CSV}'")
except Exception as e:
    print(f"Error al guardar el CSV: {e}")

print("\n--- Proceso Completado ---")
