"""LevelParser — Construye plataformas a partir de un archivo de terreno .txt.

Formato del archivo
-------------------
Una secuencia de enteros que alterna ANCHO y ESCALON:

    ancho1  escalon1  ancho2  escalon2  ...

  - ancho   (posicion impar) : bloques horizontales.
                               +x suelo (tierra hacia la derecha)
                               -x techo (techo hacia la izquierda)
  - escalon (posicion par)   : bloques verticales.
                               +y pared sube
                               -y pared baja

El mapa DEBE ser cerrado: el ultimo vertice debe coincidir con el primero.

Tiles y cuando se usan
-----------------------
  tierra       tramo +x (suelo pisable)
  relleno      relleno interior bajo tierra o sobre techo
  techo        tramo -x (techo, cara inferior visible)
  techo_iz     esquina: -x seguido de +y
  techo_iz_ar  esquina: +y seguido de -x
  techo_der    esquina: -y seguido de -x
  techo_der_ar esquina: -x seguido de -y
  final_iz     esquina superior izquierda de pared (suelo sube)
  final_der    esquina superior derecha de pared
  pared_iz     cuerpo pared izquierda
  pared_der    cuerpo pared derecha
  union_iz     esquina inferior izquierda
  union_der    esquina inferior derecha
"""

import os
import pygame
import Constantes
from view.Plataforma import Plataforma


TILE_SIZE = 16

_TILES = {
    'tierra':       pygame.Rect(0,   0,  TILE_SIZE, TILE_SIZE),
    'relleno':      pygame.Rect(0,   16, TILE_SIZE, TILE_SIZE),
    'final_der':    pygame.Rect(128, 0,  TILE_SIZE, TILE_SIZE),
    'final_iz':     pygame.Rect(48,  0,  TILE_SIZE, TILE_SIZE),
    'pared_der':    pygame.Rect(128, 16, TILE_SIZE, TILE_SIZE),
    'pared_iz':     pygame.Rect(48,  16, TILE_SIZE, TILE_SIZE),
    'union_der':    pygame.Rect(128, 48, TILE_SIZE, TILE_SIZE),
    'union_iz':     pygame.Rect(48,  48, TILE_SIZE, TILE_SIZE),
    'techo':        pygame.Rect(80,  64, TILE_SIZE, TILE_SIZE),
    'techo_der':    pygame.Rect(112, 64, TILE_SIZE, TILE_SIZE),
    'techo_iz':     pygame.Rect(64,  64, TILE_SIZE, TILE_SIZE),
    'techo_der_ar': pygame.Rect(80,  80, TILE_SIZE, TILE_SIZE),
    'techo_iz_ar':  pygame.Rect(64,  80, TILE_SIZE, TILE_SIZE),
}

GROSOR_SUELO = TILE_SIZE
GROSOR_PARED = TILE_SIZE
GROSOR_TECHO = TILE_SIZE


class LevelParser:

    def __init__(self, tileset: pygame.Surface):
        self.tileset = tileset

    # -----------------------------------------------------------------------
    # API publica
    # -----------------------------------------------------------------------

    def cargar(self, ruta: str) -> list:
        numeros   = self._leer_numeros(ruta)
        segmentos = self._numeros_a_segmentos(numeros)
        self._verificar_cierre(segmentos, ruta)
        return self._construir(segmentos)

    # -----------------------------------------------------------------------
    # Lectura
    # -----------------------------------------------------------------------

    def _leer_numeros(self, ruta: str) -> list:
        ruta_abs = os.path.join(os.path.dirname(os.path.abspath(__file__)), ruta)
        with open(ruta_abs, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        tokens = []
        for linea in lineas:
            linea = linea.split('#')[0].strip()
            tokens.extend(linea.split())
        return [int(t) for t in tokens if t]

    def _numeros_a_segmentos(self, numeros: list) -> list:
        """Convierte la secuencia compacta a lista de segmentos.

        Cada segmento tiene:
            tipo  : 'suelo' | 'techo' | 'pared'
            x1,y1 : inicio en pixeles pygame
            x2,y2 : fin    en pixeles pygame
            dx    : desplazamiento horizontal en bloques (con signo, 0 si pared)
            dy    : desplazamiento vertical   en bloques (con signo, 0 si horizontal)
        """
        cx, cy = 0, 0
        segmentos = []

        for i, n in enumerate(numeros):
            px1 = cx * TILE_SIZE
            py1 = Constantes.SUELO_Y - cy * TILE_SIZE

            if i % 2 == 0:
                cx  += n
                tipo = 'suelo' if n > 0 else 'techo'
                dx, dy = n, 0
            else:
                cy  += n
                tipo = 'pared'
                dx, dy = 0, n

            px2 = cx * TILE_SIZE
            py2 = Constantes.SUELO_Y - cy * TILE_SIZE

            segmentos.append({
                'tipo': tipo,
                'x1': px1, 'y1': py1,
                'x2': px2, 'y2': py2,
                'dx': dx,  'dy': dy,
            })

        return segmentos

    def _verificar_cierre(self, segmentos: list, ruta: str):
        if not segmentos:
            return
        x0, y0 = segmentos[0]['x1'], segmentos[0]['y1']
        xf, yf = segmentos[-1]['x2'], segmentos[-1]['y2']
        if x0 != xf or y0 != yf:
            raise ValueError(
                f"[LevelParser] '{ruta}' no esta cerrado.\n"
                f"  Inicio : ({x0}, {y0})\n"
                f"  Final  : ({xf}, {yf})"
            )

    # -----------------------------------------------------------------------
    # Construccion
    # -----------------------------------------------------------------------

    def _construir(self, segmentos: list) -> list:
        plataformas = []
        ts = self.tileset
        n  = len(segmentos)

        for i, seg in enumerate(segmentos):
            prev_seg = segmentos[(i - 1) % n]
            next_seg = segmentos[(i + 1) % n]

            if seg['tipo'] == 'suelo':
                self._tramo_suelo(plataformas, ts, seg)
            elif seg['tipo'] == 'techo':
                self._tramo_techo(plataformas, ts, seg, prev_seg, next_seg)
            elif seg['tipo'] == 'pared':
                self._tramo_pared(plataformas, ts, seg, prev_seg, next_seg)

        return plataformas

    # -----------------------------------------------------------------------
    # Tramo suelo (+x)
    # -----------------------------------------------------------------------

    def _tramo_suelo(self, lista, ts, seg):
        x1, x2 = seg['x1'], seg['x2']
        y       = seg['y1']
        xmin    = min(x1, x2)
        ancho   = abs(x2 - x1)
        if ancho <= 0:
            return
        t = _TILES
        lista.append(Plataforma(xmin, y, ancho, GROSOR_SUELO, ts, t['tierra']))
        fondo   = Constantes.HEIGHT + TILE_SIZE
        relleno = fondo - (y + GROSOR_SUELO)
        if relleno > 0:
            lista.append(Plataforma(
                xmin, y + GROSOR_SUELO, ancho, relleno, ts, t['relleno']
            ))

    # -----------------------------------------------------------------------
    # Tramo techo (-x)
    # -----------------------------------------------------------------------

    def _tramo_techo(self, lista, ts, seg, prev_seg, next_seg):
        """Techo con esquinas segun contexto anterior y siguiente.

        El tramo -x va de derecha a izquierda, asi que:
          x1 > x2  (x1 es el lado derecho, x2 es el lado izquierdo)

        Esquina derecha (inicio del -x, lado x1):
          prev dy > 0  (+y antes de -x) -> techo_iz_ar
          prev dy < 0  (-y antes de -x) -> techo_der

        Esquina izquierda (fin del -x, lado x2):
          next dy > 0  (-x seguido de +y) -> techo_iz
          next dy < 0  (-x seguido de -y) -> techo_der_ar
        """
        x1, x2 = seg['x1'], seg['x2']   # x1 > x2 porque dx < 0
        y       = seg['y1']
        xmin    = min(x1, x2)
        xmax    = max(x1, x2)
        ancho   = xmax - xmin
        if ancho <= 0:
            return

        t = _TILES

        # Esquina derecha (lado x1, inicio del recorrido -x)
        prev_dy = prev_seg['dy']
        if prev_dy > 0:
            tile_der = t['techo_iz_ar']
        elif prev_dy < 0:
            tile_der = t['techo_der']
        else:
            tile_der = t['techo']

        # Esquina izquierda (lado x2, fin del recorrido -x)
        next_dy = next_seg['dy']
        if next_dy > 0:
            tile_iz = t['techo_iz']
        elif next_dy < 0:
            tile_iz = t['techo_der_ar']
        else:
            tile_iz = t['techo']

        if ancho <= TILE_SIZE:
            lista.append(Plataforma(xmin, y, ancho, GROSOR_TECHO, ts, tile_der))
        elif ancho <= 2 * TILE_SIZE:
            lista.append(Plataforma(xmax - TILE_SIZE, y, TILE_SIZE, GROSOR_TECHO, ts, tile_der))
            lista.append(Plataforma(xmin,             y, TILE_SIZE, GROSOR_TECHO, ts, tile_iz))
        else:
            lista.append(Plataforma(xmax - TILE_SIZE, y, TILE_SIZE, GROSOR_TECHO, ts, tile_der))
            cuerpo = ancho - 2 * TILE_SIZE
            lista.append(Plataforma(xmin + TILE_SIZE, y, cuerpo,    GROSOR_TECHO, ts, t['techo']))
            lista.append(Plataforma(xmin,             y, TILE_SIZE, GROSOR_TECHO, ts, tile_iz))

        # Relleno encima del techo hasta el borde superior de camara
        if y > 0:
            lista.append(Plataforma(xmin, 0, ancho, y, ts, t['relleno']))

    # -----------------------------------------------------------------------
    # Tramo pared (+-y)
    # -----------------------------------------------------------------------

    def _tramo_pared(self, lista, ts, seg, prev_seg, next_seg):
        x  = seg['x1']
        y1 = seg['y1']
        y2 = seg['y2']
        dy = seg['dy']

        ymin = min(y1, y2)
        ymax = max(y1, y2)
        alto = ymax - ymin
        if alto <= 0:
            return

        t    = _TILES
        sube = dy > 0

        if sube:
            # Pared que sube (+y): interior a la izquierda, cara derecha visible
            # sprite se coloca en x - GROSOR_PARED
            tile_pared = t['pared_iz']
            x_sprite   = x - GROSOR_PARED
            # Esquina superior: conecta con el segmento anterior
            # prev es suelo (+x) -> final_iz
            # prev es techo (-x) -> techo_iz_ar
            tile_sup = t['techo_iz_ar'] if prev_seg['dx'] < 0 else t['final_iz']
            # Esquina inferior: conecta con el segmento siguiente
            # next es suelo (+x) -> union_iz
            # next es techo (-x) -> techo_iz
            tile_inf = t['techo_iz'] if next_seg['dx'] < 0 else t['union_iz']
        else:
            # Pared que baja (-y): interior a la derecha, cara izquierda visible
            tile_pared = t['pared_der']
            x_sprite   = x
            # Esquina superior: conecta con el segmento anterior
            # prev es suelo (+x) -> final_der
            # prev es techo (-x) -> techo_der
            tile_sup = t['techo_der'] if prev_seg['dx'] < 0 else t['final_der']
            # Esquina inferior: conecta con el segmento siguiente
            # next es suelo (+x) -> union_der
            # next es techo (-x) -> techo_der_ar
            tile_inf = t['techo_der_ar'] if next_seg['dx'] < 0 else t['union_der']

        # Esquina superior
        lista.append(Plataforma(
            x_sprite, ymin, GROSOR_PARED, GROSOR_PARED, ts, tile_sup
        ))
        # Cuerpo
        cuerpo = alto - GROSOR_PARED
        if cuerpo > 0:
            lista.append(Plataforma(
                x_sprite, ymin + GROSOR_PARED,
                GROSOR_PARED, cuerpo, ts, tile_pared
            ))
        # Esquina inferior
        lista.append(Plataforma(
            x_sprite, ymax, GROSOR_PARED, GROSOR_PARED, ts, tile_inf
        ))
