import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import re
from datetime import datetime, timedelta

#========================================================================================
RUTA_GUARDADO = "DST_GAMONAL_SWP.png"  # Especifica la ruta completa aquí
#========================================================================================

# Diccionario para mapear números de meses a nombres de meses
month_names = {
    '01': 'Enero', '02': 'Febrero', '03': 'Marzo', '04': 'Abril',
    '05': 'Mayo', '06': 'Junio', '07': 'Julio', '08': 'Agosto',
    '09': 'Septiembre', '10': 'Octubre', '11': 'Noviembre', '12': 'Diciembre'
}

def update_data():
    print("Iniciando la función update_data")

    # Obtener el mes y el año actuales
    try:
        now = datetime.now()
        year = now.year
        month = now.month
        day = now.day
        month_str = str(month).zfill(2)
    except Exception as e:
        print(f"Error obteniendo fecha actual: {e}")
        return

    # Verificación previa para evitar fallos en los primeros días del mes
    if day < 5:
        print("Los datos aún no están disponibles para este mes. Intente nuevamente más tarde.")
        return

    # URL del archivo
    url = f'https://wdc.kugi.kyoto-u.ac.jp/dst_realtime/{year}{month_str}/dst{year % 100}{month_str}.for.request'
    print(f"URL generada: {url}")

    # Intentar descargar el archivo con manejo de excepciones
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Lanza excepción si la respuesta no es 200 OK
        print("Datos descargados correctamente")
    except requests.exceptions.RequestException as e:
        print(f"Error al intentar conectar con {url}: {e}")
        return

    # Verificación del contenido descargado
    if response.content.strip() == b'':  # Revisa si el archivo está vacío
        print("El archivo descargado está vacío.")
        return

    # Guardar el archivo descargado
    filename = f'dst{year % 100}{month_str}.for.request'
    try:
        with open(filename, 'wb') as file:
            file.write(response.content)
            print(f"Archivo guardado como: {filename}")
    except Exception as e:
        print(f"Error guardando el archivo: {e}")
        return

    # Leer el contenido del archivo
    try:
        with open(filename, 'r') as file:
            data = file.readlines()
        if 'Created at' in data[-1]:
            data = data[:-1]
    except Exception as e:
        print(f"Error leyendo el archivo: {e}")
        return

    # Expresión regular para detectar números
    number_pattern = re.compile(r'-?\d+')

    # Procesar los datos
    try:
        first_column = []
        values = []

        for line in data:
            parts = number_pattern.findall(line)
            if parts:
                first_column.append(parts[0])  # La primera parte es el identificador
                cleaned_values = []
                for value in parts[1:]:
                    try:
                        val = int(value)
                        # Detectar valores erróneos y reemplazarlos por NaN
                        if val == 9999999999 or abs(val) > 999:
                            cleaned_values.append(np.nan)
                        else:
                            cleaned_values.append(val)
                    except ValueError:
                        cleaned_values.append(np.nan)
                values.append(cleaned_values)
    except Exception as e:
        print(f"Error procesando los datos: {e}")
        return

    # Crear DataFrame
    try:
        df = pd.DataFrame(values)
        print("DataFrame procesado completo:")
        print(df)
    except Exception as e:
        print(f"Error creando el DataFrame: {e}")
        return

    # Graficar los datos
    if not df.empty:
        try:
            flattened_list = [item for sublist in df.values.tolist() for item in sublist]
            days = np.arange(1, len(flattened_list) + 1)
            plt.figure(figsize=(10, 6))
            plt.plot(days, flattened_list, color='black', label='Dst')
            plt.title(f'{month_names[month_str]} - {year}', fontsize=14, fontweight='bold')
            plt.xlabel('Días', fontsize=12)
            plt.ylabel('Índice Dst (nT)', fontsize=12)
            plt.grid(True, which='both', linestyle='--', linewidth=0.5)
            plt.legend(loc='lower left', bbox_to_anchor=(0, 0), fancybox=True, shadow=True, prop={'size': 8})
            plt.xlim(0, len(days) + 1)
            plt.ylim([-350, 100])
            plt.savefig(RUTA_GUARDADO, dpi=300, bbox_inches='tight')
            plt.close()
        except Exception as e:
            print(f"Error graficando los datos: {e}")

update_data()
