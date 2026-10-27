from src.validacion import texto_util, exigir_autorizacion

class NarradorCuento:
    """Narra el cuento, sin metadatos ni mensajes técnicos."""
    def __init__(self, clientes, modelo, voz):
        self.clientes = clientes
        self.modelo = modelo
        self.voz = voz

    def comprobar(self):
        self.clientes.configuracion.validar_openai()

    def generar(self, cuento, autorizado=False):
        cuento = texto_util(cuento, "El cuento para narrar", 3000)
        exigir_autorizacion(autorizado)
        with self.clientes.abrir() as c:
            respuesta = c.audio.speech.create(model=self.modelo, voice=self.voz, input=cuento,
                instructions="Narra en español con voz cálida, pronunciación clara y ritmo tranquilo para niños.",
                response_format="mp3")
            contenido = respuesta.read()
        if not isinstance(contenido, bytes) or not contenido:
            raise RuntimeError("No se recibió audio utilizable.")
        return contenido
