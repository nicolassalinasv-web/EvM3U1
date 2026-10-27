from config.client import FabricaClienteOpenAI
from src.aplicacion_cuentos import AplicacionCuentos
from src.texto.generador_cuento import GeneradorCuento
from src.texto.generador_local import GeneradorLocal
from src.gestor_archivos import GestorArchivos
from src.imagen.ilustrador_openai import IlustradorOpenAI
from src.imagen.ilustrador_comfyui import IlustradorComfyUI
from src.audio.narrador_cuento import NarradorCuento
from src.audio.narrador_local import NarradorLocal

def crear_aplicacion(configuracion):
    clientes = FabricaClienteOpenAI(configuracion)
    return AplicacionCuentos(
        {"openai": GeneradorCuento(clientes, configuracion.modelo_texto), "local": GeneradorLocal(configuracion)},
        {"local": IlustradorComfyUI(configuracion), "openai": IlustradorOpenAI(clientes, configuracion.modelo_imagen)},
        {"openai": NarradorCuento(clientes, configuracion.modelo_audio, configuracion.voz), "local": NarradorLocal(configuracion)},
        GestorArchivos(configuracion.base_dir))
