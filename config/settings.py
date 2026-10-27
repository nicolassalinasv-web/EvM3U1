import os
from pathlib import Path
from dataclasses import dataclass
from urllib.parse import urlsplit
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class Configuracion:
    base_dir: Path
    api_key: str
    habilitar_api: bool = False
    modelo_texto: str = "gpt-6-luna"
    modelo_imagen: str = "gpt-image-1-mini"
    modelo_audio: str = "gpt-4o-mini-tts"
    voz: str = "alloy"
    comfyui_url: str = "http://127.0.0.1:8188"
    comfyui_timeout: int = 600

    ollama_url: str = "http://127.0.0.1:11434"
    modelo_local_texto: str = "qwen3:8b"
    ollama_timeout: int = 300
    voz_local: str = "es_MX-ald-medium"

    @property
    def modelo_piper(self):
        return self.base_dir / "models" / "piper" / (self.voz_local + ".onnx")

    @property
    def workflow(self):
        return self.base_dir / "config" / "moss_api.json"

    def validar_openai(self):
        if not self.habilitar_api:
            raise ValueError("OpenAI deshabilitado. Configura HABILITAR_API_REAL=true en .env y reinicia.")
        if not self.api_key or self.api_key == "pega_aqui_tu_clave":
            raise ValueError("Falta OPENAI_API_KEY. No compartas su valor.")
        if not all((self.modelo_texto, self.modelo_imagen, self.modelo_audio, self.voz)):
            raise ValueError("Modelos y voz no pueden estar vacíos.")

    def validar_local(self):
        u = urlsplit(self.comfyui_url)
        if (u.scheme != "http" or u.hostname not in {"localhost", "127.0.0.1", "::1"}
                or u.username or u.password or u.path or u.query or u.fragment):
            raise ValueError("COMFYUI_URL debe ser HTTP local, por ejemplo http://127.0.0.1:8188.")
        if self.comfyui_timeout <= 0:
            raise ValueError("COMFYUI_TIMEOUT debe ser positivo.")

def cargar_configuracion():
    load_dotenv(BASE_DIR / ".env", override=False)
    try:
        espera = int(os.getenv("COMFYUI_TIMEOUT", "600"))
        espera_ollama = int(os.getenv("OLLAMA_TIMEOUT", "300"))
    except ValueError as error:
        raise ValueError("Los tiempos de espera deben ser números enteros.") from error
    return Configuracion(BASE_DIR, os.getenv("OPENAI_API_KEY", "").strip(),
        os.getenv("HABILITAR_API_REAL", "false").strip().lower() == "true",
        os.getenv("MODELO_TEXTO", "gpt-6-luna").strip(),
        os.getenv("MODELO_IMAGEN", "gpt-image-1-mini").strip(),
        os.getenv("MODELO_AUDIO", "gpt-4o-mini-tts").strip(),
        os.getenv("VOZ_AUDIO", "alloy").strip(),
        os.getenv("COMFYUI_URL", "http://127.0.0.1:8188").strip().rstrip("/"), espera,
        os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").strip().rstrip("/"),
        os.getenv("MODELO_LOCAL_TEXTO", "qwen3:8b").strip(), espera_ollama,
        os.getenv("VOZ_LOCAL", "es_MX-ald-medium").strip())
