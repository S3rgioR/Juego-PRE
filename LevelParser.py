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
  pared_iz     cuerpo pared izquierda (dy > 0)
  pared_der    cuerpo pared derecha   (dy < 0)

  Esquinas — PROPIETARIO UNICO (solo _tramo_pared las dibuja, nunca _tramo_techo):
  ---------------------------------------------------------------------------------
  ESQUINAS SUPERIORES (en ymin de la pared):
    final_iz     : x+ → pared_iz   (arriba tierra, debajo pared_iz)
    final_der    : x+ → pared_der  (arriba tierra, debajo pared_der)
    techo_iz_ar  : -x → pared_iz   (arriba techo,  debajo pared_iz)
    techo_der_ar : -x → pared_der  (arriba techo,  debajo pared_der)

  ESQUINAS INFERIORES (en ymax de la pared, solapan el primer tile del seg. siguiente):
    union_iz     : pared_iz  → x+  (arriba pared_iz,  derecha tierra)
    union_der    : pared_der → x+  (arriba pared_der, derecha tierra)
    techo_iz     : pared_iz  → -x  (arriba pared_iz,  derecha techo)   [pared_iz termina en techo]
    techo_der    : pared_der → -x  (arriba pared_der, izquierda techo) [pared_der termina en techo]

  _tramo_techo dibuja SOLO el cuerpo 'techo' puro, entre las columnas de las esquinas.
  Las columnas de esquina de techo quedan reservadas para _tramo_pared.

Geometria de las paredes
------------------------
  La pared ocupa exactamente el rango Y = [ymin, ymax].

    tile_sup  (1 tile) : y = ymin              — esquina superior
    cuerpo             : y = [ymin+TS, ymax]   — cuerpo de la pared
    tile_inf  (1 tile) : y = ymax              — esquina inferior
                                                 (solapada con el seg. siguiente,
                                                  que empieza en ymax)

  Para modificar que tile aparece en cada esquina edita el bloque
  if/elif en _tramo_pared bajo los comentarios:
    "# === ESQUINAS SUPERIORES ==="
    "# === ESQUINAS INFERIORES ==="

Estrategia de relleno
---------------------
  Los segmentos forman un poligono cerrado. El relleno solido se calcula
  columna a columna usando scanline sobre ese poligono: para cada columna X
  de tiles se determinan los rangos Y que estan FUERA del poligono jugable
  y se rellenan con tiles de relleno.

  Ademas, los bordes visibles (tierra, techo, paredes) se superponen encima.
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

    # -----------------------------------------------------------------------
    # Trazas de depuracion
    # Pon DEBUG_LEVEL_PARSER = True para ver los segmentos en consola.
    # Pon DEBUG_ONLY_PARED   = True para ver solo las paredes.
    # -----------------------------------------------------------------------
    DEBUG_LEVEL_PARSER = True
    DEBUG_ONLY_PARED   = False   # True = solo imprime segmentos de tipo 'pared'

    def _trazar_segmento(self, i, seg, prev_seg, next_seg):
        """Imprime los valores de un segmento y sus vecinos por consola."""
        if not self.DEBUG_LEVEL_PARSER:
            return
        if self.DEBUG_ONLY_PARED and seg['tipo'] != 'pared':
            return


        if seg['tipo'] == 'pared':
            sube = seg['dy'] > 0
            print(f"  direccion: {'SUBE (pared_iz)' if sube else 'BAJA (pared_der)'}")
            print(f"  y_inicio (tile_sup) = {seg['y1']}  →  y_fin (tile_inf) = {seg['y2']}")

    def _construir(self, segmentos: list) -> list:
        plataformas = []
        ts = self.tileset
        n  = len(segmentos)

        if self.DEBUG_LEVEL_PARSER:
            print(f"\n[LevelParser] ════ INICIO CONSTRUCCION ({n} segmentos) ════")

        # 1. Extraer vertices del poligono para el scanline de relleno
        vertices = self._extraer_vertices(segmentos)

        # 2. Relleno solido por scanline (se dibuja PRIMERO, queda debajo)
        self._rellenar_scanline(plataformas, ts, vertices, segmentos)

        # 3. Tiles de borde visibles encima del relleno
        for i, seg in enumerate(segmentos):
            prev_seg = segmentos[(i - 1) % n]
            next_seg = segmentos[(i + 1) % n]

            self._trazar_segmento(i, seg, prev_seg, next_seg)

            if seg['tipo'] == 'suelo':
                self._tramo_suelo(plataformas, ts, seg, prev_seg, next_seg)
            elif seg['tipo'] == 'techo':
                self._tramo_techo(plataformas, ts, seg, prev_seg, next_seg)
            elif seg['tipo'] == 'pared':
                self._tramo_pared(plataformas, ts, seg, prev_seg, next_seg)

        if self.DEBUG_LEVEL_PARSER:
            print(f"\n[LevelParser] ════ FIN: {len(plataformas)} plataformas generadas ════\n")

        return plataformas

    # -----------------------------------------------------------------------
    # Vertices del poligono
    # -----------------------------------------------------------------------

    def _extraer_vertices(self, segmentos):
        verts = []
        for seg in segmentos:
            verts.append((seg['x1'], seg['y1']))
        return verts

    # -----------------------------------------------------------------------
    # Scanline fill
    # -----------------------------------------------------------------------

    def _rellenar_scanline(self, lista, ts, vertices, segmentos):
        if not vertices:
            return

        t = _TILES

        xs = [v[0] for v in vertices]
        ys = [v[1] for v in vertices]
        poly_xmin = min(xs)
        poly_xmax = max(xs)
        y_min = min(ys) - Constantes.HEIGHT * 2
        y_max = max(ys) + Constantes.HEIGHT * 2

        aristas = self._construir_aristas(segmentos)

        area_xmin = poly_xmin - Constantes.WIDTH  * 2
        area_xmax = poly_xmax + Constantes.WIDTH  * 2

        col = area_xmin
        while col < area_xmax:
            col_centro = col + TILE_SIZE // 2

            if col_centro <= poly_xmin or col_centro >= poly_xmax:
                alto = y_max - y_min
                if alto >= TILE_SIZE:
                    lista.append(Plataforma(col, y_min, TILE_SIZE, alto, ts, t['relleno']))
            else:
                cortes = self._intersecciones_verticales(aristas, col_centro)
                cortes.sort()
                cortes = self._dedup_cortes(cortes)
                rangos_solidos = self._rangos_exterior(cortes, y_min, y_max)
                for (ry_start, ry_end) in rangos_solidos:
                    alto = ry_end - ry_start
                    if alto >= TILE_SIZE:
                        lista.append(Plataforma(col, ry_start, TILE_SIZE, alto, ts, t['relleno']))

            col += TILE_SIZE

    def _construir_aristas(self, segmentos):
        aristas = []
        for seg in segmentos:
            aristas.append(((seg['x1'], seg['y1']), (seg['x2'], seg['y2'])))
        return aristas

    def _intersecciones_verticales(self, aristas, x):
        cortes = []
        for (x1, y1), (x2, y2) in aristas:
            if x1 == x2:
                continue
            if not (min(x1, x2) <= x < max(x1, x2)):
                continue
            t = (x - x1) / (x2 - x1)
            y = y1 + t * (y2 - y1)
            cortes.append(y)
        return cortes

    def _dedup_cortes(self, cortes, tolerancia=2):
        if not cortes:
            return cortes
        resultado = [cortes[0]]
        for c in cortes[1:]:
            if abs(c - resultado[-1]) > tolerancia:
                resultado.append(c)
        return resultado

    def _rangos_exterior(self, cortes, y_min, y_max):
        rangos = []

        if not cortes:
            alto = y_max - y_min
            if alto > 0:
                rangos.append((y_min, y_max))
            return rangos

        if cortes[0] - y_min >= TILE_SIZE:
            rangos.append((y_min, int(cortes[0])))

        i = 1
        while i + 1 < len(cortes):
            y_start = int(cortes[i])
            y_end   = int(cortes[i + 1])
            if y_end - y_start >= TILE_SIZE:
                rangos.append((y_start, y_end))
            i += 2

        if y_max - cortes[-1] >= TILE_SIZE:
            rangos.append((int(cortes[-1]), y_max))

        return rangos

    # -----------------------------------------------------------------------
    # Tramo suelo (+x)
    # -----------------------------------------------------------------------

    def _tramo_suelo(self, lista, ts, seg, prev_seg,next_seg):
        x1, x2 = seg['x1'], seg['x2']
        y       = seg['y1']
        xmin    = min(x1, x2)
        xmax    = max(x1, x2)
        if prev_seg['dy']<0:
            xmin=xmin+TILE_SIZE

        ancho   = xmax - xmin
        if ancho <= 0:
            return
        lista.append(Plataforma(xmin, y, ancho, GROSOR_SUELO, ts, _TILES['tierra']))

    # -----------------------------------------------------------------------
    # Tramo techo (-x)
    # Solo dibuja el cuerpo de techo puro.
    # Las esquinas (techo_iz_ar, techo_der_ar, techo_iz, techo_der) son
    # propiedad de _tramo_pared y se dibujan en los extremos de la pared.
    # -----------------------------------------------------------------------

    def _tramo_techo(self, lista, ts, seg, prev_seg, next_seg):
        """Dibuja solo los tiles 'techo' puros del tramo.

        Las columnas de esquina en los extremos del techo las dibuja
        _tramo_pared (tile_sup / tile_inf), por lo que aqui se dejan libres:
          - extremo derecho (x1): si el seg anterior es pared, esa columna
            ya tiene su esquina → no dibujar techo ahi.
          - extremo izquierdo (x2): igual con el seg siguiente.
        """
        t = _TILES
        x1, x2 = seg['x1'], seg['x2']
        y       = seg['y1']
        xmin    = min(x1, x2)
        xmax    = max(x1, x2)
        if xmax - xmin <= 0:
            return

        # Retranquear los extremos que lindan con una pared
        # (la esquina ya la pone _tramo_pared)

        x_ini = xmin if next_seg['dy'] != 0 else xmin

        x_fin = xmax-TILE_SIZE if prev_seg['dy'] > 0 else xmax

        ancho = x_fin - x_ini
        if ancho > 0:
            lista.append(Plataforma(x_ini, y, ancho, GROSOR_TECHO, ts, t['techo']))

    # -----------------------------------------------------------------------
    # Tramo pared (+-y)
    # Unico responsable de dibujar TODAS las esquinas.
    # Para cambiar que tile aparece en cada esquina edita los bloques
    # marcados con "# === ESQUINAS SUPERIORES ===" y "# === ESQUINAS INFERIORES ==="
    # -----------------------------------------------------------------------

    def _tramo_pared(self, lista, ts, seg, prev_seg, next_seg):
        t  = _TILES
        x  = seg['x1']
        y1 = seg['y1']
        y2 = seg['y2']
        dy = seg['dy']

        ymin = min(y1, y2)
        ymax = max(y1, y2)
        alto = ymax - ymin
        if alto <= 0:
            return

        sube = dy > 0   # True = pared_iz, False = pared_der

        if sube:
            tile_pared = t['pared_iz']
            x_sprite   = x - GROSOR_PARED

            # === ESQUINAS SUPERIORES (y1) — pared_iz ===
            # y1 es donde la pared empieza (conecta con el seg. anterior)
            if prev_seg['dx'] > 0:
                tile_sup = t['union_iz']       # x+ → pared_iz
            elif prev_seg['dx'] < 0:
                tile_sup = t['techo_iz']    # -x → pared_iz
            else:
                tile_sup = t['pared_iz']       # pared → pared (sin esquina)

            # === ESQUINAS INFERIORES (y2) — pared_iz ===
            # y2 es donde la pared termina (conecta con el seg. siguiente)
            if next_seg['dx'] > 0:
                tile_inf = t['final_iz']       # pared_iz → x+
            elif next_seg['dx'] < 0:
                tile_inf = t['techo_iz_ar']       # pared_iz → -x
            else:
                tile_inf = None                # pared_iz → pared (sin esquina)

        else:
            tile_pared = t['pared_der']
            x_sprite   = x

            # === ESQUINAS SUPERIORES (ymin) — pared_der ===
            # Modificar aqui para cambiar que aparece en la esquina superior
            # de una pared derecha segun el segmento anterior.
            if prev_seg['dx'] > 0:
                tile_sup = t['final_der']      # x+ → pared_der
            elif prev_seg['dx'] < 0:
                tile_sup = t['techo_der_ar']   # -x → pared_der
            else:
                tile_sup = t['pared_der']      # pared → pared (sin esquina)

            # === ESQUINAS INFERIORES (ymax) — pared_der ===
            # Modificar aqui para cambiar que aparece en la esquina inferior
            # de una pared derecha segun el segmento siguiente.
            if next_seg['dx'] > 0:
                tile_inf = t['union_der']      # pared_der → x+
            elif next_seg['dx'] < 0:
                tile_inf = t['techo_der']      # pared_der → -x
            else:
                tile_inf = None                # pared_der → pared (sin esquina)

        # --- Colocar tiles ---
        # tile_sup: en y1 (inicio del segmento, donde conecta con el seg. anterior)
        # cuerpo:   entre y1 y y2, excluyendo las esquinas
        # tile_inf: en y2 (fin del segmento, solapado con el inicio del seg. siguiente)
        #
        # IMPORTANTE: se usa y1/y2 directamente, NO ymin/ymax, para respetar
        # la direccion del segmento. y1 es siempre el inicio (donde viene el
        # segmento anterior) y y2 el fin (donde empieza el siguiente).

        # Direccion del cuerpo: de y1 hacia y2
        paso     = TILE_SIZE if y2 > y1 else -TILE_SIZE
        y_cuerpo = y1 + paso   # primer tile del cuerpo tras tile_sup
        y_inf    = y2          # posicion de tile_inf

        if tile_inf is None:
            lista.append(Plataforma(x_sprite, y1, GROSOR_PARED, TILE_SIZE, ts, tile_sup))
            cuerpo_alto = alto - TILE_SIZE
            if cuerpo_alto > 0:
                y_c = min(y1, y2) + TILE_SIZE
                lista.append(Plataforma(x_sprite, y_c, GROSOR_PARED, cuerpo_alto, ts, tile_pared))
            return

        # Con esquina inferior
        lista.append(Plataforma(x_sprite, y1, GROSOR_PARED, TILE_SIZE, ts, tile_sup))
        cuerpo_alto = alto - TILE_SIZE
        if cuerpo_alto > 0:
            y_c = min(y1, y2) + TILE_SIZE
            lista.append(Plataforma(x_sprite, y_c, GROSOR_PARED, cuerpo_alto, ts, tile_pared))
        # tile_inf en y2: solapado con el segmento siguiente
        lista.append(Plataforma(x_sprite, y2, GROSOR_PARED, TILE_SIZE, ts, tile_inf))
