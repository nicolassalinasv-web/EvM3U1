from io import BytesIO
from pathlib import Path
import subprocess
import wave
from src.validacion import texto_util

class NarradorLocal:
    """Piper en CPU y conversión MP3 con FFmpeg. Sin llamadas de red."""
    def __init__(self, configuracion):
        self.configuracion = configuracion

    def comprobar(self):
        modelo = self.configuracion.modelo_piper
        if not modelo.is_file() or not Path(str(modelo) + ".json").is_file():
            raise ValueError("Falta la voz Piper. Ejecuta preparar_voz_local.py antes de usar modo Local.")
        try:
            from piper import PiperVoice
            import imageio_ffmpeg
            if not Path(imageio_ffmpeg.get_ffmpeg_exe()).is_file():
                raise ValueError("Falta FFmpeg local.")
        except ImportError as error:
            raise RuntimeError("Instala las dependencias locales de requirements.txt.") from error

    def generar(self, cuento, autorizado=False):
        cuento = texto_util(cuento, "El cuento para narrar", 3000)
        self.comprobar()
        from piper import PiperVoice
        import imageio_ffmpeg
        try:
            voz = PiperVoice.load(str(self.configuracion.modelo_piper), use_cuda=False)
            buffer = BytesIO()
            with wave.open(buffer, "wb") as wav:
                voz.synthesize_wav(cuento, wav)
            conversion = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error",
                "-i", "pipe:0", "-f", "mp3", "-codec:a", "libmp3lame", "-q:a", "4", "pipe:1"],
                input=buffer.getvalue(), capture_output=True, timeout=120,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), check=True)
        except (OSError, RuntimeError, ValueError, wave.Error, subprocess.SubprocessError) as error:
            raise RuntimeError("Falló la narración local. Revisa la voz Piper y las dependencias de audio.") from error
        if not conversion.stdout:
            raise RuntimeError("La narración local quedó vacía.")
        return conversion.stdout
