import os
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import modules.file_utils as fu
import modules.audio_utils as au


def _create_dummy_audio(dir_path):
    # create a fake mp3 file
    file_path = os.path.join(dir_path, "sonido.mp3")
    with open(file_path, "w") as f:
        f.write("dummy")
    return file_path


def test_buscar_archivos_caches_walk():
    with TemporaryDirectory() as tmp:
        _create_dummy_audio(tmp)
        fu.limpiar_indices()
        with patch("modules.file_utils.os.walk", wraps=os.walk) as mock_walk:
            fu.buscar_archivos(tmp, "sonido")
            assert mock_walk.call_count == 1
            fu.buscar_archivos(tmp, "sonido")
            assert mock_walk.call_count == 1


def test_get_sonidos_rutas_uses_cache():
    with TemporaryDirectory() as tmp:
        _create_dummy_audio(tmp)
        fu.limpiar_indices()
        sonidos = {"p1": "sonido"}
        with patch("modules.audio_utils.extraer_informacion_audio", lambda r: {"ruta": r}), \
             patch("modules.file_utils.os.walk", wraps=os.walk) as mock_walk:
            au.get_sonidos_rutas(sonidos, audio_path=tmp)
            assert mock_walk.call_count == 1
            au.get_sonidos_rutas(sonidos, audio_path=tmp)
            assert mock_walk.call_count == 1


def test_get_sonidos_rutas_with_precomputed_index():
    with TemporaryDirectory() as tmp:
        _create_dummy_audio(tmp)
        fu.limpiar_indices()
        sonidos = {"p1": "sonido"}
        with patch("modules.audio_utils.extraer_informacion_audio", lambda r: {"ruta": r}), \
             patch("modules.file_utils.os.walk", wraps=os.walk) as mock_walk:
            indice = fu.obtener_indice(tmp)
            mock_walk.reset_mock()
            au.get_sonidos_rutas(sonidos, audio_path=tmp, indice=indice)
            assert mock_walk.call_count == 0
