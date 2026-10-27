import base64
import binascii
from src.validacion import exigir_autorizacion
from src.imagen.ilustrador_cuento import construir_prompt_visual

class IlustradorOpenAI:
    proveedor = "openai"
    def __init__(self, clientes, modelo):
        self.clientes = clientes
        self.modelo = modelo

    def comprobar(self):
        self.clientes.configuracion.validar_openai()

    def generar(self, cuento, autorizado=False):
        prompt = construir_prompt_visual(cuento)
        exigir_autorizacion(autorizado)
        with self.clientes.abrir() as c:
            respuesta = c.images.generate(model=self.modelo, prompt=prompt, n=1,
                quality="low", size="1024x1024", output_format="png")
        if not respuesta.data or not respuesta.data[0].b64_json:
            raise RuntimeError("OpenAI no devolvió una imagen.")
        try:
            return base64.b64decode(respuesta.data[0].b64_json, validate=True)
        except (binascii.Error, ValueError, TypeError) as error:
            raise RuntimeError("La imagen tiene codificación inválida.") from error
