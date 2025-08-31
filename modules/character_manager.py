import os
import pandas as pd
import re
import json
from PIL import Image

# Se asume que estos módulos se han creado en la estructura propuesta
from modules.file_utils import get_folder_content
from modules.utils import get_sentimientos

from openai import OpenAI

from config import PERSONAJES_PATH, OPENAI_API_KEY


import logging

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,  # Cambia a logging.DEBUG para ver más detalles
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def reflejar_imagenes(df, max_workers=4):
    """Genera imágenes reflejadas en paralelo para las filas con mirada 'right'."""
    from concurrent.futures import ThreadPoolExecutor

    def procesar(row):
        if row['Mirada'] != 'right':
            return
        ruta_imagen = row['Ruta']
        nombre_imagen = row['Nombre']
        ruta_carpeta, _ = os.path.split(ruta_imagen)
        nuevo_nombre = 'Correct_' + nombre_imagen.replace('right', 'left')
        nueva_ruta = os.path.join(ruta_carpeta, nuevo_nombre)
        if os.path.exists(nueva_ruta):
            return
        try:
            with Image.open(ruta_imagen) as imagen:
                imagen.transpose(Image.FLIP_LEFT_RIGHT).save(nueva_ruta, 'PNG')
        except FileNotFoundError:
            print(f"No se encontró la imagen en la ruta {ruta_imagen}")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        list(executor.map(procesar, [row for _, row in df.iterrows()]))


def get_personajes_features():
    path_per = './media/personajes/Descripciones/Avances_Personajes_Memorias_de_7.csv'
    
    personajes_car = pd.read_csv(path_per)
    return personajes_car

def extraer_personajes_contexto(contexto):
    """
    Extrae la lista de personajes (LP) del contexto.
    Se espera que el contexto tenga líneas donde cada personaje
    aparece al inicio, seguido de un paréntesis con detalles.
    Ejemplo de línea:
    "Cactus (Sexo: H, Rango: Senior): Algo narcisista, Incompetente, ..."
    """
    personajes = []
    # Separa el contexto por líneas
    for linea in contexto.splitlines():
        # Ignora la línea que introduce la LP
        if linea.startswith("Aquí"):
            continue
        # Si la línea contiene '(', extrae el nombre antes del paréntesis
        if "(" in linea:
            nombre = linea.split("(")[0].strip()
            if nombre:
                personajes.append(nombre)
    return personajes

def get_dict_personajes_(ESCENAS_, contexto, verbose=True):
    client = OpenAI(api_key=OPENAI_API_KEY,)
    # Extraer personajes que participan en el diálogo
    dialogue_personajes = list(set([item for sublist in [c for a, b, c in ESCENAS_] for item in sublist]))
    pepepersonas = ', '.join(dialogue_personajes)
    print("Personajes en diálogo:", pepepersonas)
    
    # Extraer la lista de personajes (LP) del contexto
    lp_personajes = extraer_personajes_contexto(contexto)
    print("Personajes en LP:", ', '.join(lp_personajes))
    
    # Crear un diccionario auxiliar para mapear versiones en minúsculas a su versión original en la LP
    lp_dict = {nombre.lower(): nombre for nombre in lp_personajes}
    
    # Verificar de forma insensible a mayúsculas/minúsculas si todos los personajes del diálogo están en la LP
    if set([p.lower() for p in dialogue_personajes]).issubset(set(lp_dict.keys())):
        logging.info("Todos los personajes ya están en la LP. No se llama a la API.")
        # Mapear cada personaje del diálogo a la versión original encontrada en la LP
        return {p: lp_dict.get(p.lower(), p) for p in dialogue_personajes}
    
    # Se genera el diálogo completo
    Dialogo_completo = '\n'.join([
        extraer_dialogos_con_sentimientos(escenas_info_)
        for escenas_info_, sentimientos, personajes in ESCENAS_
    ])
    
    # Primero, obtener el diccionario de jerarquías
    mensajes_jerarquia = [
        {"role": "system", "content": "Eres un asistente que ayuda a identificar la jerarquía laboral entre personajes según el contexto del diálogo. Analiza el tono, el contenido y las interacciones para determinar la jerarquía. Los personajes pueden tener la misma jerarquía."},
        {"role": "user", "content": f"Basándote en el siguiente diálogo, asigna una jerarquía laboral a los personajes {pepepersonas}. Usa números donde 0 es el nivel más bajo y 9 es el nivel más alto. Solo devuelve el diccionario tipo python con la asignación de jerarquías y nada más.\n\nDiálogo:\n{Dialogo_completo}"}
    ]
    
    diccionario_jerarquico = get_diccionario_jerarquico(mensajes_jerarquia)
    
    # Ahora se construye el mensaje para obtener el emparejamiento de personajes
    mensajes = [
        {"role": "system", "content": "Eres un asistente que ayuda a emparejar diálogos con los personajes que mejor se ajusten según sus características, rango laboral y sentimientos"},
        {"role": "user", "content": f"{contexto}"},
        {"role": "user", "content": f"Crea un diccionario en una sola línea donde las llaves sean los personajes del diálogo ({pepepersonas}) y los valores sean los nombres de la lista de personajes (LP) que mejor se ajusten a cada parte del diálogo. Solo devuelve el diccionario y solo el diccionario, sin explicaciones adicionales.\nLas posiciones son:\n{str(diccionario_jerarquico).replace('{','').replace('}','')}.\nDiálogo:\n{Dialogo_completo}"}
    ]
    logging.info("Esperando a OpenAI")
    # Solicitar la asignación de personajes a la API
    respuesta = client.chat.completions.create(
        model="o1",#"gpt-4-turbo"
        messages=mensajes
    )
    respuesta_completa = respuesta.choices[0].message.content
    if verbose:
        print(respuesta_completa)
    
    respuesta_completa = respuesta_completa.replace("'", '"').replace("\n", '').replace("json", '')
    
    sust_dd = json.loads(respuesta_completa)
    
    return sust_dd


def get_diccionario_jerarquico(mensajes_jerarquia):
    
    client = OpenAI(api_key=OPENAI_API_KEY,)
    # Crear una solicitud de finalización de chat
    respuesta_jerarquia = client.chat.completions.create(
        model="o1",#"gpt-4-turbo" (No funcionó: gpt-4.0-o1), o1
        messages=mensajes_jerarquia,
        # temperature=0.05
    )
    
    # Convertir jerarquía
    diccionario_jerarquico = convertir_jerarquia(respuesta_jerarquia.choices[0].message.content)
    return diccionario_jerarquico

def convertir_jerarquia(string):
    # Limpiar el string utilizando una expresión regular para mantener solo el contenido dentro de {}
    match = re.search(r'\{.*\}', string, re.DOTALL)
    if match:
        string_limpio = match.group(0)
    else:
        raise ValueError("No se encontró un contenido válido entre llaves {} en el string proporcionado.")

    # Convertir el string limpio en un diccionario
    # diccionario = json.loads(string_limpio)
    string_limpio = string_limpio.replace("'", '"')
    diccionario = json.loads(string_limpio)

    # Ordenar los nombres por los valores de mayor a menor
    ordenados = sorted(diccionario.items(), key=lambda item: item[1], reverse=False)

    # Crear una lista de etiquetas jerárquicas
    etiquetas_base = ["inferior", "superior", "superior superior"]

    # Generar etiquetas adicionales si es necesario
    while len(etiquetas_base) < len(ordenados):
        etiquetas_base.append(f"superior {'superior ' * (len(etiquetas_base) - 1)}")

    # Crear el nuevo diccionario jerárquico
    diccionario_jerarquico = {}

    # Asignar etiquetas jerárquicas
    last_value = None
    etiqueta_index = 0

    for i, (nombre, valor) in enumerate(ordenados):
        if last_value is not None and valor == last_value:
            diccionario_jerarquico[nombre] = etiquetas_base[etiqueta_index - 1]
        else:
            diccionario_jerarquico[nombre] = etiquetas_base[etiqueta_index]
            etiqueta_index += 1
        last_value = valor

    return diccionario_jerarquico

def extraer_dialogos_con_sentimientos(lista_escenas):
    onomato_idea, Ambiente, sonidos_personas = get_onomatos()
    dialogos = []
    onomats = list(onomato_idea.keys())
    for escena, detalles in lista_escenas.items():
        personaje = detalles[0]
        sentimiento = detalles[2][0]  # Sentimiento principal
        dialogos_escena = detalles[4]

        for dialogo in dialogos_escena:
            dialogo_texto = dialogo['Diálogo']
            if dialogo_texto in onomats:
                continue

            dialogos.append(f"{personaje} ({sentimiento}) : {dialogo_texto}")

    return "\n".join(dialogos)


def get_onomatos():
  onomato_idea = {'Snif, snif': 'Llorar o sollozar.',
                  'Cof, cof': 'Toser.',
                  '¿Eh?': 'Confusión.',
                  'Zzzz': 'Dormir.',
                  'Hmm': 'Duda o pensamiento.',
                  'Shhh': 'Pedir silencio.',
                  'Jaja': 'Risa en texto.',
                  'Ay': 'Sorpresa o dolor leve.',
                  'Eh': 'Llamar la atención o sorpresa.',
                  '¡Uh!': 'Golpe',
                  'Bu': 'Asustar o indicar sorpresa.',
                  'Uh-oh': 'Preocupación o error.',
                  'Tsk, tsk': 'Desaprobación o disgusto.',
                  'Huh': 'Confusión o sorpresa leve.',
                  'Brrr': 'Indicar frío.',
                  'Achoo': 'Estornudo.',
                  'Boo': 'Desaprobación o abucheo.',
                  'Ahhhh': 'Descanso o placer.',
                  'Yay': 'Alegría o celebración.',
                  'Eek': 'Miedo o sorpresa.',
                  'Psst': 'Llamar la atención sigilosamente.',
                  'Ugh': 'Desagrado.',
                  '¡Aha!': 'Surge una idea',
                  'Wow': 'Sorprendente',
                  '¡Ah...!': 'Bostezo',
                  'Gruñido': 'Expresión de disgusto o enfado.',
                  'Braaaack': 'Eructo',
                  'Prrrrt': 'Sonido de pedo',
                  'Dum!': 'Suspenso',
                  'Bip bip': 'Censura',
                  ':(':'Tristeza',
                  '...':'Silencio',
                  '':'Silencio'}

  Ambiente = {'Bosque':'ambiente de bosque por la mañana',
              'Teclados': 'Efecto de sonido escribiendo en teclado pc',
              'Poco Tráfico':'ambiente de ciudad poco trafico',
              'Ciudad noche':'ambiente de ciudad residencial de noche',
              'Tráfico pesado': 'ambiente de ciudad, trafico',
              'Oficina':'ambiente de oficina 2',
              'Correos':'ambiente de correos',
              'Gente pasando':'ambiente peatonal pasos',
              'Se abre puerta': 'puerta de madera chirrido',
              'Sala de juntas':'proyector de diapositiva'}

  sonidos_personas = {'Snif, snif': 'Sniffing Sound Effect',
  'Cof, cof': ['cof_corto_hombre (man)',
    'cof_woman (woman)'],
  '¿Eh?': ['Microsoft Windows XP Error'],
  'Zzzz': ['Roncar Ronquidos Efecto (man)',
    'Mujer que Ronca - Efecto de Sonido (HD) (woman)'],
  'Hmm': ['Minecraft Villager (huh) - Sound Effect'],#    'KAHOOT Music (10 Second Countdown) 3_3'
  'Shhh': 'shhhhhhhhh sound',
  'Jaja': ['Ha Sound Effect (man)', 'Risa de ibai'],
  'Ay': 'Duck Toy Squeak Dog Toy Sound Effect (download)',
  'Eh': ['Eh', 'MSN Sound'],
  '¡Uh!': ['ROBLOX Oof Sound Effect', 'Impact sound shitpost'],
  'Bu': 'Spongebob Boo-womp Sound Effect',
  'Uh-oh': ['ROBLOX Oof Sound Effect'],
  'Tsk, tsk': 'Tsk Tsk (Solo el final)',
  'Huh': ['Duck Quack Sound Effect', 'Playstation 2 Startup Noise'],
  'Brrr': 'Freezing cold (Sound Effect)',
  'Achoo': ['mujer que estornuda (women)', 'Sneeze Sound Effect #2 (men)'],
  'Boo': 'SpongeBob Music Hawaiian',
  'Ahhhh': ['Funny Turtle Vine', 'Panting', 'Old Spice Silbido - Efecto de sonido'],
  'Yay': 'Angel - Sound Effect (HD)',
  'Eek': ['Moai sound', 'música perturbadora', 'FNAF ambiente 2'],
  'Psst': 'Psst sound effect (DOORS)',
  'Ugh': ['Diarrea - efecto de sonido (shitpost)',
    'Sonido de perturbación-incomodidad'],
  '¡Aha!': ['Microsoft Windows XP Startup Sound',
    'Windows 11 Startup Sound',
    'Microsoft Windows 95 sonido de inicio'],
  'Wow': 'Wow sound effect',
  '¡Ah...!': ['Sonido bostezo (women)', 'Hombre bostezando (man)'],
  'Gruñido': 'Gruñido de Monstruo Sonido',
  'Braaaack': 'eructos',
  'Prrrrt': ['Fart with reverb sound effect'],
  'Dum!': 'Impact sound shitpost',
  'Bip bip': 'Censor - Sound Effect (HD)',
  ':(': 'Poppy Playtime Theme',
                  '...':'silencio_medio_segundo',
                  '':'silencio_medio_segundo'
                  }

  return onomato_idea, Ambiente, sonidos_personas
