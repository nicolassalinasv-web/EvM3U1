import base64
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, MagicMock, patch
from dataclasses import replace
import requests
from config.settings import Configuracion
from config.client import FabricaClienteOpenAI
from src.texto.generador_cuento import GeneradorCuento
from src.audio.narrador_cuento import NarradorCuento
from src.imagen.ilustrador_openai import IlustradorOpenAI
from src.imagen.ilustrador_comfyui import IlustradorComfyUI
from tests.test_aplicacion import CUENTO, png

class TestOpenAI(unittest.TestCase):
    def setUp(self):
        self.clientes = MagicMock()
        self.c = self.clientes.abrir.return_value.__enter__.return_value = Mock()
        self.generador = GeneradorCuento(self.clientes, "modelo-prueba")
        self.c.responses.create.return_value = SimpleNamespace(status="completed", output_text=CUENTO)

    def test_prompt_incluye_tema_y_contexto(self):
        self.assertEqual(self.generador.generar("Tema", "Contexto", True), CUENTO)
        datos = self.c.responses.create.call_args.kwargs
        self.assertEqual(datos["input"], "Tema: Tema\nContexto: Contexto")

    def test_todos_los_proveedores_de_pago_exigen_autorizacion(self):
        for funcion in [lambda: self.generador.generar("Tema", "Contexto"),
                lambda: NarradorCuento(self.clientes, "audio", "voz").generar(CUENTO),
                lambda: IlustradorOpenAI(self.clientes, "imagen").generar(CUENTO)]:
            with self.assertRaises(ValueError): funcion()
        self.clientes.abrir.assert_not_called()

    def test_respuesta_vacia_o_incompleta(self):
        for estado, texto in [("incomplete", CUENTO), ("completed", " "), ("completed", None)]:
            self.c.responses.create.return_value = SimpleNamespace(status=estado, output_text=texto)
            with self.assertRaises(RuntimeError): self.generador.generar("Tema", "Contexto", True)

    def test_narracion_utiliza_solo_cuento(self):
        self.c.audio.speech.create.return_value.read.return_value = b"ID3-test"
        NarradorCuento(self.clientes, "audio", "voz").generar(CUENTO, True)
        self.assertEqual(self.c.audio.speech.create.call_args.kwargs["input"], CUENTO)

    def test_narracion_larga_no_envia(self):
        with self.assertRaises(ValueError): NarradorCuento(self.clientes, "audio", "voz").generar("a"*3001, True)
        self.clientes.abrir.assert_not_called()

    def test_imagen_openai_desde_cuento(self):
        self.c.images.generate.return_value = SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(png()).decode())])
        contenido = IlustradorOpenAI(self.clientes, "imagen").generar(CUENTO, True)
        self.assertEqual(contenido, png())
        self.assertIn(CUENTO, self.c.images.generate.call_args.kwargs["prompt"])

    def test_fabrica_configura_cero_reintentos(self):
        cfg = Configuracion(Path.cwd(), "ficticia", True)
        with patch("config.client.OpenAI") as constructor:
            with FabricaClienteOpenAI(cfg).abrir(): pass
            self.assertEqual(constructor.call_args.kwargs["max_retries"], 0)

    def test_sin_clave_no_crea_cliente(self):
        with patch("config.client.OpenAI") as constructor:
            with self.assertRaises(ValueError):
                with FabricaClienteOpenAI(Configuracion(Path.cwd(), "", True)).abrir(): pass
            constructor.assert_not_called()

class TestLocal(unittest.TestCase):
    def setUp(self):
        self.config = Configuracion(Path.cwd(), "")
        self.local = IlustradorComfyUI(self.config)
        cambio = patch("src.imagen.ilustrador_comfyui.requests.Session")
        self.addCleanup(cambio.stop)
        self.cliente = cambio.start().return_value.__enter__.return_value

    def respuesta(self, datos, contenido=b""):
        return Mock(status_code=200, json=Mock(return_value=datos), content=contenido)

    def terminado(self):
        return self.respuesta({"id": {"status": {"completed": True},
            "outputs": {"9": {"images": [{"filename": "moss.png"}]}}}})

    def test_local_sin_clave_prompt_y_descarga(self):
        original = self.config.workflow.read_bytes()
        self.cliente.request.side_effect = [self.respuesta({"prompt_id": "id"}), self.terminado(), self.respuesta({}, png())]
        self.assertEqual(self.local.generar(CUENTO), png())
        enviada = self.cliente.request.call_args_list[0]
        self.assertIn(CUENTO, enviada.kwargs["json"]["prompt"]["18:17"]["inputs"]["value"])
        self.assertEqual(self.config.workflow.read_bytes(), original)
        self.assertFalse(self.cliente.trust_env)
        self.assertFalse(enviada.kwargs["allow_redirects"])

    def test_timeout_no_reenvia_trabajo(self):
        self.cliente.request.side_effect = [self.respuesta({"prompt_id": "id"})]
        with patch("src.imagen.ilustrador_comfyui.time.monotonic", side_effect=[0,601]):
            with self.assertRaisesRegex(RuntimeError, "cola"): self.local.generar(CUENTO)
        self.assertEqual(self.cliente.request.call_count, 1)

    def test_rechazo_flujo(self):
        self.cliente.request.side_effect = [self.respuesta({"error": "fallo"})]
        with self.assertRaises(RuntimeError): self.local.generar(CUENTO)

    def test_error_ejecucion(self):
        self.cliente.request.side_effect = [self.respuesta({"prompt_id":"id"}),
            self.respuesta({"id":{"status":{"status_str":"error"}}})]
        with self.assertRaises(RuntimeError): self.local.generar(CUENTO)

    def test_conexion_apagada(self):
        self.cliente.request.side_effect = requests.ConnectionError()
        with self.assertRaises(RuntimeError): self.local.comprobar()

    def test_solo_loopback(self):
        self.local = IlustradorComfyUI(replace(self.config, comfyui_url="https://example.com"))
        with self.assertRaises(ValueError): self.local.comprobar()
        self.cliente.request.assert_not_called()

    def test_historial_malformado_controlado(self):
        self.cliente.request.side_effect = [self.respuesta({"prompt_id":"id"}), self.respuesta({"id": "invalido"})]
        with self.assertRaises(RuntimeError): self.local.generar(CUENTO)
