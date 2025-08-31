# audio_utils.py
from tinytag import TinyTag
from mutagen.mp3 import MP3
from pydub import AudioSegment
from moviepy.editor import AudioFileClip
from elevenlabs import Voice, VoiceSettings, generate, play, save, voices, clone

import time
import pandas as pd
import sympy
import datetime
import os

# Se asume que la función buscar_archivos está definida en file_utils.py
from modules.character_manager import get_personajes_features
from modules.file_utils import buscar_archivos, buscar_en_indice
from config import AUDIO_PATH, valor_A, valor_B

def get_dict_voces():
  return {
    'Adam': 'pNInz6obpgDQGcFmaJgB',
    'Antoni': 'ErXwobaYiN019PkySvjV',
    'Arnold': 'VR6AewLTigWG4xSOukaG',
    'Bella': 'EXAVITQu4vr4xnSDxMaL',
    'Callum': 'N2lVS1w4EtoT3dr4eOWO',
    'Charlie': 'IKne3meq5aSn9XLyUdCD',
    'Charlotte': 'XB0fDUnXU5powFXDhCwa',
    'Clyde': '2EiwWnXFnvU5JabPnv8n',
    'Daniel': 'onwK4e9ZLuTAKqWW03F9',
    'Dave': 'CYw3kZ02Hs0563khs1Fj',
    'Domi': 'AZnzlk1XvdvUeBnXmlld',
    'Dorothy': 'ThT5KcBeYPX3keUQqHPh',
    'Elli': 'MF3mGyEYCl7XYWbV9V6O',
    'Emily': 'LcfcDJNUP1GQjkzn1xUU',
    'Ethan': 'g5CIjZEefAph4nQFvHAz',
    'Fin': 'D38z5RcWu1voky8WS1ja',
    'Freya': 'jsCqWAovK2LkecY7zXl4',
    'Gigi': 'jBpfuIE2acCO8z3wKNLl',
    'Giovanni': 'zcAOhNBS3c14rBihAFp1',
    'Glinda': 'z9fAnlkpzviPz146aGWa',
    'Grace': 'oWAxZDx7w5VEj9dCyTzz',
    'Harry': 'SOYHLrjzK2X1ezoPC6cr',
    'James': 'ZQe5CZNOzWyzPSCn5a3c',
    'Jeremy': 'bVMeCyTHy58xNoL34h3p',
    'Jessie': 't0jbNlBVZ17f02VDIeMI',
    'Joseph': 'Zlb1dXrM653N07WRdFW3',
    'Josh': 'TxGEqnHWrfWFTfGW9XjX',
    'Liam': 'TX3LPaxmHKxFdv7VOQHJ',
    'Matilda': 'XrExE9yKIg1WjnnlVkGX',
    'Matthew': 'Yko7PKHZNXotIFUBG7I9',
    'Michael': 'flq6f7yk4E4fJM5XTYuZ',
    'Mimi': 'zrHiDhphv9ZnVXBqCLjz',
    'Nicole': 'piTKgcLEGmPE4e6mEKli',
    'Patrick': 'ODq5zmih8GrVes37Dizd',
    'Rachel': '21m00Tcm4TlvDq8ikWAM',
    'Ryan': 'wViXBPUzp2ZZixB1xQuM',
    'Sam': 'yoZ06aMxZJJ28mfd3POQ',
    'Serena': 'pMsXgVXv3BLzUgSXRplE',
    'Thomas': 'GBv7mTt0atIp3Br8iCZE',
    'Sarah':'EXAVITQu4vr4xnSDxMaL'
  }


def extraer_informacion_audio(ruta):
    try:
        audio = MP3(ruta)
        detalles_audio = {
            "ruta": ruta,
            "duracion": audio.info.length,
            "bitrate": audio.info.bitrate,
            "frecuencia_muestreo": audio.info.sample_rate,
            "canales": audio.info.channels,
        }
    except Exception as e:
        print(f"[ERROR] Al extraer información de audio en '{ruta}': {e}")
        detalles_audio = {
            "ruta": ruta,
            "duracion": None,
            "bitrate": None,
            "frecuencia_muestreo": None,
            "canales": None,
        }
    return detalles_audio


def get_sonidos_rutas(sonidos_personas, audio_path=AUDIO_PATH, indice=None):
    """
    Dado un diccionario de sonidos (con nombres y rutas o lista de rutas),
    busca los archivos de audio en la ruta especificada en 'audio_path' utilizando
    la función buscar_archivos y retorna un diccionario con la información extraída.

    Parámetros:
      - sonidos_personas: Diccionario con claves que representan nombres y valores
                          que pueden ser una cadena o una lista de cadenas (nombres de sonidos).
      - audio_path: Ruta base donde buscar los archivos de audio.

    Retorna:
      Diccionario donde cada clave corresponde a una entrada de sonidos y el valor es
      una lista con la información extraída de cada archivo.
    """
    sonidos_rutas = {}
    for key, v in sonidos_personas.items():
        ls_rutas = []
        if isinstance(v, list):
            nombres = v
        else:
            nombres = [v]

        for nombre in nombres:
            nombre_agender = nombre.replace(' (man)', '').replace(' (woman)', '') \
                                    .replace(' (men)', '').replace(' (women)', '')
            if indice is not None:
                res_ = buscar_en_indice(indice, nombre_agender)
            else:
                res_ = buscar_archivos(audio_path, nombre_agender)

            if len(res_) == 0:
                print(key, ":" if not isinstance(v, list) else ":_", nombre)
            else:
                ls_rutas.append(extraer_informacion_audio(res_[0]))

        sonidos_rutas[key] = ls_rutas
    return sonidos_rutas

# def extraer_duracion_rapida(datos_audio):
#     """
#     Extrae la duración de archivos de audio usando pydub.
#     Recibe un diccionario con claves y rutas de archivos de audio, y retorna
#     un diccionario con la duración en segundos de cada archivo.
#     """
#     resultados = {}
#     for llave, ruta_mp3 in datos_audio.items():
#         try:
#             audio = AudioSegment.from_file(ruta_mp3)
#             duracion_segundos = len(audio) / 1000.0  # Conversión de ms a s
#             resultados[llave] = {
#                 "ruta_mp3": ruta_mp3,
#                 "duracion_segundos": duracion_segundos
#             }
#         except Exception as e:
#             print(f"Error al cargar el archivo {ruta_mp3}: {e}")
#             resultados[llave] = None
#     return resultados

def extraer_duracion_rapida(datos_audio):
    resultados = {}
    for llave, ruta_mp3 in datos_audio.items():
        try:
            tag = TinyTag.get(ruta_mp3)
            resultados[llave] = {
                "ruta_mp3": ruta_mp3,
                "duracion_segundos": tag.duration
            }
        except Exception as e:
            print(f"Error al cargar el archivo {ruta_mp3}: {e}")
            resultados[llave] = None
    return resultados

def asignar_audio_a_clips(lista_clips, lista_rutas_audio, modo_audio='cortar'):
    """
    Asigna archivos de audio a una lista de clips de video utilizando moviepy.
    
    Parámetros:
      - lista_clips: Lista de objetos VideoFileClip.
      - lista_rutas_audio: Lista de rutas a archivos de audio.
      - modo_audio: 'cortar' para recortar el audio a la duración del clip,
                    'bucle' para repetir el audio hasta completar la duración del clip,
                    'audio corto' para dejarlo sin cambios.
    
    Retorna la lista de clips con el audio asignado.
    """
    
    clips_con_audio = []
    for clip, ruta_audio in zip(lista_clips, lista_rutas_audio):
        audio_clip = AudioFileClip(ruta_audio)
        if modo_audio == 'cortar':
            if audio_clip.duration > clip.duration:
                audio_clip = audio_clip.subclip(0, clip.duration)
        elif modo_audio == 'bucle':
            audio_clip = audio_clip.loop(duration=clip.duration)
        elif modo_audio == 'audio corto':
            pass  # No se realizan modificaciones
        clip = clip.set_audio(audio_clip)
        clips_con_audio.append(clip)
    return clips_con_audio


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
                  '…':'Silencio',#Aaaah… Aaaah…
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
  'Hmm': ['Minecraft Villager (huh) - Sound Effect'],#,'KAHOOT Music (10 Second Countdown) 3_3'
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
                  '...':'Cricket Sound',
                  '…':'Silencio',
                  '':'silencio_medio_segundo'
                  }

  return onomato_idea, Ambiente, sonidos_personas


def imprimir_dialogs(escenas_info, personajes, sust_dd, verbose=False):
  onomato_idea, Ambiente, sonidos_personas = get_onomatos()
  personajes_car = get_personajes_features()
  dialogos_pers = []

  personajes_animales = pd.Series(personajes).replace(sust_dd).tolist()

  ret_dialog = {}
  for per in personajes:
    dialogos = []


    for llave, lista in escenas_info.items():
      orden = 0
      for dialogo in lista[4]:
        if per in lista[0]:
          dialogos.append(dialogo['Diálogo'])
          ret_dialog[(llave,orden, per)] = dialogo['Diálogo']
          orden += 1
          dialogos = [x for x in dialogos if x not in onomato_idea.keys()]
          dialogs = '...\n.\n'.join(dialogos)

    nombre_voz = list(personajes_car[personajes_car['Personajes']==sust_dd[per]]['Voz'].values)
    # print(nombre_voz)

    if len(nombre_voz)==0:
      voce = 'noname'
    else:
      voce = nombre_voz[0]

    dialogos_pers.append('%s\n'%(voce)+dialogs+'\n')
  if verbose:
    [print(x) for x in dialogos_pers]

  return {sk:ret_dialog[sk] for sk in sorted(ret_dialog.keys())}


def ordenar_diccionario_por_llave(diccionario):
  """
  Ordena un diccionario por sus llaves.

  Args:
      diccionario: El diccionario a ordenar.

  Returns:
      Un nuevo diccionario ordenado por sus llaves.
  """

  # Obtener las llaves del diccionario y ordenarlas
  llaves_ordenadas = sorted(diccionario.keys())

  # Crear un nuevo diccionario ordenado
  diccionario_ordenado = {}

  # Agregar los elementos del diccionario original al nuevo diccionario en orden
  for llave in llaves_ordenadas:
    diccionario_ordenado[llave] = diccionario[llave]

  return diccionario_ordenado

def actualizar_duracion_escenas(info_escenas, duraciones_calculadas):
    # Actualizar la duración de cada escena en el diccionario info_escenas
    for escena, info in info_escenas.items():
        if escena in duraciones_calculadas:
            # Convertir la duración en segundos a un formato de cadena con ' segundos'
            info[1] = duraciones_calculadas[escena]

    return info_escenas

def get_day_of_year():
  today = datetime.date.today()
  day_of_year = today.timetuple().tm_yday
  return day_of_year

def suma_digitos_factores_primos(n):
    factores = sympy.factorint(n)
    suma_digitos = sum(int(digit) for factor in factores for digit in str(factor) * factores[factor])
    return suma_digitos

def transformar_dialogo_acctime(diccionario_original):
    # Crear un diccionario vacío para almacenar el resultado
    resultado = {}

    # Recorrer cada entrada en el diccionario original
    for clave, valor in diccionario_original.items():
        # Extraer la escena y el diálogo
        escena = clave[0]
        dialogo = round(valor, 2)  # Redondear el valor a 2 decimales

        # Si la escena no está en el diccionario de resultado, agregarla con una lista vacía
        if escena not in resultado:
            resultado[escena] = []

        # Agregar el diálogo a la lista correspondiente de la escena
        resultado[escena].append(dialogo)

    return resultado

def create_folder(path):
  if not os.path.exists(path):
    os.makedirs(path)

def AUDIOS(personajes_car, info_dialogos, onomato_idea, api_key, sust_dd):

  Dialogos_con_voz = {(llave[0],llave[1],personajes_car[personajes_car['Personajes']==sust_dd[llave[2]]]['Voz'].values[0]):
  valor for llave, valor in info_dialogos.items() if valor not in onomato_idea.keys()}

  Dialogos_onomatos = {(llave[0],llave[1],personajes_car[personajes_car['Personajes']==sust_dd[llave[2]]]['Voz'].values[0]):
  valor for llave, valor in info_dialogos.items() if valor in onomato_idea.keys()}

  diccionario_voces = get_dict_voces()

  audios_generados = {}
  for llave, dialogo in Dialogos_con_voz.items():
    print('Procesando diálogo: '+ dialogo)
    # print(llave)
    if llave[2] in diccionario_voces.keys():
      time.sleep(6)
      voice_id = diccionario_voces[llave[2]]
      try:
        audio_t2 = generate(
            text=dialogo,
            voice=Voice(voice_id=voice_id,
                        settings=VoiceSettings(stability=.78, similarity_boost=0.91, 
                                               style=0.0, use_speaker_boost=True)),
            model='eleven_multilingual_v2')
      except:
        print('Se está usando la API')
        audio_t2 = generate(
            text=dialogo,
            voice=Voice(voice_id=voice_id,
                        settings=VoiceSettings(stability=.78, similarity_boost=0.91, 
                                               style=0.0, use_speaker_boost=True)),
            model='eleven_multilingual_v2',api_key=api_key)
    else:
      audio_t2 = generate(text=dialogo,
                  voice=llave[2],
                  model='eleven_multilingual_v2',
                  api_key=api_key)

    audios_generados[llave] = audio_t2

  personajes_aud_path = 'Audios_personajes'
  create_folder(personajes_aud_path)

  ruta_audios = {}

  for llave, audio in audios_generados.items():
    nombre_guardado = personajes_aud_path+'/'+'-'.join([str(k) for k in (llave)]) + '.mp3'
    save(audio,nombre_guardado)
    ruta_audios[llave] = nombre_guardado

  return ruta_audios, audios_generados, Dialogos_onomatos, Dialogos_con_voz


def renderizar_audios(escenas_info_, personajes_car, onomato_idea, personajes, sust_dd):
    onomato_idea, Ambiente, sonidos_personas = get_onomatos()
    # Colocar los nombres asignados
    info_dialogos = imprimir_dialogs(escenas_info_, personajes, sust_dd)
    sonidos_rutas = get_sonidos_rutas(sonidos_personas)
    
    # APK = valor_A if suma_digitos_factores_primos(get_day_of_year()) % 2 == 0 else valor_B
    APK = valor_A

    ruta_audios, audios_generados, Dialogos_onomatos, Dialogos_con_voz = AUDIOS(personajes_car,
                                                                                info_dialogos,
                                                                                onomato_idea,
                                                                                APK,
                                                                                sust_dd)

    caract_audios = extraer_duracion_rapida(ruta_audios)
    dialogo_dur = {key: val['duracion_segundos'] for key, val in caract_audios.items()}
    onomatos_dur = {key: sonidos_rutas[val][0]['duracion'] for key, val in Dialogos_onomatos.items()}
    dialogo_dur.update(onomatos_dur)
    dialogo_dur = ordenar_diccionario_por_llave(dialogo_dur)
    escenas_info = actualizar_duracion_escenas(escenas_info_, transformar_dialogo_acctime(dialogo_dur))

    return escenas_info, Dialogos_onomatos, Dialogos_con_voz, audios_generados, ruta_audios

