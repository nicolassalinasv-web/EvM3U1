# EvM3U1 y evaluación de la Unidad 1 M3

Esta matriz orienta la revisión; no constituye una calificación otorgada.

| Criterio | Evidencia en el proyecto |
| --- | --- |
| POO, 20 puntos | Clases, objetos, constructores, atributos y métodos; composición en AplicacionCuentos |
| Arquitectura, 15 puntos | config, src, outputs, tests; settings.py, client.py y main.py |
| Cuento IA, 15 puntos | Tema y contexto validados en GeneradorCuento; ambos en prompt; cuento en pantalla |
| Multimodalidad, 15 puntos | TXT, PNG derivado del cuento y MP3 del mismo cuento; persistencia en outputs |
| Seguridad, 10 puntos | .env, cliente centralizado, .gitignore y mensajes sin credenciales |
| Errores, 10 puntos | Tema/contexto vacíos, clave ausente, errores API, cuento inválido y bloqueo de etapas dependientes |
| Buenas prácticas, 10 puntos | Dependencias registradas, nombres por responsabilidad, pathlib y configuración centralizada |
| Integración, 5 puntos | main.py inicia consola; tema/contexto, cuento, imagen y narración en secuencia |

## Adaptaciones y ampliaciones

La carpeta se llama EvM3U1 en lugar de Cuentos2026. La interfaz Streamlit
complementa la consola. Se puede elegir imagen OpenAI para demostrar el
proveedor ejemplificado en la guía o MOSS/ComfyUI como alternativa local.
La rúbrica no exige un proveedor único. Toda sustitución de proveedor requiere
una decisión del usuario. No es obligatorio usar herencia en la solución base.

## Evidencias reales pendientes

- Ejecutar main.py con tema y contexto y comprobar los tres archivos.
- Comprobar visualmente la imagen y escuchar la narración.
- Capturar la ejecución sin exponer claves ni .env.
- Mostrar el manejo de un fallo y la confirmación al elegir OpenAI.

Las pruebas con proveedores simulados no sustituyen estas evidencias reales.

## Modo completo de proveedor

La selección inicial OpenAI o Local controla texto, imagen y narración.
Modo Local utiliza Ollama/Qwen, MOSS/ComfyUI y Piper. Se verificó una ejecución
real local completa, con las tres salidas. La demostración por consola y la
revisión auditiva se mantienen como evidencias recomendadas para la entrega.
