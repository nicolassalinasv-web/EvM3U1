from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4
from src.validacion import texto_util, exigir_autorizacion
from src.imagen.ilustrador_cuento import IlustradorCuento
from typing import Mapping

@dataclass
class Resultado:
    tema: str
    contexto: str
    proveedor_elegido: str
    identificador: str = field(default_factory=lambda: uuid4().hex)
    creado: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    cuento: str = ""
    texto: str = ""
    imagen: str = ""
    audio: str = ""
    proveedor_imagen: str = ""
    proveedor_texto: str = ""
    proveedor_audio: str = ""
    estado: str = "nuevo"
    error: str = ""
    intentos: list = field(default_factory=list)

    def registro(self):
        return {"id": self.identificador, "creado_utc": self.creado,
            "tema": self.tema, "contexto": self.contexto,
            "proveedor_elegido": self.proveedor_elegido, "proveedor_imagen": self.proveedor_imagen,
            "proveedor_texto": self.proveedor_texto, "proveedor_audio": self.proveedor_audio,
            "estado": self.estado, "error": self.error,
            "archivos": {"texto": self.texto, "imagen": self.imagen, "audio": self.audio},
            "intentos_imagen": self.intentos}

class AplicacionCuentos:
    """Coordina objetos y decisiones, sin sustitución automática de proveedores."""
    def __init__(self, generadores, ilustradores: Mapping[str, IlustradorCuento], narradores, gestor):
        self.generadores = generadores
        self.ilustradores = ilustradores
        self.narradores = narradores
        self.gestor = gestor

    def _guardar(self, r):
        self.gestor.guardar_registro(r)
        return r

    def iniciar(self, tema, contexto, proveedor, autorizado=False):
        tema = texto_util(tema, "El tema", 200)
        contexto = texto_util(contexto, "El contexto", 2000)
        if proveedor not in self.ilustradores:
            raise ValueError("Selecciona un proveedor disponible.")
        if proveedor == "openai":
            exigir_autorizacion(autorizado)
        self.gestor.preparar()
        r = Resultado(tema, contexto, proveedor)
        try:
            for motor in (self.generadores[proveedor], self.ilustradores[proveedor], self.narradores[proveedor]):
                motor.comprobar()
        except (ValueError, RuntimeError, OSError) as error:
            r.estado = "error_disponibilidad"
            r.error = f"Un recurso del modo {proveedor} no está disponible. No se solicitó el cuento. {error}"
            return self._guardar(r)
        try:
            r.cuento = self.generadores[proveedor].generar(tema, contexto, autorizado=autorizado)
            r.cuento = texto_util(r.cuento, "El cuento", 6000)
            r.texto = str(self.gestor.guardar_texto(r.identificador, tema, contexto, r.cuento))
            r.proveedor_texto = proveedor
        except (ValueError, RuntimeError, OSError):
            r.estado = "error_cuento"
            r.error = "No se pudo generar o guardar un cuento válido. No se solicitaron imagen ni audio."
            if proveedor == "openai":
                r.error += " Una solicitud enviada puede consumir saldo."
            return self._guardar(r)
        r.estado = "cuento_listo"
        self._guardar(r)
        return self.intentar_imagen(r, proveedor, autorizado=autorizado)

    def intentar_imagen(self, r, proveedor, autorizado=False):
        if r.estado not in {"cuento_listo", "error_imagen"}:
            raise ValueError("No se permite solicitar otra imagen en este estado.")
        if proveedor not in self.ilustradores:
            raise ValueError("Proveedor desconocido.")
        if proveedor == "openai":
            exigir_autorizacion(autorizado)
        intento = {"proveedor": proveedor, "autorizacion_pago": proveedor == "openai" and autorizado is True,
                   "estado": "iniciado"}
        r.intentos.append(intento)
        r.error = ""
        self._guardar(r)
        try:
            ilustrador = self.ilustradores[proveedor]
            ilustrador.comprobar()
            contenido = ilustrador.generar(r.cuento, autorizado=autorizado)
            r.imagen = str(self.gestor.guardar_imagen(r.identificador, contenido))
        except (ValueError, RuntimeError, OSError):
            intento["estado"] = "error"
            r.estado = "error_imagen"
            r.error = ("No se completó la ilustración. El cuento se conserva. No hubo cambio automático de proveedor. "
                       "Si enviaste un trabajo local, revisa la cola de ComfyUI antes de reintentar: puede seguir ejecutándose. "
                       "Si elegiste OpenAI, la solicitud enviada puede consumir saldo.")
            return self._guardar(r)
        intento["estado"] = "completado"
        r.proveedor_imagen = proveedor
        r.estado = "imagen_lista"
        return self._guardar(r)

    def narrar(self, r, autorizado=False):
        if r.estado not in {"imagen_lista", "error_imagen", "error_audio"}:
            raise ValueError("No hay un cuento listo para narrar en este estado.")
        if r.proveedor_elegido == "openai":
            exigir_autorizacion(autorizado)
        r.error = ""
        try:
            contenido = self.narradores[r.proveedor_elegido].generar(r.cuento, autorizado=autorizado)
            r.audio = str(self.gestor.guardar_audio(r.identificador, contenido))
            r.proveedor_audio = r.proveedor_elegido
        except (ValueError, RuntimeError, OSError):
            r.estado = "error_audio"
            r.error = "No se pudo generar o guardar la narración. El cuento y la imagen disponible se conservan. Revisa longitud, configuración y servicio antes de reintentar."
            return self._guardar(r)
        r.estado = "completo" if r.imagen else "completo_sin_imagen"
        return self._guardar(r)

    def finalizar(self, r):
        r.estado = "finalizado"
        r.error = ""
        return self._guardar(r)
