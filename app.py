from pathlib import Path
import streamlit as st
from config.settings import cargar_configuracion
from src.fabrica import crear_aplicacion

st.set_page_config(page_title="EvM3U1 · Cuentos", page_icon="📚", layout="centered")
st.title("Cuentos con imagen y narración")
st.caption("EvM3U1 · Selecciona un modo para generar los tres resultados.")
try:
    configuracion = cargar_configuracion()
    app = crear_aplicacion(configuracion)
except (ValueError, RuntimeError, OSError):
    st.error("No se pudo cargar la configuración. Revisa .env sin compartir tu clave.")
    st.stop()

anterior = st.session_state.get("resultado")
if anterior is not None and not hasattr(anterior, "proveedor_texto"):
    st.session_state.pop("resultado")
    st.info("Inicia un nuevo cuento con la selección completa de proveedor. Los archivos anteriores se conservan en outputs.")
actual = st.session_state.get("resultado")
pendiente = actual is not None and actual.estado in {"error_imagen", "imagen_lista", "error_audio"}
modo = st.radio("Modo de generación", ["openai", "local"], index=1, horizontal=True,
                format_func=lambda p: "OpenAI" if p == "openai" else "Local", disabled=pendiente)
if modo == "local":
    st.info("Texto: Ollama / Qwen. Imagen: MOSS / ComfyUI. Audio: Piper. Todo se genera en tu equipo, sin clave ni saldo de OpenAI.")
    st.caption("Mantén Ollama y ComfyUI (instancia Local Image) iniciados. La voz Piper debe estar descargada.")
else:
    st.info("Texto, imagen y narración se generarán con OpenAI y consumirán saldo de la API.")
    if not configuracion.habilitar_api:
        st.warning("OpenAI está deshabilitado. Configura HABILITAR_API_REAL=true en .env y reinicia para usar este modo.")

def operar(funcion, completar=False):
    try:
        with st.spinner("Procesando… La generación local puede tardar varios minutos."):
            resultado = funcion()
            st.session_state.resultado = resultado
            if completar and resultado.estado == "imagen_lista":
                st.session_state.resultado = app.narrar(
                    resultado, autorizado=resultado.proveedor_elegido == "openai")
        st.rerun()
    except (ValueError, RuntimeError, OSError):
        st.error("No se completó la operación. Revisa configuración, conexión y permisos. Los archivos completados se conservan.")

with st.form("cuento"):
    tema = st.text_input("Tema", max_chars=200, placeholder="La amistad")
    contexto = st.text_area("Contexto", max_chars=2000,
        placeholder="Un conejo y una tortuga se conocen en un bosque y deben ayudarse.")
    consentimiento = False
    if modo == "openai":
        consentimiento = st.checkbox("Autorizo el consumo de OpenAI para el cuento, la imagen y la narración de esta ejecución.")
    generar = st.form_submit_button("Generar material educativo",
        disabled=pendiente or (modo == "openai" and not configuracion.habilitar_api))
if generar:
    if not tema.strip() or not contexto.strip():
        st.error("Completa el tema y el contexto.")
    elif modo == "openai" and not consentimiento:
        st.error("Confirma el consumo de OpenAI antes de generar.")
    else:
        operar(lambda: app.iniciar(tema, contexto, modo, autorizado=consentimiento), completar=True)

r = st.session_state.get("resultado")
if r is not None:
    st.divider()
    st.caption("Modo de esta ejecución: " + ("Local" if r.proveedor_elegido == "local" else "OpenAI"))
    if r.error:
        st.warning(r.error)
    if r.cuento:
        st.subheader("Cuento")
        st.caption("Proveedor: " + r.proveedor_texto)
        st.text(r.cuento)
    for atributo, titulo, mime in [("texto", "Descargar cuento TXT", "text/plain"),
            ("imagen", "Descargar imagen PNG", "image/png"), ("audio", "Descargar narración MP3", "audio/mpeg")]:
        ruta = getattr(r, atributo)
        if ruta:
            try:
                contenido = Path(ruta).read_bytes()
                if atributo == "imagen":
                    st.subheader("Ilustración")
                    st.caption("Proveedor: " + r.proveedor_imagen)
                    st.image(contenido)
                elif atributo == "audio":
                    st.subheader("Narración")
                    st.caption("Voz generada por inteligencia artificial. Proveedor: " + r.proveedor_audio)
                    st.audio(contenido, format="audio/mpeg")
                st.download_button(titulo, contenido, file_name=Path(ruta).name, mime=mime)
            except OSError:
                st.error("No se pudo leer un resultado guardado. Revisa outputs.")
    if r.estado == "error_imagen":
        st.subheader("Decide cómo continuar")
        st.caption("Antes de reintentar localmente, revisa la cola de ComfyUI: un trabajo enviado puede seguir ejecutándose.")
        if st.button("Reintentar imagen local"):
            operar(lambda: app.intentar_imagen(r, "local"), completar=True)
        with st.form("cambiar_openai_" + str(len(r.intentos))):
            st.caption("El cambio afectará solo a esta imagen. La voz conservará el modo elegido al inicio.")
            autorizar = st.checkbox("Confirmo una nueva solicitud de imagen a OpenAI que consumirá saldo.")
            cambiar = st.form_submit_button("Usar OpenAI para esta imagen")
        if cambiar:
            if autorizar:
                operar(lambda: app.intentar_imagen(r, "openai", autorizado=True), completar=True)
            else:
                st.error("Debes confirmar el consumo de esta solicitud de imagen.")
        if st.button("Continuar con narración sin imagen"):
            operar(lambda: app.narrar(r, autorizado=r.proveedor_elegido == "openai"))
        if st.button("Finalizar conservando el cuento"):
            operar(lambda: app.finalizar(r))
    elif r.estado == "imagen_lista":
        etiqueta = "Generar narración local" if r.proveedor_elegido == "local" else "Generar narración con OpenAI"
        if st.button(etiqueta):
            operar(lambda: app.narrar(r, autorizado=r.proveedor_elegido == "openai"))
        if st.button("Finalizar conservando cuento e imagen"):
            operar(lambda: app.finalizar(r))
    elif r.estado == "error_audio":
        if r.proveedor_elegido == "local":
            if st.button("Reintentar narración local"):
                operar(lambda: app.narrar(r))
        else:
            with st.form("reintentar_audio"):
                autorizar_audio = st.checkbox("Confirmo otra solicitud de narración que consumirá saldo.")
                reintentar = st.form_submit_button("Reintentar narración")
            if reintentar:
                if autorizar_audio:
                    operar(lambda: app.narrar(r, autorizado=True))
                else:
                    st.error("Confirma el consumo para reintentar la narración.")
        if st.button("Finalizar conservando resultados"):
            operar(lambda: app.finalizar(r))
    elif r.estado in {"completo", "completo_sin_imagen"}:
        st.success("Proceso completado." if r.imagen else "Cuento y narración completados sin imagen.")
    st.caption("Estado: " + r.estado + " · Identificador: " + r.identificador)
