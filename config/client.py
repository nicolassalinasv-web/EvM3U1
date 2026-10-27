from contextlib import contextmanager
from openai import OpenAI, APIError, AuthenticationError, RateLimitError

class FabricaClienteOpenAI:
    """Cliente centralizado, sin reintentos automáticos."""
    def __init__(self, configuracion):
        self.configuracion = configuracion

    @contextmanager
    def abrir(self):
        self.configuracion.validar_openai()
        try:
            with OpenAI(api_key=self.configuracion.api_key, base_url="https://api.openai.com/v1",
                        timeout=120, max_retries=0) as cliente:
                yield cliente
        except AuthenticationError as error:
            raise RuntimeError("OpenAI rechazó la autenticación. Revisa tu clave sin mostrarla.") from error
        except RateLimitError as error:
            raise RuntimeError("OpenAI alcanzó un límite de uso o saldo.") from error
        except APIError as error:
            raise RuntimeError("Falló OpenAI. Revisa conexión, permisos y modelo. Una solicitud enviada puede consumir saldo.") from error
