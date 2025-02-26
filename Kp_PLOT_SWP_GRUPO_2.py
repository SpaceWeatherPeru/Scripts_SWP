import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta, timezone
import json
import urllib.request
import time

#===============================================
# Ruta manual para guardar la imagen
RUTA_GUARDADO = "KP_GAMONAL_SWP.png"  # Especifica la ruta completa aquí
#===============================================

# Diccionario para los meses en español
meses_espanol = {
    1: 'Enero',
    2: 'Febrero',
    3: 'Marzo',
    4: 'Abril',
    5: 'Mayo',
    6: 'Junio',
    7: 'Julio',
    8: 'Agosto',
    9: 'Septiembre',
    10: 'Octubre',
    11: 'Noviembre',
    12: 'Diciembre'
}

def _checkdate(starttime, endtime):
    if starttime > endtime:
        raise NameError("Error! Start time must be before or equal to end time")
    return True

def _checkIndex(index):
    valid_indices = ['Kp', 'ap', 'Ap', 'Cp', 'C9', 'Hp30', 'Hp60', 'ap30', 'ap60', 'SN', 'Fobs', 'Fadj']
    if index not in valid_indices:
        raise IndexError(f"Error! Wrong index parameter! \nAllowed are only the following: {', '.join(valid_indices)}")
    return True

def _checkstatus(status):
    valid_status = ['all', 'def']
    if status not in valid_status:
        raise IndexError(f"Error! Wrong option parameter! \nAllowed are only: {', '.join(valid_status)}")
    return True

def _addstatus(url, status):
    if status == 'def':
        url = url + '&status=def'
    return url

def getKpindex(starttime, endtime, index, status='all'):
    result_t = []
    result_index = []
    result_s = []

    # Verificar formato de las fechas
    if len(starttime) == 10 and len(endtime) == 10:
        starttime = starttime + 'T00:00:00Z'
        endtime = endtime + 'T23:59:00Z'

    try:
        d1 = datetime.strptime(starttime, '%Y-%m-%dT%H:%M:%SZ')
        d2 = datetime.strptime(endtime, '%Y-%m-%dT%H:%M:%SZ')

        # Verificar la validez de la fecha, índice y estatus
        _checkdate(d1, d2)
        _checkIndex(index)
        _checkstatus(status)

        # Generar la URL
        time_string = "start=" + d1.strftime('%Y-%m-%dT%H:%M:%SZ') + "&end=" + d2.strftime('%Y-%m-%dT%H:%M:%SZ')
        url = 'https://kp.gfz-potsdam.de/app/json/?' + time_string + "&index=" + index
        if index not in ['Hp30', 'Hp60', 'ap30', 'ap60', 'Fobs', 'Fadj']:
            url = _addstatus(url, status)

        # Realizar la solicitud HTTP con un timeout
        print(f"Conectando a la API: {url}")
        webURL = urllib.request.urlopen(url, timeout=10)  # 10 segundos de tiempo máximo
        binary = webURL.read()
        text = binary.decode('utf-8')

        try:
            # Procesar la respuesta JSON
            data = json.loads(text)
            result_t = data["datetime"]
            result_index = data[index]
            if index not in ['Hp30', 'Hp60', 'ap30', 'ap60', 'Fobs', 'Fadj']:
                result_s = data["status"]
            print(f"Número de puntos obtenidos: {len(result_t)}")
        except KeyError as e:
            print(f"KeyError: {e}. Response data: {data}")
        except json.JSONDecodeError:
            print("Error decodificando la respuesta JSON. Verifica la respuesta de la API.")
        except Exception as e:
            print(f"Error general procesando la respuesta JSON: {e}")
            print(text)

    except NameError as er:
        print(f"Error en la validación de fecha: {er}")
    except IndexError as er:
        print(f"Error en el índice: {er}")
    except ValueError as e:
        print(f"Error! Formato de fecha incorrecto: {e}")
        print("Las fechas deben estar en el formato yyyy-mm-dd o yyyy-mm-ddTHH:MM:SSZ")
    except urllib.error.URLError as e:
        print(f"Error de conexión: {e}\nNo se pudo conectar a la URL {url}")
    except Exception as e:
        print(f"Error inesperado al obtener el índice Kp: {e}")
    finally:
        return result_t, result_index, result_s

def plotKpIndex(time, index):
    try:
        fechas_dt = [datetime.strptime(fecha, '%Y-%m-%dT%H:%M:%SZ') for fecha in time]
        d = np.arange(1, len(index) + 1)

        # Asignar colores según el valor del índice
        colors = []
        for value in index:
            if value >= 9:
                colors.append('red')
            elif value >= 8:
                colors.append('orange')
            elif value >= 7:
                colors.append('yellow')
            elif value >= 6:
                colors.append('lightgreen')
            elif value >= 5:
                colors.append('cyan')
            else:
                colors.append('blue')

        # Título del gráfico con mes y año en español
        current_time = datetime.now()
        mes = meses_espanol[current_time.month]
        ano = current_time.year
        title = f'{mes} - {ano}'

        # Crear el gráfico
        fig, ax2 = plt.subplots(figsize=(10, 5))  # Cambiar las dimensiones del gráfico
        barras = ax2.bar(d, index, width=0.6, color='black')

        # Configuración de los ejes
        ax2.set_xticks(np.arange(1, len(d) + 1, max(1, int(len(d) / 7))))
        ax2.set_xticklabels([fecha.strftime('%d - %H') for fecha in fechas_dt][::max(1, int(len(d) / 7))], 
                            ha='center', size=12)
        ax2.set_xlim(1, len(d))
        ax2.set_ylim(1, 10)
        ax2.set_xlabel('Fecha (Día - Hora)', fontsize=14)
        ax2.set_ylabel('Índice Kp', fontsize=14)
        ax2.set_title(title, fontsize=16)

        # Marcar los niveles de severidad
        ax2.set_yticks(np.arange(0, 11, 1))
        ax2.tick_params(axis='both', which='major', labelsize=12)

        # Colorear las regiones por severidad
        ax2.fill_between(d, 5, 6, color='cyan', alpha=0.3)
        ax2.fill_between(d, 6, 7, color='lightgreen', alpha=0.3)
        ax2.fill_between(d, 7, 8, color='yellow', alpha=0.3)
        ax2.fill_between(d, 8, 9, color='orange', alpha=0.3)
        ax2.fill_between(d, 9, 10, color='red', alpha=0.3)

        # Leyenda personalizada fuera de la gráfica (parte derecha)
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='cyan', label='Menor (Kp = 5)'),
            Patch(facecolor='lightgreen', label='Moderado (Kp = 6)'),
            Patch(facecolor='yellow', label='Fuerte (Kp = 7)'),
            Patch(facecolor='orange', label='Severo (Kp = 8)'),
            Patch(facecolor='red', label='Extremo (Kp = 9)'),
        ]
        ax2.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(1, 0.5), fontsize=12)

        # Ajustar el diseño del gráfico
        plt.tight_layout()
        plt.subplots_adjust(right=0.75, left=0.07, bottom=0.17, top=0.943)

        # Guardar el gráfico en un archivo
        try:
            plt.savefig(RUTA_GUARDADO, dpi=300, bbox_inches='tight')
            print("Gráfico guardado exitosamente.")
        except Exception as e:
            print(f"Error guardando el gráfico: {e}")
        finally:
            plt.close()
    except Exception as e:
        print(f"Error durante la creación o el guardado del gráfico: {e}")

def update_and_plot():
    try:
        current_time = datetime.now(timezone.utc)
        start_time = (current_time - timedelta(days=5)).strftime('%Y-%m-%dT%H:%M:%SZ')
        end_time = current_time.strftime('%Y-%m-%dT%H:%M:%SZ')

        # Obtener datos de Kp y graficarlos
        print("Obteniendo datos...")
        time_data, index, status = getKpindex(start_time, end_time, 'Kp')

        if time_data and index:
            print("Datos obtenidos. Generando gráfico...")
            plotKpIndex(time_data, index)
        else:
            print("No se recuperaron datos.")
    except Exception as e:
        print(f"Error durante la actualización y graficado: {e}")

def main():
    try:
        update_and_plot()
    except Exception as e:
        print(f"Error en el ciclo principal: {e}")

if __name__ == "__main__":
    main()

