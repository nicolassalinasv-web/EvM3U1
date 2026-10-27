from config.settings import cargar_configuracion
from src.fabrica import crear_aplicacion
from src.consola import ejecutar_consola

def main():
    try:
        app = crear_aplicacion(cargar_configuracion())
        ejecutar_consola(app)
    except (ValueError, RuntimeError, OSError):
        print("No se pudo continuar. Revisa .env, conexión y permisos de outputs. Los archivos existentes se conservan.")
    except (KeyboardInterrupt, EOFError):
        print("\nSesión finalizada. Los archivos guardados se conservan. Un trabajo enviado puede seguir en el proveedor.")

if __name__ == "__main__":
    main()
