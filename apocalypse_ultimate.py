"""
Apocalypse: Last Survivor
Gráficos mejorados, sonidos procedurales, jefes, power-ups, clima, logros.
Ejecutar: python apocalypse_ultimate.py
Audio incluido sin archivos externos: F1 silencio, F2/F3 música, F4/F5 efectos.
"""

import pygame as pg
import math
import random
import sys
import json
import os
from datetime import datetime

pg.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=512)
pg.init()
pg.joystick.init()
try:
    pg.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
    AUDIO_OK = True
except pg.error:
    AUDIO_OK = False

ANCHO, ALTO, FPS = 1200, 700, 60
pantalla = pg.display.set_mode((ANCHO, ALTO))
pg.display.set_caption("Apocalypse: Last Survivor")
reloj = pg.time.Clock()

# ============ FUENTES Y RECURSOS ============
BASE = os.path.dirname(os.path.abspath(__file__))
def buscar_gocake():
    for carpeta, dirs, archivos in os.walk(BASE):
        dirs[:] = sorted(d for d in dirs if not d.startswith('.') and d.lower() not in ('node_modules', '__pycache__', 'venv', 'env'))
        for nombre in sorted(archivos):
            if 'gocake' in nombre.lower() and nombre.lower().endswith(('.ttf','.otf')):
                return os.path.join(carpeta,nombre)
    return None
RUTA_GOCAKE = buscar_gocake()
def fuente_tema(tamano):
    if RUTA_GOCAKE:
        try: return pg.font.Font(RUTA_GOCAKE,tamano)
        except (OSError,pg.error): pass
    return pg.font.SysFont('consolas',tamano,bold=True)
fuente_peq = pg.font.SysFont('consolas',13,bold=True)
fuente = pg.font.SysFont('consolas',17,bold=True)
fuente_med = fuente_tema(26)
fuente_gran = fuente_tema(44)
fuente_titulo = fuente_tema(72)
fuente_icono = pg.font.SysFont('segoeuiemoji',24)
if not RUTA_GOCAKE:
    print('Gocake no encontrada: coloca su archivo .ttf u .otf en una carpeta del juego.')

def cargar_imagen(nombre):
    ruta=os.path.join(BASE,'assets',nombre)
    try: return pg.image.load(ruta).convert_alpha()
    except (OSError,pg.error) as e:
        raise RuntimeError('Falta el recurso '+ruta+'. Extrae el ZIP completo junto al archivo Python.') from e
FONDO_INICIO=pg.transform.smoothscale(cargar_imagen('fondo_inicio.png'),(ANCHO,ALTO))
HOJA_PERSONAJES=cargar_imagen('personajes.png')
# Coordenadas normalizadas de los cuatro retratos; excluyen las etiquetas.
RETRATOS=[]
for x,y,w,h in [(0,0,.5,.452),(.5,0,.5,.452),(0,.505,.5,.435),(.5,.505,.5,.435)]:
    sw,sh=HOJA_PERSONAJES.get_size()
    recorte=HOJA_PERSONAJES.subsurface(pg.Rect(round(x*sw),round(y*sh),round(w*sw),round(h*sh))).copy()
    RETRATOS.append(recorte.subsurface(recorte.get_bounding_rect()).copy())

def ajustar_imagen(imagen,ancho,alto):
    escala=min(ancho/imagen.get_width(),alto/imagen.get_height())
    return pg.transform.smoothscale(imagen,(max(1,round(imagen.get_width()*escala)),max(1,round(imagen.get_height()*escala))))
AVATARES=[ajustar_imagen(im,200,175) for im in RETRATOS]
SPRITES_HEROES=[ajustar_imagen(im,70,78) for im in RETRATOS]

# Secuencia de pasos: atlas original, precargado y sin rotar el cuerpo.
ATLAS_PASOS=cargar_imagen('caminata.png')
PASOS=[]
for fila in range(4):
    cuadros=[]
    # La cuarta celda de Roberto se descarta: pertenece a otro personaje.
    for columna in ([0,1,2,1] if fila==2 else [0,1,2,3]):
        w,h=ATLAS_PASOS.get_size()
        x0,x1=round(columna*w/4),round((columna+1)*w/4)
        y0,y1=round(fila*h/4),round((fila+1)*h/4)
        celda=ATLAS_PASOS.subsurface((x0,y0,x1-x0,y1-y0)).copy()
        limites=celda.get_bounding_rect(min_alpha=100)
        figura=celda.subsurface(limites).copy()
        figura=ajustar_imagen(figura,72,78)
        cuadros.append((figura,pg.transform.flip(figura,True,False)))
    PASOS.append(cuadros)
IDLE_HEROES=[(im,pg.transform.flip(im,True,False)) for im in SPRITES_HEROES]
SIMBOLO_MONEDA=pg.font.SysFont('dejavusans',21,bold=True).render('$',True,(92,49,8))

def dibujar_arma(surf,j):
    dx,dy=j.direccion
    lateral=(-dy,dx)
    disparando=j.destello>0
    retroceso=3 if disparando else 0
    largo=38 if j.arma else 29
    # Coordenadas locales: empuñadura, corredera, cañón y mano.
    origen=(j.x+dx*(8-retroceso),j.y+dy*(8-retroceso))
    def punto(u,v):
        return (round(origen[0]+dx*u+lateral[0]*v),round(origen[1]+dy*u+lateral[1]*v))
    def forma(color,coords):
        pg.draw.polygon(surf,color,[punto(u,v) for u,v in coords])
    forma((12,15,20),[(0,-6),(largo,-6),(largo,5),(13,5),(10,13),(2,12)])
    forma((126,139,153),[(2,-4),(largo-3,-4),(largo-3,1),(2,1)])
    forma((52,64,76),[(5,1),(largo-2,1),(largo-2,3),(5,3)])
    forma((96,62,38),[(3,4),(11,4),(8,11),(3,10)])
    if j.arma:
        forma((161,100,47),[(16,2),(28,2),(28,6),(16,6)])
    pg.draw.circle(surf,(25,21,22),punto(3,8),5)
    pg.draw.circle(surf,(234,176,123),punto(3,8),3)
    pg.draw.line(surf,(214,226,234),punto(7,-4),punto(12,-4),2)
    if disparando:
        forma((255,172,32),[(largo,-3),(largo+8,-7),(largo+6,-2),(largo+15,0),(largo+6,3),(largo+8,7),(largo,3)])
        pg.draw.circle(surf,(255,247,184),punto(largo+3,0),3)


def fondo_portada():
    pantalla.blit(FONDO_INICIO,(0,0))
    # Panel translúcido: asegura contraste sin ocultar a los personajes laterales.
    panel=pg.Surface((540,ALTO),pg.SRCALPHA)
    for x in range(540):
        alpha=round(170*min(1,x/90,(539-x)/90))
        pg.draw.line(panel,(5,10,20,alpha),(x,0),(x,ALTO))
    pantalla.blit(panel,((ANCHO-540)//2,0))

def texto_ajustado(f,texto,color,ancho):
    im=f.render(texto,True,color)
    if im.get_width()>ancho:
        im=pg.transform.smoothscale(im,(ancho,max(1,round(im.get_height()*ancho/im.get_width()))))
    return im

# ============ COLORES ============
NEGRO = (8, 10, 16)
BLANCO = (240, 240, 245)
GRIS = (70, 75, 85)
GRIS_OSCURO = (35, 40, 50)
GRIS_CLARO = (150, 155, 165)
VERDE = (60, 200, 110)
VERDE_OSCURO = (30, 120, 60)
ROJO = (220, 60, 80)
ROJO_OSCURO = (140, 30, 50)
AMARILLO = (240, 200, 70)
NARANJA = (240, 145, 50)
AZUL = (60, 140, 220)
MORADO = (150, 90, 210)
MARRON = (110, 75, 45)
SANGRE = (160, 30, 40)
SANGRE_OSCURA = (100, 15, 25)
PIEL = (235, 190, 150)
DORADO = (255, 215, 0)
CIAN = (80, 230, 240)

# ============ TEMAS CON CLIMA ============
TEMAS = [
    {"nombre": "Calles", "fondo": (48, 48, 55), "acento": (100, 100, 115), "clima": "soleado"},
    {"nombre": "Downtown", "fondo": (40, 45, 62), "acento": (70, 90, 130), "clima": "nublado"},
    {"nombre": "Hospital", "fondo": (52, 58, 65), "acento": (140, 200, 200), "clima": "lluvia"},
    {"nombre": "Base", "fondo": (42, 48, 45), "acento": (100, 130, 90), "clima": "niebla"},
    {"nombre": "Dead Zone", "fondo": (60, 38, 42), "acento": (200, 70, 80), "clima": "tormenta"},
    {"nombre": "Final", "fondo": (28, 26, 42), "acento": (140, 70, 200), "clima": "tormenta_arena"},
]

# ============ ARCHIVOS ============
BASE = os.path.dirname(os.path.abspath(__file__))
F_SCORES = os.path.join(BASE, "highscores.json")
F_CREDITOS = os.path.join(BASE, "creditos.json")
F_LOGROS = os.path.join(BASE, "logros.json")

def cargar_json(f, d):
    try:
        with open(f, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except (OSError, ValueError):
        return d


def guardar_json(f, d):
    try:
        with open(f+".tmp", "w", encoding="utf-8") as fp:
            json.dump(d, fp, indent=2, ensure_ascii=False)
        os.replace(f+".tmp", f)
        return True
    except OSError as error:
        print(f"No se pudo guardar {os.path.basename(f)}: {error}")
        return False

creditos = cargar_json(F_CREDITOS, {"cantidad": 0})
if not isinstance(creditos, dict) or type(creditos.get("cantidad")) is not int:
    creditos = {"cantidad": 0}
creditos["cantidad"] = max(0, creditos["cantidad"])
highscores = cargar_json(F_SCORES, [])
if not isinstance(highscores, list):
    highscores = []
highscores = [s for s in highscores if isinstance(s, dict)
              and isinstance(s.get("nombre"), str)
              and type(s.get("puntos")) is int and s["puntos"] >= 0
              and type(s.get("nivel")) is int and 1 <= s["nivel"] <= len(TEMAS)]
highscores.sort(key=lambda s:s["puntos"], reverse=True)
highscores = highscores[:10]
logros = cargar_json(F_LOGROS, {})
if not isinstance(logros, dict):
    logros = {}
if type(logros.get("_monedas_total")) is not int:
    logros["_monedas_total"] = 0
logros["_monedas_total"] = max(0,logros["_monedas_total"])

# ============ AUDIO PROCEDURAL ============
def gen_sonido(freq, dur, forma="sine", vol=0.25):
    # Sin NumPy: las muestras respetan la frecuencia y canales reales del mixer.
    if not AUDIO_OK:
        return None
    from array import array
    try:
        sr, formato, canales = pg.mixer.get_init()
        if formato != -16:
            return None
        muestras = array("h")
        for i in range(max(1,int(sr*dur))):
            t = i/sr
            seno = math.sin(2*math.pi*freq*t)
            if forma == "square": onda = 1 if seno >= 0 else -1
            elif forma == "saw": onda = 2*(t*freq-math.floor(t*freq+0.5))
            elif forma == "noise": onda = random.uniform(-1,1)
            else: onda = seno
            valor = max(-32768,min(32767,int(onda*math.exp(-3*t/dur)*32767*vol)))
            muestras.extend([valor]*canales)
        return pg.mixer.Sound(buffer=muestras.tobytes())
    except (pg.error, TypeError, ValueError) as error:
        print(f"Audio desactivado para un efecto: {error}")
        return None

S_DISPARO = gen_sonido(900, 0.06, "square", 0.15)
S_ZOMBIE = gen_sonido(120, 0.15, "saw", 0.2)
S_MUERTE = gen_sonido(80, 0.4, "saw", 0.3)
S_MONEDA = gen_sonido(1400, 0.08, "sine", 0.2)
S_POWERUP = gen_sonido(1800, 0.15, "square", 0.25)
S_HIT = gen_sonido(300, 0.08, "noise", 0.2)
S_JEFE = gen_sonido(60, 0.8, "saw", 0.4)
S_NIVEL = gen_sonido(1200, 0.3, "sine", 0.3)

# ============ AUDIO INTEGRADO ============
# Música original sintetizada al arrancar; no necesita MP3, WAV ni NumPy.
F_AUDIO = os.path.join(BASE, "audio_config.json")
config_audio = cargar_json(F_AUDIO, {})
if not isinstance(config_audio, dict): config_audio = {}

def volumen_valido(valor, predeterminado):
    if type(valor) not in (int,float) or not math.isfinite(valor):
        return predeterminado
    return max(0.0,min(1.0,float(valor)))

volumen_musica = volumen_valido(config_audio.get("musica"), 0.35)
volumen_efectos = volumen_valido(config_audio.get("efectos"), 0.70)
audio_silenciado = config_audio.get("silenciado") is True
ultima_reproduccion = {}
pista_actual = None
canal_musica = None
if AUDIO_OK:
    pg.mixer.set_num_channels(24)
    pg.mixer.set_reserved(4)  # Música, interfaz y alertas no compiten con disparos.
    canal_musica = pg.mixer.Channel(0)


def guardar_audio():
    guardar_json(F_AUDIO, {"musica":volumen_musica, "efectos":volumen_efectos,
                          "silenciado":audio_silenciado})


def aplicar_volumen():
    if not AUDIO_OK: return
    canal_musica.set_volume(0 if audio_silenciado else volumen_musica)
    pg.mixer.music.set_volume(0 if audio_silenciado else volumen_musica)
    for i in range(1,pg.mixer.get_num_channels()):
        pg.mixer.Channel(i).set_volume(0 if audio_silenciado else volumen_efectos)


def play(sonido, grupo="efecto", espera=45):
    if sonido is None or not AUDIO_OK or audio_silenciado: return
    ahora=pg.time.get_ticks()
    clave=id(sonido)
    if ahora-ultima_reproduccion.get(clave,-100000)<espera: return
    ultima_reproduccion[clave]=ahora
    if grupo == "menu": canal=pg.mixer.Channel(1)
    elif grupo == "alerta": canal=pg.mixer.Channel(2)
    else:
        canal=next((pg.mixer.Channel(i) for i in range(4,24)
                    if not pg.mixer.Channel(i).get_busy()),None)
        if canal is None: return
    canal.set_volume(volumen_efectos)
    canal.play(sonido)


def crear_musica(notas, bpm, tension=False):
    if not AUDIO_OK: return None
    from array import array
    try:
        sr,formato,canales=pg.mixer.get_init()
        if formato != -16: return None
        paso=60/bpm
        muestras=array("h")
        azar=random.Random(82)
        for nota in notas:
            frecuencia=440*2**((nota-69)/12)
            for i in range(round(sr*paso)):
                t=i/sr
                fase=t/paso
                env=min(1,t/.015)*min(1,(paso-t)/.045)
                melodia=(math.sin(math.tau*frecuencia*t)
                         +.22*math.sin(math.tau*frecuencia*2*t))*math.exp(-3*fase)
                bajo=.5*math.sin(math.tau*(frecuencia/4)*t)*math.sin(math.pi*fase)**2
                golpe=.24*math.sin(math.tau*65*t)*math.exp(-28*fase) if tension else 0
                ruido=azar.uniform(-1,1)*math.exp(-60*fase)*.10 if tension else 0
                valor=int((melodia*.20+bajo*.22+golpe+ruido)*env*24000)
                muestras.extend([max(-32768,min(32767,valor))]*canales)
        return pg.mixer.Sound(buffer=muestras.tobytes())
    except (pg.error,TypeError,ValueError) as error:
        print(f"No se pudo crear música: {error}")
        return None

MUSICA = {
    "menu":crear_musica([57,60,64,60,55,59,62,59,53,57,60,57,52,55,59,55],100),
    "mision":crear_musica([45,45,52,48,45,52,50,48,41,41,48,45,40,47,43,47],125,True),
    "jefe":crear_musica([40,41,40,47,40,43,41,47,38,39,38,45,40,41,43,47],155,True),
    "victoria":crear_musica([60,64,67,72,67,64,65,69],115),
    "derrota":crear_musica([52,50,48,45,43,40,38,33],90),
}
S_MENU=gen_sonido(620,.045,"sine",.16)
S_CONFIRMAR=gen_sonido(1050,.12,"sine",.20)
S_CREDITO=gen_sonido(1600,.18,"sine",.20)
S_GOLPE=gen_sonido(210,.10,"noise",.18)
S_ARMA=gen_sonido(450,.07,"square",.12)
S_LANZAR=gen_sonido(320,.12,"saw",.14)
S_EXPLOSION=gen_sonido(70,.55,"noise",.30)
S_TRUENO=gen_sonido(50,.85,"noise",.16)
S_ESCOPETA=gen_sonido(180,.14,"noise",.23)
S_IMPACTO=gen_sonido(180,.08,"noise",.12)
S_ALERTA=gen_sonido(760,.18,"square",.12)
S_LOGRO=gen_sonido(1900,.25,"sine",.19)


musica_externa = False
externa_iniciada = False
externa_pausada = False
ruta_musica_normal = None
ruta_musica_jefe = None
pista_externa_actual = None


def cargar_musica_fondo():
    global musica_externa, externa_iniciada, externa_pausada
    global ruta_musica_normal, ruta_musica_jefe, pista_externa_actual
    musica_externa = externa_iniciada = externa_pausada = False
    ruta_musica_normal = ruta_musica_jefe = pista_externa_actual = None
    if not AUDIO_OK: return

    # Música normal del juego.
    for nombre in ("musicfondo.mpeg", "musicfondo.mp3", "musicfondo.ogg", "musicfondo.wav"):
        ruta = os.path.join(BASE, nombre)
        if os.path.isfile(ruta):
            ruta_musica_normal = ruta
            print(f"[AUDIO] Música normal cargada: {nombre}")
            break

    # Música exclusiva de la habitación del jefe.
    ruta_jefe = os.path.join(BASE, "jefe.mpeg")
    if os.path.isfile(ruta_jefe):
        ruta_musica_jefe = ruta_jefe
        print("[AUDIO] Música del jefe cargada: jefe.mpeg")
    else:
        print("[AUDIO] No se encontró jefe.mpeg. Se usará la música normal en la sala del jefe.")

    musica_externa = ruta_musica_normal is not None
    if not musica_externa:
        print("[AUDIO] Se usará la música integrada.")


cargar_musica_fondo()


def cambiar_musica_externa(ruta, reiniciar=True):
    global externa_iniciada, externa_pausada, pista_externa_actual
    if not AUDIO_OK or not ruta: return False
    if pista_externa_actual == ruta and not reiniciar:
        return True
    try:
        pg.mixer.music.stop()
        pg.mixer.music.load(ruta)
        pg.mixer.music.play(loops=-1, fade_ms=350)
        pista_externa_actual = ruta
        externa_iniciada = True
        externa_pausada = False
        return True
    except (pg.error, OSError) as error:
        print(f"[AUDIO] No se pudo reproducir {os.path.basename(ruta)}: {error}")
        pg.mixer.music.stop()
        externa_iniciada = False
        externa_pausada = False
        pista_externa_actual = None
        return False


def actualizar_audio_base():
    global pista_actual, musica_externa, externa_iniciada, externa_pausada
    if not AUDIO_OK: return

    # La música externa tiene prioridad. En la sala del jefe cambia a jefe.mpeg;
    # cuando el jefe muere, vuelve automáticamente a musicfondo.
    if musica_externa and ruta_musica_normal:
        if estado == PAUSA:
            if externa_iniciada and not externa_pausada:
                pg.mixer.music.pause()
                externa_pausada = True
            aplicar_volumen()
            return

        if externa_pausada:
            pg.mixer.music.unpause()
            externa_pausada = False

        if estado == JUGANDO and jefe_actual and jefe_actual.vida > 0 and ruta_musica_jefe:
            pista_deseada = ruta_musica_jefe
        else:
            pista_deseada = ruta_musica_normal

        if pista_deseada != pista_externa_actual or not pg.mixer.music.get_busy():
            cambiar_musica_externa(pista_deseada)
        aplicar_volumen()
        return

    if estado == PAUSA:
        canal_musica.pause()
        return
    canal_musica.unpause()
    if estado == JUGANDO:
        pista="jefe" if jefe_actual and jefe_actual.vida>0 else "mision"
    elif estado in (VICTORIA,NIVEL_COMPLETO): pista="victoria"
    elif estado == GAME_OVER: pista="derrota"
    else: pista="menu"
    if pista != pista_actual:
        canal_musica.stop()
        sonido=MUSICA.get(pista)
        if sonido is not None:
            canal_musica.play(sonido, loops=0 if pista in ("victoria","derrota") else -1,
                              fade_ms=180)
        pista_actual=pista
    aplicar_volumen()

# Un canal independiente permite oír zombis y música simultáneamente.
SONIDOS_ZOMBIS = {}
canal_zombis = pg.mixer.Channel(3) if AUDIO_OK else None
nivel_audio_zombi = None
espera_zombi = 0.8
volumen_zombi = 0.0
zombi_en_pausa = False


def cargar_voces_zombi():
    SONIDOS_ZOMBIS.clear()
    if not AUDIO_OK: return
    for nombre in ("zomb1", "zomb2"):
        for carpeta in (BASE, os.path.join(BASE,"audio")):
            for extension in (".mpeg", ".mp3", ".ogg", ".wav"):
                ruta=os.path.join(carpeta,nombre+extension)
                if not os.path.isfile(ruta): continue
                try:
                    SONIDOS_ZOMBIS[nombre]=pg.mixer.Sound(ruta)
                    print(f"[AUDIO] Voz cargada: {nombre+extension}")
                    break
                except (pg.error,OSError) as error:
                    print(f"[AUDIO] No se pudo abrir {nombre+extension}: {error}")
            if nombre in SONIDOS_ZOMBIS: break
        if nombre not in SONIDOS_ZOMBIS:
            SONIDOS_ZOMBIS[nombre]=S_ZOMBIE
            print(f"[AUDIO] {nombre}: se usará el gruñido integrado.")


cargar_voces_zombi()


def actualizar_voces_zombi(dt):
    global nivel_audio_zombi, espera_zombi, volumen_zombi, zombi_en_pausa
    if not AUDIO_OK: return
    if estado == PAUSA:
        if not zombi_en_pausa:
            canal_zombis.pause()
            zombi_en_pausa=True
        canal_zombis.set_volume(0 if audio_silenciado else volumen_zombi*volumen_efectos)
        return
    if zombi_en_pausa:
        canal_zombis.unpause()
        zombi_en_pausa=False
    if estado != JUGANDO:
        canal_zombis.stop()
        nivel_audio_zombi=None
        espera_zombi=.8
        return
    if nivel_audio_zombi != nivel_actual:
        canal_zombis.stop()
        nivel_audio_zombi=nivel_actual
        espera_zombi=.8
    vivos=[j for j in jugadores if j.vida>0]
    cercanos=[z for z in zombies if z.vida>0 and vivos]
    distancia=min((math.hypot(z.x-j.x,z.y-j.y) for z in cercanos for j in vivos),default=1000)
    if distancia > 480:
        canal_zombis.stop()
        espera_zombi=max(.5,espera_zombi)
        return
    volumen_zombi=.25+.55*(1-min(1,distancia/480))
    canal_zombis.set_volume(0 if audio_silenciado else volumen_zombi*volumen_efectos)
    espera_zombi=max(0,espera_zombi-dt)
    if not audio_silenciado and espera_zombi<=0 and not canal_zombis.get_busy():
        sonido=SONIDOS_ZOMBIS["zomb1" if nivel_actual%2==0 else "zomb2"]
        if sonido:
            canal_zombis.play(sonido,maxtime=3500,fade_ms=90)
        espera_zombi=random.uniform(4,7)


def actualizar_audio(dt=1/60):
    actualizar_audio_base()
    actualizar_voces_zombi(dt)


def tecla_audio(tecla):
    global audio_silenciado,volumen_musica,volumen_efectos
    if tecla == pg.K_F1: audio_silenciado=not audio_silenciado
    elif tecla == pg.K_F2: volumen_musica=max(0,round(volumen_musica-.1,2))
    elif tecla == pg.K_F3: volumen_musica=min(1,round(volumen_musica+.1,2))
    elif tecla == pg.K_F4: volumen_efectos=max(0,round(volumen_efectos-.1,2))
    elif tecla == pg.K_F5: volumen_efectos=min(1,round(volumen_efectos+.1,2))
    else: return False
    aplicar_volumen()
    guardar_audio()
    return True

aplicar_volumen()

# ============ JOYSTICKS ============
joysticks = []
def actualizar_mandos():
    global joysticks
    joysticks = []
    for i in range(pg.joystick.get_count()):
        try:
            j = pg.joystick.Joystick(i); j.init(); joysticks.append(j)
        except: pass
    for j in jugadores: j.joy_index = j.num-1 if j.num<=len(joysticks) else -1

def btn(idx, b):
    if not (0<=idx<len(joysticks)): return False
    try: return 0<=b<joysticks[idx].get_numbuttons() and joysticks[idx].get_button(b)
    except: return False

def dir_joy(idx):
    if not (0<=idx<len(joysticks)): return (0,0)
    try:
        j = joysticks[idx]
        if j.get_numhats():
            x,y = j.get_hat(0)
            if x or y: return x,-y
        if j.get_numaxes()>=2:
            x,y = j.get_axis(0), j.get_axis(1)
            return (x if abs(x)>0.25 else 0, y if abs(y)>0.25 else 0)
    except: pass
    return (0,0)

# ============ ESTADOS ============
MENU, INSERT_COIN, INSTRUCCIONES, HISTORIA, SELECCION = "menu","coin","instr","hist","sel"
JUGANDO, PAUSA, NIVEL_COMPLETO, GAME_OVER, VICTORIA, HIGHSCORES = "jug","pau","nc","go","vic","hs"

estado = INSERT_COIN
nivel_actual = 0
escena_historia = 0
coop = False
opcion_menu = 0
seleccionados = [0,1]
turno_seleccion = 0
cursor_personaje = 0

# ============ NIVELES ============
NIVELES = [
    {"nombre":"Calles Abandonadas","zombies":5,"monedas":10,"botiquines":2,"obstaculos":5,"salas":6,"tiempo":150},
    {"nombre":"Downtown","zombies":8,"monedas":14,"botiquines":3,"obstaculos":8,"salas":7,"tiempo":170},
    {"nombre":"Hospital","zombies":10,"monedas":12,"botiquines":4,"obstaculos":10,"salas":8,"tiempo":190,"jefe":True},
    {"nombre":"Base Militar","zombies":12,"monedas":15,"botiquines":3,"obstaculos":12,"salas":8,"tiempo":200},
    {"nombre":"Dead Zone","zombies":16,"monedas":18,"botiquines":2,"obstaculos":15,"salas":9,"tiempo":220},
    {"nombre":"Last Extraction","zombies":20,"monedas":20,"botiquines":3,"obstaculos":18,"salas":10,"tiempo":240,"jefe":True},
]

PERSONAJES = [
    {"nombre":"Obed","color":ROJO,"desc":"Líder del equipo"},
    {"nombre":"Alexis","color":AZUL,"desc":"Explorador veloz"},
    {"nombre":"Roberto","color":NARANJA,"desc":"Fuerza bruta"},
    {"nombre":"Daniel","color":CIAN,"desc":"Táctico preciso"},
]

# ============ HISTORIA ============
def preparar_historia():
    global INTRO, DESCUBRIMIENTO, ESCENAS_HISTORIA, voz_final
    idx = seleccionados[:2 if coop else 1]
    activos = " y ".join(PERSONAJES[i]["nombre"] for i in idx)
    ausentes = [p["nombre"] for i,p in enumerate(PERSONAJES) if i not in idx]
    buscados = ", ".join(ausentes[:-1])+" y "+ausentes[-1] if len(ausentes)>1 else ausentes[0]
    voz_final = ausentes[0]
    INTRO = [
        {"titulo":"ANTES DEL APOCALIPSIS","texto":["Obed, Alexis, Roberto y Daniel","regresan de una misión.","Un reporte anuncia una enfermedad."],"color":(35,45,65)},
        {"titulo":"EL BROTE","texto":["Los hospitales colapsan.","Los cuatro compañeros reciben","una llamada urgente."],"color":(65,30,35)},
        {"titulo":"LA PROMESA","texto":["Preparan su equipo.","«Pase lo que pase,","volveremos a encontrarnos.»"],"color":(55,35,55)},
        {"titulo":"LA CIUDAD CAE","texto":["Los infectados desbordan las defensas.","Los compañeros quedan","separados entre el caos."],"color":(55,30,30)},
        {"titulo":"EL PUNTO DE REUNIÓN","texto":[f"{activos}: la búsqueda comienza.","El refugio está vacío.","Solo quedan suministros y una radio."],"color":(30,35,45)},
        {"titulo":"SEIS MESES DESPUÉS","texto":["La ciudad está en ruinas.","El objetivo sigue siendo","encontrar a "+buscados+"."],"color":(30,40,40)},
        {"titulo":"LA TRANSMISIÓN","texto":["Una vieja radio emite una señal.","Menciona una base militar.","Podría ser una pista."],"color":(30,40,55)},
        {"titulo":"LA MISIÓN","texto":["Recorre las salas del piso.","Sobrevive a los infectados.","Derrota al jefe de la zona."],"color":(25,45,40)},
    ]
    DESCUBRIMIENTO = [
        {"titulo":"EL DESCUBRIMIENTO","texto":["Aparecen registros de evacuación.",f"La lista incluye a {buscados}.","Salieron con vida."],"color":(30,45,55)},
        {"titulo":"UNA NUEVA ESPERANZA","texto":["Los registros señalan un refugio.","Todavía hay una oportunidad.","«No vamos a dejar a nadie atrás.»"],"color":(35,40,55)},
    ]
    ESCENAS_HISTORIA = INTRO

preparar_historia()

# ============ VARIABLES ============
jugadores, zombies, balas, monedas, botiquines, particulas, obstaculos = [],[],[],[],[],[],[]
sangre_piso = []
monedas_obtenidas = 0
tiempo_restante = 0
tiempo_extraccion = 0
puntuacion_total = 0
mensaje_flotante = ""
tiempo_mensaje = 0
efectos = {"shake":0,"flash":0,"flash_color":BLANCO}
estrellas = [(random.randint(0,ANCHO),random.randint(0,ALTO),random.uniform(0.3,1.5)) for _ in range(120)]
jefe_actual = None
jefe_alertado = False
daño_nivel = False

# ============ MAPA TIPO ISAAC ============
# Cada sala ocupa una pantalla; las puertas conectan salas vecinas.
INTERIOR_X0, INTERIOR_X1 = 40, ANCHO-40
INTERIOR_Y0, INTERIOR_Y1 = 115, ALTO-40
MID_X, MID_Y = ANCHO//2, (INTERIOR_Y0+INTERIOR_Y1)//2
ANCHO_PUERTA = 80
DIRS_SALA = {"N":(0,-1),"S":(0,1),"O":(-1,0),"E":(1,0)}
PUERTA_POS = {"N":(MID_X,INTERIOR_Y0),"S":(MID_X,INTERIOR_Y1),
              "O":(INTERIOR_X0,MID_Y),"E":(INTERIOR_X1,MID_Y)}
# Punto de aparición al entrar por la puerta opuesta de la sala nueva.
SPAWN_PUERTA = {"N":(MID_X,INTERIOR_Y1-55),"S":(MID_X,INTERIOR_Y0+55),
                "O":(INTERIOR_X1-55,MID_Y),"E":(INTERIOR_X0+55,MID_Y)}
def rect_puerta(d):
    x,y=PUERTA_POS[d]
    if d=="N": return (x-ANCHO_PUERTA//2,80,ANCHO_PUERTA,INTERIOR_Y0-80)
    if d=="S": return (x-ANCHO_PUERTA//2,INTERIOR_Y1,ANCHO_PUERTA,ALTO-INTERIOR_Y1)
    if d=="O": return (0,y-ANCHO_PUERTA//2,INTERIOR_X0,ANCHO_PUERTA)
    return (INTERIOR_X1,y-ANCHO_PUERTA//2,ANCHO-INTERIOR_X1,ANCHO_PUERTA)
mapa_salas = {}
sala_actual = None
transicion = None
actualizar_mandos()

# ============ EFECTOS ============
def shake(i=10): efectos["shake"] = i
def flash(c=BLANCO,d=10): efectos["flash"]=d; efectos["flash_color"]=c

# ============ DIBUJADO DE FONDO CON GRADIENTE ============
def crear_fondo_gradiente(tema):
    surf = pg.Surface((ANCHO,ALTO))
    color = tema["fondo"]
    for y in range(ALTO):
        factor = y/ALTO
        r = int(color[0]*(0.7+0.5*factor))
        g = int(color[1]*(0.7+0.5*factor))
        b = int(color[2]*(0.7+0.5*factor))
        pg.draw.line(surf,(min(r,255),min(g,255),min(b,255)),(0,y),(ANCHO,y))
    # Cuadrícula
    for x in range(0,ANCHO,60):
        pg.draw.line(surf,tuple(max(0,c-15) for c in color),(x,80),(x,ALTO),1)
    for y in range(80,ALTO,60):
        pg.draw.line(surf,tuple(max(0,c-15) for c in color),(0,y),(ANCHO,y),1)
    # Viñeta
    v = pg.Surface((ANCHO,ALTO),pg.SRCALPHA)
    for i in range(150):
        pg.draw.rect(v,(0,0,0,int(i*0.35)),(i,i,ANCHO-i*2,ALTO-i*2),1)
    surf.blit(v,(0,0))
    return surf

fondos_cache = {}

def dibujar_fondo(tema):
    k = tema["nombre"]
    if k not in fondos_cache:
        fondos_cache[k] = crear_fondo_gradiente(tema)
    pantalla.blit(fondos_cache[k],(0,0))

# ============ DIBUJAR CLIMA ============
clima_particulas = []

def actualizar_clima(tema):
    global clima_particulas
    tipo = tema["clima"]
    # Spawn
    if tipo == "lluvia":
        for _ in range(8): clima_particulas.append({"x":random.randint(0,ANCHO),"y":-10,"vx":-2,"vy":14,"t":0,"tipo":"lluvia"})
    elif tipo == "tormenta":
        for _ in range(12): clima_particulas.append({"x":random.randint(0,ANCHO),"y":-10,"vx":-3,"vy":18,"t":0,"tipo":"lluvia"})
        if random.random() < 0.005: flash(BLANCO,15); play(S_TRUENO,espera=1500)
    elif tipo == "tormenta_arena":
        for _ in range(6): clima_particulas.append({"x":random.randint(0,ANCHO),"y":random.randint(80,ALTO),"vx":-6,"vy":random.uniform(-1,1),"t":0,"tipo":"arena"})
    elif tipo == "niebla":
        for _ in range(2): clima_particulas.append({"x":random.randint(0,ANCHO),"y":random.randint(80,ALTO),"vx":random.uniform(-0.5,0.5),"vy":random.uniform(-0.3,0.3),"t":0,"tipo":"niebla"})
    # Update
    for p in clima_particulas[:]:
        p["x"] += p["vx"]; p["y"] += p["vy"]; p["t"] += 1
        if p["y"]>ALTO+20 or p["x"]<-20 or p["t"]>300:
            clima_particulas.remove(p)

def dibujar_clima():
    for p in clima_particulas:
        if p["tipo"] == "lluvia":
            pg.draw.line(pantalla,(120,150,200,180),(p["x"],p["y"]),(p["x"]+2,p["y"]+10),1)
        elif p["tipo"] == "arena":
            s = pg.Surface((4,4),pg.SRCALPHA)
            pg.draw.circle(s,(200,180,120,100),(2,2),2)
            pantalla.blit(s,(p["x"],p["y"]))
        elif p["tipo"] == "niebla":
            s = pg.Surface((80,80),pg.SRCALPHA)
            pg.draw.circle(s,(180,180,190,20),(40,40),40)
            pantalla.blit(s,(p["x"]-40,p["y"]-40))

# ============ CLASES ============
class Jugador:
    def __init__(self,x,y,num,color,ji):
        self.x,self.y=x,y
        self.num=num
        p=PERSONAJES[seleccionados[num-1]]
        self.nombre=p["nombre"]; self.color=p["color"]
        self.sprite_indice=seleccionados[num-1]
        self.ultimo_movimiento=-1000
        self.mira_izquierda=False
        self.joy_index=ji
        self.radio=18; self.velocidad=3.5
        self.vida=100; self.vida_max=100
        self.botiquines=2; self.monedas=0
        self.recarga_habilidad=0; self.impulso=0
        self.direccion=(0,-1)
        self.tiempo_disparo=0; self.invencible=0
        self.destello=0
        self.anim=0; self.vel_actual=0
        self.tiempo_melee=0; self.energia=100.0
        self.arma=0; self.granadas=2; self.escudo=0

    def mover(self,dx,dy):
        if self.vida<=0 or (dx==0 and dy==0): return
        m=math.hypot(dx,dy); dx,dy=dx/m,dy/m
        mover_col(self,dx*self.velocidad,dy*self.velocidad)
        self.direccion=(dx,dy); self.anim+=0.25
        self.ultimo_movimiento=pg.time.get_ticks()
        if dx: self.mira_izquierda=dx<0

    def disparar(self):
        if self.vida<=0 or self.tiempo_disparo>0: return
        self.tiempo_disparo=12 if self.arma==0 else 35
        self.destello=4
        if self.impulso: self.tiempo_disparo=max(5,self.tiempo_disparo//2)
        inicio_balas=len(balas)
        dx,dy=self.direccion
        ang=math.atan2(dy,dx)
        offsets=[0] if self.arma==0 else [-0.18,0,0.18]
        for off in offsets:
            ax,ay=math.cos(ang+off),math.sin(ang+off)
            balas.append(Bala(self.x+ax*(46 if self.arma else 37),self.y+ay*(46 if self.arma else 37),ax,ay))
        for b in balas[inicio_balas:]: b.dano=20+5*mejoras[self.num-1]["dano"]
        play(S_DISPARO if self.arma==0 else S_ESCOPETA)
        for _ in range(6):
            particulas.append(Particula(self.x+dx*(46 if self.arma else 37),self.y+dy*(46 if self.arma else 37),AMARILLO,4,10))

    def golpear(self):
        if self.vida<=0 or self.tiempo_melee>0: return
        self.tiempo_melee=30
        play(S_GOLPE)
        for z in zombies[:]:
            dx,dy=z.x-self.x,z.y-self.y
            d=math.hypot(dx,dy)
            frente=(dx*self.direccion[0]+dy*self.direccion[1])/max(d,1)
            if d<65+z.radio and frente>0.2:
                z.recibir_daño(35)
                mover_col(z,dx/max(d,1)*15,dy/max(d,1)*15)
                for _ in range(8):
                    particulas.append(Particula(z.x,z.y,SANGRE,4,15))
        for _ in range(15):
            particulas.append(Particula(self.x+self.direccion[0]*40,self.y+self.direccion[1]*40,BLANCO,4,12))

    def curar(self):
        if self.vida>0 and self.botiquines>0 and self.vida<self.vida_max:
            self.vida=min(self.vida+40,self.vida_max)
            self.botiquines-=1
            play(S_POWERUP); flash(VERDE,6)
            return True
        return False

    def lanzar_granada(self):
        if self.vida>0 and self.granadas>0:
            play(S_LANZAR)
            self.granadas-=1
            dx,dy=self.direccion
            particulas.append(Granada(self.x+dx*30,self.y+dy*30,dx*7,dy*7))

    def recibir_daño(self,c):
        global daño_nivel
        if c <= 0: return
        if self.vida<=0 or self.invencible>0 or self.escudo>0: return
        daño_nivel=True
        self.vida-=c; self.invencible=30
        shake(8); flash(ROJO,8); play(S_HIT)
        if self.vida<0: self.vida=0

    def update(self):
        if self.destello>0: self.destello-=1
        self.recarga_habilidad=max(0,self.recarga_habilidad-1)
        self.impulso=max(0,self.impulso-1)
        if self.tiempo_melee>0: self.tiempo_melee-=1
        if self.tiempo_disparo>0: self.tiempo_disparo-=1
        if self.invencible>0: self.invencible-=1
        if self.escudo>0: self.escudo-=1

    def dibujar(self,surf):
        if self.vida<=0:
            pg.draw.line(surf,GRIS_CLARO,(self.x-14,self.y-14),(self.x+14,self.y+14),4)
            pg.draw.line(surf,GRIS_CLARO,(self.x+14,self.y-14),(self.x-14,self.y+14),4)
            return
        if self.invencible>0 and (self.invencible//5)%2==0: return
        # Escudo
        if self.escudo>0:
            pulso=abs(math.sin(pg.time.get_ticks()/150))*5
            s=pg.Surface((int((self.radio+pulso)*4),int((self.radio+pulso)*4)),pg.SRCALPHA)
            pg.draw.circle(s,(100,200,255,80),(int((self.radio+pulso)*2),int((self.radio+pulso)*2)),int(self.radio+pulso))
            surf.blit(s,(self.x-(self.radio+pulso)*2,self.y-(self.radio+pulso)*2))
        # Sombra
        som=pg.Surface((self.radio*2+16,self.radio+12),pg.SRCALPHA)
        pg.draw.ellipse(som,(0,0,0,120),(0,0,self.radio*2+16,self.radio))
        surf.blit(som,(self.x-self.radio-8,self.y+self.radio-5))
        # Aura
        aura=pg.Surface((self.radio*5,self.radio*5),pg.SRCALPHA)
        pg.draw.circle(aura,(*self.color,25),(int(self.radio*2.5),int(self.radio*2.5)),int(self.radio*1.8))
        surf.blit(aura,(self.x-self.radio*2.5,self.y-self.radio*2.5))
        caminando=pg.time.get_ticks()-self.ultimo_movimiento<80
        fase=int(self.anim*1.4)%4 if caminando else 1
        im=PASOS[self.sprite_indice][fase][int(self.mira_izquierda)]
        if not caminando:
            # Descanso con ambos pies apoyados: retrato aprobado original.
            im=IDLE_HEROES[self.sprite_indice][int(self.mira_izquierda)]
        im=aplicar_skin(im,self.sprite_indice)
        surf.blit(im,im.get_rect(midbottom=(round(self.x),round(self.y+18))))
        dibujar_arma(surf,self)
        # Nombre
        t=fuente_peq.render(f"P{self.num} {self.nombre}",True,BLANCO)
        surf.blit(t,t.get_rect(center=(self.x,self.y-76)))
        # Barra vida
        ab=48; xb=self.x-ab//2; yb=self.y-94
        pg.draw.rect(surf,GRIS_OSCURO,(xb-1,yb-1,ab+2,8),border_radius=3)
        av=int(ab*max(0,min(self.vida,self.vida_max))/self.vida_max)
        cv=VERDE if self.vida>60 else AMARILLO if self.vida>30 else ROJO
        pg.draw.rect(surf,cv,(xb,yb,av,6),border_radius=2)
        # Barra energía
        ye=yb+9
        pg.draw.rect(surf,GRIS_OSCURO,(xb-1,ye-1,ab+2,5),border_radius=2)
        ee=int(ab*self.energia/100)
        pg.draw.rect(surf,CIAN,(xb,ye,ee,3),border_radius=1)


SPRITES_ZOMBIS = {}


def crear_sprite_zombi(tipo, fase, ataque=False, jefe=False):
    """Caricatura vectorial original, dibujada al doble para suavizar bordes."""
    lienzo=pg.Surface((192,224),pg.SRCALPHA)
    borde=(24,28,23)
    piel={"normal":(118,163,69),"rapido":(138,186,86),"tanque":(107,141,61),
          "escupe":(144,177,63),"explosivo":(125,158,65)}.get(tipo,(118,163,69))
    camisa={"normal":(92,108,137),"rapido":(107,79,105),"tanque":(215,154,43),
            "escupe":(128,97,60),"explosivo":(177,75,48)}.get(tipo,(92,108,137))
    if jefe: camisa=(134,44,50)
    paso=math.sin(fase*math.tau/8)
    salto=abs(paso)*2 if not ataque else 2
    def puntos(ps): return [(round(x*2),round((y-salto)*2)) for x,y in ps]
    def pol(color,ps):
        pg.draw.polygon(lienzo,color,puntos(ps));pg.draw.polygon(lienzo,borde,puntos(ps),5)
    def el(color,r,contorno=3):
        x,y,w,h=r;rect=pg.Rect(round(x*2),round((y-salto)*2),round(w*2),round(h*2))
        pg.draw.ellipse(lienzo,color,rect)
        if contorno:pg.draw.ellipse(lienzo,borde,rect,contorno*2)
    def linea(color,ps,ancho=2): pg.draw.lines(lienzo,color,False,puntos(ps),ancho*2)
    # Botas y piernas alternadas.
    for x,oscilacion in [(38,paso*4),(55,-paso*4)]:
        pol((76,64,50),[(x,83),(x+10,83),(x+10+oscilacion,100),(x+oscilacion,100)])
        el((44,43,39),(x-3+oscilacion,96,19,9),2)
    # Brazo lejano extendido.
    alcance=8 if ataque else paso*2
    linea(borde,[(57,68),(72,65),(80+alcance,60)],9)
    linea(piel,[(57,68),(72,65),(80+alcance,60)],5)
    # Camisa rasgada, cuello y costura.
    pol(camisa,[(33,57),(58,57),(65,78),(62,92),(55,89),(50,94),(44,90),(32,92),(30,72)])
    linea((55,57,47),[(45,66),(47,87)],2)
    pol(piel,[(35,86),(44,88),(36,92)])
    # Oreja y cabeza grande inclinada: ojos desiguales y mandíbula.
    el(piel,(18,41,18,19),2)
    el(piel,(24,16,51,51),3)
    linea((71,100,43),[(26,48),(22,47),(23,53)],2)
    el((235,209,78),(40,32,19,23),3)
    el((246,223,103),(59,28,16,20),3)
    el((28,30,24),(51,40,4,7),0)
    el((28,30,24),(68,34,4,6),0)
    el((255,245,194),(49,36,3,3),0)
    pol((49,42,32),[(44,57),(63,53),(63,62),(53,66)])
    pol((239,223,167),[(51,57),(56,56),(56,61),(51,62)])
    linea((66,101,43),[(32,31),(39,29)],2)
    el((78,113,42),(31,52,4,3),0)
    # Variantes reconocibles como en la referencia.
    if tipo in ("normal","rapido") and not jefe:
        pol((48,43,36),[(25,40),(20,25),(23,15),(28,20),(39,7),(39,16),
                       (52,8),(71,17),(78,27),(62,25),(53,21),(54,29),(37,26),(35,44)])
        linea((78,68,51),[(29,22),(39,17),(56,15)],2)
    elif tipo in ("tanque","explosivo") and not jefe:
        el((229,173,36),(23,11,53,28),3)
        pol((239,192,42),[(22,32),(79,27),(81,34),(21,41)])
        linea((251,216,92),[(46,15),(43,29)],4)
        el((111,86,45),(27,19,11,8),2)
    else:
        el((208,103,115),(29,10,37,27),3)
        linea((94,43,51),[(39,14),(44,18),(39,23),(46,26),(43,33)],2)
        linea((94,43,51),[(52,13),(49,20),(57,25),(53,31)],2)
        if jefe: linea((228,157,163),[(32,19),(36,16)],2)
    # Brazo cercano con dedos, balanceo al andar y extensión al atacar.
    hx=72+alcance;hy=76+(0 if ataque else paso*2)
    linea(borde,[(36,69),(47,77),(hx,hy)],10)
    linea(camisa,[(36,69),(46,76)],7)
    linea(piel,[(48,77),(hx,hy)],6)
    el(piel,(hx-5,hy-5,12,11),2)
    for dx,dy in [(4,-4),(7,0),(5,4)]:
        linea(borde,[(hx,hy),(hx+dx,hy+dy)],4)
        linea(piel,[(hx,hy),(hx+dx,hy+dy)],2)
    if tipo=="escupe": el((169,213,56),(65,62,4,9),1)
    return lienzo


def sprite_zombi(z):
    fase=int(z.anim*2)%8
    ataque=z.tiempo_ataque>25
    clave=(z.tipo,z.es_jefe,fase,ataque,z.mira_izquierda)
    if clave not in SPRITES_ZOMBIS:
        original=crear_sprite_zombi(z.tipo,fase,ataque,z.es_jefe)
        ancho=150 if z.es_jefe else 83 if z.tipo=="tanque" else 70
        alto=round(ancho*224/192)
        img=pg.transform.smoothscale(original,(ancho,alto))
        if z.mira_izquierda:img=pg.transform.flip(img,True,False)
        SPRITES_ZOMBIS[clave]=img
    return SPRITES_ZOMBIS[clave]


def dibujar_zombi_animado(z,surf):
    img=sprite_zombi(z)
    sombra=pg.Surface((z.radio*3,20),pg.SRCALPHA)
    pg.draw.ellipse(sombra,(0,0,0,95),sombra.get_rect())
    surf.blit(sombra,(round(z.x-sombra.get_width()/2),round(z.y+z.radio-8)))
    rect=img.get_rect(midbottom=(round(z.x),round(z.y+z.radio+5)))
    surf.blit(img,rect)
    if z.vida<z.vida_max or z.es_jefe:
        ab=100 if z.es_jefe else 42
        x,y=round(z.x-ab/2),rect.top-9
        pg.draw.rect(surf,GRIS_OSCURO,(x-1,y-1,ab+2,7),border_radius=3)
        pg.draw.rect(surf,ROJO,(x,y,round(ab*max(0,min(1,z.vida/z.vida_max))),5),border_radius=2)
        if z.es_jefe:
            txt=fuente_peq.render("JEFE",True,ROJO)
            surf.blit(txt,txt.get_rect(midbottom=(round(z.x),y-4)))


class Zombie:
    def __init__(self,x,y,tipo=None):
        self.x,self.y=x,y
        self.radio=16
        self.velocidad=random.uniform(0.8,1.6)
        self.vida=30; self.vida_max=30
        self.daño=8; self.tiempo_ataque=0
        self.tipo=tipo or random.choice(["normal","normal","rapido","tanque","escupe","explosivo"])
        self.anim=random.uniform(0,6.28)
        self.es_jefe=False
        self.mira_izquierda=False
        self.cooldown_habilidad=0
        if self.tipo=="rapido":
            self.velocidad*=1.8; self.vida=20; self.radio=14
        elif self.tipo=="tanque":
            self.velocidad*=0.6; self.vida=70; self.radio=21
        elif self.tipo=="escupe":
            self.velocidad*=0.7; self.vida=35; self.radio=17
        elif self.tipo=="explosivo":
            self.velocidad*=1.2; self.vida=25; self.radio=18
        self.vida_max=self.vida

    def update(self,jugs,obs):
        vivos=[j for j in jugs if j.vida>0]
        if not vivos or self.vida<=0: return
        obj=min(vivos,key=lambda j:math.hypot(j.x-self.x,j.y-self.y))
        dx,dy=obj.x-self.x,obj.y-self.y
        d=math.hypot(dx,dy)
        if abs(dx)>2:self.mira_izquierda=dx<0
        self.anim+=0.15 if d<500 else 0.025
        if self.tiempo_ataque>0: self.tiempo_ataque-=1
        if self.cooldown_habilidad>0: self.cooldown_habilidad-=1
        if d<500:
            if d>self.radio+obj.radio+2:
                mover_col(self,dx/d*self.velocidad,dy/d*self.velocidad)
            elif self.tiempo_ataque<=0:
                if self.tipo=="explosivo":
                    self.explotar(); return
                obj.recibir_daño(self.daño); self.tiempo_ataque=40
        if self.tipo=="escupe" and 0<d<250 and self.cooldown_habilidad<=0:
            balas.append(BalaZombie(self.x,self.y,dx/d*4,dy/d*4))
            self.cooldown_habilidad=90

    def explotar(self):
        play(S_EXPLOSION)
        for j in jugadores:
            if math.hypot(j.x-self.x,j.y-self.y)<80: j.recibir_daño(25)
        for _ in range(40): particulas.append(Particula(self.x,self.y,NARANJA,7,25))
        self.vida=0

    def recibir_daño(self,c): self.vida-=c
    def esta_vivo(self): return self.vida>0

    def dibujar(self,surf):
        dibujar_zombi_animado(self,surf)


class Jefe(Zombie):
    def __init__(self,x,y):
        super().__init__(x,y,"tanque")
        self.vida=500; self.vida_max=500
        self.radio=45; self.daño=20
        self.es_jefe=True
        self.velocidad=0.8
        self.fase=1
        self.anim_ataque=0

    def update(self,jugs,obs):
        if self.vida<=0 or not any(j.vida>0 for j in jugs): return
        super().update(jugs,obs)
        if self.vida<self.vida_max*0.5: self.fase=2
        if self.fase==2 and self.cooldown_habilidad<=0 and len(zombies)<60:
            # Invoca zombies
            for _ in range(2):
                ang=random.uniform(0,6.28)
                x,y=self.x+math.cos(ang)*80,self.y+math.sin(ang)*80
                if libre(x,y,14):
                    zombies.append(Zombie(x,y,"rapido"))
            self.cooldown_habilidad=180

    def dibujar(self,surf):
        dibujar_zombi_animado(self,surf)


class Bala:
    def __init__(self,x,y,dx,dy):
        self.x,self.y=x,y
        self.dx,self.dy=dx,dy
        self.velocidad=13; self.vida=80
        self.trail=[]
    def update(self):
        self.trail.append((self.x,self.y))
        if len(self.trail)>6: self.trail.pop(0)
        self.x+=self.dx*self.velocidad; self.y+=self.dy*self.velocidad
        self.vida-=1
        return self.vida>0 and INTERIOR_X0<self.x<INTERIOR_X1 and INTERIOR_Y0<self.y<INTERIOR_Y1
    def dibujar(self,surf):
        for i,(tx,ty) in enumerate(self.trail):
            alpha=int(255*(i/len(self.trail)))
            tam=max(1,5-(len(self.trail)-i))
            s=pg.Surface((tam*2,tam*2),pg.SRCALPHA)
            pg.draw.circle(s,(255,200,80,alpha),(tam,tam),tam)
            surf.blit(s,(tx-tam,ty-tam))
        # Glow
        g=pg.Surface((20,20),pg.SRCALPHA)
        pg.draw.circle(g,(255,255,180,100),(10,10),10)
        surf.blit(g,(self.x-10,self.y-10))
        pg.draw.circle(surf,BLANCO,(int(self.x),int(self.y)),5)
        pg.draw.circle(surf,AMARILLO,(int(self.x),int(self.y)),3)


class BalaZombie:
    def __init__(self,x,y,dx,dy):
        self.x,self.y=x,y; self.dx,self.dy=dx,dy
        self.velocidad=5; self.vida=120
    def update(self):
        self.x+=self.dx; self.y+=self.dy
        self.vida-=1
        return self.vida>0 and INTERIOR_X0<self.x<INTERIOR_X1 and INTERIOR_Y0<self.y<INTERIOR_Y1
    def dibujar(self,surf):
        g=pg.Surface((16,16),pg.SRCALPHA)
        pg.draw.circle(g,(100,255,100,150),(8,8),8)
        surf.blit(g,(self.x-8,self.y-8))
        pg.draw.circle(surf,(100,255,100),(int(self.x),int(self.y)),4)


class Moneda:
    def __init__(self,x,y):
        self.x,self.y=x,y; self.radio=10
        self.anim=random.uniform(0,6.28)
    def update(self): self.anim+=0.12
    def dibujar(self,surf):
        x,y=round(self.x),round(self.y-2*math.sin(self.anim))
        brillo=pg.Surface((52,52),pg.SRCALPHA)
        pg.draw.circle(brillo,(255,194,48,45),(26,26),23)
        surf.blit(brillo,(x-26,y-26))
        pg.draw.ellipse(surf,(30,24,16),(x-13,y+12,26,6))
        pg.draw.circle(surf,(73,44,10),(x,y+2),16)
        pg.draw.circle(surf,(235,158,26),(x,y),15)
        pg.draw.circle(surf,(255,216,68),(x,y-1),12)
        pg.draw.circle(surf,(255,240,149),(x,y-1),12,2)
        surf.blit(SIMBOLO_MONEDA,SIMBOLO_MONEDA.get_rect(center=(x,y)))


class Botiquin:
    def __init__(self,x,y):
        self.x,self.y=x,y; self.radio=12
        self.anim=random.uniform(0,6.28)
    def update(self): self.anim+=0.1
    def dibujar(self,surf):
        pulso=abs(math.sin(self.anim))*2
        tam=self.radio+pulso
        s=pg.Surface((int(tam*5),int(tam*5)),pg.SRCALPHA)
        pg.draw.circle(s,(60,200,110,60),(int(tam*2.5),int(tam*2.5)),int(tam*2))
        surf.blit(s,(self.x-tam*2.5,self.y-tam*2.5))
        pg.draw.rect(surf,(30,120,60),(self.x-tam,self.y-tam,tam*2,tam*2),border_radius=4)
        pg.draw.rect(surf,BLANCO,(self.x-4,self.y-10,8,20))
        pg.draw.rect(surf,BLANCO,(self.x-10,self.y-4,20,8))


class PowerUp:
    def __init__(self,x,y,tipo):
        self.x,self.y=x,y; self.tipo=tipo
        self.vida=600; self.anim=0
    def update(self):
        self.anim+=0.15; self.vida-=1
        return self.vida>0
    def dibujar(self,surf):
        colores={"velocidad":CIAN,"escudo":(100,200,255),"daño":ROJO,"vida":VERDE}
        color=colores.get(self.tipo,BLANCO)
        pulso=abs(math.sin(self.anim))*5
        tam=12+pulso
        s=pg.Surface((int(tam*4),int(tam*4)),pg.SRCALPHA)
        pg.draw.circle(s,(*color,60),(int(tam*2),int(tam*2)),int(tam*1.8))
        pg.draw.circle(s,(*color,120),(int(tam*2),int(tam*2)),int(tam*1.3))
        surf.blit(s,(self.x-tam*2,self.y-tam*2))
        pg.draw.circle(surf,color,(int(self.x),int(self.y)),int(tam))
        pg.draw.circle(surf,BLANCO,(int(self.x),int(self.y)),int(tam),2)


class Granada:
    def __init__(self,x,y,dx,dy):
        self.x,self.y=x,y; self.dx,self.dy=dx,dy
        self.vida=35; self.anim=0
    def update(self):
        self.x+=self.dx; self.y+=self.dy
        self.dx*=0.95; self.dy*=0.95
        self.vida-=1; self.anim+=0.3
        if self.vida<=0:
            # Explosión
            for z in zombies[:]:
                if math.hypot(z.x-self.x,z.y-self.y)<120: z.recibir_daño(80)
            for _ in range(60):
                particulas.append(Particula(self.x,self.y,random.choice([NARANJA,AMARILLO,ROJO]),10,30))
            shake(15); flash(NARANJA,12); play(S_EXPLOSION)
            return False
        return True
    def dibujar(self,surf):
        pg.draw.circle(surf,VERDE_OSCURO,(int(self.x),int(self.y)),7)
        pg.draw.circle(surf,(100,200,100),(int(self.x-2),int(self.y-2)),3)
        pg.draw.line(surf,ROJO,(self.x,self.y-7),(self.x,self.y-12),2)


class Obstaculo:
    def __init__(self,x,y,radio,tema):
        self.x,self.y,self.radio=x,y,radio
        self.tipo=random.choice(["escombro","vehiculo","barricada"])
        self.color=tema["acento"]
    def dibujar(self,surf):
        som=pg.Surface((self.radio*2+10,self.radio),pg.SRCALPHA)
        pg.draw.ellipse(som,(0,0,0,110),(0,0,self.radio*2+10,self.radio))
        surf.blit(som,(self.x-self.radio-5,self.y+self.radio-8))
        if self.tipo=="vehiculo":
            r=pg.Rect(0,0,self.radio*2,self.radio*1.3); r.center=(int(self.x),int(self.y))
            pg.draw.rect(surf,self.color,r,border_radius=8)
            pg.draw.rect(surf,tuple(max(0,c-40) for c in self.color),r,3,border_radius=8)
            pg.draw.rect(surf,(60,70,90),(r.x+6,r.y+6,r.width-12,12),border_radius=3)
            pg.draw.rect(surf,(40,50,70),(r.x+6,r.y+r.height-18,r.width-12,12),border_radius=3)
        elif self.tipo=="barricada":
            pg.draw.rect(surf,self.color,(self.x-self.radio,self.y-self.radio//2,self.radio*2,self.radio),border_radius=4)
            for i in range(4):
                pg.draw.line(surf,NARANJA,(self.x-self.radio+i*10,self.y-self.radio//2),(self.x-self.radio+i*10,self.y+self.radio//2),3)
        else:
            for _ in range(6):
                r=random.Random(self.x+_*100)
                ox,oy=r.uniform(-self.radio,self.radio),r.uniform(-self.radio,self.radio)
                tam=r.uniform(5,13)
                pg.draw.circle(surf,self.color,(int(self.x+ox),int(self.y+oy)),int(tam))
                pg.draw.circle(surf,tuple(max(0,c-30) for c in self.color),(int(self.x+ox),int(self.y+oy)),int(tam),2)


class Particula:
    def __init__(self,x,y,color,vel=4,vida=30):
        self.x,self.y=x,y
        self.vx=random.uniform(-vel,vel); self.vy=random.uniform(-vel,vel)
        self.vida=vida; self.vida_max=vida
        self.color=color; self.tam=random.uniform(2,5)
    def update(self):
        self.x+=self.vx; self.y+=self.vy
        self.vx*=0.94; self.vy*=0.94
        self.vida-=1
        return self.vida>0
    def dibujar(self,surf):
        alpha=int(255*(self.vida/self.vida_max))
        tam=max(1,int(self.tam*(self.vida/self.vida_max)))
        s=pg.Surface((tam*2,tam*2),pg.SRCALPHA)
        pg.draw.circle(s,(*self.color,alpha),(tam,tam),tam)
        surf.blit(s,(self.x-tam,self.y-tam))


class SangrePiso:
    def __init__(self,x,y):
        self.x,self.y=x,y; self.vida=600
        self.manchas=[(random.uniform(-20,20),random.uniform(-20,20),random.uniform(8,20)) for _ in range(5)]
    def update(self):
        self.vida-=1; return self.vida>0
    def dibujar(self,surf):
        alpha=int(150*(self.vida/600))
        for mx,my,r in self.manchas:
            s=pg.Surface((int(r*2),int(r*2)),pg.SRCALPHA)
            pg.draw.circle(s,(80,10,20,alpha),(int(r),int(r)),int(r))
            surf.blit(s,(self.x+mx-r,self.y+my-r))


# ============ HELPERS ============
def libre(x,y,radio,es_jugador=False):
    if not (INTERIOR_X0<=x<=INTERIOR_X1 and INTERIOR_Y0<=y<=INTERIOR_Y1):
        if not (es_jugador and vano_transitable(x,y)): return False
    return all(math.hypot(x-o.x,y-o.y)>=radio+o.radio+4 for o in obstaculos)

def mover_col(obj,dx,dy):
    pasos=max(1,math.ceil(max(abs(dx),abs(dy))/3))
    es_jugador=isinstance(obj,Jugador)
    for _ in range(pasos):
        if libre(obj.x+dx/pasos,obj.y,obj.radio,es_jugador): obj.x+=dx/pasos
        if libre(obj.x,obj.y+dy/pasos,obj.radio,es_jugador): obj.y+=dy/pasos

def pos_libre(radio,usados=(),dist_jug=0):
    for _ in range(400):
        x,y=random.randint(65,ANCHO-65),random.randint(140,ALTO-65)
        if (libre(x,y,radio) and all(math.hypot(x-j.x,y-j.y)>=dist_jug for j in jugadores)
            and all(math.hypot(x-u.x,y-u.y)>=radio+u.radio+8 for u in usados)):
            return x,y
    for y in range(140,ALTO-60,30):
        for x in range(65,ANCHO-60,30):
            if (libre(x,y,radio)
                and all(math.hypot(x-j.x,y-j.y)>=dist_jug for j in jugadores)
                and all(math.hypot(x-u.x,y-u.y)>=radio+u.radio+8 for u in usados)):
                return x,y
    return None

# ============ SALAS (mapa tipo Isaac) ============
class Sala:
    def __init__(self,cx,cy,tipo="normal"):
        self.cx,self.cy=cx,cy
        self.tipo=tipo  # inicio | normal | tesoro | jefe
        self.visitada=False
        self.limpia=tipo in ("inicio","tesoro")
        self.habia_enemigos=False
        self.generada=False
        self.trampilla=None
        self.zombies=[]; self.monedas=[]; self.botiquines=[]
        self.obstaculos=[]; self.sangre=[]; self.extras=[]

def generar_mapa(idx):
    """Laberinto estilo Isaac: sin bloques 2x2; el jefe queda al fondo."""
    salas={(0,0):Sala(0,0,"inicio")}
    objetivo=NIVELES[idx]["salas"]
    intentos=0
    while len(salas)<objetivo and intentos<5000:
        intentos+=1
        base=random.choice(list(salas.values()))
        libres=[(base.cx+dx,base.cy+dy) for dx,dy in DIRS_SALA.values()
                if (base.cx+dx,base.cy+dy) not in salas
                and abs(base.cx+dx)<=3 and abs(base.cy+dy)<=3]
        if not libres: continue
        c=random.choice(libres)
        tocadas=sum((c[0]+dx,c[1]+dy) in salas for dx,dy in DIRS_SALA.values())
        if tocadas>1: continue
        salas[c]=Sala(*c)
    dist={(0,0):0}; cola=[(0,0)]
    while cola:
        c=cola.pop(0)
        for dx,dy in DIRS_SALA.values():
            n=(c[0]+dx,c[1]+dy)
            if n in salas and n not in dist:
                dist[n]=dist[c]+1; cola.append(n)
    def callejon(c):
        return sum((c[0]+dx,c[1]+dy) in salas for dx,dy in DIRS_SALA.values())==1
    candidatos=sorted([c for c in salas if c!=(0,0) and callejon(c)],
                      key=lambda c:-dist.get(c,0))
    if candidatos:
        salas[candidatos.pop(0)].tipo="jefe"
    else:
        salas[max(dist,key=lambda c:dist[c])].tipo="jefe"
    if candidatos and random.random()<0.9:
        salas[candidatos[0]].tipo="tesoro"
    return salas

def vecino_en(d):
    if sala_actual is None: return None
    dx,dy=DIRS_SALA[d]
    return (sala_actual.cx+dx,sala_actual.cy+dy)

def puertas_abiertas():
    return not any(z.esta_vivo() for z in zombies)

def vano_transitable(x,y):
    """Permite al jugador meterse en el vano de una puerta abierta."""
    if sala_actual is None or not puertas_abiertas(): return False
    activas={d for d in DIRS_SALA if vecino_en(d) in mapa_salas}
    if "N" in activas and abs(x-MID_X)<=34 and INTERIOR_Y0-26<=y<=INTERIOR_Y0: return True
    if "S" in activas and abs(x-MID_X)<=34 and INTERIOR_Y1<=y<=INTERIOR_Y1+26: return True
    if "O" in activas and abs(y-MID_Y)<=34 and INTERIOR_X0-26<=x<=INTERIOR_X0: return True
    if "E" in activas and abs(y-MID_Y)<=34 and INTERIOR_X1<=x<=INTERIOR_X1+26: return True
    return False

def puerta_cruzada():
    if sala_actual is None or transicion is not None or not puertas_abiertas(): return None
    for j in jugadores:
        if j.vida<=0: continue
        if vecino_en("N") in mapa_salas and abs(j.x-MID_X)<=40 and j.y<=INTERIOR_Y0-20: return "N"
        if vecino_en("S") in mapa_salas and abs(j.x-MID_X)<=40 and j.y>=INTERIOR_Y1+20: return "S"
        if vecino_en("O") in mapa_salas and abs(j.y-MID_Y)<=40 and j.x<=INTERIOR_X0-20: return "O"
        if vecino_en("E") in mapa_salas and abs(j.y-MID_Y)<=40 and j.x>=INTERIOR_X1+20: return "E"
    return None

def iniciar_transicion(d):
    global transicion
    if transicion is not None: return
    transicion={"dir":d,"t":0,"cambiada":False}

def guardar_sala_actual():
    if sala_actual is None: return
    sala_actual.zombies=zombies
    sala_actual.monedas=monedas
    sala_actual.botiquines=botiquines
    sala_actual.obstaculos=obstaculos
    sala_actual.sangre=sangre_piso
    sala_actual.extras=[p for p in particulas if isinstance(p,PowerUp)]

def cargar_sala(sala):
    global zombies,monedas,botiquines,obstaculos,sangre_piso,particulas,balas,jefe_actual
    zombies,monedas,botiquines=sala.zombies,sala.monedas,sala.botiquines
    obstaculos,sangre_piso=sala.obstaculos,sala.sangre
    balas=[]
    particulas=list(sala.extras)
    jefe_actual=next((z for z in zombies if z.es_jefe and z.esta_vivo()),None)

def cambiar_sala():
    global sala_actual,tiempo_extraccion,jefe_actual
    d=transicion["dir"]; dx,dy=DIRS_SALA[d]
    destino=mapa_salas[(sala_actual.cx+dx,sala_actual.cy+dy)]
    guardar_sala_actual()
    cargar_sala(destino)
    poblar_sala(destino,nivel_actual)
    sala_actual=destino
    destino.visitada=True
    vivos=[j for j in jugadores if j.vida>0]
    sx,sy=SPAWN_PUERTA[d]
    for n,j in enumerate(vivos):
        j.x=sx+(0 if n==0 else -34 if n==1 else 34)
        j.y=sy+(0 if n==0 else 20 if n==1 else -20)
        j.invencible=max(j.invencible,30)
    tiempo_extraccion=0
    transicion["cambiada"]=True
    jefe_actual=next((z for z in zombies if z.es_jefe and z.esta_vivo()),None)
    if destino.tipo=="jefe" and any(z.esta_vivo() for z in zombies):
        play(S_JEFE,"alerta"); shake(12); flash(ROJO,14)
        mostrar_mensaje("¡ZONA DEL JEFE!")
    elif destino.tipo=="tesoro":
        mostrar_mensaje("Sala del tesoro")

def poblar_sala(sala,idx):
    global zombies,monedas,botiquines,obstaculos,sangre_piso,jefe_actual
    zombies,monedas,botiquines=sala.zombies,sala.monedas,sala.botiquines
    obstaculos,sangre_piso=sala.obstaculos,sala.sangre
    if sala.generada:
        jefe_actual=next((z for z in zombies if z.es_jefe and z.esta_vivo()),None)
        return
    sala.generada=True
    tema=TEMAS[idx]; nivel=NIVELES[idx]
    activas=[PUERTA_POS[d] for d in DIRS_SALA
             if (sala.cx+DIRS_SALA[d][0],sala.cy+DIRS_SALA[d][1]) in mapa_salas]
    def lejos_puertas(p,minimo=150):
        return all(math.hypot(p[0]-px,p[1]-py)>=minimo for px,py in activas)
    if sala.tipo=="inicio":
        for _ in range(2):
            p=pos_libre(25,monedas,120)
            if p and lejos_puertas(p,110): monedas.append(Moneda(*p))
        return
    if sala.tipo=="tesoro":
        for _ in range(3):
            p=pos_libre(30,obstaculos,180)
            if p and lejos_puertas(p): obstaculos.append(Obstaculo(*p,random.randint(18,26),tema))
        for _ in range(6):
            p=pos_libre(25,monedas,60)
            if p: monedas.append(Moneda(*p))
        p=pos_libre(14,botiquines,90)
        if p: botiquines.append(Botiquin(*p))
        tipo=random.choice(["velocidad","escudo","daño","vida"])
        p2=pos_libre(20,botiquines+monedas,60)
        if p2:
            extra=PowerUp(*p2,tipo)
            particulas.append(extra)
            sala.extras.append(extra)
        return
    if sala.tipo=="jefe":
        # Zona del jefe: pocos escombros, el jefe espera dentro.
        for _ in range(2):
            p=pos_libre(30,obstaculos,240)
            if p and lejos_puertas(p): obstaculos.append(Obstaculo(*p,random.randint(18,28),tema))
        p=pos_libre(50,zombies,260)
        if p:
            jefe=Jefe(*p)
            factor=1.35 if nivel.get("jefe") else 1.0
            jefe.vida=jefe.vida_max=int(420*(1+0.18*idx)*factor)
            zombies.append(jefe)
            jefe_actual=jefe
        for _ in range(2):
            p=pos_libre(25,zombies,240)
            if p: zombies.append(Zombie(*p,"normal"))
        sala.habia_enemigos=True
        return
    # Sala normal: obstaculos lejos de las puertas.
    for _ in range(random.randint(2,max(3,nivel["obstaculos"]//3))):
        p=pos_libre(30,obstaculos,180)
        if p and lejos_puertas(p): obstaculos.append(Obstaculo(*p,random.randint(18,32),tema))
    base=max(3,nivel["zombies"]//2)
    extra_z=min(4,(abs(sala.cx)+abs(sala.cy))//2)
    for _ in range(base+extra_z):
        tipos=["normal","normal","normal"]
        if idx>=1: tipos+=["rapido"]
        if idx>=2: tipos+=["escupe"]
        if idx>=3: tipos+=["tanque","explosivo"]
        p=pos_libre(25,zombies,200)
        if p: zombies.append(Zombie(*p,random.choice(tipos)))
    sala.habia_enemigos=bool(zombies)
    for _ in range(random.randint(2,4)):
        p=pos_libre(25,monedas,60)
        if p: monedas.append(Moneda(*p))
    if random.random()<0.35:
        p=pos_libre(14,botiquines,90)
        if p: botiquines.append(Botiquin(*p))

def iniciar_nivel(idx):
    global nivel_actual,jugadores,zombies,balas,monedas,botiquines
    global particulas,obstaculos,mapa_salas,sala_actual,transicion
    global monedas_obtenidas,tiempo_restante,tiempo_extraccion,sangre_piso,jefe_actual,jefe_alertado
    global daño_nivel, mensaje_flotante
    daño_nivel=False
    mensaje_flotante=""
    clima_particulas.clear()
    recursos={j.num:(j.botiquines,j.granadas) for j in jugadores} if idx>0 else {}
    nivel_actual=idx; nivel=NIVELES[idx]
    jugadores=[Jugador(MID_X-40,MID_Y+110,1,AZUL,0 if joysticks else -1)]
    if coop:
        jugadores.append(Jugador(MID_X+40,MID_Y+110,2,NARANJA,1 if len(joysticks)>1 else -1))
    for j in jugadores:
        j.vida_max=100+20*mejoras[j.num-1]["vida"]
        j.vida=j.vida_max
        if j.num in recursos: j.botiquines,j.granadas=recursos[j.num]
    mapa_salas=generar_mapa(idx)
    sala_actual=mapa_salas[(0,0)]
    sala_actual.visitada=True
    zombies=[]; monedas=[]; botiquines=[]
    obstaculos=[]; sangre_piso=[]
    balas=[]; particulas=[]
    poblar_sala(sala_actual,idx)
    jefe_actual=None; jefe_alertado=False; transicion=None
    tiempo_extraccion=0
    monedas_obtenidas=0
    tiempo_restante=nivel["tiempo"]
    efectos.update(shake=0,flash=0)
    if idx==5: desbloquear_logro("nivel_6","Llegar al nivel 6")

def mostrar_mensaje(t):
    global mensaje_flotante,tiempo_mensaje
    mensaje_flotante=t; tiempo_mensaje=pg.time.get_ticks()

def desbloquear_logro(clave,nombre):
    global logros
    if clave not in logros or not logros[clave]:
        logros[clave]=True
        play(S_LOGRO,"alerta")
        guardar_json(F_LOGROS,logros)
        mostrar_mensaje(f"🏆 LOGRO: {nombre}")

def guardar_highscore(nombre,puntos,nivel):
    global highscores
    highscores.append({"nombre":nombre,"puntos":puntos,"nivel":nivel,"fecha":datetime.now().isoformat(timespec="seconds")})
    highscores.sort(key=lambda x:x["puntos"],reverse=True)
    highscores=highscores[:10]
    guardar_json(F_SCORES,highscores)


# ============ MINIMAPA (estilo Isaac) ============
def caja_minimapa():
    if not mapa_salas: return None
    c,m=15,3
    xs=[s.cx for s in mapa_salas.values()]; ys=[s.cy for s in mapa_salas.values()]
    w=(max(xs)-min(xs)+1)*(c+m)-m+8
    h=(max(ys)-min(ys)+1)*(c+m)-m+8
    return (ANCHO-14-w,8,w,h)

def dibujar_minimapa():
    caja=caja_minimapa()
    if caja is None: return
    ox,oy,w,h=caja
    panel=pg.Surface((w,h),pg.SRCALPHA)
    panel.fill((8,12,20,165))
    pantalla.blit(panel,(ox,oy))
    pg.draw.rect(pantalla,GRIS,(ox,oy,w,h),1,border_radius=4)
    c,m=15,3
    xs=[s.cx for s in mapa_salas.values()]; ys=[s.cy for s in mapa_salas.values()]
    minx,miny=min(xs),min(ys)
    conocidas={(s.cx+dx,s.cy+dy) for s in mapa_salas.values() if s.visitada
               for dx,dy in DIRS_SALA.values()}
    for sala in mapa_salas.values():
        if not (sala.visitada or (sala.cx,sala.cy) in conocidas): continue
        rx=ox+4+(sala.cx-minx)*(c+m); ry=oy+4+(sala.cy-miny)*(c+m)
        actual=sala is sala_actual
        if actual: color=BLANCO
        elif sala.tipo=="jefe": color=ROJO
        elif sala.tipo=="tesoro": color=DORADO
        elif sala.visitada: color=(110,120,135)
        else: color=GRIS_OSCURO
        pg.draw.rect(pantalla,color,(rx,ry,c,c),border_radius=3)
        if actual:
            pg.draw.rect(pantalla,DORADO,(rx-2,ry-2,c+4,c+4),2,border_radius=4)
        elif sala.tipo=="jefe" and not sala.visitada:
            pg.draw.rect(pantalla,ROJO,(rx-2,ry-2,c+4,c+4),1,border_radius=4)
            pg.draw.circle(pantalla,ROJO,(rx+c//2,ry+c//2-1),3)
        elif sala.tipo=="tesoro" and not sala.visitada:
            t=fuente_peq.render("$",True,(255,230,120))
            pantalla.blit(t,t.get_rect(center=(rx+c//2,ry+c//2)))

# ============ HUD MEJORADO ============
def dibujar_hud():
    # Panel superior con gradiente
    panel=pg.Surface((ANCHO,80),pg.SRCALPHA)
    for y in range(80):
        alpha=int(240*(1-y/80*0.3))
        pg.draw.line(panel,(18,22,32,alpha),(0,y),(ANCHO,y))
    pantalla.blit(panel,(0,0))
    pg.draw.line(pantalla,AMARILLO,(0,80),(ANCHO,80),3)
    nivel=NIVELES[nivel_actual]
    # Nombre nivel
    t=fuente_med.render(nivel["nombre"],True,BLANCO)
    pantalla.blit(t,(20,15))
    t=fuente_peq.render(f"PUNTOS: {puntuacion_total}",True,AMARILLO)
    pantalla.blit(t,(20,52))
    # Progreso del piso y monedas
    limpias=sum(1 for s in mapa_salas.values() if s.limpia)
    t=fuente.render(f"SALAS {limpias}/{len(mapa_salas)} | $ {monedas_obtenidas} | Bolsa: ${dinero}",True,DORADO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,25)))
    # Tiempo con color dinámico
    ct=BLANCO if tiempo_restante>30 else AMARILLO if tiempo_restante>10 else ROJO
    t=fuente.render(f"⏱ {int(tiempo_restante)}s",True,ct)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,55)))
    # Info jugadores (a la izquierda del minimapa)
    caja=caja_minimapa()
    mmw=(caja[2]+16) if caja else 0
    for i,j in enumerate(jugadores):
        y=12+i*32
        txt=f"P{j.num} {j.nombre} HP:{int(j.vida)} 🩹{j.botiquines} 💣{j.granadas}"
        t=fuente_peq.render(txt,True,VERDE if j.vida>50 else AMARILLO if j.vida>25 else ROJO)
        pantalla.blit(t,t.get_rect(topright=(ANCHO-24-mmw,y)))
    dibujar_minimapa()

def dibujar_muros(tema):
    muro=tuple(max(0,int(c*0.5)) for c in tema["fondo"])
    borde=tuple(max(0,int(c*0.3)) for c in tema["fondo"])
    pg.draw.rect(pantalla,muro,(0,80,ANCHO,INTERIOR_Y0-80))
    pg.draw.rect(pantalla,muro,(0,INTERIOR_Y1,ANCHO,ALTO-INTERIOR_Y1))
    pg.draw.rect(pantalla,muro,(0,80,INTERIOR_X0,ALTO-80))
    pg.draw.rect(pantalla,muro,(INTERIOR_X1,80,ANCHO-INTERIOR_X1,ALTO-80))
    pg.draw.rect(pantalla,borde,(INTERIOR_X0,INTERIOR_Y0,INTERIOR_X1-INTERIOR_X0,INTERIOR_Y1-INTERIOR_Y0),3)
    sala=sala_actual
    if sala and sala.tipo=="jefe":
        s=pg.Surface((ANCHO,ALTO),pg.SRCALPHA)
        pg.draw.rect(s,(130,20,30,55),(INTERIOR_X0,INTERIOR_Y0,INTERIOR_X1-INTERIOR_X0,INTERIOR_Y1-INTERIOR_Y0))
        pantalla.blit(s,(0,0))
        for ex,ey in ((100,155),(ANCHO-100,155),(100,ALTO-80),(ANCHO-100,ALTO-80)):
            t=fuente_icono.render("☠",True,(150,34,48))
            pantalla.blit(t,t.get_rect(center=(ex,ey)))
    elif sala and sala.tipo=="tesoro":
        s=pg.Surface((ANCHO,ALTO),pg.SRCALPHA)
        pg.draw.rect(s,(210,170,50,30),(INTERIOR_X0,INTERIOR_Y0,INTERIOR_X1-INTERIOR_X0,INTERIOR_Y1-INTERIOR_Y0))
        pantalla.blit(s,(0,0))

def dibujar_puertas():
    tema=TEMAS[nivel_actual]
    for d in DIRS_SALA:
        if vecino_en(d) not in mapa_salas: continue
        x,y,w,h=rect_puerta(d)
        pg.draw.rect(pantalla,(10,10,14),(x,y,w,h))
        if puertas_abiertas():
            marco=(255,205,80)
            luz=pg.Surface((w,h),pg.SRCALPHA)
            pg.draw.rect(luz,(120,200,255,70),(0,0,w,h))
            pantalla.blit(luz,(x,y))
        else:
            marco=GRIS
            # Barras cerradas mientras queden zombis vivos.
            if d in ("N","S"):
                for bx in (x+10,x+w//2-2,x+w-12):
                    pg.draw.rect(pantalla,(66,70,80),(bx,y,5,h))
                pg.draw.rect(pantalla,(40,44,52),(x,y+h//2-3,w,6))
            else:
                for by in (y+10,y+h//2-2,y+h-12):
                    pg.draw.rect(pantalla,(66,70,80),(x,by,w,5))
                pg.draw.rect(pantalla,(40,44,52),(x+w//2-3,y,6,h))
        if d=="N": pg.draw.rect(pantalla,marco,(x-4,y-4,w+8,h+4),3)
        elif d=="S": pg.draw.rect(pantalla,marco,(x-4,y,w+8,h+8),3)
        elif d=="O": pg.draw.rect(pantalla,marco,(x-4,y-4,w+4,h+8),3)
        else: pg.draw.rect(pantalla,marco,(x,y-4,w+8,h+8),3)

def dibujar_trampilla():
    if not sala_actual or not sala_actual.trampilla: return
    x,y=sala_actual.trampilla
    pulso=abs(math.sin(pg.time.get_ticks()/250))
    s=pg.Surface((150,150),pg.SRCALPHA)
    pg.draw.circle(s,(90,255,150,int(45+pulso*45)),(75,75),70)
    pantalla.blit(s,(x-75,y-75))
    pg.draw.ellipse(pantalla,(14,16,12),(x-48,y-30,96,60))
    pg.draw.ellipse(pantalla,(36,48,34),(x-42,y-25,84,50),4)
    pg.draw.ellipse(pantalla,(6,8,6),(x-32,y-15,64,30))
    t=fuente_peq.render("SIGUIENTE NIVEL",True,(130,255,180))
    pantalla.blit(t,t.get_rect(center=(x,y-52)))

def dibujar_mensaje():
    if not mensaje_flotante: return
    e=pg.time.get_ticks()-tiempo_mensaje
    if e>2000: return
    alpha=max(0,255-int(e/2000*255))
    t=fuente_med.render(mensaje_flotante,True,AMARILLO)
    t.set_alpha(alpha)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,110)))


# ============ PANTALLAS ============
def dibujar_insert_coin():
    fondo_portada()
    # Título con glow
    pulso=abs(math.sin(pg.time.get_ticks()/500))
    for offset in [(0,0,4),(0,0,2)]:
        glow=texto_ajustado(fuente_titulo,"APOCALYPSE",(200,50,70),500)
        glow.set_alpha(int(100*pulso))
        pantalla.blit(glow,glow.get_rect(center=(ANCHO//2+offset[0],180+offset[1])))
    t=texto_ajustado(fuente_titulo,"APOCALYPSE",(255,80,100),500)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,180)))
    t=fuente_gran.render("LAST SURVIVOR",True,BLANCO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,250)))
    if (pg.time.get_ticks()//500)%2==0:
        t=fuente_gran.render("INSERT COIN",True,DORADO)
        pantalla.blit(t,t.get_rect(center=(ANCHO//2,430)))
    t=fuente.render("Presiona 5 para agregar créditos | ENTER: menú",True,GRIS_CLARO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,500)))
    t=fuente_med.render(f"CREDITOS: {creditos['cantidad']}",True,VERDE)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,570)))
    if creditos["cantidad"]>0:
        if (pg.time.get_ticks()//500)%2==0:
            t=fuente_med.render("PRESIONA START (ENTER)",True,BLANCO)
            pantalla.blit(t,t.get_rect(center=(ANCHO//2,630)))
    info=f"{len(joysticks)} joystick(s)" if joysticks else "Modo teclado"
    t=fuente_peq.render(info,True,VERDE if joysticks else AMARILLO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO-25)))

def dibujar_menu():
    fondo_portada()
    t=fuente_gran.render("APOCALYPSE",True,ROJO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,80)))
    t=fuente_med.render("LAST SURVIVOR",True,BLANCO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,130)))
    opciones=[("1 JUGADOR",not coop),("2 JUGADORES (COOP)",coop),
              ("INSTRUCCIONES",None),("HIGH SCORES",None),("LOGROS",None),("HABILIDADES Y SKINS",None),("SALIR",None)]
    y=230
    for i,(texto,sel) in enumerate(opciones):
        color=DORADO if i==opcion_menu else BLANCO
        if sel is not None:
            texto=f"{'▶' if sel else '  '} {texto}"
        t=fuente_med.render(texto,True,color)
        rect=t.get_rect(center=(ANCHO//2,y))
        pantalla.blit(t,rect)
        if i==opcion_menu:
            pg.draw.rect(pantalla,DORADO,(rect.x-20,rect.y-5,rect.width+40,rect.height+10),2,border_radius=8)
        y+=50
    t=fuente.render(f"CREDITOS: {creditos['cantidad']}",True,VERDE)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO-40)))

def dibujar_highscores():
    pantalla.fill((15,12,22))
    t=fuente_gran.render("HIGH SCORES",True,DORADO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,80)))
    if not highscores:
        t=fuente_med.render("Sin records aún",True,GRIS_CLARO)
        pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO//2)))
    else:
        y=160
        t=fuente.render("#   NOMBRE                PUNTOS   NIVEL",True,AMARILLO)
        pantalla.blit(t,t.get_rect(center=(ANCHO//2,y))); y+=35
        for i,s in enumerate(highscores):
            color=DORADO if i==0 else BLANCO if i<3 else GRIS_CLARO
            t=fuente.render(f"{i+1:<3} {s['nombre'][:20]:<22} {s['puntos']:>7}   {s['nivel']}",True,color)
            pantalla.blit(t,t.get_rect(center=(ANCHO//2,y))); y+=32
    pulso=abs(math.sin(pg.time.get_ticks()/400))
    t=fuente_med.render("START / ENTER para volver",True,(int(150+pulso*105),)*3)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO-50)))

def dibujar_logros():
    pantalla.fill((15,12,22))
    t=fuente_gran.render("LOGROS",True,DORADO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,80)))
    lista=[("primer_zombie","Primer zombie eliminado"),
           ("100_monedas","100 monedas recolectadas"),
           ("sin_daño","Superar un nivel sin recibir daño"),
           ("jefe_derrotado","Derrotar al primer jefe"),
           ("5000_puntos","Puntuación mayor a 5000"),
           ("nivel_6","Llegar al nivel 6"),
           ("explorador","Explorar todas las salas de un piso")]
    y=180
    for clave,nombre in lista:
        obtenido=logros.get(clave,False)
        icono="✅" if obtenido else "⬜"
        color=VERDE if obtenido else GRIS_CLARO
        t=fuente_med.render(f"{icono} {nombre}",True,color)
        pantalla.blit(t,t.get_rect(center=(ANCHO//2,y)))
        y+=55
    pulso=abs(math.sin(pg.time.get_ticks()/400))
    t=fuente_med.render("START / ENTER para volver",True,(int(150+pulso*105),)*3)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO-50)))

def dibujar_instrucciones():
    pantalla.fill((15,12,22))
    t=fuente_gran.render("INSTRUCCIONES",True,AMARILLO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,50)))
    y=110
    t=fuente_med.render("JUGADOR 1",True,AZUL)
    pantalla.blit(t,t.get_rect(center=(ANCHO//4,y)))
    t=fuente_med.render("JUGADOR 2",True,NARANJA)
    pantalla.blit(t,t.get_rect(center=(3*ANCHO//4,y)))
    p1=["WASD: mover","ESPACIO: disparar","Q: curar | E: golpear","R: cambiar arma | G: granada","SHIFT izq.: correr"]
    p2=["Flechas: mover","ENTER: disparar",".: curar | CTRL der.: golpe",",: arma | /: granada","SHIFT der.: correr"]
    y+=45
    for a,b in zip(p1,p2):
        t=fuente.render(a,True,BLANCO)
        pantalla.blit(t,t.get_rect(center=(ANCHO//4,y)))
        t=fuente.render(b,True,BLANCO)
        pantalla.blit(t,t.get_rect(center=(3*ANCHO//4,y)))
        y+=28
    y=345
    t=fuente_med.render("EL MAPA (ESTILO ISAAC)",True,AMARILLO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,y))); y+=36
    for linea in ["Cada piso es un laberinto de salas unidas por puertas.",
                  "Las puertas se cierran con zombis vivos; limpia la sala para abrir.",
                  "Encuentra la sala del JEFE, derrota al jefe y pisa la trampilla.",
                  "El minimapa (arriba a la derecha) marca tu sala, el jefe y el tesoro."]:
        t=fuente.render(linea,True,BLANCO)
        pantalla.blit(t,t.get_rect(center=(ANCHO//2,y))); y+=27
    y=ALTO-140
    t=fuente_med.render("MODO ARCADE",True,GRIS_CLARO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,y))); y+=35
    t=fuente.render("B1: correr | B2: disparar | B3: golpear | B4: granada",True,BLANCO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,y))); y+=25
    t=fuente.render("B5: arma | B6: curar | B7: pausa | B8: START",True,GRIS_CLARO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,y)))
    pulso=abs(math.sin(pg.time.get_ticks()/400))
    t=fuente_med.render("START / ENTER para volver",True,(int(150+pulso*105),)*3)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO-40)))

def dibujar_historia():
    esc=ESCENAS_HISTORIA[escena_historia]
    pantalla.fill(esc["color"])
    for i in range(30):
        r=random.Random(i)
        x,y=r.randint(0,ANCHO),r.randint(0,ALTO)
        pg.draw.circle(pantalla,tuple(max(0,c-20) for c in esc["color"]),(x,y),r.randint(20,80))
    pg.draw.rect(pantalla,NEGRO,(50,50,ANCHO-100,ALTO-100),3)
    t=fuente_gran.render(esc["titulo"],True,BLANCO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,130)))
    pg.draw.line(pantalla,AMARILLO,(200,180),(ANCHO-200,180),2)
    y=270
    for linea in esc["texto"]:
        t=fuente_med.render(linea,True,BLANCO)
        pantalla.blit(t,t.get_rect(center=(ANCHO//2,y))); y+=60
    pulso=abs(math.sin(pg.time.get_ticks()/400))
    t=fuente.render("START / ENTER para continuar",True,(int(150+pulso*105),)*3)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO-80)))

def dibujar_seleccion():
    pantalla.fill((12,17,27))
    t=fuente_gran.render(f"ELIGE PERSONAJE — JUGADOR {turno_seleccion+1}",True,BLANCO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,80)))
    for i,p in enumerate(PERSONAJES):
        rect=pg.Rect(25+i*295,140,270,360)
        ocupado=coop and turno_seleccion==1 and i==seleccionados[0]
        pg.draw.rect(pantalla,(26,34,47),rect,border_radius=16)
        pg.draw.rect(pantalla,DORADO if i==cursor_personaje else GRIS,rect,4 if i==cursor_personaje else 1,border_radius=16)
        avatar=aplicar_skin(AVATARES[i],i)
        pantalla.blit(avatar,avatar.get_rect(midbottom=(rect.centerx,325)))
        t=fuente_med.render(p["nombre"],True,p["color"])
        pantalla.blit(t,t.get_rect(center=(rect.centerx,340)))
        t=fuente.render("P1 seleccionado" if ocupado else HABILIDADES[i][0],True,GRIS_CLARO)
        pantalla.blit(t,t.get_rect(center=(rect.centerx,390)))
        t=fuente.render("Skin: "+NOMBRES_SKIN[skins[i]],True,CIAN)
        pantalla.blit(t,t.get_rect(center=(rect.centerx,440)))
    for texto,y in [("A / D: personaje | X: skin | H: habilidades | ENTER: confirmar",570),
                    ("Cuatro personajes disponibles; hasta dos jugadores simultáneos.",615),
                    ("Cada personaje tiene una habilidad especial. Las skins son cosméticas.",650)]:
        t=fuente.render(texto,True,BLANCO)
        pantalla.blit(t,t.get_rect(center=(ANCHO//2,y)))

def dibujar_pausa():
    capa=pg.Surface((ANCHO,ALTO),pg.SRCALPHA); capa.fill((0,0,0,180))
    pantalla.blit(capa,(0,0))
    t=fuente_titulo.render("PAUSA",True,AMARILLO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO//2-60)))
    t=fuente_med.render("START / P - Continuar",True,BLANCO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO//2+30)))
    t=fuente.render("M - Menú principal | H - Habilidades y skins",True,GRIS_CLARO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO//2+80)))

def dibujar_nivel_completo():
    capa=pg.Surface((ANCHO,ALTO),pg.SRCALPHA); capa.fill((0,0,0,180))
    pantalla.blit(capa,(0,0))
    t=fuente_titulo.render("¡NIVEL COMPLETO!",True,VERDE)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO//2-80)))
    t=fuente_med.render(f"{NIVELES[nivel_actual]['nombre']} superado",True,BLANCO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO//2)))
    t=fuente_med.render(f"PUNTOS: {puntuacion_total}",True,DORADO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO//2+60)))
    if nivel_actual+1<len(NIVELES):
        t=fuente.render("START / ENTER - Tienda y siguiente nivel",True,AMARILLO)
    else:
        t=fuente.render("START / ENTER - Ver el final",True,AMARILLO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO//2+120)))

def dibujar_game_over():
    capa=pg.Surface((ANCHO,ALTO),pg.SRCALPHA); capa.fill((0,0,0,200))
    pantalla.blit(capa,(0,0))
    t=fuente_titulo.render("GAME OVER",True,ROJO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO//2-80)))
    t=fuente_med.render(f"Puntuación: {puntuacion_total}",True,DORADO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO//2)))
    t=fuente.render("START / ENTER / R - Volver a INSERT COIN",True,AMARILLO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO//2+80)))
    t=fuente.render("M - Menú principal",True,GRIS_CLARO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO//2+120)))

def dibujar_victoria():
    capa=pg.Surface((ANCHO,ALTO),pg.SRCALPHA); capa.fill((0,0,0,200))
    pantalla.blit(capa,(0,0))
    t=fuente_titulo.render("THEY ARE ALIVE",True,VERDE)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO//2-100)))
    aviso=fuente.render(f"El refugio está vacío. En la radio se escucha la voz de {voz_final}.",True,BLANCO)
    pantalla.blit(aviso,aviso.get_rect(center=(ANCHO//2,ALTO//2-30)))
    t=fuente_med.render("\"¿Me escuchan? Seguimos vivos.\"",True,AMARILLO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO//2+20)))
    t=fuente.render("TO BE CONTINUED...",True,GRIS_CLARO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO//2+80)))
    t=fuente_med.render(f"PUNTUACION FINAL: {puntuacion_total}",True,DORADO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO//2+140)))
    t=fuente.render("START / ENTER - Volver al menú",True,BLANCO)
    pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO//2+200)))


# ============ LÓGICA ============
def impacto_seg(x0,y0,x1,y1,cx,cy,r):
    dx,dy=x1-x0,y1-y0
    fx,fy=x0-cx,y0-cy
    c=fx*fx+fy*fy-r*r
    if c<=0: return 0.0
    a=dx*dx+dy*dy
    if a==0: return None
    b=2*(fx*dx+fy*dy)
    disc=b*b-4*a*c
    if disc<0: return None
    t=(-b-math.sqrt(disc))/(2*a)
    return t if 0<=t<=1 else None

def actualizar_balas():
    for b in balas[:]:
        if isinstance(b,BalaZombie):
            x0,y0=b.x,b.y
            vigente=b.update()
            impactos=[]
            for o in obstaculos+[j for j in jugadores if j.vida>0]:
                t=impacto_seg(x0,y0,b.x,b.y,o.x,o.y,o.radio+4)
                if t is not None: impactos.append((t,o))
            if impactos:
                _,o=min(impactos,key=lambda par:par[0])
                if isinstance(o,Jugador): o.recibir_daño(8)
                balas.remove(b)
            elif not vigente:
                balas.remove(b)
            continue
        x0,y0=b.x,b.y
        vig=b.update()
        impactos=[]
        for o in obstaculos+[z for z in zombies if z.vida>0]:
            t=impacto_seg(x0,y0,b.x,b.y,o.x,o.y,o.radio+4)
            if t is not None: impactos.append((t,o))
        if impactos:
            play(S_IMPACTO,espera=70)
            t,o=min(impactos,key=lambda p:p[0])
            x,y=x0+(b.x-x0)*t,y0+(b.y-y0)*t
            if isinstance(o,Zombie):
                o.recibir_daño(getattr(b,"dano",20) if isinstance(b,Bala) else 15)
                for _ in range(10): particulas.append(Particula(x,y,SANGRE,4,18))
                sangre_piso.append(SangrePiso(x,y))
            else:
                for _ in range(8): particulas.append(Particula(x,y,AMARILLO,3,15))
            balas.remove(b)
        elif not vig: balas.remove(b)

def actualizar_partida(teclas):
    global particulas,monedas_obtenidas,puntuacion_total,transicion,jefe_actual
    global tiempo_restante,tiempo_extraccion,estado,sangre_piso

    if transicion is not None:
        transicion["t"]+=1
        if not transicion["cambiada"] and transicion["t"]>=7:
            cambiar_sala()
        if transicion["t"]>=16: transicion=None
        return

    for j in jugadores:
        if j.vida<=0: continue
        j.update()
        dx,dy=dir_joy(j.joy_index)
        if j.num==1:
            dx+=int(teclas[pg.K_d])-int(teclas[pg.K_a])
            dy+=int(teclas[pg.K_s])-int(teclas[pg.K_w])
            disp=teclas[pg.K_SPACE]
        else:
            dx+=int(teclas[pg.K_RIGHT])-int(teclas[pg.K_LEFT])
            dy+=int(teclas[pg.K_DOWN])-int(teclas[pg.K_UP])
            disp=teclas[pg.K_RETURN]
        correr=teclas[pg.K_LSHIFT if j.num==1 else pg.K_RSHIFT] or btn(j.joy_index,0)
        if correr and (dx or dy) and j.energia>0:
            j.velocidad=5.5; j.energia=max(0,j.energia-0.8)
        else:
            j.velocidad=3.5
            if not correr: j.energia=min(100,j.energia+0.45)
        if j.impulso: j.velocidad*=1.2
        j.mover(dx,dy)
        if disp or btn(j.joy_index,1): j.disparar()

    if transicion is None:
        d=puerta_cruzada()
        if d: iniciar_transicion(d)

    actualizar_balas()

    for z in zombies[:]:
        if not z.esta_vivo():
            for _ in range(20): particulas.append(Particula(z.x,z.y,SANGRE,5,20))
            for _ in range(3): sangre_piso.append(SangrePiso(z.x+random.randint(-20,20),z.y+random.randint(-20,20)))
            puntuacion_total+=50 if not z.es_jefe else 500
            zombies.remove(z)
            play(S_MUERTE if z.es_jefe else S_ZOMBIE, espera=120)
            if z.es_jefe:
                desbloquear_logro("jefe_derrotado","Derrotar al primer jefe")
                jefe_actual=None
                if sala_actual:
                    sala_actual.trampilla=(round(z.x),min(round(z.y),INTERIOR_Y1-70))
                mostrar_mensaje("¡JEFE DERROTADO! Pisa la trampilla")
                for _ in range(30): particulas.append(Particula(z.x,z.y,DORADO,7,30))
            else: desbloquear_logro("primer_zombie","Primer zombie eliminado")
        else:
            z.update(jugadores,obstaculos)

    # Sala despejada: se abren las puertas y suelta una recompensa.
    if (sala_actual and sala_actual.habia_enemigos and not sala_actual.limpia
            and not any(z.esta_vivo() for z in zombies)):
        sala_actual.limpia=True
        puntuacion_total+=25
        if sala_actual.tipo=="jefe":
            mostrar_mensaje("¡Zona del jefe despejada!")
        else:
            play(S_ALERTA,"alerta")
            for _ in range(2):
                p=pos_libre(25,monedas,80)
                if p: monedas.append(Moneda(*p))
            mostrar_mensaje("Sala despejada")

    vivos=[j for j in jugadores if j.vida>0]

    # Cada objeto se actualiza una sola vez. Las explosiones pueden agregar
    # nuevas partículas; se conservan sin actualizarlas en este mismo paso.
    pendientes=particulas
    particulas=[]
    for p in pendientes:
        if p.update():
            particulas.append(p)

    # Monedas
    for m in monedas[:]:
        m.update()
        for j in vivos:
            if math.hypot(m.x-j.x,m.y-j.y)<m.radio+j.radio:
                monedas.remove(m); monedas_obtenidas+=1; j.monedas+=1
                sumar_dinero(1)
                puntuacion_total+=10
                play(S_MONEDA)
                for _ in range(10): particulas.append(Particula(m.x,m.y,DORADO,4,22))
                logros["_monedas_total"]+=1
                if logros["_monedas_total"]>=100:
                    desbloquear_logro("100_monedas","100 monedas recolectadas")
                # Probabilidad de power-up
                if random.random()<0.1:
                    tipo=random.choice(["velocidad","escudo","daño","vida"])
                    particulas.append(PowerUp(m.x,m.y,tipo))
                break

    # Botiquines
    for b in botiquines[:]:
        b.update()
        for j in vivos:
            if math.hypot(b.x-j.x,b.y-j.y)<b.radio+j.radio:
                botiquines.remove(b); j.botiquines+=1
                mostrar_mensaje(f"P{j.num} obtuvo botiquín")
                break

    # Power-ups
    for p in particulas[:]:
        if isinstance(p,PowerUp):
            for j in vivos:
                if math.hypot(p.x-j.x,p.y-j.y)<20+j.radio:
                    if p.tipo=="velocidad": j.energia=100
                    elif p.tipo=="escudo": j.escudo=300
                    elif p.tipo=="daño": j.arma=1
                    elif p.tipo=="vida": j.vida=min(100,j.vida+30)
                    play(S_POWERUP)
                    mostrar_mensaje(f"¡Power-up: {p.tipo}!")
                    particulas.remove(p)
                    break

    # Sangre piso
    sangre_piso=[s for s in sangre_piso if s.update()]

    # Partículas
    objetos=[p for p in particulas if isinstance(p,(PowerUp,Granada))]
    visuales=[p for p in particulas if isinstance(p,Particula)]
    particulas=objetos+visuales[-600:]

    # Tiempo
    tiempo_restante=max(0,tiempo_restante-1/60)
    if not vivos or tiempo_restante<=0:
        terminar_partida(GAME_OVER); return

    # Trampilla: aparece al vencer al jefe; písala para bajar al siguiente piso.
    trp=sala_actual.trampilla if sala_actual else None
    if trp and vivos:
        reunidos=all(math.hypot(j.x-trp[0],j.y-trp[1])<60 for j in vivos)
        tiempo_extraccion=tiempo_extraccion+1/60 if reunidos else 0
        if tiempo_extraccion>=1.2:
            puntuacion_total+=int(tiempo_restante)*5
            guardar_json(F_LOGROS,logros)
            if not daño_nivel: desbloquear_logro("sin_daño","Superar un nivel sin recibir daño")
            if puntuacion_total>=5000: desbloquear_logro("5000_puntos","Puntuación mayor a 5000")
            if mapa_salas and all(s.visitada for s in mapa_salas.values()):
                desbloquear_logro("explorador","Explorar todas las salas de un piso")
            play(S_NIVEL)
            estado=NIVEL_COMPLETO


def terminar_partida(res):
    global estado,score_guardado
    estado=res
    if not score_guardado:
        guardar_json(F_LOGROS,logros)
        guardar_highscore("+".join(j.nombre for j in jugadores),puntuacion_total,nivel_actual+1)
        score_guardado=True


score_guardado=False
jugando=True

def confirmar():
    global estado,coop,escena_historia,puntuacion_total,score_guardado
    global turno_seleccion,cursor_personaje,ESCENAS_HISTORIA,nivel_tras_historia,jugando
    play(S_CONFIRMAR,"menu")
    if estado==INSERT_COIN: estado=MENU
    elif estado==MENU:
        if opcion_menu in (0,1):
            if creditos["cantidad"]<=0: estado=INSERT_COIN; return
            creditos["cantidad"]-=1; guardar_json(F_CREDITOS,creditos)
            coop=opcion_menu==1
            escena_historia=0; puntuacion_total=0; score_guardado=False
            reiniciar_mejoras()
            turno_seleccion=0; cursor_personaje=0
            estado=SELECCION
        elif opcion_menu==2: estado=INSTRUCCIONES
        elif opcion_menu==3: estado=HIGHSCORES
        elif opcion_menu==4: estado="logros"
        elif opcion_menu==5: abrir_habilidades(MENU)
        else: jugando=False
    elif estado==SELECCION:
        if turno_seleccion==1 and cursor_personaje==seleccionados[0]: return
        seleccionados[turno_seleccion]=cursor_personaje
        if coop and turno_seleccion==0:
            turno_seleccion=1; cursor_personaje=(cursor_personaje+1)%4
        else:
            preparar_historia(); escena_historia=0; nivel_tras_historia=0
            estado=HISTORIA
    elif estado in (INSTRUCCIONES,HIGHSCORES,VICTORIA,"logros"): estado=MENU
    elif estado==HISTORIA:
        escena_historia+=1
        if escena_historia>=len(ESCENAS_HISTORIA):
            iniciar_nivel(nivel_tras_historia); estado=JUGANDO
    elif estado==PAUSA: estado=JUGANDO
    elif estado==NIVEL_COMPLETO:
        if nivel_actual+1<len(NIVELES):
            abrir_tienda(); return
        terminar_partida(VICTORIA)
    elif estado=="salir_tienda":
        if nivel_actual==3:
            ESCENAS_HISTORIA=DESCUBRIMIENTO; escena_historia=0
            nivel_tras_historia=4; estado=HISTORIA
        elif nivel_actual+1<len(NIVELES):
            iniciar_nivel(nivel_actual+1); estado=JUGANDO
        else:
            desbloquear_logro("nivel_6","Llegar al nivel 6")
            terminar_partida(VICTORIA)
    elif estado==GAME_OVER: estado=INSERT_COIN

def agregar_credito():
    play(S_CREDITO,"menu")
    creditos["cantidad"]+=1; guardar_json(F_CREDITOS,creditos); flash(DORADO,10)

def accion_jugador(num,acc):
    if estado!=JUGANDO: return
    j=next((x for x in jugadores if x.num==num and x.vida>0),None)
    if not j: return
    if acc=="curar" and j.curar(): mostrar_mensaje(f"P{num} se curó")
    elif acc=="golpear": j.golpear()
    elif acc=="arma":
        j.arma=1-j.arma
        play(S_ARMA)
    elif acc=="granada": j.lanzar_granada()

def procesar_evento(ev):
    global estado,jugando,opcion_menu,cursor_personaje
    if ev.type==pg.QUIT: jugando=False
    elif ev.type in (pg.JOYDEVICEADDED,pg.JOYDEVICEREMOVED):
        actualizar_mandos()
        if estado==JUGANDO: estado=PAUSA
    elif ev.type==pg.WINDOWFOCUSLOST and estado==JUGANDO: estado=PAUSA
    elif ev.type==pg.KEYDOWN:
        k=ev.key
        if tecla_audio(k): return
        if estado in (MENU,SELECCION) and k in (pg.K_UP,pg.K_DOWN,pg.K_LEFT,pg.K_RIGHT,pg.K_a,pg.K_d):
            play(S_MENU,"menu")
        if k==pg.K_5: agregar_credito()
        elif k==pg.K_ESCAPE:
            if estado==JUGANDO: estado=PAUSA
            elif estado==PAUSA: estado=JUGANDO
            elif estado in (MENU,INSERT_COIN): jugando=False
            else: estado=MENU
        elif k==pg.K_p and estado in (JUGANDO,PAUSA):
            estado=PAUSA if estado==JUGANDO else JUGANDO
        elif k==pg.K_m and estado!=JUGANDO: estado=MENU
        elif estado==SELECCION and k in (pg.K_LEFT,pg.K_RIGHT,pg.K_a,pg.K_d):
            cursor_personaje=(cursor_personaje+(1 if k in (pg.K_RIGHT,pg.K_d) else -1))%4
        elif estado==MENU and k in (pg.K_UP,pg.K_DOWN):
            opcion_menu=(opcion_menu+(1 if k==pg.K_DOWN else -1))%7
        elif k==pg.K_RETURN and estado!=JUGANDO: confirmar()
        elif k==pg.K_r and estado==GAME_OVER: confirmar()
        elif estado==JUGANDO:
            acc={pg.K_q:(1,"curar"),pg.K_e:(1,"golpear"),
                 pg.K_PERIOD:(2,"curar"),pg.K_RCTRL:(2,"golpear"),
                 pg.K_r:(1,"arma"),pg.K_COMMA:(2,"arma"),
                 pg.K_g:(1,"granada"),pg.K_SLASH:(2,"granada")}
            if k in acc: accion_jugador(*acc[k])
    elif ev.type==pg.JOYBUTTONDOWN:
        idx=next((i for i,j in enumerate(joysticks) if j.get_instance_id()==ev.instance_id),-1)
        if idx<0: return
        b=ev.button
        if b==8: agregar_credito()
        elif b==7:
            if estado==JUGANDO: estado=PAUSA
            else: confirmar()
        elif b==6 and estado in (JUGANDO,PAUSA):
            estado=PAUSA if estado==JUGANDO else JUGANDO
        elif estado==JUGANDO:
            if b==5: accion_jugador(idx+1,"curar")
            elif b==2: accion_jugador(idx+1,"golpear")
            elif b==4: accion_jugador(idx+1,"arma")
            elif b==3: accion_jugador(idx+1,"granada")
        elif b in (0,6): confirmar()


def dibujar():
    if estado==INSERT_COIN: dibujar_insert_coin()
    elif estado==MENU: dibujar_menu()
    elif estado==SELECCION: dibujar_seleccion()
    elif estado==HISTORIA: dibujar_historia()
    elif estado==INSTRUCCIONES: dibujar_instrucciones()
    elif estado==HIGHSCORES: dibujar_highscores()
    elif estado=="logros": dibujar_logros()
    else:
        tema=TEMAS[nivel_actual]
        dibujar_fondo(tema)
        dibujar_muros(tema)
        # Sangre en piso
        for s in sangre_piso: s.dibujar(pantalla)
        dibujar_trampilla()
        dibujar_puertas()
        # Entidades ordenadas por Y
        todos=monedas+botiquines+[p for p in particulas if isinstance(p,PowerUp)]
        todos+=obstaculos+zombies+jugadores
        todos+=balas+[p for p in particulas if isinstance(p,Granada)]
        todos+= [p for p in particulas if not isinstance(p,(PowerUp,Granada))]
        for obj in sorted(todos,key=lambda o:getattr(o,"y",0)):
            if hasattr(obj,"dibujar"): obj.dibujar(pantalla)
        # Clima encima de todo
        dibujar_clima()
        # Barra de la trampilla
        if tiempo_extraccion>0 and estado==JUGANDO:
            pg.draw.rect(pantalla,GRIS_OSCURO,(450,ALTO-30,300,12),border_radius=6)
            pg.draw.rect(pantalla,VERDE,(450,ALTO-30,int(300*min(1,tiempo_extraccion/1.2)),12),border_radius=6)
            t=fuente_peq.render("Abriendo el paso...",True,BLANCO)
            pantalla.blit(t,t.get_rect(center=(ANCHO//2,ALTO-40)))
        # Shake
        if efectos["shake"]>0:
            i=math.ceil(efectos["shake"])
            copia=pantalla.copy()
            pantalla.fill(NEGRO)
            pantalla.blit(copia,(random.randint(-i,i),random.randint(-i,i)))
        if transicion is not None:
            tt=transicion["t"]
            fracc=min(tt/7,(16-tt)/9,1.0)
            capa=pg.Surface((ANCHO,ALTO))
            capa.fill((5,6,10))
            capa.set_alpha(int(255*max(0,fracc)))
            pantalla.blit(capa,(0,0))
        dibujar_hud()
        dibujar_mensaje()
        if estado==PAUSA: dibujar_pausa()
        elif estado==NIVEL_COMPLETO: dibujar_nivel_completo()
        elif estado==GAME_OVER: dibujar_game_over()
        elif estado==VICTORIA: dibujar_victoria()
    if efectos["flash"]>0:
        capa=pg.Surface((ANCHO,ALTO),pg.SRCALPHA)
        capa.fill((*efectos["flash_color"],min(100,int(efectos["flash"]*10))))
        pantalla.blit(capa,(0,0))


def dibujar_control_audio():
    if estado not in (INSERT_COIN,MENU,PAUSA,INSTRUCCIONES): return
    estado_audio="SIN DISPOSITIVO" if not AUDIO_OK else "SILENCIADO" if audio_silenciado else "ACTIVO"
    texto=f"AUDIO {estado_audio} | F1: silencio | F2/F3 música {round(volumen_musica*100)}% | F4/F5 efectos {round(volumen_efectos*100)}%"
    imagen=fuente_peq.render(texto,True,CIAN)
    caja=imagen.get_rect(center=(ANCHO//2,ALTO-12))
    pg.draw.rect(pantalla,NEGRO,caja.inflate(16,5),border_radius=4)
    pantalla.blit(imagen,caja)


def main():
    global opcion_menu,cursor_personaje
    acumulador=0.0; nav_cd=0.0
    try:
        while jugando:
            dt=min(reloj.tick(FPS)/1000,0.1)
            ant=estado
            for ev in pg.event.get(): procesar_evento(ev)
            nav_cd=max(0,nav_cd-dt)
            if estado in (MENU,SELECCION):
                dx,dy=dir_joy(turno_seleccion if estado==SELECCION and turno_seleccion<len(joysticks) else 0)
                if estado==SELECCION: dy=dx
                if abs(dy)>0.5 and nav_cd<=0:
                    if estado==MENU: opcion_menu=(opcion_menu+(1 if dy>0 else -1))%7
                    else: cursor_personaje=(cursor_personaje+(1 if dy>0 else -1))%4
                    play(S_MENU,"menu")
                    nav_cd=0.22
                elif abs(dy)<0.3: nav_cd=0
            if estado==JUGANDO:
                acumulador+=dt if ant==JUGANDO else 0
                teclas=pg.key.get_pressed()
                while acumulador>=1/60 and estado==JUGANDO:
                    actualizar_partida(teclas)
                    actualizar_clima(TEMAS[nivel_actual])
                    acumulador-=1/60
            else:
                acumulador=0
                if estado==INSERT_COIN or estado==MENU: actualizar_clima({"clima":"niebla"})
            if estado!=PAUSA:
                for e in ("shake","flash"): efectos[e]=max(0,efectos[e]-dt*60)
            actualizar_audio(dt)
            dibujar()
            dibujar_control_audio()
            pg.display.flip()
    finally:
        guardar_json(F_LOGROS,logros)
        pg.quit()


# ============ HABILIDADES, TIENDA Y SKINS ============
import colorsys
HABILIDADES=[
    ("Inspiracion", "Obed acelera al equipo y duplica su cadencia durante 6 s.", 18),
    ("Evasion", "Alexis avanza hacia donde apunta, inmune durante 0.6 s.", 8),
    ("Impacto", "Roberto hace 45 de dano y empuja enemigos a 145 px.", 14),
    ("Auxilio", "Daniel cura 35 HP a aliados vivos a 220 px, incluido el mismo.", 20),
]
NOMBRES_SKIN=["Original", "Esmeralda", "Violeta", "Artico"]
F_SKINS=os.path.join(BASE,'skins.json')
_config_skins=cargar_json(F_SKINS,{})
if not isinstance(_config_skins,dict): _config_skins={}
skins=[_config_skins.get(str(i),0) for i in range(4)]
skins=[v if type(v) is int and 0<=v<4 else 0 for v in skins]
CACHE_SKINS={}
dinero=0
mejoras=[{"dano":0,"vida":0} for _ in range(2)]
regreso_habilidades=MENU
cursor_habilidad=0
cursor_tienda=0
comprador=0
aviso_tienda=""
PRODUCTOS=[("Botiquin +1",3),("Granada +1",4),("Dano +5 (max. 3)",6),("Salud maxima +20 (max. 3)",6)]

def reiniciar_mejoras():
    global dinero,mejoras
    dinero=0
    mejoras=[{"dano":0,"vida":0} for _ in range(2)]

def sumar_dinero(cantidad):
    global dinero
    dinero+=cantidad

def cambiar_skin(i):
    skins[i]=(skins[i]+1)%len(NOMBRES_SKIN)
    guardar_json(F_SKINS,{str(n):v for n,v in enumerate(skins)})
    play(S_MENU,'menu')

def aplicar_skin(im,i):
    variante=skins[i]
    if not variante: return im
    clave=(id(im),i,variante)
    if clave in CACHE_SKINS: return CACHE_SKINS[clave]
    resultado=im.copy()
    # Cambia tonos de la ropa, preservando piel, pelo, alpha y sombreado.
    for y in range(int(im.get_height()*.38),im.get_height()):
        for x in range(im.get_width()):
            r,g,b,a=im.get_at((x,y))
            if a<30: continue
            h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
            objetivo=((h<.065 or h>.94) if i==0 else (.51<h<.72) if i==1 else (.09<h<.17) if i==2 else (.43<h<.57))
            if objetivo and s>.32:
                nh,ns=(.38,.70) if variante==1 else (.78,.60) if variante==2 else (.54,.18)
                nr,ng,nb=colorsys.hsv_to_rgb(nh,ns,v)
                resultado.set_at((x,y),(round(nr*255),round(ng*255),round(nb*255),a))
    CACHE_SKINS[clave]=resultado
    return resultado

def usar_habilidad(j):
    if j.vida<=0 or j.recarga_habilidad>0: return False
    i=j.sprite_indice
    if i==0:
        for aliado in jugadores:
            if aliado.vida>0: aliado.impulso=360
    elif i==1:
        dx,dy=j.direccion
        for _ in range(12): mover_col(j,dx*7,dy*7)
        j.invencible=max(j.invencible,36)
    elif i==2:
        for z in zombies[:]:
            dx,dy=z.x-j.x,z.y-j.y; distancia=math.hypot(dx,dy)
            if distancia<145+z.radio:
                z.recibir_daño(45)
                for _ in range(6): mover_col(z,dx/max(1,distancia)*6,dy/max(1,distancia)*6)
        shake(5)
    elif i==3:
        aliados=[a for a in jugadores if a.vida>0 and a.vida<a.vida_max and math.hypot(a.x-j.x,a.y-j.y)<=220]
        if not aliados:
            mostrar_mensaje('No hay aliados heridos cerca'); return False
        for a in aliados: a.vida=min(a.vida_max,a.vida+35)
    j.recarga_habilidad=HABILIDADES[i][2]*60
    for _ in range(18): particulas.append(Particula(j.x,j.y,j.color,4,25))
    play(S_POWERUP)
    mostrar_mensaje(j.nombre+': '+HABILIDADES[i][0])
    return True

def abrir_habilidades(regreso):
    global estado,regreso_habilidades,cursor_habilidad
    regreso_habilidades=regreso
    cursor_habilidad=cursor_personaje if regreso==SELECCION else 0
    estado='habilidades'

def abrir_tienda():
    global estado,cursor_tienda,comprador,aviso_tienda
    estado='tienda'; cursor_tienda=0; comprador=0; aviso_tienda=''

def comprar():
    global dinero,aviso_tienda
    j=jugadores[comprador]; nombre,precio=PRODUCTOS[cursor_tienda]
    clave='dano' if cursor_tienda==2 else 'vida'
    if cursor_tienda>=2 and mejoras[comprador][clave]>=3:
        aviso_tienda='Mejora al maximo'; return False
    if dinero<precio:
        aviso_tienda='No alcanzan las monedas'; return False
    dinero-=precio
    if cursor_tienda==0: j.botiquines+=1
    elif cursor_tienda==1: j.granadas+=1
    else:
        mejoras[comprador][clave]+=1
        if clave=='vida': j.vida_max+=20; j.vida=min(j.vida_max,j.vida+20)
    aviso_tienda='Comprado para '+j.nombre+': '+nombre
    play(S_POWERUP); return True

def texto_centro(texto,y,color=BLANCO,f=None):
    im=texto_ajustado(f or fuente_med,texto,color,ANCHO-80)
    pantalla.blit(im,im.get_rect(center=(ANCHO//2,y)))

def dibujar_habilidades():
    pantalla.fill((12,19,30))
    texto_centro('HABILIDADES Y SKINS',55,DORADO,fuente_gran)
    i=cursor_habilidad
    avatar=aplicar_skin(AVATARES[i],i)
    pantalla.blit(avatar,avatar.get_rect(midbottom=(ANCHO//2,285)))
    texto_centro(PERSONAJES[i]['nombre']+' - '+HABILIDADES[i][0],330,CIAN)
    texto_centro(HABILIDADES[i][1],385,BLANCO,fuente)
    texto_centro('Recarga: '+str(HABILIDADES[i][2])+' segundos de juego',425,AMARILLO,fuente)
    texto_centro('Skin: '+NOMBRES_SKIN[skins[i]]+' (cosmetica, gratuita)',470,VERDE)
    texto_centro('P1: F | P2: 0 o NUM 0 | Mando: pulsar stick izquierdo (boton 9)',535,BLANCO,fuente)
    texto_centro('A/D: personaje | X: cambiar skin | ENTER / ESC: volver',585,BLANCO,fuente)
    texto_centro('Mando: LB/RB personaje | X skin | A / START volver',620,GRIS_CLARO,fuente)

def dibujar_tienda():
    pantalla.fill((12,19,30))
    texto_centro('TIENDA DE SUPERVIVENCIA',55,DORADO,fuente_gran)
    texto_centro('Bolsa del equipo: $'+str(dinero),110,VERDE)
    j=jugadores[comprador]
    texto_centro('Comprando para P'+str(j.num)+': '+j.nombre,160,CIAN)
    for i,(nombre,precio) in enumerate(PRODUCTOS):
        texto_centro(('> ' if cursor_tienda==i else '')+nombre+'   $'+str(precio),235+i*55,DORADO if i==cursor_tienda else BLANCO)
    texto_centro('Dano: '+str(mejoras[comprador]['dano'])+'/3 | Salud: '+str(mejoras[comprador]['vida'])+'/3 | Botiquines: '+str(j.botiquines)+' | Granadas: '+str(j.granadas),460,GRIS_CLARO,fuente)
    texto_centro(aviso_tienda,500,AMARILLO,fuente)
    texto_centro('Arriba/abajo: producto | TAB: jugador | ENTER: comprar',550,BLANCO,fuente)
    texto_centro('N: siguiente nivel | Mando: LB/RB producto, Y jugador, A comprar, START seguir',590,BLANCO,fuente)
    texto_centro('Las compras duran esta partida. Cada nivel restaura la salud.',630,GRIS_CLARO,fuente)

_evento_original=procesar_evento
_confirmar_original=confirmar
_dibujar_original=dibujar
_hud_original=dibujar_hud

def confirmar():
    global estado
    if estado=='habilidades': estado=regreso_habilidades
    elif estado=='tienda': comprar()
    else: _confirmar_original()

def siguiente_desde_tienda():
    global estado
    estado='salir_tienda'; _confirmar_original()

def procesar_evento(ev):
    global estado,cursor_habilidad,cursor_tienda,comprador
    if ev.type==pg.KEYDOWN:
        k=ev.key
        if estado=='habilidades':
            if k in (pg.K_a,pg.K_LEFT,pg.K_d,pg.K_RIGHT): cursor_habilidad=(cursor_habilidad+(1 if k in (pg.K_d,pg.K_RIGHT) else -1))%4
            elif k==pg.K_x: cambiar_skin(cursor_habilidad)
            elif k in (pg.K_RETURN,pg.K_ESCAPE): estado=regreso_habilidades
            else: tecla_audio(k)
            return
        if estado=='tienda':
            if k in (pg.K_UP,pg.K_DOWN): cursor_tienda=(cursor_tienda+(1 if k==pg.K_DOWN else -1))%4
            elif k==pg.K_TAB: comprador=(comprador+1)%len(jugadores)
            elif k==pg.K_RETURN: comprar()
            elif k==pg.K_n: siguiente_desde_tienda()
            else: tecla_audio(k)
            return
        if estado in (MENU,SELECCION,PAUSA) and k==pg.K_h:
            abrir_habilidades(estado); return
        if estado==SELECCION and k==pg.K_x: cambiar_skin(cursor_personaje); return
        if estado==JUGANDO and k in (pg.K_f,pg.K_0,pg.K_KP0):
            num=1 if k==pg.K_f else 2
            for j in jugadores:
                if j.num==num: usar_habilidad(j)
            return
    if ev.type==pg.JOYBUTTONDOWN:
        idx=next((i for i,j in enumerate(joysticks) if j.get_instance_id()==ev.instance_id),-1)
        if idx<0: return
        b=ev.button
        if estado=='habilidades':
            if b in (4,5): cursor_habilidad=(cursor_habilidad+(1 if b==5 else -1))%4
            elif b==2: cambiar_skin(cursor_habilidad)
            elif b in (0,7): estado=regreso_habilidades
            return
        if estado=='tienda':
            if b in (4,5): cursor_tienda=(cursor_tienda+(1 if b==5 else -1))%4
            elif b==3: comprador=(comprador+1)%len(jugadores)
            elif b==0: comprar()
            elif b==7: siguiente_desde_tienda()
            return
        if estado==SELECCION and b==2: cambiar_skin(cursor_personaje); return
        if estado==JUGANDO and b==9:
            for j in jugadores:
                if j.num==idx+1: usar_habilidad(j)
            return
    _evento_original(ev)

def dibujar_hud():
    _hud_original()
    for i,j in enumerate(jugadores):
        tecla='F' if i==0 else '0'
        tiempo=math.ceil(j.recarga_habilidad/60)
        texto='P'+str(j.num)+' ['+tecla+'] '+HABILIDADES[j.sprite_indice][0]+(': '+str(tiempo)+'s' if tiempo else ': LISTA')
        im=fuente_peq.render(texto,True,AMARILLO if tiempo else VERDE)
        pg.draw.rect(pantalla,(12,19,30),(18+i*600,ALTO-47,570,24),border_radius=5)
        pantalla.blit(im,(25+i*600,ALTO-43))

def dibujar():
    if estado=='habilidades': dibujar_habilidades()
    elif estado=='tienda': dibujar_tienda()
    else: _dibujar_original()

if __name__=="__main__":
    main()