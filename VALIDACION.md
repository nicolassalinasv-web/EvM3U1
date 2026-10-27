# Verificación de EvM3U1

Actualización del 26 de octubre de 2026: modo completo OpenAI o Local.

- 50 pruebas automáticas aprobadas con proveedores simulados.
- Verificado que modo Local funciona sin clave y con la API OpenAI deshabilitada.
- Verificada selección de los tres motores, validación de recursos al inicio,
  conservación de resultados, confirmación de gasto y ausencia de sustitución
  automática ante fallos de texto, imagen o audio local.
- Interacción Streamlit verificada mediante AppTest, incluyendo modo Local
  sin casilla de autorización y modo OpenAI con confirmación obligatoria.
- Dependencias instaladas en el entorno independiente; pip check sin conflictos.

## Prueba real completamente local

Ejecución f413f828902947bfb76d186eac519284 completada:

- Texto: Ollama con qwen3:8b, cuento completo de 903 caracteres.
- Imagen: MOSS/ComfyUI, PNG de 1024 × 1024 abierto y revisado.
- Audio: Piper es_MX-ald-medium en CPU y conversión MP3 con FFmpeg.
- MP3 de 470211 bytes decodificado sin errores. No se evaluó auditivamente
  su pronunciación o calidad perceptual.
- Registro final completo con proveedores local/local/local.
- Prueba ejecutada con clave vacía, API OpenAI deshabilitada y constructor
  OpenAI bloqueado para detectar llamadas inesperadas. No se consumió OpenAI.

Los archivos reales se guardan en outputs con el mismo identificador.
Las pruebas automáticas usan carpetas temporales. Para la entrega académica
sigue siendo conveniente capturar una ejecución real desde main.py y escuchar
la narración. La prueba real anterior utilizó el mismo coordinador desde Python.

El proyecto anterior EvU3 y los archivos del proyecto Ollama/Qwen se conservaron.
Se reutilizó el servicio Ollama ya instalado, sin cambiar sus modelos ni su
configuración permanente. El ZIP excluye .env, .venv, modelos y resultados.

## Flujo web completo

El botón Generar material educativo continúa automáticamente con la narración
tras una imagen correcta, también al recuperarse de un fallo de imagen.
Se verificaron ambos modos con proveedores simulados y que actualizar la
página no repite el audio. Un fallo de voz conserva cuento e imagen y espera
una acción explícita; no activa otro proveedor ni reintenta automáticamente.
