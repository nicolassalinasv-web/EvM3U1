def ejecutar_consola(app, leer=input, mostrar=print):
    mostrar("EvM3U1 - Cuentos con imagen y narración")
    opcion = leer("Modo para texto, imagen y audio: 1 = Local, 2 = OpenAI: ").strip()
    if opcion not in {"1", "2"}:
        mostrar("Modo inválido. No se generó contenido.")
        return
    modo = "local" if opcion == "1" else "openai"
    tema = leer("Tema: ")
    contexto = leer("Contexto (personajes, lugar y situación): ")
    autorizado = False
    if modo == "openai":
        mostrar("Cuento, imagen y narración usarán OpenAI y consumirán saldo.")
        autorizado = leer("Escribe GENERAR para autorizar estas operaciones: ").strip() == "GENERAR"
        if not autorizado:
            mostrar("Cancelado antes de generar.")
            return
    else:
        mostrar("Texto: Ollama. Imagen: MOSS/ComfyUI. Audio: Piper. No se utiliza OpenAI.")
        if leer("Escribe GENERAR para iniciar localmente: ").strip() != "GENERAR":
            mostrar("Cancelado antes de generar.")
            return
    r = app.iniciar(tema, contexto, modo, autorizado=autorizado)
    if r.cuento:
        mostrar("\nCUENTO GENERADO\n" + r.cuento)
    while r.estado == "error_imagen":
        mostrar(r.error)
        opcion = leer("1 Reintentar local | 2 OpenAI (pago) | 3 Narrar sin imagen | 4 Finalizar: ").strip()
        if opcion == "1":
            r = app.intentar_imagen(r, "local")
        elif opcion == "2":
            if leer("Solo esta imagen consumirá saldo. Escribe USAR OPENAI para confirmar: ").strip() == "USAR OPENAI":
                r = app.intentar_imagen(r, "openai", autorizado=True)
        elif opcion == "3":
            r = app.narrar(r, autorizado=autorizado)
        elif opcion == "4":
            r = app.finalizar(r)
    if r.estado == "imagen_lista":
        r = app.narrar(r, autorizado=autorizado)
    while r.estado == "error_audio":
        mostrar(r.error)
        aviso = " (otra solicitud de pago)" if modo == "openai" else " localmente"
        if leer("Escribe REINTENTAR para narrar" + aviso + ", o ENTER para finalizar: ").strip() == "REINTENTAR":
            r = app.narrar(r, autorizado=autorizado)
        else:
            r = app.finalizar(r)
    if r.error:
        mostrar(r.error)
    mostrar("Estado: " + r.estado)
    for nombre in ("texto", "imagen", "audio"):
        if getattr(r, nombre):
            mostrar(nombre + ": " + getattr(r, nombre))
    return r
