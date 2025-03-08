import re
import os
import shutil
import unicodedata
import random
from datetime import datetime
from config import AUDIO_PATH, RENDER_PATH, CLIPS_PATH

def normalizar_cadena(cadena):
    """
    Convierte la cadena a minúsculas, normaliza caracteres (NFKD) y elimina diacríticos.
    Retorna la cadena limpia sin espacios adicionales.
    """
    cadena = cadena.lower()
    cadena = ''.join(c for c in unicodedata.normalize('NFKD', cadena) if unicodedata.category(c) != 'Mn')
    return cadena.strip()

def buscar_archivos(directorio, string_busqueda):
    """
    Busca de forma recursiva en 'directorio' archivos cuyo nombre contenga 'string_busqueda'
    (tras normalizar ambos). Retorna una lista de rutas encontradas.
    """
    archivos_encontrados = []
    busq_norm = normalizar_cadena(string_busqueda)
    for raiz, _, archivos in os.walk(directorio):
        for archivo in archivos:
            if busq_norm in normalizar_cadena(archivo):
                archivos_encontrados.append(os.path.join(raiz, archivo))
    return archivos_encontrados

def get_folder_content(folder_path):
    """
    Obtiene el contenido de una carpeta (archivos y subcarpetas) de forma recursiva
    y lo retorna ordenado por la fecha de creación.
    """
    files = []
    for entry in os.listdir(folder_path):
        full_path = os.path.join(folder_path, entry)
        if os.path.isfile(full_path) or os.path.isdir(full_path):
            files.append(full_path)

    extended_files = []
    for file in files:
        if os.path.isdir(file):
            extended_files.extend(get_folder_content(file))
        else:
            extended_files.append(file)

    files_sorted_by_creation = sorted(extended_files, key=os.path.getctime)
    return files_sorted_by_creation

def move_and_rename_file(file_path, new_directory, new_file_name):
    """
    Mueve un archivo desde 'file_path' a 'new_directory' y luego lo renombra a 'new_file_name'.
    
    Args:
        file_path (str): Ruta actual del archivo.
        new_directory (str): Nuevo directorio donde se moverá el archivo.
        new_file_name (str): Nuevo nombre para el archivo.
    
    Returns:
        str: La ruta completa del archivo renombrado.
    """
    new_path_with_old_name = shutil.move(file_path, new_directory)
    new_file_path = os.path.join(new_directory, new_file_name)
    os.rename(new_path_with_old_name, new_file_path)
    return new_file_path

def create_folder(path):
    """
    Crea la carpeta especificada en 'path' si no existe.
    
    Args:
        path (str): Ruta de la carpeta a crear.
    """
    if not os.path.exists(path):
        os.makedirs(path)


def get_chapter_number(path):
    # Lista todos los archivos en el directorio especificado
    archivos = os.listdir(path)

    max_num = 0
    pattern = re.compile(r'Cap(\d+)')

    for archivo in archivos:
        match = pattern.match(archivo)
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num

    return max_num + 1

def get_paths_save(rutas_vid, n_chapter=random.randint(1, 1000000)):

    n_chapter = int(datetime.now().strftime('%Y%m%d%H%M%S'))

    # 10 minutos por un video de
    ruta_audio = AUDIO_PATH+'/Background/background.mp3'
    ruta_audio = AUDIO_PATH+'/Background/Acelerado_Sonic The Hedgehog OST - Green Hill Zone.mp3'
    ruta_audio = AUDIO_PATH+'/Background/Pasarla bien_Menu - Cooking Mama Soundtrack.mp3'
    ruta_audio = AUDIO_PATH+'/Background/background.mp3'  # Actualiza esto con la ruta de tu archivo de audio


    rutas_horizontal = [ruta for ruta in rutas_vid if '/BetaH/' in ruta]
    rutas_vertical = [ruta for ruta in rutas_vid if '/BetaV/' in ruta]

    output_paths = [RENDER_PATH+'/Horizontal/',
                    RENDER_PATH+'/Vertical/',]

    rutas_ending = [AUDIO_PATH+'/Endings/END1.mp4',
                  AUDIO_PATH+'/Endings/END1_V.mp4']

    output_paths_start = [CLIPS_PATH+'/Caps_'+str(n_chapter)+'.mp4' for x in output_paths]
    output_paths = [x+'Caps_'+str(n_chapter)+'.mp4' for x in output_paths]

    return ruta_audio, output_paths, output_paths_start, rutas_ending


import os
import re
import json
from datetime import datetime

def clean_directory(directory):
    """
    Revisa los archivos JSON en el directorio y, para aquellos cuyo nombre contenga "_RENDERIZAR_",
    conserva únicamente el archivo más reciente (basado en la fecha en el nombre).
    
    Los archivos deben tener el formato:
      <titulo>_RENDERIZAR_<yyyymmddHHMMSS>.json
      
    Se eliminarán las versiones antiguas.
    
    Args:
        directory (str): Ruta al directorio donde se encuentran los archivos.
    
    Returns:
        set: Conjunto con los nombres de archivo que se han conservado.
    """
    # Patrón para extraer el título y la fecha
    pattern = re.compile(r"^(.*)_RENDERIZAR_(\d{14})\.json$")
    latest_files = {}

    for file_name in os.listdir(directory):
        match = pattern.match(file_name)
        if match:
            title, date_str = match.groups()
            try:
                date_obj = datetime.strptime(date_str, "%Y%m%d%H%M%S")
            except Exception as e:
                print(f"Error parsing date in {file_name}: {e}")
                continue

            # Si no existe o la fecha es más reciente, lo guardamos
            if title not in latest_files:
                latest_files[title] = (file_name, date_obj)
            else:
                existing_file, existing_date = latest_files[title]
                if date_obj > existing_date or (date_obj == existing_date and file_name > existing_file):
                    latest_files[title] = (file_name, date_obj)

    # Conjunto de archivos a conservar
    files_to_keep = {file_name for file_name, _ in latest_files.values()}

    # Elimina los archivos que no sean los más recientes
    for file_name in os.listdir(directory):
        # Procesa solo los que siguen el patrón
        if pattern.match(file_name) and file_name not in files_to_keep:
            file_path = os.path.join(directory, file_name)
            try:
                os.remove(file_path)
                print(f"Archivo eliminado: {file_name}")
            except Exception as e:
                print(f"Error eliminando {file_name}: {e}")

    print("Archivos conservados:")
    for file_name in sorted(files_to_keep):
        print(file_name)
    return files_to_keep

def mark_files_as_processed(directory):
    """
    Recorre los archivos en el directorio que contengan "RENDERIZAR" en su nombre, 
    modifica su contenido JSON actualizando el campo "status" a "procesado",
    y renombra el archivo reemplazando "RENDERIZAR" por "PROCESADO".
    
    Luego, se elimina el archivo original.
    
    Args:
        directory (str): Ruta al directorio donde se encuentran los archivos.
    """
    # Patrón para identificar archivos con "RENDERIZAR"
    pattern = re.compile(r"^(.*)_RENDERIZAR_(\d{14})\.json$")
    
    for file_name in os.listdir(directory):
        match = pattern.match(file_name)
        if match:
            file_path = os.path.join(directory, file_name)
            try:
                # Leer contenido JSON
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Actualizar el status a "procesado"
                data["status"] = "procesado"
                
                # Nuevo nombre de archivo: reemplazar "RENDERIZAR" por "PROCESADO"
                new_file_name = file_name.replace("RENDERIZAR", "PROCESADO")
                new_file_path = os.path.join(directory, new_file_name)
                
                # Guardar el contenido actualizado en el nuevo archivo
                with open(new_file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # Eliminar el archivo original
                os.remove(file_path)
                print(f"Archivo {file_name} renombrado y actualizado a {new_file_name}")
            except Exception as e:
                print(f"Error procesando {file_name}: {e}")

