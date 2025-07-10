import pandas as pd
import googlemaps
from datetime import datetime

# --------------------------------------------------------------------------
#                         CONFIGURACIÓN INICIAL
# --------------------------------------------------------------------------
# TODO: Reemplaza 'TU_API_KEY' con tu clave de la API de Google Maps.
API_KEY = 'AIzaSyDp2uLQOLN5ZQggkbJx93ICoNIOf8K1_98'

# TODO: Reemplaza 'coordenadas.xlsx' con el nombre de tu archivo de Excel.
NOMBRE_ARCHIVO_EXCEL = 'coordenadas.xlsx'

COLUMNA_COORDENADAS = 'localizaciones'



def obtener_direccion_desde_coordenadas(lat, lon, gmaps):
    """
    Obtiene los componentes de la dirección (país, ciudad, provincia, comuna)
    a partir de la latitud y longitud utilizando la API de Google Maps.
    (Esta función no cambia)
    """
    try:
        # Realiza la solicitud de geocodificación inversa
        reverse_geocode_result = gmaps.reverse_geocode((lat, lon))

        # Inicializa las variables de dirección
        pais = ''
        ciudad = ''
        provincia = ''
        comuna = ''

        # Itera a través de los componentes de la dirección en la respuesta
        if reverse_geocode_result:
            for component in reverse_geocode_result[0]['address_components']:
                types = component.get('types', [])
                if 'country' in types:
                    pais = component.get('long_name', '')
                if 'locality' in types:
                    ciudad = component.get('long_name', '')
                if 'administrative_area_level_1' in types:
                    provincia = component.get('long_name', '')
                if 'administrative_area_level_2' in types or 'sublocality' in types:
                    comuna = component.get('long_name', '')
        
        return pais, ciudad, provincia, comuna

    except Exception as e:
        print(f"Error al procesar las coordenadas ({lat}, {lon}): {e}")
        return None, None, None, None

def main():
    """
    Función principal para leer el archivo de Excel, procesar las coordenadas
    y guardar los resultados en un nuevo archivo de Excel.
    """
    print("Iniciando el proceso de geocodificación inversa...")

    # Inicializa el cliente de Google Maps con tu clave de API
    gmaps = googlemaps.Client(key=API_KEY)

    try:
        # Lee el archivo de Excel
        df = pd.read_excel(NOMBRE_ARCHIVO_EXCEL)
        print(f"Archivo '{NOMBRE_ARCHIVO_EXCEL}' cargado correctamente.")

        # Listas para almacenar los nuevos datos
        paises = []
        ciudades = []
        provincias = []
        comunas = []

        # Itera sobre cada fila del DataFrame
        for index, row in df.iterrows():
            coordenadas_str = row[COLUMNA_COORDENADAS]

            # Inicializa las variables por si hay un error en esta fila
            pais, ciudad, provincia, comuna = '', '', '', ''
            lat, lon = None, None

            # Procesa la cadena de coordenadas para separarla
            try:
                # Asegurarse de que el valor es una cadena antes de dividir
                if isinstance(coordenadas_str, str):
                    partes = coordenadas_str.split(',')
                    if len(partes) == 2:
                        lat = float(partes[0].strip())
                        lon = float(partes[1].strip())
                        print(f"Procesando fila {index + 1}: Latitud={lat}, Longitud={lon}")
                        # Obtiene la dirección para las coordenadas actuales
                        pais, ciudad, provincia, comuna = obtener_direccion_desde_coordenadas(lat, lon, gmaps)
                    else:
                        print(f"Advertencia en la fila {index + 1}: El formato de coordenadas '{coordenadas_str}' no es válido. Se omitirá.")
                else:
                    print(f"Advertencia en la fila {index + 1}: El valor no es una cadena de texto válida. Se omitirá.")

            except (ValueError, IndexError) as e:
                 print(f"Advertencia en la fila {index + 1}: No se pudieron procesar las coordenadas '{coordenadas_str}'. Error: {e}. Se omitirá.")

            # Agrega los resultados (o valores vacíos si hubo error) a las listas
            paises.append(pais)
            ciudades.append(ciudad)
            provincias.append(provincia)
            comunas.append(comuna)

        # Agrega las nuevas columnas al DataFrame
        df['País'] = paises
        df['Ciudad'] = ciudades
        df['Provincia'] = provincias
        df['Comuna'] = comunas
        print("\nNuevas columnas de dirección agregadas al DataFrame.")

        # Guarda el DataFrame actualizado en un nuevo archivo de Excel
        nombre_archivo_salida = f"resultados_geocodificacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(nombre_archivo_salida, index=False)
        print(f"Proceso completado. Los resultados se han guardado en '{nombre_archivo_salida}'.")

    except FileNotFoundError:
        print(f"Error: No se pudo encontrar el archivo '{NOMBRE_ARCHIVO_EXCEL}'.")
        print("Asegúrate de que el archivo esté en la misma carpeta que el script o proporciona la ruta completa.")
    except KeyError as e:
        print(f"Error: La columna {e} no se encontró en el archivo de Excel.")
        print(f"Por favor, verifica que la columna de coordenadas se llame '{COLUMNA_COORDENADAS}'.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

if __name__ == '__main__':
    main()