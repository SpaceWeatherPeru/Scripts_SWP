import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
from datetime import datetime

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

    try:
        now = datetime.now()
        year = now.year
        month = now.month
        day = now.day
        month_str = str(month).zfill(2)
    except Exception as e:
        print(f"Error obteniendo fecha actual: {e}")
        return

    if day < 5:
        print("Los datos aún no están disponibles para este mes. Intente nuevamente más tarde.")
        return

    url = f'https://wdc.kugi.kyoto-u.ac.jp/dst_realtime/{year}{month_str}/dst{year % 100}{month_str}.for.request'
    print(f"URL generada: {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        print("Datos descargados correctamente")
    except requests.exceptions.RequestException as e:
        print(f"Error al intentar conectar con {url}: {e}")
        return

    if response.content.strip() == b'':
        print("El archivo descargado está vacío.")
        return

    filename = f'dst{year % 100}{month_str}.for.request'
    try:
        with open(filename, 'wb') as file:
            file.write(response.content)
            print(f"Archivo guardado como: {filename}")
    except Exception as e:
        print(f"Error guardando el archivo: {e}")
        return

    try:
        with open(filename, 'r') as file:
            data = file.readlines()
        if 'Created at' in data[-1]:
            data = data[:-1]
    except Exception as e:
        print(f"Error leyendo el archivo: {e}")
        return

    number_pattern = re.compile(r'-?\d+')
    try:
        values = []
        for line in data:
            parts = number_pattern.findall(line)
            if parts:
                cleaned_values = [int(value) if value != '9999999999' and abs(int(value)) <= 999 else np.nan for value in parts[1:]]
                values.append(cleaned_values)
    except Exception as e:
        print(f"Error procesando los datos: {e}")
        return

    try:
        df = pd.DataFrame(values)
        df = df.dropna(how='all', axis=1)  # Elimina columnas completamente vacías
        print("DataFrame procesado completo:")
        print(df)
    except Exception as e:
        print(f"Error creando el DataFrame: {e}")
        return

    if not df.empty:
        try:
            flattened_list = df.values.flatten()
            days = np.arange(1, len(flattened_list) + 1)

            plt.figure(figsize=(10, 6))
            plt.fill_between(days, -30, -50, color='yellow', alpha=0.3, label='Débil (-30 a -50 nT)')
            plt.fill_between(days, -50, -100, color='orange', alpha=0.3, label='Moderada (-50 a -100 nT)')
            plt.fill_between(days, -100, -250, color='green', alpha=0.3, label='Intensa (-100 a -250 nT)')
            plt.fill_between(days, -250, -350, color='red', alpha=0.3, label='Muy Intensa (< -250 nT)')
            plt.plot(days, flattened_list, color='black', label='Dst')

            plt.title(f'{month_names[month_str]} - {year}', fontsize=14, fontweight='bold')
            plt.xlabel('Días', fontsize=12)
            plt.ylabel('Índice Dst (nT)', fontsize=12)
            plt.xticks(np.arange(0, len(flattened_list), 24), np.arange(1, (len(flattened_list) // 24) + 1))
            plt.grid(True, which='both', linestyle='--', linewidth=0.5)
            plt.subplots_adjust(top=0.880, bottom=0.110, left=0.085, right=0.975, hspace=0.200, wspace=0.200)
            plt.legend(loc='lower left', bbox_to_anchor=(0, 0), fancybox=True, shadow=True, prop={'size': 8})
            plt.xlim(0, len(flattened_list))
            plt.ylim([-350, 100])
            plt.savefig(RUTA_GUARDADO, dpi=300, bbox_inches='tight')
            plt.close()
        except Exception as e:
            print(f"Error graficando los datos: {e}")

update_data()
