"""Arte procedural precalculado: no cambia colisiones ni consume el azar del juego."""
import random
from functools import lru_cache
import pygame as pg

def tono(color,factor,extra=0):
    return tuple(max(0,min(255,int(c*factor+extra))) for c in color)

@lru_cache(maxsize=24)
def halo(radio,color):
    superficie=pg.Surface((radio*2,radio*2)).convert()
    superficie.fill((0,0,0))
    for r in range(radio,0,-3):
        fuerza=(1-r/radio)**2*.42
        pg.draw.circle(superficie,tono(color,fuerza),(radio,radio),r)
    return superficie

def luz(surf,pos,radio,color):
    surf.blit(halo(radio,color),(round(pos[0]-radio),round(pos[1]-radio)),special_flags=pg.BLEND_RGB_ADD)

@lru_cache(maxsize=12)
def suelo(nombre,color,acento,cx,cy,ancho,alto):
    surf=pg.Surface((ancho,alto)).convert()
    rng=random.Random(f'{nombre}:{cx}:{cy}')
    surf.fill(tono(color,.85))
    interior=pg.Rect(40,115,ancho-80,alto-155)
    surf.set_clip(interior)
    baldosa=64 if nombre=='Hospital' else 96
    for y in range(115,alto,baldosa):
        for x in range(40,ancho,baldosa):
            rect=pg.Rect(x,y,baldosa,baldosa)
            c=tono(color,rng.uniform(.85,1.16))
            pg.draw.rect(surf,tono(c,.65),rect)
            pg.draw.rect(surf,c,rect.inflate(-3,-3))
            pg.draw.line(surf,tono(c,1.3),(x+2,y+2),(x+baldosa-3,y+2))
            if nombre in ('Base','Final'):
                for bx,by in ((x+8,y+8),(x+baldosa-9,y+baldosa-9)):
                    pg.draw.circle(surf,tono(c,.45),(bx,by),2)
    # Grano, arañazos y grietas permanecen fijos al revisitar una sala.
    for _ in range(5500):
        x,y=rng.randrange(40,ancho-40),rng.randrange(115,alto-40)
        pg.draw.line(surf,tono(color,rng.uniform(.55,1.35)),(x,y),(x+rng.randrange(1,4),y))
    if nombre in ('Calles','Downtown'):
        for x in range(95,ancho-95,145):
            pg.draw.rect(surf,(125,113,72),(x,alto//2+26,78,5),border_radius=2)
        for y in (156,alto-85):
            pg.draw.line(surf,tono(color,1.6),(70,y),(ancho-70,y),2)
        for i in range(5):
            pg.draw.rect(surf,(100,101,98),(100+i*31,190,18,75))
        for x,y in ((ancho-160,205),(150,alto-135)):
            pg.draw.ellipse(surf,(23,28,34),(x-28,y-15,56,30))
            pg.draw.ellipse(surf,(67,75,84),(x-28,y-15,56,30),2)
            for offset in range(-18,20,7): pg.draw.line(surf,(62,70,77),(x+offset,y-10),(x+offset,y+10),2)
    elif nombre=='Hospital':
        pg.draw.line(surf,(63,105,109),(80,173),(ancho-80,173),7)
        pg.draw.line(surf,(63,105,109),(80,173),(80,alto-80),7)
        pg.draw.rect(surf,(119,148,142),(ancho-150,190,45,13))
        pg.draw.rect(surf,(119,148,142),(ancho-134,174,13,45))
    else:
        for x in range(88,ancho-88,30):
            pg.draw.polygon(surf,(136,116,54),[(x,153),(x+12,153),(x+21,163),(x+9,163)])
        for y in (205,alto-110):
            pg.draw.rect(surf,tono(acento,.38),(90,y,ancho-180,2))
        # Placa de servicio con rejilla.
        pg.draw.rect(surf,tono(color,.6),(ancho-215,190,110,64),border_radius=6)
        for y in range(204,240,9): pg.draw.line(surf,tono(color,1.4),(ancho-204,y),(ancho-117,y),3)
    for _ in range(14):
        x,y=rng.randrange(90,ancho-90),rng.randrange(180,alto-80)
        puntos=[(x,y)]
        for _ in range(rng.randrange(3,7)):
            x+=rng.randrange(-13,14); y+=rng.randrange(5,16)
            puntos.append((x,y))
        pg.draw.lines(surf,tono(color,.48),False,puntos,2)
        pg.draw.lines(surf,tono(color,1.28),False,[(x+2,y) for x,y in puntos],1)
    surf.set_clip(None)
    return surf

@lru_cache(maxsize=12)
def paredes(color,acento,tipo,ancho,alto):
    surf=pg.Surface((ancho,alto),pg.SRCALPHA)
    muro=tono(color,.48)
    borde=tono(color,1.6)
    for rect in ((0,80,ancho,35),(0,alto-40,ancho,40),(0,115,40,alto-155),(ancho-40,115,40,alto-155)):
        pg.draw.rect(surf,muro,rect)
    pg.draw.rect(surf,tono(color,.2),(36,111,ancho-72,alto-147),7)
    pg.draw.rect(surf,borde,(39,114,ancho-78,alto-153),2)
    for x in range(65,ancho-65,90):
        pg.draw.rect(surf,tono(color,.7),(x,87,80,20),border_radius=3)
        pg.draw.line(surf,borde,(x+4,89),(x+75,89))
        for bx in (x+5,x+73): pg.draw.circle(surf,tono(color,1.8),(bx,101),2)
    for y in range(150,alto-70,80):
        for x in (8,ancho-28):
            pg.draw.rect(surf,tono(color,.8),(x,y,20,60),border_radius=2)
            pg.draw.line(surf,borde,(x+2,y+3),(x+2,y+56))
    # Sombra interior: profundidad sin oscurecer a los personajes.
    for i in range(18):
        alpha=int(90*(1-i/18))
        pg.draw.rect(surf,(0,0,0,alpha),(43+i,118+i,ancho-86-2*i,alto-161-2*i),1)
    couleur=(240,75,65) if tipo=='jefe' else (245,193,88) if tipo=='tesoro' else tono(acento,1.1,45)
    for x,y in ((150,110),(ancho-150,110),(150,alto-38),(ancho-150,alto-38)):
        pg.draw.rect(surf,(8,13,20),(x-30,y-7,60,14),border_radius=4)
        pg.draw.rect(surf,couleur,(x-22,y-2,44,4),border_radius=2)
    return surf

def ambiente(surf,acento,tipo):
    ancho,alto=surf.get_size()
    color=(235,65,55) if tipo=='jefe' else (245,193,88) if tipo=='tesoro' else tono(acento,1,45)
    for x,y in ((150,130),(ancho-150,130),(150,alto-58),(ancho-150,alto-58)):
        luz(surf,(x,y),110,color)

def reticula(surf,j,color):
    if j.vida<=0: return
    dx,dy=j.direccion
    # La mira está a la altura del cañón (pecho), no a la de los pies.
    x,y=round(j.x+dx*84),round(j.y-12+dy*84)
    for ax,ay,bx,by in ((-9,0,-5,0),(5,0,9,0),(0,-9,0,-5),(0,5,0,9)):
        pg.draw.line(surf,(9,15,22),(x+ax,y+ay),(x+bx,y+by),3)
        pg.draw.line(surf,color,(x+ax,y+ay),(x+bx,y+by),1)
    if j.destello>0:
        luz(surf,(j.x+dx*44,j.y+dy*44),65,(255,180,62))
