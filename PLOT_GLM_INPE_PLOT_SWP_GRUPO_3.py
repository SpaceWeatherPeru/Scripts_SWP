import requests
from bs4 import BeautifulSoup
import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.img_tiles as cimgt
import matplotlib.lines as mlines
from datetime import datetime, timedelta
import io
import time
import os

#=============================================================================
# RUTA DE GUARDADO DEL PLOT
RUTA_GUARDADO = "./"
#=============================================================================

# Base URL del directorio que contiene los archivos
base_url = "http://ftp.cptec.inpe.br/goes/goes16/goes16_web/glm_acumulado_nc/2025/"

def get_last_file_url(url):
    retries = 3  # Número de reintentos en caso de error
    for _ in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a')
            file_links = [link.get('href') for link in links if link.get('href').endswith('.nc')]
            if file_links:
                return url + file_links[-1]
            else:
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL {url}: {e}")
            time.sleep(5)  # Esperar antes de reintentar
    return None

def download_file_to_memory(url):
    retries = 3  # Número de reintentos en caso de error
    for _ in range(retries):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"Archivo descargado exitosamente desde: {url}")
                return io.BytesIO(response.content)  # Retorna el archivo en memoria
            else:
                print(f"Error al descargar el archivo: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error downloading file {url}: {e}")
            time.sleep(5)  # Esperar antes de reintentar
    print(f"Fallo al descargar el archivo después de {retries} intentos.")
    return None

while True:
    try:
        current_month = datetime.utcnow().month
        formatted_month = f"{current_month:02}"
        url = f"{base_url}{formatted_month}/"
        last_file_url = get_last_file_url(url)
        
        if last_file_url:
            file_memory = download_file_to_memory(last_file_url)
            if file_memory is None:
                print("No se pudo descargar el archivo.")
                time.sleep(600)
                continue

            # Abrir el archivo NetCDF desde memoria
            dataset = nc.Dataset('in-memory.nc', memory=file_memory.read())
            file_name = last_file_url.split('/')[-1]
            fecha = file_name[10:22]
            fecha_datetime = datetime.strptime(fecha, '%Y%m%d%H%M')
            fecha_datetime_peru = fecha_datetime - timedelta(hours=5)
            fecha = str(fecha_datetime.date())
            hora = str(fecha_datetime.time().strftime('%H:%M'))
            hora_peru = str(fecha_datetime_peru.time().strftime('%H:%M'))

            # Extraer datos
            lat = dataset.variables['lat'][:]
            lon = dataset.variables['lon'][:]
            DATOS = "flash"  # se puede cambiar a event o group
            flash_data = dataset.variables[DATOS][:]
            lat_min, lat_max = -19.2, 0.7
            lon_min, lon_max = -82.1, -68.10
            lat_inds = np.where((lat >= lat_min) & (lat <= lat_max))[0]
            lon_inds = np.where((lon >= lon_min) & (lon <= lon_max))[0]
            flash_data_peru = flash_data[:, lat_inds, :][:, :, lon_inds]
            flash_indices = np.where(flash_data_peru > 0)
            flash_lats = lat[lat_inds][flash_indices[1]]
            flash_lons = lon[lon_inds][flash_indices[2]]
            flash_energy = dataset.variables['duration_flash'][:]
            flash_energy_peru = flash_energy[:, lat_inds, :][:, :, lon_inds]
            flash_energy_values = flash_energy_peru[flash_indices]
            dataset.close()

            # Definir caché de OpenStreetMap
            cache_dir = os.path.join(os.path.expanduser('~'), '.cache', 'tiles')
            os.makedirs(cache_dir, exist_ok=True)
            osm_tiles = cimgt.OSM(cache=cache_dir)

            # Graficar
            fig, ax = plt.subplots(figsize=(10, 8), subplot_kw={'projection': ccrs.PlateCarree()})
            ax.add_image(osm_tiles, 6)
            ax.add_feature(cfeature.COASTLINE)
            ax.add_feature(cfeature.BORDERS, linestyle=':')
            ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())
            sc = ax.scatter(flash_lons, flash_lats, c=flash_energy_values, marker='*', s=30, cmap='turbo', transform=ccrs.PlateCarree())
            plt.colorbar(sc, label='Duración (segundos)', pad=0)
            ax.text(0.47, 0.01, 'Fuente: CPTEC/INPE', fontsize=8, ha='left', va='bottom', transform=ax.transAxes)
            plt.title(f'GLM - Acumulación de 5 minutos - {fecha}', fontweight='bold', fontsize=13)
            ax.legend(handles=[
                mlines.Line2D([], [], color='black', marker='*', linestyle='None', markersize=6, label='Flashes'),
                mlines.Line2D([], [], color='none', marker='None', linestyle='None', label=f'Hora Perú: {hora_peru}'),
                mlines.Line2D([], [], color='none', marker='None', linestyle='None', label=f'Hora GMT: {hora}')
            ], loc='lower left')
            plt.tight_layout()
            plt.savefig('GLM_INPE_PLOT_SWP_GRUPO_3.png', dpi=300, bbox_inches='tight', pad_inches=0.1)
            plt.close()

        else:
            print("No se encontraron archivos para descargar.")
    except Exception as e:
        print(f"An error occurred: {e}. Trying again in 10 minutes.")
    
    time.sleep(600)  # Espera 10 minutos antes de la siguiente ejecución
