"""LevelParser — Construye plataformas a partir de un archivo de terreno .txt.

Formato del archivo
-------------------
Una sola línea (o varias) con pares de enteros separados por espacios:

    x1 y1 x2 y2 x3 y3 ...

Cada par (xN, yN) es un vértice del contorno del terreno en coordenadas
absolutas de mundo (Y=0 arriba, igual que pygame). Las coordenadas pueden
ser negativas.

Entre dos vértices consecutivos el parser infiere automáticamente si el
tramo es:
  - HORIZONTAL : mismo Y → franja de suelo (tile_tierra + relleno)
  - VERTICAL   : mismo X → pared lateral (tile_pared + esquinas)

El contorno debe estar cerrado o terminar en el borde del mapa; el parser
no exige que se cierre manualmente.

Tiles del tileset usados (mismo layout que Nivel.py original)
--------------------------------------------------------------
  (0,   0,  16, 16)  tile_tierra    — superficie pisable (fila superior)
  (0,   16, 16, 16)  tile_relleno   — relleno interior oscuro
  (48,  0,  16, 16)  tile_final_der — esquina superior derecha
  (128, 0,  16, 16)  tile_final_iz  — esquina superior izquierda
  (48,  16, 16, 16)  tile_pared_der — pared lateral derecha
  (128, 16, 16, 16)  tile_pared_iz  — pared lateral izquierda
  (48,  48, 16, 16)  tile_union_der — esquina inferior derecha (unión suelo)
  (128, 48, 16, 16)  tile_union_iz  — esquina inferior izquierda (unión suelo)

Uso
---
    from LevelParser import LevelParser
    parser = LevelParser(tileset)
    plataformas = parser.cargar("levels/nivel1.txt")
"""

import pygame
from view.Plataforma import Plataforma


# ---------------------------------------------------------------------------
# Definición de tiles (coordenadas dentro del tileset, igual que Nivel.py)
# ---------------------------------------------------------------------------
TILE_SIZE = 16   # tamaño de cada tile en el tileset

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

# Grosor visual/físico de suelo y paredes (en píxeles)
GROSOR_SUELO  = TILE_SIZE       # 16 px — capa superior pisable
GROSOR_PARED  = TILE_SIZE       # 16 px — paredes laterales
RELLENO_EXTRA = 160             # px de relleno bajo el suelo (invisible)


class LevelParser:
    """Lee un archivo .txt de vértices y construye la lista de Plataforma.

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
        """Carga el archivo de terreno y devuelve la lista de Plataforma.

        Parameters
        ----------
        ruta : str
            Ruta al archivo .txt del nivel.

        Returns
        -------
        list of Plataforma
        """
        vertices = self._leer_vertices(ruta)
        if len(vertices) < 2:
            raise ValueError(f"[LevelParser] El archivo '{ruta}' necesita al menos 2 vértices.")
        return self._construir(vertices)

    # -----------------------------------------------------------------------
    # Lectura del archivo
    # -----------------------------------------------------------------------

    def _leer_vertices(self, ruta: str) -> list:
        """Devuelve la lista de (x, y) leída del archivo."""
        import os
        ruta_abs = os.path.join(os.path.dirname(os.path.abspath(__file__)), ruta)

        with open(ruta_abs, 'r', encoding='utf-8') as f:
            lineas = f.readlines()

        # Ignorar comentarios (#) y líneas vacías
        tokens = []
        for linea in lineas:
            linea = linea.split('#')[0].strip()
            tokens.extend(linea.split())

        numeros = [int(t) for t in tokens if t]
        if len(numeros) % 2 != 0:
            raise ValueError(
                f"[LevelParser] El archivo '{ruta}' tiene un número impar de valores "
                f"({len(numeros)}). Cada vértice necesita un par x y."
            )
        return [(numeros[i], numeros[i + 1]) for i in range(0, len(numeros), 2)]

    # -----------------------------------------------------------------------
    # Construcción de plataformas
    # -----------------------------------------------------------------------

    def _construir(self, vertices: list) -> list:
        """Recorre los tramos entre vértices y genera las Plataforma."""
        plataformas = []
        ts = self.tileset

        for i in range(len(vertices) - 1):
            x1, y1 = vertices[i]
            x2, y2 = vertices[i + 1]

            if y1 == y2:
                # ── Tramo HORIZONTAL → franja de suelo ──────────────────
                self._tramo_suelo(plataformas, ts, x1, x2, y1)

            elif x1 == x2:
                # ── Tramo VERTICAL → pared ──────────────────────────────
                # Si la pared SUBE (y2 < y1) es el lado izquierdo del bloque.
                # Si la pared BAJA (y2 > y1) es el lado derecho del bloque.
                sube = y2 < y1
                self._tramo_pared(plataformas, ts, x1, y1, y2, sube)

            else:
                print(
                    f"[LevelParser] ⚠ Tramo diagonal ({x1},{y1})→({x2},{y2}) "
                    f"no soportado. Se ignora."
                )

        return plataformas

    # -----------------------------------------------------------------------
    # Helpers de construcción
    # -----------------------------------------------------------------------

    def _tramo_suelo(self, lista, ts, x1, x2, y):
        """Genera la capa de tierra + relleno para un tramo horizontal.

        El suelo va de x1 a x2 (se acepta x1 > x2, se ordena internamente).
        """
        xmin = min(x1, x2)
        ancho = abs(x2 - x1)
        if ancho <= 0:
            return

        t = _TILES
        # Capa superior pisable
        lista.append(Plataforma(xmin, y, ancho, GROSOR_SUELO, ts, t['tierra']))
        # Relleno bajo el suelo
        lista.append(Plataforma(
            xmin, y + GROSOR_SUELO,
            ancho, RELLENO_EXTRA,
            ts, t['relleno']
        ))

    def _tramo_pared(self, lista, ts, x, y1, y2, pared_derecha: bool):
        """Genera la pared vertical en x entre y1 e y2.

        Coordenadas:
          ymin = y del suelo ALTO (valor Y menor, más arriba en pantalla)
          ymax = y del suelo BAJO (valor Y mayor, más abajo en pantalla)

        La esquina superior se coloca en ymin (al ras del suelo alto).
        La esquina inferior se solapa con el tile de tierra del suelo bajo,
        es decir en ymax (mismo Y que el tile de tierra), no en ymax-16.

        pared_derecha:
          True  → la cara visible es la derecha del escalón
                  (el suelo bajo queda a la IZQUIERDA del vértice)
                  → tile_pared_iz / final_iz / union_iz
          False → la cara visible es la izquierda del escalón
                  (el suelo bajo queda a la DERECHA del vértice)
                  → tile_pared_der / final_der / union_der
        """
        ymin = min(y1, y2)   # y del suelo alto
        ymax = max(y1, y2)   # y del suelo bajo
        alto = ymax - ymin
        if alto <= 0:
            return

        t = _TILES

        # sube=True  → lado izquierdo del bloque → tile_iz, sprite a x-16
        # sube=False → lado derecho del bloque  → tile_der, sprite en x
        if pared_derecha:   # sube → izquierda del bloque
            tile_pared    = t['pared_iz']
            tile_superior = t['final_iz']
            tile_inferior = t['union_iz']
            x_sprite      = x - GROSOR_PARED
        else:               # baja → derecha del bloque
            tile_pared    = t['pared_der']
            tile_superior = t['final_der']
            tile_inferior = t['union_der']
            x_sprite      = x

        # Esquina superior: al ras del suelo alto
        lista.append(Plataforma(
            x_sprite, ymin,
            GROSOR_PARED, GROSOR_PARED,
            ts, tile_superior
        ))
        # Cuerpo de la pared (entre esquina superior y esquina inferior)
        cuerpo_alto = alto - GROSOR_PARED
        if cuerpo_alto > 0:
            lista.append(Plataforma(
                x_sprite, ymin + GROSOR_PARED,
                GROSOR_PARED, cuerpo_alto,
                ts, tile_pared
            ))
        # Esquina inferior: solapada sobre el tile de tierra del suelo bajo
        lista.append(Plataforma(
            x_sprite, ymax,
            GROSOR_PARED, GROSOR_PARED,
            ts, tile_inferior
        ))
