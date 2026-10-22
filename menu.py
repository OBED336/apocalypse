"""Portada y menú principal con navegación por ratón, teclado y mando."""
import math
import pygame as pg

G = None
BOTONES = (pg.Rect(54, 232, 410, 66), pg.Rect(54, 310, 410, 66),
           pg.Rect(54, 398, 199, 50), pg.Rect(265, 398, 199, 50),
           pg.Rect(54, 460, 199, 50), pg.Rect(265, 460, 199, 50),
           pg.Rect(54, 528, 410, 42))
CREDITO = pg.Rect(916, 38, 230, 48)
ETIQUETAS = ('JUGAR SOLO', 'COOPERATIVO', 'CONTROLES', 'RECORDS', 'LOGROS', 'PERSONAJES', 'SALIR DEL JUEGO')
BLANCO = (241, 238, 221)
SUAVE = (164, 179, 181)
MENTA = (125, 228, 191)
aviso = ''
hasta_aviso = 0
fuentes = {}
fondo = None


def texto(cadena, x, y, tipo='normal', color=BLANCO):
    im = fuentes[tipo].render(cadena, True, color)
    G.pantalla.blit(im, (x, y))
    return im


def icono_persona(x, y, doble=False, color=MENTA):
    for dx in ((-8, 9) if doble else (0,)):
        pg.draw.circle(G.pantalla, color, (x+dx, y-7), 5)
        pg.draw.arc(G.pantalla, color, (x+dx-9, y, 18, 16), 0, math.pi, 3)


def dibujar():
    G.pantalla.blit(fondo, (0, 0))
    tiempo = pg.time.get_ticks()/1000
    # Polvo tenue de fondo: posiciones deterministas, sin consumir el azar del juego.
    for n in range(22):
        x = 510+(n*163)%680
        y = 100+((n*83-tiempo*(5+n%4))%510)
        pg.draw.circle(G.pantalla, (122, 113, 95), (x, int(y)), 1)
    pg.draw.rect(G.pantalla, MENTA, (54, 43, 7, 15), border_radius=2)
    texto('UNA HISTORIA DE SUPERVIVENCIA', 74, 43, 'micro', MENTA)
    texto('APOCALYPSE', 51, 75, 'titulo')
    texto('L A S T   S U R V I V O R', 57, 145, 'subtitulo', (221, 183, 116))
    texto('Reúne al equipo. Sobrevive al siguiente piso.', 56, 192, 'pequena', SUAVE)

    creditos = G.creditos['cantidad']
    pg.draw.rect(G.pantalla, (20, 35, 39), CREDITO, border_radius=12)
    pg.draw.rect(G.pantalla, (65, 101, 93), CREDITO, 1, border_radius=12)
    pg.draw.circle(G.pantalla, (221, 183, 116), (940, 62), 10, 2)
    texto(str(creditos)+' CRÉDITOS', 960, 52, 'pequena', BLANCO)
    pg.draw.rect(G.pantalla, (50, 78, 70), (1096, 49, 37, 26), border_radius=5)
    texto('+', 1108, 48, 'boton', MENTA)

    for i, r in enumerate(BOTONES):
        activo = G.opcion_menu == i
        principal = i in (0, 1)
        bg = (41, 74, 66) if activo else (19, 30, 37)
        borde = MENTA if activo else (58, 74, 78)
        pg.draw.rect(G.pantalla, bg, r, border_radius=10)
        pg.draw.rect(G.pantalla, borde, r, 2 if activo else 1, border_radius=10)
        if activo:
            pg.draw.rect(G.pantalla, MENTA, (r.x, r.y+12, 4, r.h-24), border_radius=2)
        if principal:
            icono_persona(r.x+31, r.y+29, i==1, MENTA if activo else SUAVE)
            texto(ETIQUETAS[i], r.x+62, r.y+10, 'boton', BLANCO)
            texto('Tu misión comienza aquí' if i==0 else 'Dos jugadores, un mismo equipo', r.x+62, r.y+37, 'micro', SUAVE)
            texto('1 CR.', r.right-62, r.y+26, 'micro', (221, 183, 116))
        elif i==6:
            texto(ETIQUETAS[i], r.x+20, r.y+12, 'pequena', SUAVE if not activo else BLANCO)
            texto('ESC', r.right-52, r.y+14, 'micro', SUAVE)
        else:
            texto(ETIQUETAS[i], r.x+18, r.y+17, 'pequena', BLANCO)
            if activo: texto('›', r.right-25, r.y+11, 'boton', MENTA)

    if pg.time.get_ticks()<hasta_aviso:
        pg.draw.rect(G.pantalla, (48, 36, 28), (54, 583, 700, 31), border_radius=6)
        texto(aviso, 66, 591, 'micro', (246, 205, 138))
    else:
        texto('RATÓN: elegir y pulsar  /  ↑ ↓ + ENTER: confirmar', 56, 596, 'micro', SUAVE)
    pg.draw.line(G.pantalla, (54, 71, 77), (54, 634), (1146, 634))
    texto('5: añadir crédito   ·   F1: silencio   ·   F2 / F3: música', 56, 652, 'micro', SUAVE)
    modo = 'MANDO CONECTADO' if G.joysticks else 'TECLADO Y RATÓN'
    texto(modo, 914, 652, 'micro', MENTA)


def instalar(juego):
    global G, fondo
    G = juego
    fuentes.update({
        'titulo': G.fuente_tema(61), 'hero': G.fuente_tema(36),
        'normal': pg.font.SysFont('segoeui',18), 'boton': pg.font.SysFont('segoeui',22,bold=True),
        'subtitulo': pg.font.SysFont('segoeui',17,bold=True),
        'pequena': pg.font.SysFont('segoeui',15,bold=True), 'micro': pg.font.SysFont('segoeui',12,bold=True),
    })
    fondo = G.FONDO_INICIO.copy()
    sombra = pg.Surface((1200,700),pg.SRCALPHA)
    for x in range(1200):
        alpha = 244 if x<490 else max(72, 215-int((x-490)*.23))
        pg.draw.line(sombra, (9,17,25,alpha), (x,0), (x,700))
    fondo.blit(sombra, (0,0))
    confirmar_original = G.confirmar
    evento_original = G.procesar_evento
    audio_original = G.dibujar_control_audio

    def confirmar():
        global aviso, hasta_aviso
        if G.estado==G.MENU and G.opcion_menu in (0,1) and G.creditos['cantidad']<=0:
            aviso='Necesitas 1 crédito. Pulsa 5 o haz clic en el contador de créditos.'
            hasta_aviso=pg.time.get_ticks()+4500
            G.play(G.S_MENU,'menu')
            return
        confirmar_original()

    def evento(ev):
        if G.estado in (G.MENU,G.INSERT_COIN):
            if ev.type==pg.MOUSEMOTION:
                for i,r in enumerate(BOTONES):
                    if r.collidepoint(ev.pos) and G.opcion_menu!=i:
                        G.opcion_menu=i
                        G.play(G.S_MENU,'menu')
                return
            if ev.type==pg.MOUSEBUTTONDOWN and ev.button==1:
                if CREDITO.collidepoint(ev.pos):
                    G.agregar_credito()
                else:
                    for i,r in enumerate(BOTONES):
                        if r.collidepoint(ev.pos):
                            G.estado=G.MENU
                            G.opcion_menu=i
                            G.confirmar()
                            break
                return
            if G.estado==G.INSERT_COIN and ev.type in (pg.KEYDOWN,pg.JOYBUTTONDOWN,pg.JOYHATMOTION):
                G.estado=G.MENU
            if ev.type==pg.JOYHATMOTION and ev.value[1]:
                G.opcion_menu=(G.opcion_menu-ev.value[1])%7
                G.play(G.S_MENU,'menu')
                return
            if ev.type==pg.KEYDOWN and ev.key in (pg.K_HOME,pg.K_END):
                G.opcion_menu=0 if ev.key==pg.K_HOME else 6
                return
        evento_original(ev)

    def audio():
        if G.estado not in (G.MENU,G.INSERT_COIN): audio_original()

    G.dibujar_menu=dibujar
    G.dibujar_insert_coin=dibujar
    G.confirmar=confirmar
    G.procesar_evento=evento
    G.dibujar_control_audio=audio
    G.estado=G.MENU
