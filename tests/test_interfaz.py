from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from config.settings import Configuracion
import tests.test_aplicacion as casos
import unittest

class TestInterfaz(unittest.TestCase):
    setUp = casos.CasoAplicacion.setUp
    # Solo ejecuta las pruebas de interacción de esta clase; la base aporta fixtures.
    def interfaz(self, habilitar=True):
        cfg = Configuracion(Path(self.temporal.name), "ficticia" if habilitar else "", habilitar)
        configuracion = patch("config.settings.cargar_configuracion", return_value=cfg)
        fabrica = patch("src.fabrica.crear_aplicacion", return_value=self.app)
        configuracion.start(); fabrica.start()
        self.addCleanup(configuracion.stop); self.addCleanup(fabrica.stop)
        return AppTest.from_file(str(Path.cwd() / "app.py"), default_timeout=15).run()

    def boton(self, t, etiqueta):
        return next(b for b in t.button if b.label == etiqueta)

    def llenar(self, t):
        t.text_input[0].set_value("La amistad")
        t.text_area[0].set_value("Dos amigos en el bosque")
        return t

    def test_ui_no_genera_sin_confirmacion(self):
        t = self.llenar(self.interfaz())
        t.radio[0].set_value("openai").run()
        self.boton(t, "Generar material educativo").click().run()
        self.assertFalse(t.exception)
        self.assertTrue(t.error)
        self.generador.generar.assert_not_called()

    def test_ui_fallo_y_cambio_con_confirmacion(self):
        self.local.generar.side_effect = RuntimeError("Falla")
        t = self.llenar(self.interfaz())
        self.boton(t, "Generar material educativo").click().run()
        self.assertFalse(t.exception)
        self.assertEqual(t.session_state.resultado.estado, "error_imagen")
        self.remoto.generar.assert_not_called()
        self.boton(t, "Usar OpenAI para esta imagen").click().run()
        self.remoto.generar.assert_not_called()
        confirmar = next(c for c in t.checkbox if c.label.startswith("Confirmo una nueva"))
        confirmar.check()
        self.boton(t, "Usar OpenAI para esta imagen").click().run()
        self.assertFalse(t.exception)
        self.assertEqual(t.session_state.resultado.proveedor_imagen, "openai")
        self.generador.generar.assert_called_once()
        self.assertEqual(t.session_state.resultado.estado, "completo")
        t.run()
        self.remoto.generar.assert_called_once()
        self.narrador.generar.assert_called_once()

    def test_ui_finalizar_conserva_cuento(self):
        self.local.generar.side_effect = RuntimeError("Falla")
        t = self.llenar(self.interfaz())
        self.boton(t, "Generar material educativo").click().run()
        self.boton(t, "Finalizar conservando el cuento").click().run()
        self.assertFalse(t.exception)
        self.assertEqual(t.session_state.resultado.estado, "finalizado")
        self.narrador.generar.assert_not_called()

    def test_ui_local_no_necesita_clave_ni_confirmacion_pago(self):
        t = self.llenar(self.interfaz(False))
        self.assertEqual(t.radio[0].value, "local")
        self.assertEqual(len(t.checkbox), 0)
        self.boton(t, "Generar material educativo").click().run()
        self.assertFalse(t.exception)
        self.assertEqual(t.session_state.resultado.estado, "completo")
        self.generador_remoto.generar.assert_not_called()
        self.remoto.generar.assert_not_called()
        self.narrador_remoto.generar.assert_not_called()

    def test_ui_audio_falla_conserva_imagen_y_no_reintenta_solo(self):
        self.narrador.generar.side_effect = RuntimeError("Falla de audio local")
        t = self.llenar(self.interfaz(False))
        self.boton(t, "Generar material educativo").click().run()
        self.assertFalse(t.exception)
        self.assertEqual(t.session_state.resultado.estado, "error_audio")
        self.assertTrue(Path(t.session_state.resultado.texto).exists())
        self.assertTrue(Path(t.session_state.resultado.imagen).exists())
        t.run()
        self.narrador.generar.assert_called_once()
        self.narrador_remoto.generar.assert_not_called()

    def test_ui_openai_completa_tres_etapas_con_autorizacion(self):
        t = self.interfaz()
        t.radio[0].set_value("openai").run()
        self.llenar(t)
        t.checkbox[0].check()
        self.boton(t, "Generar material educativo").click().run()
        self.assertFalse(t.exception)
        self.assertEqual(t.session_state.resultado.estado, "completo")
        self.generador_remoto.generar.assert_called_once()
        self.remoto.generar.assert_called_once()
        self.narrador_remoto.generar.assert_called_once()
        t.run()
        self.narrador_remoto.generar.assert_called_once()
