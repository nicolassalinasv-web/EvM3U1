import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from config.settings import Configuracion
from src.texto.generador_local import GeneradorLocal
from src.audio.narrador_local import NarradorLocal
from tests.test_aplicacion import CUENTO

class TestOllama(unittest.TestCase):
    def setUp(self):
        self.config = Configuracion(Path.cwd(), "", False)
        self.generador = GeneradorLocal(self.config)
        cambio = patch("src.texto.generador_local.requests.Session")
        self.addCleanup(cambio.stop)
        self.sesion = cambio.start().return_value.__enter__.return_value
        self.respuesta = Mock(status_code=200)
        self.respuesta.json.return_value = {"done": True, "done_reason": "stop", "response": CUENTO}
        self.sesion.request.return_value = self.respuesta

    def test_texto_local_sin_clave_libera_modelo_para_imagen(self):
        self.assertEqual(self.generador.generar("Tema", "Contexto"), CUENTO)
        llamada = self.sesion.request.call_args
        self.assertEqual(llamada.args, ("POST", "http://127.0.0.1:11434/api/generate"))
        self.assertEqual(llamada.kwargs["json"]["keep_alive"], 0)
        self.assertFalse(llamada.kwargs["json"]["think"])
        self.assertFalse(self.sesion.trust_env)
        self.assertIn("Contexto: Contexto", llamada.kwargs["json"]["prompt"])

    def test_cuento_truncado_rechazado(self):
        self.respuesta.json.return_value = {"done": True, "done_reason":"length", "response":CUENTO}
        with self.assertRaises(RuntimeError): self.generador.generar("Tema", "Contexto")

    def test_modelo_cloud_rechazado(self):
        self.generador = GeneradorLocal(replace(self.config, modelo_local_texto="qwen:cloud"))
        with self.assertRaises((RuntimeError, ValueError)): self.generador.comprobar()
        self.sesion.request.assert_not_called()

    def test_servidor_remoto_rechazado(self):
        self.generador = GeneradorLocal(replace(self.config, ollama_url="https://example.com"))
        with self.assertRaises((RuntimeError, ValueError)): self.generador.comprobar()
        self.sesion.request.assert_not_called()

    def test_preflight_modelo_no_instalado(self):
        self.respuesta.json.return_value = {"models": []}
        with self.assertRaises(RuntimeError): self.generador.comprobar()

class TestPiper(unittest.TestCase):
    def test_voz_faltante_detectada(self):
        c = Configuracion(Path.cwd() / "modelo-no-existente", "", False)
        with self.assertRaises(ValueError): NarradorLocal(c).comprobar()

    def test_sintesis_local_y_conversion_mp3(self):
        n = NarradorLocal(Configuracion(Path.cwd(), "", False))
        def sintetizar(texto, wav):
            self.assertEqual(texto, CUENTO)
            wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(22050)
            wav.writeframes(b"\x00\x00" * 100)
        with patch.object(n, "comprobar"), patch("piper.PiperVoice.load") as cargar, \
                patch("src.audio.narrador_local.subprocess.run", return_value=SimpleNamespace(stdout=b"ID3-local")) as convertir:
            cargar.return_value.synthesize_wav.side_effect = sintetizar
            self.assertEqual(n.generar(CUENTO), b"ID3-local")
            self.assertFalse(cargar.call_args.kwargs["use_cuda"])
            self.assertIn("libmp3lame", convertir.call_args.args[0])

    def test_conversion_fallida_controlada(self):
        import subprocess
        n = NarradorLocal(Configuracion(Path.cwd(), "", False))
        def sintetizar(texto, wav):
            wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(22050)
            wav.writeframes(b"\x00\x00" * 100)
        with patch.object(n, "comprobar"), patch("piper.PiperVoice.load") as cargar, \
                patch("src.audio.narrador_local.subprocess.run", side_effect=subprocess.TimeoutExpired("ffmpeg",120)):
            cargar.return_value.synthesize_wav.side_effect = sintetizar
            with self.assertRaises(RuntimeError): n.generar(CUENTO)
