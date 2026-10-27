import json
import secrets
import time
from uuid import uuid4
import requests
from src.imagen.ilustrador_cuento import construir_prompt_visual

def _solicitar(cliente, metodo, url, **kwargs):
    try:
        respuesta = cliente.request(metodo, url, allow_redirects=False, **kwargs)
        respuesta.raise_for_status()
        if 300 <= respuesta.status_code < 400:
            raise RuntimeError("ComfyUI devolvió una redirección inesperada.")
        return respuesta
    except requests.RequestException as error:
        raise RuntimeError(
            "No se pudo completar la solicitud a ComfyUI. Abre tu instancia local "
            "y revisa COMFYUI_URL y los errores del flujo. "
            "Si la solicitud ya se envió, podría seguir en la cola; revísala antes de repetir."
        ) from error


def _json(respuesta):
    try:
        datos = respuesta.json()
        if not isinstance(datos, dict):
            raise ValueError()
        return datos
    except ValueError as error:
        raise RuntimeError("ComfyUI devolvió una respuesta JSON inválida.") from error


class IlustradorComfyUI:
    proveedor = "local"
    def __init__(self, configuracion):
        self.configuracion = configuracion

    def _flujo(self):
        self.configuracion.validar_local()
        try:
            flujo = json.loads(self.configuracion.workflow.read_text(encoding="utf-8"))
            for nodo, tipo in {"18:17": "PrimitiveStringMultiline", "18:7": "KSampler", "9": "SaveImage"}.items():
                if flujo[nodo]["class_type"] != tipo or not isinstance(flujo[nodo]["inputs"], dict):
                    raise ValueError()
            return flujo
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise ValueError("Revisa el flujo API de MOSS en config/moss_api.json.") from error

    def comprobar(self):
        self._flujo()
        with requests.Session() as cliente:
            cliente.trust_env = False
            datos = _json(_solicitar(cliente, "GET", self.configuracion.comfyui_url + "/system_stats", timeout=10))
            if "system" not in datos:
                raise RuntimeError("La dirección no corresponde a ComfyUI.")

    def generar(self, cuento, autorizado=False):
        flujo = self._flujo()
        flujo["18:17"]["inputs"]["value"] = construir_prompt_visual(cuento)
        flujo["18:7"]["inputs"]["seed"] = secrets.randbelow(2**53)
        url = self.configuracion.comfyui_url
        with requests.Session() as cliente:
            cliente.trust_env = False
            datos = _json(_solicitar(cliente, "POST", url + "/prompt", timeout=30,
                json={"prompt": flujo, "client_id": uuid4().hex}))
            prompt_id = datos.get("prompt_id")
            if datos.get("error") or datos.get("node_errors") or not isinstance(prompt_id, str) or not prompt_id:
                raise RuntimeError("ComfyUI rechazó el flujo. Revisa nodos y modelos.")
            limite = time.monotonic() + self.configuracion.comfyui_timeout
            while True:
                restante = limite - time.monotonic()
                if restante <= 0:
                    raise RuntimeError("Terminó la espera local. Revisa la cola antes de reintentar.")
                datos = _json(_solicitar(cliente, "GET", url + "/history/" + prompt_id, timeout=min(15, restante)))
                trabajo = datos.get(prompt_id)
                if trabajo:
                    if not isinstance(trabajo, dict):
                        raise RuntimeError("Historial de ComfyUI inválido.")
                    estado = trabajo.get("status", {})
                    salidas = trabajo.get("outputs", {})
                    if not isinstance(estado, dict) or not isinstance(salidas, dict):
                        raise RuntimeError("Estado de ComfyUI inválido.")
                    if estado.get("status_str") == "error":
                        raise RuntimeError("La generación de MOSS falló.")
                    salida = salidas.get("9", {})
                    if not isinstance(salida, dict):
                        raise RuntimeError("Salida de ComfyUI inválida.")
                    imagenes = salida.get("images", [])
                    if not isinstance(imagenes, list):
                        raise RuntimeError("Listado de imágenes inválido.")
                    if imagenes:
                        imagen = imagenes[0]
                        if not isinstance(imagen, dict) or not imagen.get("filename"):
                            raise RuntimeError("Referencia de imagen inválida.")
                        return _solicitar(cliente, "GET", url + "/view", timeout=30,
                            params={"filename": imagen["filename"], "subfolder": imagen.get("subfolder", ""),
                                    "type": imagen.get("type", "output")}).content
                    if estado.get("completed"):
                        raise RuntimeError("MOSS terminó sin una imagen guardada.")
                time.sleep(min(1, max(0, limite - time.monotonic())))
