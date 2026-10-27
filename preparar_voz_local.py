"""Descarga inicial explícita. La generación posterior no requiere internet."""
import subprocess
import sys
from config.settings import cargar_configuracion

def main():
    c = cargar_configuracion()
    destino = c.modelo_piper.parent
    destino.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "piper.download_voices", c.voz_local,
                    "--data-dir", str(destino)], check=True)
    print("Voz local preparada.")

if __name__ == "__main__":
    main()
