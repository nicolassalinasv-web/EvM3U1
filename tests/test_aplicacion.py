import json
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock
from PIL import Image
from src.aplicacion_cuentos import AplicacionCuentos
from src.gestor_archivos import GestorArchivos
from src.consola import ejecutar_consola

CUENTO = "La amistad del bosque. Un conejo compartió su manzana con una tortuga. Juntos aprendieron a ayudarse."

def png():
    buffer = BytesIO()
    Image.new("RGB", (8, 8), "green").save(buffer, format="PNG")
    return buffer.getvalue()

class CasoAplicacion(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.gestor = GestorArchivos(Path(self.temporal.name))
        self.generador = Mock()
        self.generador.generar.return_value = CUENTO
        self.local = Mock()
        self.local.generar.return_value = png()
        self.remoto = Mock()
        self.remoto.generar.return_value = png()
        self.narrador = Mock()
        self.narrador.generar.return_value = b"ID3-audio-simulado"
        self.generador_remoto = Mock()
        self.generador_remoto.generar.return_value = CUENTO
        self.narrador_remoto = Mock()
        self.narrador_remoto.generar.return_value = b"ID3-audio-remoto"
        self.app = AplicacionCuentos({"local": self.generador, "openai": self.generador_remoto},
            {"local": self.local, "openai": self.remoto},
            {"local": self.narrador, "openai": self.narrador_remoto}, self.gestor)

    def iniciar(self, proveedor="local"):
        return self.app.iniciar("Amistad", "Un bosque y dos amigos", proveedor, autorizado=True)

    def fallo_imagen(self):
        self.local.generar.side_effect = RuntimeError("Falla simulada")
        return self.iniciar()

    def test_completo_y_trazabilidad(self):
        r = self.iniciar()
        self.local.generar.assert_called_once_with(CUENTO, autorizado=True)
        r = self.app.narrar(r, autorizado=True)
        self.assertEqual(r.estado, "completo")
        self.assertEqual(r.proveedor_imagen, "local")
        self.narrador.generar.assert_called_once_with(CUENTO, autorizado=True)
        for ruta in (r.texto, r.imagen, r.audio):
            self.assertTrue(Path(ruta).stat().st_size)
            self.assertEqual(Path(ruta).stem, "cuento_" + r.identificador)
        texto = Path(r.texto).read_text(encoding="utf-8")
        self.assertIn("Tema: Amistad", texto)
        self.assertIn("Contexto: Un bosque y dos amigos", texto)
        self.assertIn(CUENTO, texto)
        registro = json.loads(self.gestor.ruta(r.identificador, "registro").read_text(encoding="utf-8"))
        self.assertEqual(registro["intentos_imagen"][0]["proveedor"], "local")
        self.remoto.generar.assert_not_called()

    def test_fallo_no_cambia_proveedor_ni_narra(self):
        r = self.fallo_imagen()
        self.assertEqual(r.estado, "error_imagen")
        self.assertTrue(Path(r.texto).exists())
        self.remoto.comprobar.assert_not_called()
        self.remoto.generar.assert_not_called()
        self.narrador.generar.assert_not_called()
        self.generador.generar.assert_called_once()

    def test_cambio_a_openai_exige_confirmacion_nueva(self):
        r = self.fallo_imagen()
        with self.assertRaises(ValueError):
            self.app.intentar_imagen(r, "openai")
        self.remoto.generar.assert_not_called()
        r = self.app.intentar_imagen(r, "openai", autorizado=True)
        self.assertEqual(r.proveedor_imagen, "openai")
        self.assertTrue(r.intentos[-1]["autorizacion_pago"])
        self.generador.generar.assert_called_once()

    def test_reintentar_local_conserva_cuento_e_id(self):
        r = self.fallo_imagen()
        ruta, identificador = r.texto, r.identificador
        self.local.generar.side_effect = None
        self.app.intentar_imagen(r, "local")
        self.assertEqual(r.estado, "imagen_lista")
        self.assertEqual((r.texto, r.identificador), (ruta, identificador))
        self.generador.generar.assert_called_once()

    def test_continuar_sin_imagen(self):
        r = self.fallo_imagen()
        self.app.narrar(r, autorizado=True)
        self.assertEqual(r.estado, "completo_sin_imagen")
        self.assertFalse(r.imagen)
        self.assertTrue(Path(r.audio).exists())
        self.remoto.generar.assert_not_called()

    def test_finalizar_no_envia_mas_solicitudes(self):
        r = self.fallo_imagen()
        self.app.finalizar(r)
        self.assertEqual(r.estado, "finalizado")
        self.narrador.generar.assert_not_called()
        self.remoto.generar.assert_not_called()
        with self.assertRaises(ValueError): self.app.intentar_imagen(r, "local")

    def test_proveedor_apagado_no_consume_texto(self):
        self.local.comprobar.side_effect = RuntimeError("Apagado")
        r = self.iniciar()
        self.assertEqual(r.estado, "error_disponibilidad")
        self.generador.generar.assert_not_called()

    def test_entradas_invalidas_no_consumen(self):
        for tema, contexto in [("", "Bosque"), ("Amistad", " "), (None, "Bosque")]:
            with self.subTest(tema=tema), self.assertRaises(ValueError):
                self.app.iniciar(tema, contexto, "local", autorizado=True)
        self.generador.generar.assert_not_called()
        self.local.comprobar.assert_not_called()

    def test_sin_autorizacion_no_envia(self):
        with self.assertRaises(ValueError):
            self.app.iniciar("Tema", "Contexto", "openai")
        self.generador.generar.assert_not_called()
        self.remoto.comprobar.assert_not_called()

    def test_cuento_vacio_detiene_dependientes(self):
        self.generador.generar.return_value = " "
        r = self.iniciar()
        self.assertEqual(r.estado, "error_cuento")
        self.local.generar.assert_not_called()
        self.narrador.generar.assert_not_called()

    def test_fallo_audio_conserva_cuento_e_imagen(self):
        r = self.iniciar()
        self.narrador.generar.side_effect = RuntimeError("Error")
        self.app.narrar(r, autorizado=True)
        self.assertEqual(r.estado, "error_audio")
        self.assertTrue(Path(r.texto).exists())
        self.assertTrue(Path(r.imagen).exists())
        self.app.narrar(r)  # El reintento local no requiere autorización de pago.

    def test_png_invalido_no_declara_exito(self):
        self.local.generar.return_value = b"no-es-png"
        r = self.iniciar()
        self.assertEqual(r.estado, "error_imagen")
        self.assertFalse(r.imagen)

    def test_no_repite_imagen_ya_completada(self):
        r = self.iniciar()
        with self.assertRaises(ValueError): self.app.intentar_imagen(r, "openai", autorizado=True)
        self.remoto.generar.assert_not_called()

    def test_consola_cancela_antes_de_consumir(self):
        entradas = iter(["1", "Tema", "Contexto", "CANCELAR"])
        ejecutar_consola(self.app, lambda _: next(entradas), lambda _: None)
        self.generador.generar.assert_not_called()

    def test_consola_cambio_cancelado_y_narracion_sin_imagen(self):
        self.local.generar.side_effect = RuntimeError("Falla")
        entradas = iter(["1", "Tema", "Contexto", "GENERAR", "2", "NO", "3"])
        r = ejecutar_consola(self.app, lambda _: next(entradas), lambda _: None)
        self.assertEqual(r.estado, "completo_sin_imagen")
        self.remoto.generar.assert_not_called()

    def test_consola_openai_completa(self):
        entradas = iter(["2", "Tema", "Contexto", "GENERAR"])
        r = ejecutar_consola(self.app, lambda _: next(entradas), lambda _: None)
        self.assertEqual(r.estado, "completo")
        self.remoto.generar.assert_called_once_with(CUENTO, autorizado=True)
        self.local.generar.assert_not_called()

    def test_modo_local_completo_sin_autorizacion_openai(self):
        r = self.app.iniciar("Tema", "Contexto", "local")
        self.app.narrar(r)
        self.assertEqual(r.estado, "completo")
        self.assertEqual((r.proveedor_texto, r.proveedor_imagen, r.proveedor_audio), ("local", "local", "local"))
        self.generador_remoto.comprobar.assert_not_called()
        self.generador_remoto.generar.assert_not_called()
        self.remoto.generar.assert_not_called()
        self.narrador_remoto.generar.assert_not_called()

    def test_modo_openai_usa_tres_proveedores_remotos(self):
        r = self.iniciar("openai")
        self.app.narrar(r, autorizado=True)
        self.assertEqual((r.proveedor_texto, r.proveedor_imagen, r.proveedor_audio), ("openai", "openai", "openai"))
        self.generador.generar.assert_not_called()
        self.narrador.generar.assert_not_called()

    def test_fallo_texto_local_no_recurre_a_openai(self):
        self.generador.generar.side_effect = RuntimeError("Falla")
        r = self.app.iniciar("Tema", "Contexto", "local")
        self.assertEqual(r.estado, "error_cuento")
        self.generador_remoto.generar.assert_not_called()
        self.local.generar.assert_not_called()

    def test_fallo_audio_local_no_recurre_a_openai(self):
        r = self.iniciar()
        self.narrador.generar.side_effect = RuntimeError("Falla")
        self.app.narrar(r)
        self.assertEqual(r.estado, "error_audio")
        self.narrador_remoto.generar.assert_not_called()
        self.assertTrue(Path(r.texto).is_file())
        self.assertTrue(Path(r.imagen).is_file())

    def test_excepcion_imagen_no_cambia_proveedor_audio(self):
        r = self.fallo_imagen()
        self.app.intentar_imagen(r, "openai", autorizado=True)
        self.app.narrar(r)
        self.assertEqual((r.proveedor_texto, r.proveedor_imagen, r.proveedor_audio), ("local", "openai", "local"))
        self.narrador_remoto.generar.assert_not_called()
