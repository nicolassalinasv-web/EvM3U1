# EvM3U1 — Cuentos multimodales con OpenAI o recursos locales

Evolución independiente de EvU3 para el módulo 3, unidad 1. Tema y contexto
producen un cuento, una imagen basada en ese cuento y su narración MP3.
La consola y la web utilizan las mismas clases y el mismo coordinador.

## Selección inicial para los tres resultados

| Modo | Texto | Imagen | Audio |
| --- | --- | --- | --- |
| OpenAI | Modelo de texto OpenAI | Modelo de imagen OpenAI | Voz OpenAI |
| Local | Ollama, qwen3:8b por defecto | MOSS en ComfyUI | Piper, voz española en CPU |

El modo Local no utiliza la clave de OpenAI, funciona aunque
HABILITAR_API_REAL=false y no requiere internet después de la instalación y
descarga de modelos. Usa recursos del equipo. La selección inicial controla
los tres componentes; no es solamente un selector para la imagen.

## Ejecutar en Windows

Desde la carpeta del proyecto, consola:

```powershell
.\.venv\Scripts\python.exe main.py
```

Interfaz web (puerto separado del proyecto anterior):

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8502
```

En la web selecciona OpenAI o Local al comienzo. Después introduce tema y
contexto y pulsa **Generar material educativo**. Se generan automáticamente
el cuento, la imagen y la narración MP3 con el modo elegido. En consola las
tres etapas también continúan en secuencia. Si falla la imagen, el flujo espera
tu decisión; si el reintento o cambio confirmado funciona, continúa con la voz.
Si falla el audio, el error se muestra y el reintento requiere una acción explícita. Descargas y actualizaciones
no vuelven a generar contenido. Los errores detienen el flujo y conservan los
archivos válidos. Mantén la sesión abierta: no se restaura automáticamente un
proceso interrumpido desde los archivos de disco.

## Requisitos del modo Local

1. Inicia Ollama y descarga el modelo de texto una vez:

```powershell
ollama pull qwen3:8b
ollama list
```

2. Abre Comfy Desktop e inicia **Local Image en modo Local**. No basta con tener
   el programa instalado o abierto en su catálogo. Espera a que responda en
   http://127.0.0.1:8188 y mantén la instancia ejecutándose durante la imagen.
   El flujo MOSS y todos sus modelos deben estar instalados.
3. Descarga la voz Piper una vez (ya está preparada en este equipo):

```powershell
.\.venv\Scripts\python.exe preparar_voz_local.py
```

La voz predeterminada es es_MX-ald-medium y se guarda en models/piper.
Piper utiliza CPU para dejar la GPU disponible para imágenes. El WAV temporal
se conserva en memoria y FFmpeg lo convierte a MP3. No requiere un servidor de
voz ni una instalación independiente de FFmpeg: el ejecutable se incluye en
la dependencia imageio-ffmpeg.

Antes de generar se comprueban los tres recursos del modo seleccionado.
Si alguno falta o está apagado, no se solicita el cuento. Ollama se configura
por solicitud con keep_alive=0, liberando su modelo después del cuento para
que MOSS disponga de memoria. Esto no modifica la configuración permanente
de Ollama ni los archivos del proyecto de Ollama/Qwen de otro chat.

## Configuración

En otro equipo:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Variables de generación local:

```env
OLLAMA_URL=http://127.0.0.1:11434
MODELO_LOCAL_TEXTO=qwen3:8b
OLLAMA_TIMEOUT=300
COMFYUI_URL=http://127.0.0.1:8188
COMFYUI_TIMEOUT=600
VOZ_LOCAL=es_MX-ald-medium
```

Las direcciones de los servicios locales deben ser HTTP de loopback. No se
permiten modelos marcados :cloud en el modo Local. No se descargan modelos
automáticamente al generar. El entorno de esta computadora ya está instalado.

Para OpenAI configura tu clave únicamente en .env, modelos y voz, y
HABILITAR_API_REAL=true. Además se exige confirmación explícita en la aplicación.
El modo OpenAI no necesita Ollama, ComfyUI ni la voz Piper preparada.
Las variables existentes en el entorno tienen prioridad sobre .env.
Nunca compartas .env. El ZIP no incluye claves, entorno virtual ni modelos.

## Decisiones y control de gastos

Nunca se cambia de proveedor ni se reintenta automáticamente. Si falla una
imagen puedes reintentar local, confirmar una nueva solicitud OpenAI para esa
imagen, continuar con narración sin imagen o finalizar. La excepción de imagen
es voluntaria: texto y audio conservan el modo inicial. El registro identifica
los proveedores reales para que una ejecución mixta no se confunda con local.

Un fallo de texto o voz local nunca activa OpenAI. Un reintento local no pide
confirmación de pago. Cualquier reintento de voz OpenAI requiere autorización.
Una solicitud de pago enviada puede consumir saldo aunque falle. Si vence una
espera de MOSS, el trabajo podría seguir en su cola: revísala antes de repetir.
EvM3U1 no interrumpe trabajos ajenos ni cambia silenciosamente de proveedor.

## Organización del código

```text
EvM3U1/
├── config/
│   ├── settings.py
│   ├── client.py
│   └── moss_api.json
├── src/
│   ├── texto/
│   │   ├── generador_cuento.py
│   │   └── generador_local.py
│   ├── imagen/
│   │   ├── ilustrador_cuento.py
│   │   ├── ilustrador_openai.py
│   │   └── ilustrador_comfyui.py
│   ├── audio/
│   │   ├── narrador_cuento.py
│   │   └── narrador_local.py
│   ├── aplicacion_cuentos.py
│   ├── gestor_archivos.py
│   ├── fabrica.py
│   ├── consola.py
│   └── validacion.py
├── tests/
├── models/piper/
├── outputs/
│   ├── textos/
│   ├── imagenes/
│   ├── audios/
│   └── registros/
├── preparar_voz_local.py
├── main.py
└── app.py
```

Las carpetas Python incluyen __init__.py. El código está separado de las
salidas. main.py construye dependencias mediante src/fabrica.py.
AplicacionCuentos recibe objetos especializados por constructor y coordina
sus métodos compatibles: composición, encapsulamiento y polimorfismo.
GestorArchivos administra rutas y persistencia; el cliente OpenAI está
centralizado en config/client.py y no se construye al seleccionar Local.
La ruta didáctica C:\Cuentos2026 se adapta aquí a EvM3U1.

## Resultados, validaciones y trazabilidad

Cada ejecución tiene un ID común en outputs/textos/cuento_ID.txt,
outputs/imagenes/cuento_ID.png, outputs/audios/cuento_ID.mp3 y
outputs/registros/cuento_ID.json. El TXT incluye tema, contexto y cuento.
El JSON registra modo elegido, proveedores efectivos e intentos de imagen.
Los archivos se escriben mediante un temporal y se comprueba su tamaño.
Pillow verifica el PNG. Los resultados anteriores se conservan si falla un paso.

Tema: hasta 200 caracteres. Contexto: hasta 2000. Se rechazan entradas vacías.
Se solicitan cuentos breves y completos, hasta 3000 caracteres para narración.
La salida incompleta se rechaza antes de generar imagen o audio. Si un cuento
OpenAI supera el límite de narración, se conserva y se informa el error de voz.
Las salidas contienen voces creadas por IA. Los límites de longitud no son un
presupuesto monetario. La disponibilidad y calidad de modelos externos puede
variar; esta versión usa los nombres configurados sin sustituirlos por otros.

## Pruebas y entrega

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Las pruebas automáticas simulan los motores y verifican selección completa,
control de pago, errores y conservación. No consumen API ni GPU. La entrega
académica debe incluir la demostración real por consola y las tres salidas,
sin exponer claves. El ZIP contiene código y documentación; los modelos se
preparan por separado. Consulta VALIDACION.md para las comprobaciones realizadas.

Referencias:
- https://docs.ollama.com/api/generate
- https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/API_PYTHON.md
- https://huggingface.co/rhasspy/piper-voices/blob/main/es/es_MX/ald/medium/MODEL_CARD
- https://docs.comfy.org/development/comfyui-server/comms_routes
- https://developers.openai.com/api/docs/guides/image-generation
