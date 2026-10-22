"""Carga el atlas de seis pasos con escala estable y transparencia original."""
import pygame as pg


def cargar_pasos(atlas, ancho=72, alto=78):
    # La hoja generada tiene filas de distinta altura, no cuatro bandas iguales.
    cortes = (0, 272, 535, 787, 1024)
    w, h = atlas.get_size()
    pasos = []
    for fila in range(4):
        figuras = []
        for columna in range(6):
            x0, x1 = round(columna*w/6), round((columna+1)*w/6)
            y0, y1 = round(cortes[fila]*h/1024), round(cortes[fila+1]*h/1024)
            celda = atlas.subsurface((x0, y0, x1-x0, y1-y0))
            limites = celda.get_bounding_rect(min_alpha=100)
            if not limites.width or not limites.height:
                raise ValueError(f'Fotograma vacío: fila {fila}, columna {columna}')
            figuras.append(celda.subsurface(limites).copy())
        # Una sola escala por personaje: las poses no cambian su tamaño al andar.
        escala = min(ancho/max(im.get_width() for im in figuras),
                     alto/max(im.get_height() for im in figuras))
        cuadros = []
        for figura in figuras:
            tamano = (max(1, round(figura.get_width()*escala)),
                      max(1, round(figura.get_height()*escala)))
            imagen = pg.transform.smoothscale(figura, tamano)
            lienzo = pg.Surface((ancho, alto), pg.SRCALPHA)
            lienzo.blit(imagen, imagen.get_rect(midbottom=(ancho//2, alto)))
            cuadros.append((lienzo, pg.transform.flip(lienzo, True, False)))
        pasos.append(cuadros)
    return pasos
