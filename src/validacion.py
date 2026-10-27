def texto_util(valor, nombre, maximo):
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"{nombre} no puede estar vacío.")
    valor = valor.strip()
    if len(valor) > maximo:
        raise ValueError(f"{nombre} no debe superar {maximo} caracteres.")
    return valor

def exigir_autorizacion(autorizado):
    if autorizado is not True:
        raise ValueError("Confirma explícitamente el consumo de OpenAI antes de continuar.")
