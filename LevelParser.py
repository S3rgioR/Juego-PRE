"""LevelParser — Construye plataformas a partir de un archivo de terreno .txt.

Formato del archivo
-------------------
Una sola línea (o varias) con pares de enteros separados por espacios:

    x1 y1 x2 y2 x3 y3 ...

Cada par (xN, yN) es un vértice del contorno SUPERIOR del terreno.
La lista de vértices define la silueta del suelo vista desde arriba:

  - Tramo HORIZONTAL (mismo Y) → superficie pisable en ese Y.
  - Tramo VERTICAL   (mismo X) → pared lateral entre dos alturas.

El parser rellena automáticamente el interior del sólido:
  - Cada tramo horizontal recibe una capa de tierra (tile_tierra) en su Y.
  - Debajo de esa capa se añade relleno de tile_relleno hasta el Y más bajo
    de todo el polígono (y_max), formando un sólido continuo sin huecos.
  - Las paredes verticales se generan entre la altura superior e inferior
    con esquinas apropiadas.

El archivo NO necesita cerrar el polígono manualmente; el relleno llega
siempre hasta y_max (el punto más bajo de todos los vértices).

Tiles del tileset usados
------------------------
  (0,   0,  16, 16)  tile_tierra    — superficie pisable (fila superior)
  (0,   16, 16, 16)  tile_relleno   — relleno interior oscuro
  (48,  0,  16, 16)  tile_final_iz  — esquina superior izquierda de pared
  (128, 0,  16, 16)  tile_final_der — esquina superior derecha de pared
  (48,  16, 16, 16)  tile_pared_iz  — pared lateral izquierda
  (128, 16, 16, 16)  tile_pared_der — pared lateral derecha
  (48,  48, 16, 16)  tile_union_iz  — esquina inferior izquierda (unión suelo)
  (128, 48, 16, 16)  tile_union_der — esquina inferior derecha (unión suelo)

Uso
---
    from LevelParser import LevelParser
    parser = LevelParser(tileset)
    plataformas = parser.cargar("levels/nivel1.txt")
"""

import os
import pygame
import Constantes
from view.Plataforma import Plataforma


# ---------------------------------------------------------------------------
# Definición de tiles
# ---------------------------------------------------------------------------
TILE_SIZE = 16

_TILES = {
    'tierra':    pygame.Rect(0,   0,  TILE_SIZE, TILE_SIZE),
    'relleno':   pygame.Rect(0,   16, TILE_SIZE, TILE_SIZE),
    'final_der': pygame.Rect(128, 0,  TILE_SIZE, TILE_SIZE),
    'final_iz':  pygame.Rect(48,  0,  TILE_SIZE, TILE_SIZE),
    'pared_der': pygame.Rect(128, 16, TILE_SIZE, TILE_SIZE),
    'pared_iz':  pygame.Rect(48,  16, TILE_SIZE, TILE_SIZE),
    'union_der': pygame.Rect(128, 48, TILE_SIZE, TILE_SIZE),
    'union_iz':  pygame.Rect(48,  48, TILE_SIZE, TILE_SIZE),
}

GROSOR_SUELO = TILE_SIZE   # 16 px — capa pisable superior
GROSOR_PARED = TILE_SIZE   # 16 px — paredes laterales


class LevelParser:
    """Lee un archivo .txt de vértices y construye la lista de Plataforma.

    La gran diferencia respecto a la versión anterior es el relleno
    inteligente: en lugar de un RELLENO_EXTRA fijo, cada tramo horizontal
    se rellena hasta el Y más bajo de todo el nivel (y_max), creando un
    sólido sin huecos independientemente de la altura del tramo.

    Parameters
    ----------
    tileset : pygame.Surface
        Hoja de tiles cargada en memoria.
    """

    def __init__(self, tileset: pygame.Surface):
        self.tileset = tileset

    # -----------------------------------------------------------------------
    # API pública
    # -----------------------------------------------------------------------

    def cargar(self, ruta: str) -> list:
        """Carga el archivo de terreno y devuelve la lista de Plataforma."""
        vertices = self._leer_vertices(ruta)
        if len(vertices) < 2:
            raise ValueError(
                f"[LevelParser] '{ruta}' necesita al menos 2 vértices."
            )
        return self._construir(vertices)

    # -----------------------------------------------------------------------
    # Lectura
    # -----------------------------------------------------------------------

    def _leer_vertices(self, ruta: str) -> list:
        ruta_abs = os.path.join(os.path.dirname(os.path.abspath(__file__)), ruta)
        with open(ruta_abs, 'r', encoding='utf-8') as f:
            lineas = f.readlines()

        tokens = []
        for linea in lineas:
            linea = linea.split('#')[0].strip()
            tokens.extend(linea.split())

        numeros = [int(t) for t in tokens if t]
        if len(numeros) % 2 != 0:
            raise ValueError(
                f"[LevelParser] '{ruta}' tiene número impar de valores "
                f"({len(numeros)})."
            )
        return [(numeros[i], numeros[i + 1]) for i in range(0, len(numeros), 2)]

    # -----------------------------------------------------------------------
    # Construcción
    # -----------------------------------------------------------------------

    def _construir(self, vertices: list) -> list:
        """Recorre los tramos y genera las Plataforma con relleno inteligente.

        Calcula primero el y_max global (punto más bajo de todos los vértices)
        y luego usa ese valor para rellenar cada tramo horizontal desde su Y
        hasta y_max, formando un sólido continuo.
        """
        plataformas = []
        ts = self.tileset

        for i in range(len(vertices) - 1):
            x1, y1 = vertices[i]
            x2, y2 = vertices[i + 1]

            if y1 == y2:
                # Tramo HORIZONTAL → superficie pisable + relleno hasta y_max
                self._tramo_suelo(plataformas, ts, x1, x2, y1)

            elif x1 == x2:
                # Tramo VERTICAL → pared lateral
                sube = y2 < y1
                self._tramo_pared(plataformas, ts, x1, y1, y2, sube)

            else:
                print(
                    f"[LevelParser] ⚠ Tramo diagonal ({x1},{y1})→({x2},{y2}) "
                    f"ignorado."
                )

        return plataformas

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _tramo_suelo(self, lista, ts, x1, x2, y):
        """Genera tierra + relleno para un tramo horizontal.

        La capa de tierra tiene GROSOR_SUELO px de alto.
        El relleno llena desde y+GROSOR_SUELO hasta el límite visible de la
        cámara (Constantes.HEIGHT) más una fila extra de tile para evitar
        que se vea el borde inferior en ninguna situación.
        """
        xmin  = min(x1, x2)
        ancho = abs(x2 - x1)
        if ancho <= 0:
            return

        t = _TILES

        # Capa superior pisable
        lista.append(Plataforma(xmin, y, ancho, GROSOR_SUELO, ts, t['tierra']))

        # Relleno hasta el borde inferior de la cámara + 1 tile de margen
        fondo_camara = Constantes.HEIGHT*8 + TILE_SIZE
        alto_relleno = fondo_camara - (y + GROSOR_SUELO)
        if alto_relleno > 0:
            lista.append(Plataforma(
                xmin, y + GROSOR_SUELO,
                ancho, alto_relleno,
                ts, t['relleno']
            ))

    def _tramo_pared(self, lista, ts, x, y1, y2, pared_derecha: bool):
        """Genera la pared vertical en x entre y1 e y2.

        pared_derecha=True  → pared visible por la derecha del escalón
                              (el jugador sube por la izquierda).
        pared_derecha=False → pared visible por la izquierda del escalón
                              (el jugador sube por la derecha).

        La esquina superior se coloca al ras del suelo alto (ymin).
        La esquina inferior se solapa con el tile de tierra del suelo bajo
        (en ymax, no en ymax-16) para que encaje visualmente con el relleno.
        """
        ymin = min(y1, y2)   # y del suelo más alto
        ymax = max(y1, y2)   # y del suelo más bajo
        alto = ymax - ymin
        if alto <= 0:
            return

        t = _TILES

        if pared_derecha:
            # Sube → izquierda del bloque → tiles _iz, sprite en x-16
            tile_pared    = t['pared_iz']
            tile_superior = t['final_iz']
            tile_inferior = t['union_iz']
            x_sprite      = x - GROSOR_PARED
        else:
            # Baja → derecha del bloque → tiles _der, sprite en x
            tile_pared    = t['pared_der']
            tile_superior = t['final_der']
            tile_inferior = t['union_der']
            x_sprite      = x

        # Esquina superior (al ras del suelo alto)
        lista.append(Plataforma(
            x_sprite, ymin,
            GROSOR_PARED, GROSOR_PARED,
            ts, tile_superior
        ))

        # Cuerpo de la pared
        cuerpo_alto = alto - GROSOR_PARED
        if cuerpo_alto > 0:
            lista.append(Plataforma(
                x_sprite, ymin + GROSOR_PARED,
                GROSOR_PARED, cuerpo_alto,
                ts, tile_pared
            ))

        # Esquina inferior (solapada sobre el tile de tierra del suelo bajo)
        lista.append(Plataforma(
            x_sprite, ymax,
            GROSOR_PARED, GROSOR_PARED,
            ts, tile_inferior
        ))
