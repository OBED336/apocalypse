"""Pausa con controles y audio sin abandonar la partida congelada.

En el apartado AUDIO, las voces tienen su propio volumen, separado del de
los efectos: MÚSICA, EFECTOS, VOCES; más SILENCIO GENERAL y el interruptor
de voces activas.
"""
import pygame as pg
import menu as estilo

G=None
cursor=0
vista='inicio'
fila_audio=0
nav_hasta=0
botones=tuple(pg.Rect(140,245+i*62,310,50) for i in range(5))
etiquetas=('CONTINUAR', 'HABILIDADES Y SKINS', 'CONTROLES', 'AUDIO', 'MENU PRINCIPAL')
atras=pg.Rect(938,566,100,32)
barras=(pg.Rect(560,267,420,18), pg.Rect(560,337,420,18), pg.Rect(560,407,420,18))
silencio=pg.Rect(560,452,200,38)
voces_boton=pg.Rect(775,452,205,38)


def texto(s,x,y,tipo='pequena',color=estilo.BLANCO):
    estilo.texto(s,x,y,tipo,color)


def ajustar_audio(fila,delta):
    if fila==0: G.volumen_musica=max(0,min(1,round(G.volumen_musica+delta,2)))
    elif fila==1: G.volumen_efectos=max(0,min(1,round(G.volumen_efectos+delta,2)))
    elif fila==2: G.volumen_voces=max(0,min(1,round(G.volumen_voces+delta,2)))
    elif fila==3: G.audio_silenciado=not G.audio_silenciado
    else:
        import voces
        voces.voces_activas=not voces.voces_activas
    G.aplicar_volumen()
    G.guardar_audio()


def activar():
    global vista
    G.play(G.S_CONFIRMAR,'menu')
    if cursor==0: G.estado=G.JUGANDO
    elif cursor==1: G.abrir_habilidades(G.PAUSA)
    elif cursor==2: vista='controles'
    elif cursor==3: vista='audio'
    else:
        import voces
        if voces.canal: voces.canal.stop()
        G.estado=G.MENU


def dibujar():
    capa=pg.Surface((1200,700),pg.SRCALPHA)
    capa.fill((5,12,18,175))
    G.pantalla.blit(capa,(0,0))
    pg.draw.rect(G.pantalla,(14,25,33),(100,80,1000,552),border_radius=18)
    pg.draw.rect(G.pantalla,(61,88,91),(100,80,1000,552),1,border_radius=18)
    pg.draw.rect(G.pantalla,estilo.MENTA,(140,119,6,14),border_radius=2)
    texto('UN MOMENTO PARA RESPIRAR',157,118,'micro',estilo.MENTA)
    texto('PAUSA',137,145,'titulo')
    texto('El combate y el reloj están detenidos.',142,216,'micro',estilo.SUAVE)
    for i,r in enumerate(botones):
        activo=cursor==i
        pg.draw.rect(G.pantalla,(41,74,66) if activo else (22,37,45),r,border_radius=8)
        pg.draw.rect(G.pantalla,estilo.MENTA if activo else (55,74,80),r,2 if activo else 1,border_radius=8)
        texto(etiquetas[i],r.x+18,r.y+16,'pequena',estilo.BLANCO if i<4 or activo else estilo.SUAVE)
        if i==0: texto('ESC',r.right-48,r.y+19,'micro',estilo.MENTA)
    pg.draw.line(G.pantalla,(55,75,80),(490,120),(490,555))
    if vista=='controles':
        texto('CONTROLES',530,132,'hero')
        datos=(('JUGADOR 1','JUGADOR 2'),('WASD: mover','Flechas: mover'),
               ('ESPACIO: disparar','ENTER: disparar'),('SHIFT izq.: correr','SHIFT der.: correr'),
               ('Q: curar | E: golpe','Punto: curar | CTRL: golpe'),('R: arma | G: granada','Coma: arma | /: granada'),
               ('F: habilidad','0: habilidad'),('T: conversar | Y: frase','L: conversar | U: frase'))
        for i,(a,b) in enumerate(datos):
            color=estilo.MENTA if i==0 else estilo.BLANCO
            texto(a,530,204+i*35,'micro' if i else 'pequena',color)
            texto(b,795,204+i*35,'micro' if i else 'pequena',color)
        texto('Mando: stick mueve, B dispara, X golpea, Y lanza granada.',530,511,'micro',estilo.SUAVE)
        texto('P / ESC / START: pausa. V: activar o silenciar voces.',530,537,'micro',estilo.SUAVE)
    elif vista=='audio':
        import voces
        texto('AUDIO',530,132,'hero')
        texto('Ajusta el sonido sin salir de la partida.',530,192,'pequena',estilo.SUAVE)
        for i,(r,valor,nombre) in enumerate(zip(barras,(G.volumen_musica,G.volumen_efectos,G.volumen_voces),('MÚSICA','EFECTOS','VOCES'))):
            color=estilo.MENTA if fila_audio==i else estilo.SUAVE
            texto(nombre,r.x,r.y-30,'pequena',color)
            texto(str(round(valor*100))+'%',r.right-40,r.y-30,'pequena',estilo.BLANCO)
            pg.draw.rect(G.pantalla,(44,62,68),r,border_radius=8)
            if valor: pg.draw.rect(G.pantalla,estilo.MENTA,(r.x,r.y,max(1,round(r.w*valor)),r.h),border_radius=8)
            pg.draw.circle(G.pantalla,estilo.BLANCO,(r.x+round(r.w*valor),r.centery),10)
        for i,(r,cadena,activo) in enumerate(((silencio,'SILENCIO GENERAL',G.audio_silenciado),(voces_boton,'VOCES',voces.voces_activas))):
            pg.draw.rect(G.pantalla,(41,74,66) if activo else (25,40,48),r,border_radius=7)
            pg.draw.rect(G.pantalla,estilo.MENTA if fila_audio==i+3 else (65,85,88),r,1,border_radius=7)
            texto(cadena+(' · SI' if activo else ' · NO'),r.x+13,r.y+12,'micro')
        texto('Haz clic en las barras o usa ↑ ↓ y ← →.',560,516,'pequena',estilo.SUAVE)
        texto('ENTER cambia el interruptor seleccionado.',560,544,'micro',estilo.SUAVE)
    else:
        texto('TU PARTIDA',530,132,'hero')
        texto(G.NIVELES[G.nivel_actual]['nombre'],530,192,'boton',estilo.MENTA)
        texto('Piso '+str(G.nivel_actual+1)+' / '+str(len(G.NIVELES))+'   ·   Tiempo '+str(max(0,int(G.tiempo_restante)))+' s',530,231,'pequena',estilo.SUAVE)
        texto('Puntos '+str(G.puntuacion_total)+'   ·   Monedas $'+str(G.dinero),530,257,'pequena',estilo.SUAVE)
        for i,j in enumerate(G.jugadores[:2]):
            r=pg.Rect(530+i*260,305,500 if len(G.jugadores)==1 else 240,235)
            pg.draw.rect(G.pantalla,(22,37,45),r,border_radius=11)
            im=G.ajustar_imagen(G.RETRATOS[j.sprite_indice],120,140)
            G.pantalla.blit(im,im.get_rect(midbottom=(r.centerx,r.y+150)))
            texto('P'+str(j.num)+' · '+j.nombre,r.x+16,r.y+159,'boton',j.color)
            barra=pg.Rect(r.x+16,r.y+195,r.w-32,6)
            pg.draw.rect(G.pantalla,(51,65,71),barra,border_radius=3)
            salud=max(0,min(1,j.vida/j.vida_max))
            if salud: pg.draw.rect(G.pantalla,j.color,(barra.x,barra.y,round(barra.w*salud),6),border_radius=3)
            texto('SALUD '+str(max(0,int(j.vida)))+' / '+str(j.vida_max),r.x+16,r.y+209,'micro',estilo.SUAVE)
        if cursor==4: texto('Volver al menú finaliza esta partida.',530,550,'micro',(237,186,132))
    pg.draw.line(G.pantalla,(55,75,80),(140,565),(1060,565))
    texto('RATÓN o ↑ ↓ + ENTER: elegir   ·   ESC: '+('volver' if vista!='inicio' else 'continuar'),142,590,'micro',estilo.SUAVE)
    if vista!='inicio':
        pg.draw.rect(G.pantalla,(35,55,60),atras,border_radius=6)
        texto('VOLVER',atras.x+23,atras.y+10,'micro',estilo.MENTA)


def instalar(juego):
    global G
    G=juego
    evento_original=G.procesar_evento
    audio_original=G.dibujar_control_audio
    confirmar_original=G.confirmar
    def confirmar():
        if G.estado==G.PAUSA: activar()
        else: confirmar_original()
    def evento(ev):
        global cursor,vista,fila_audio,nav_hasta
        if G.estado!=G.PAUSA:
            antes=G.estado
            evento_original(ev)
            if antes==G.JUGANDO and G.estado==G.PAUSA:
                cursor=0
                vista='inicio'
            return
        if ev.type==pg.KEYDOWN:
            k=ev.key
            if G.tecla_audio(k): return
            if k in (pg.K_ESCAPE,pg.K_p):
                if vista!='inicio': vista='inicio'
                else: G.estado=G.JUGANDO
            elif k==pg.K_h: G.abrir_habilidades(G.PAUSA)
            elif vista=='audio' and k in (pg.K_UP,pg.K_DOWN): fila_audio=(fila_audio+(1 if k==pg.K_DOWN else -1))%5
            elif vista=='audio' and k in (pg.K_LEFT,pg.K_RIGHT) and fila_audio<3:
                ajustar_audio(fila_audio,.05 if k==pg.K_RIGHT else -.05)
            elif vista=='audio' and k==pg.K_RETURN:
                if fila_audio>=3: ajustar_audio(fila_audio,0)
            elif k in (pg.K_UP,pg.K_DOWN): cursor=(cursor+(1 if k==pg.K_DOWN else -1))%5
            elif k==pg.K_RETURN: activar()
            elif k==pg.K_v:
                import voces
                voces.voces_activas=not voces.voces_activas
            return
        if ev.type==pg.MOUSEMOTION:
            for i,r in enumerate(botones):
                if r.collidepoint(ev.pos): cursor=i
            return
        if ev.type==pg.MOUSEBUTTONDOWN and ev.button==1:
            if vista!='inicio' and atras.collidepoint(ev.pos): vista='inicio'; return
            for i,r in enumerate(botones):
                if r.collidepoint(ev.pos): cursor=i; activar(); return
            if vista=='audio':
                for i,r in enumerate(barras):
                    if r.inflate(18,20).collidepoint(ev.pos):
                        fila_audio=i
                        valor=max(0,min(1,(ev.pos[0]-r.x)/r.w))
                        actual=(G.volumen_musica,G.volumen_efectos,G.volumen_voces)[i]
                        ajustar_audio(i,valor-actual)
                for i,r in enumerate((silencio,voces_boton)):
                    if r.collidepoint(ev.pos): fila_audio=i+3; ajustar_audio(i+3,0)
            return
        if ev.type in (pg.JOYHATMOTION,pg.JOYBUTTONDOWN,pg.JOYAXISMOTION):
            if ev.type==pg.JOYAXISMOTION:
                ahora=pg.time.get_ticks()
                if abs(ev.value)<.35: nav_hasta=0
                elif abs(ev.value)>.55 and ahora>=nav_hasta:
                    signo=1 if ev.value>0 else -1
                    if ev.axis==1:
                        if vista=='audio': fila_audio=(fila_audio+signo)%5
                        else: cursor=(cursor+signo)%5
                    elif ev.axis==0 and vista=='audio' and fila_audio<3: ajustar_audio(fila_audio,.05*signo)
                    nav_hasta=ahora+220
            elif ev.type==pg.JOYHATMOTION:
                if vista=='audio':
                    if ev.value[1]: fila_audio=(fila_audio-ev.value[1])%5
                    if ev.value[0] and fila_audio<3: ajustar_audio(fila_audio,.05*ev.value[0])
                elif ev.value[1]: cursor=(cursor-ev.value[1])%5
            elif ev.type==pg.JOYBUTTONDOWN:
                if ev.button in (1,6,7):
                    if vista!='inicio': vista='inicio'
                    else: G.estado=G.JUGANDO
                elif ev.button==0:
                    if vista=='audio':
                        if fila_audio>=3: ajustar_audio(fila_audio,0)
                    else: activar()
            return
        evento_original(ev)
    def audio():
        if G.estado!=G.PAUSA: audio_original()
    G.dibujar_pausa=dibujar
    G.procesar_evento=evento
    G.confirmar=confirmar
    G.dibujar_control_audio=audio
