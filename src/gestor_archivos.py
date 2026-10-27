import json
from io import BytesIO
from pathlib import Path
from PIL import Image

class GestorArchivos:
    """Persistencia con ID común y comprobación de los archivos."""
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.outputs = self.base_dir / "outputs"

    def preparar(self):
        for carpeta in ("textos", "imagenes", "audios", "registros"):
            (self.outputs / carpeta).mkdir(parents=True, exist_ok=True)

    def ruta(self, identificador, tipo):
        if not identificador or not identificador.isalnum():
            raise ValueError("Identificador inválido.")
        carpeta, extension = {"texto": ("textos", "txt"), "imagen": ("imagenes", "png"),
            "audio": ("audios", "mp3"), "registro": ("registros", "json")}[tipo]
        return self.outputs / carpeta / f"cuento_{identificador}.{extension}"

    def _escribir(self, ruta, contenido):
        if not contenido:
            raise RuntimeError("No se guardará un archivo vacío.")
        ruta.parent.mkdir(parents=True, exist_ok=True)
        temporal = ruta.with_suffix(ruta.suffix + ".tmp")
        try:
            temporal.write_bytes(contenido)
            if temporal.stat().st_size != len(contenido):
                raise OSError("Escritura incompleta")
            temporal.replace(ruta)
        except OSError as error:
            raise RuntimeError(f"No se pudo guardar {ruta.name}. Los archivos anteriores se conservan.") from error
        return ruta

    def guardar_texto(self, identificador, tema, contexto, cuento):
        texto = f"Tema: {tema}\nContexto: {contexto}\n\nCUENTO GENERADO\n\n{cuento}\n"
        return self._escribir(self.ruta(identificador, "texto"), texto.encode("utf-8"))

    def guardar_imagen(self, identificador, contenido):
        try:
            with Image.open(BytesIO(contenido)) as imagen:
                if imagen.format != "PNG":
                    raise ValueError("Formato distinto de PNG")
                imagen.verify()
        except (OSError, ValueError, SyntaxError) as error:
            raise RuntimeError("El proveedor no devolvió un PNG válido.") from error
        return self._escribir(self.ruta(identificador, "imagen"), contenido)

    def guardar_audio(self, identificador, contenido):
        if not isinstance(contenido, bytes) or not contenido:
            raise RuntimeError("No se recibió audio utilizable.")
        return self._escribir(self.ruta(identificador, "audio"), contenido)

    def guardar_registro(self, r):
        self._escribir(self.ruta(r.identificador, "registro"),
            json.dumps(r.registro(), ensure_ascii=False, indent=2).encode("utf-8"))
