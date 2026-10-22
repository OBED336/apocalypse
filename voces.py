"""Frases y voces españolas incluidas: sin servicios externos ni síntesis en ejecución.

Nueva generación con 55 voces expresivas en assets/voces_emotivas:
entonación, ritmo, pausas y énfasis según la situación; la música se atenúa
al 40% de su volumen configurado mientras suena una voz y se recupera al
terminar. El volumen de las voces se mantiene separado de los efectos
(G.volumen_voces, guardado en audio_config.json).
"""
import json
from pathlib import Path
import pygame as pg

G = None
frases = {}
sonidos = {}
canal = None
bocadillos = {}
cuadro = 0
ultimo = {}
voces_activas = True
musica_atenuada = False


def volumen_voces():
    return getattr(G, "volumen_voces", G.volumen_efectos)


def reproducir(clave, forzar=False):
    if not voces_activas or G.audio_silenciado or canal is None:
        return
    if canal.get_busy() and not forzar:
        return
    sonido = sonidos.get(clave)
    if sonido:
        canal.set_volume(volumen_voces())
        canal.play(sonido)


def decir(jugador, evento, forzar=False):
    if jugador.vida <= 0:
        return False
    if not forzar and cuadro-ultimo.get(jugador.num, -1000) < 180:
        return False
    clave = f'p{jugador.sprite_indice}_{evento}'
    if clave not in frases:
        return False
    ultimo[jugador.num] = cuadro
    texto = frases[clave]['texto']
    duracion = max(210, int(sonidos[clave].get_length()*60)+30) if clave in sonidos else 240
    bocadillos[jugador.num] = (texto, cuadro+duracion)
    reproducir(clave, forzar)
    return True


def dibujar_frases():
    for jugador in G.jugadores:
        dato = bocadillos.get(jugador.num)
        if not dato or dato[1] <= cuadro or jugador.vida <= 0:
            continue
        lineas = G.lineas_dialogo(dato[0], 320)
        ancho = max(G.fuente.size(t)[0] for t in lineas)+24
        alto = len(lineas)*22+16
        x = max(8, min(G.ANCHO-ancho-8, int(jugador.x-ancho/2)))
        y = max(94, int(jugador.y)-110-alto)
        r = pg.Rect(x, y, ancho, alto)
        pg.draw.rect(G.pantalla, (15, 26, 34), r, border_radius=9)
        pg.draw.rect(G.pantalla, jugador.color, r, 2, border_radius=9)
        punta = max(r.left+12, min(r.right-12, int(jugador.x)))
        pg.draw.polygon(G.pantalla, jugador.color, ((punta-6, r.bottom-1), (punta+6, r.bottom-1), (punta, r.bottom+7)))
        for i, linea in enumerate(lineas):
            G.pantalla.blit(G.fuente.render(linea, True, (240, 244, 232)), (r.x+12, r.y+8+i*22))
    G.pantalla.blit(G.fuente_peq.render('Y: frase P1 | U: frase P2 | V: voces '+('SI' if voces_activas else 'NO'), True, (185, 206, 200)), (20, 626))


def instalar(juego):
    global G, frases, canal
    G = juego
    ruta = Path(G.BASE)/'assets'
    frases = json.loads((ruta/'frases.json').read_text(encoding='utf-8'))
    if G.AUDIO_OK:
        # El motor usa los canales 0–23; las voces tienen uno propio.
        pg.mixer.set_num_channels(25)
        canal = pg.mixer.Channel(24)
        for clave in frases:
            try:
                sonidos[clave] = pg.mixer.Sound(str(ruta/'voces_emotivas'/(clave+'.wav')))
            except (OSError, pg.error):
                pass
    iniciar_original = G.iniciar_nivel
    actualizar_original = G.actualizar_partida
    dibujar_original = G.dibujar
    evento_original = G.procesar_evento
    abrir_original = G.abrir_conversacion
    elegir_original = G.elegir_dialogo
    cerrar_original = G.cerrar_conversacion
    habilidad_original = G.usar_habilidad
    daño_original = G.Jugador.recibir_daño
    curar_original = G.Jugador.curar
    granada_original = G.Jugador.lanzar_granada
    instrucciones_original = G.dibujar_instrucciones
    audio_original = G.actualizar_audio

    def iniciar(idx):
        global cuadro
        cuadro = 0
        ultimo.clear()
        bocadillos.clear()
        if canal: canal.stop()
        iniciar_original(idx)
        for j in G.jugadores:
            decir(j, 'inicio')

    def actualizar(teclas):
        global cuadro
        cuadro += 1
        sala = G.sala_actual
        limpia_antes = sala.limpia if sala else True
        actualizar_original(teclas)
        if sala is G.sala_actual and sala and not limpia_antes and sala.limpia:
            j = next((j for j in G.jugadores if j.vida > 0), None)
            if j: decir(j, 'despejada')

    def daño(j, cantidad):
        antes = j.vida
        daño_original(j, cantidad)
        if 0 < j.vida < antes: decir(j, 'herida')

    def curar(j):
        resultado = curar_original(j)
        if resultado: decir(j, 'curar', True)
        return resultado

    def granada(j):
        antes = j.granadas
        granada_original(j)
        if j.granadas < antes: decir(j, 'granada', True)

    def habilidad(j):
        resultado = habilidad_original(j)
        if resultado: decir(j, 'habilidad', True)
        return resultado

    def abrir(num):
        resultado = abrir_original(num)
        if resultado: reproducir(f"n{G.dialogo['companero']['indice']}_saludo", True)
        return resultado

    def elegir():
        opcion = G.dialogo['opcion']
        indice = G.dialogo['companero']['indice']
        elegir_original()
        if opcion < 3:
            reproducir(f"n{indice}_"+('estado', 'consejo', 'equipo')[opcion], True)

    def cerrar():
        if canal: canal.stop()
        cerrar_original()

    def evento(ev):
        global voces_activas
        if ev.type == pg.KEYDOWN and G.estado in (G.JUGANDO, G.PAUSA, 'dialogo'):
            if ev.key == pg.K_v:
                voces_activas = not voces_activas
                if canal: canal.stop()
                return
            if G.estado == G.JUGANDO and ev.key in (pg.K_y, pg.K_u):
                num = 1 if ev.key == pg.K_y else 2
                j = next((j for j in G.jugadores if j.num == num and j.vida > 0), None)
                if j and cuadro-ultimo.get(num, -1000) >= 90: decir(j, 'manual', True)
                return
        evento_original(ev)

    def dibujar():
        dibujar_original()
        if G.estado == G.JUGANDO:
            dibujar_frases()

    def audio(dt):
        global musica_atenuada
        audio_original(dt)
        if canal:
            canal.set_volume(0 if G.audio_silenciado or not voces_activas else volumen_voces())
            if G.estado in (G.JUGANDO, 'dialogo'):
                canal.unpause()
            else:
                canal.pause()
            hablando = (G.estado in (G.JUGANDO, 'dialogo') and voces_activas
                         and not G.audio_silenciado and canal.get_busy())
            if hablando:
                volumen = G.volumen_musica * .40
                if G.canal_musica: G.canal_musica.set_volume(volumen)
                pg.mixer.music.set_volume(volumen)
                musica_atenuada = True
            elif musica_atenuada:
                G.aplicar_volumen()
                musica_atenuada = False

    def instrucciones():
        instrucciones_original()
        G.texto_centro('Y / U: decir una frase | V: activar o silenciar las voces', 525, G.CIAN, G.fuente)

    G.iniciar_nivel = iniciar
    G.actualizar_partida = actualizar
    G.dibujar = dibujar
    G.procesar_evento = evento
    G.abrir_conversacion = abrir
    G.elegir_dialogo = elegir
    G.cerrar_conversacion = cerrar
    G.usar_habilidad = habilidad
    G.Jugador.recibir_daño = daño
    G.Jugador.curar = curar
    G.Jugador.lanzar_granada = granada
    G.dibujar_instrucciones = instrucciones
    G.actualizar_audio = audio
