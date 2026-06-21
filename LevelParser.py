"""LevelParser — Construye plataformas a partir de un archivo de terreno .txt.

Formato del archivo
-------------------
El archivo se divide en secciones, cada una entre corchetes `[ ]`:

    [ ancho1  escalon1  ancho2  escalon2 ... ]   ← primera secc.: poligono
    [ columna  fila ]                            ← plataforma flotante 1
    [ columna  fila ]                            ← plataforma flotante 2
    ...

El PRIMER bloque `[ ]` es siempre el polígono del terreno, con la
secuencia de enteros que alterna ANCHO y ESCALON:

  - ancho   (posicion impar) : bloques horizontales.
                               +x suelo (tierra hacia la derecha)
                               -x techo (techo hacia la izquierda)
  - escalon (posicion par)   : bloques verticales.
                               +y pared sube
                               -y pared baja

El mapa DEBE ser cerrado: el ultimo vertice debe coincidir con el primero.

Cada bloque `[ ]` SIGUIENTE define una plataforma flotante: dos enteros,
"columna fila" en coordenadas de tiles. La columna es la del tile MAS A
LA DERECHA de la plataforma; esta se extiende 4 tiles hacia la izquierda
(plataformas de 1 tile de alto x 4 de ancho). Son atravesables desde
abajo: solo actuan como suelo si se cae sobre ellas desde arriba. Son
opcionales: un nivel sin plataformas flotantes solo tiene el primer
bloque `[ ]`.

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
import re
import pygame
import Constantes
from view.Plataforma import Plataforma, PlataformaFlotante


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

# Tiles de la plataforma flotante: 4 tiles distintos, uno junto al otro
# (no se repiten), formando una imagen de 4 tiles de ancho x 1 de alto.
_TILES_PLATAFORMA_FLOTANTE = [
    pygame.Rect(144, 0, TILE_SIZE, TILE_SIZE),
    pygame.Rect(160, 0, TILE_SIZE, TILE_SIZE),
    pygame.Rect(176, 0, TILE_SIZE, TILE_SIZE),
    pygame.Rect(192, 0, TILE_SIZE, TILE_SIZE),
]

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
        secciones = self._leer_secciones(ruta)
        if not secciones:
            raise ValueError(f"[LevelParser] '{ruta}' no contiene ninguna sección [ ].")

        numeros_poligono = secciones[0]
        segmentos = self._numeros_a_segmentos(numeros_poligono)
        self._verificar_cierre(segmentos, ruta)
        plataformas = self._construir(segmentos)

        for bloque in secciones[1:]:
            plataformas.append(self._construir_plataforma_flotante(bloque, ruta))

        return plataformas

    # -----------------------------------------------------------------------
    # Lectura
    # -----------------------------------------------------------------------

    def _leer_secciones(self, ruta: str) -> list:
        """Lee el archivo y devuelve una lista de secciones (listas de int).

        Cada sección es el contenido de un bloque `[ ... ]`. Los comentarios
        con '#' se descartan línea a línea antes de buscar los corchetes, así
        que pueden usarse libremente dentro o fuera de un bloque.
        """
        ruta_abs = os.path.join(os.path.dirname(os.path.abspath(__file__)), ruta)
        with open(ruta_abs, 'r', encoding='utf-8') as f:
            lineas = f.readlines()

        sin_comentarios = ' '.join(linea.split('#')[0] for linea in lineas)

        # Eliminar secciones con prefijo conocido (P.Boss:, Spikes:, etc.)
        # para que no se confundan con plataformas flotantes
        sin_comentarios = re.sub(r'P\.Boss\s*:\s*\[[^\]]*\]', '', sin_comentarios)
        sin_comentarios = re.sub(r'Spikes\s*:\s*\[[^\]]*\]', '', sin_comentarios)

        secciones = []
        for bloque in re.findall(r'\[([^\]]*)\]', sin_comentarios):
            numeros = [int(t) for t in bloque.split() if t]
            secciones.append(numeros)
        return secciones

    def _construir_plataforma_flotante(self, bloque: list, ruta: str) -> PlataformaFlotante:
        """Construye una PlataformaFlotante a partir de un bloque [columna fila].

        `columna` es el tile MAS A LA DERECHA de la plataforma; esta se
        extiende 4 tiles hacia la izquierda.
        """
        if len(bloque) != 2:
            raise ValueError(
                f"[LevelParser] '{ruta}': plataforma flotante mal formada {bloque}. "
                f"Se esperan exactamente 2 numeros: [columna fila]."
            )
        columna, fila = bloque
        ancho_tiles = len(_TILES_PLATAFORMA_FLOTANTE)
        x = (columna - (ancho_tiles - 1)) * TILE_SIZE
        y = Constantes.SUELO_Y - fila * TILE_SIZE
        return PlataformaFlotante(x, y, self.tileset, _TILES_PLATAFORMA_FLOTANTE)

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

    # ----------------------------------------------------------------------

    def _trazar_segmento(self, i, seg, prev_seg, next_seg):
        """Imprime los valores de un segmento y sus vecinos por consola."""



        if seg['tipo'] == 'pared':
            sube = seg['dy'] > 0


    def _construir(self, segmentos: list) -> list:
        plataformas = []
        ts = self.tileset
        n  = len(segmentos)




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

    def cargar_pared_boss(self, ruta: str):
        import os, re
        import Constantes
        ruta_abs = os.path.join(os.path.dirname(os.path.abspath(__file__)), ruta)
        with open(ruta_abs, 'r', encoding='utf-8') as f:
            contenido = f.read()

        m = re.search(r'P\.Boss\s*:\s*\[([^\]]*)\]', contenido)
        if not m:
            return None

        nums = [int(t) for t in m.group(1).split() if t]
        if len(nums) != 2:
            raise ValueError(
                f"[LevelParser] P.Boss en '{ruta}' necesita exactamente 2 números: "
                f"[tx  ty], se encontraron {len(nums)}: {nums}"
            )
        tx, ty = nums
        tile = max(1, Constantes.WIDTH_PERSONAJE)
        ancho = tile  # 1 tile de ancho
        alto = tile * 5  # 6 tiles de alto
        x = tx * tile
        y = Constantes.SUELO_Y - ty * tile - alto  # borde superior de la pared
        return {'x': x, 'y': y, 'ancho': ancho, 'alto': alto}

    def cargar_spikes(self, ruta: str) -> list:
        """Parsea TODOS los bloques `Spikes: [x y ancho]` de un archivo de nivel.

        Formato
        -------
        Spikes: [ x  y  ancho ]

          x     : columna de tile del extremo IZQUIERDO del conjunto de
                  pinchos (igual convención que P.Boss: tiles desde el
                  origen del nivel).
          y     : fila de tile sobre el suelo (0 = pegado al suelo) en la
                  que se apoya la base de los pinchos.
          ancho : número de tiles que ocupa el conjunto hacia la derecha
                  desde `x`. La altura es siempre 1 tile (16 px), el
                  tamaño de Assets/Enviorments/Spikes.png.

        Puede haber varios bloques `Spikes:` en el mismo archivo (varios
        grupos de pinchos); se devuelven todos.

        Cada elemento devuelto es un dict:
            {
                'x': int, 'y': int, 'ancho': int, 'alto': int,   # px
                'barrera_izq': {'x','y','ancho','alto'},          # px
                'barrera_der': {'x','y','ancho','alto'},          # px
            }

        Las "barreras" son zonas sensoras invisibles, adyacentes a cada
        lado del conjunto de pinchos, de 20 tiles de alto. La Vista las
        usa para recordar la última posición del jugador antes de caer
        sobre los pinchos (ver view/SpikesView.py).
        """
        ruta_abs = os.path.join(os.path.dirname(os.path.abspath(__file__)), ruta)
        with open(ruta_abs, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        contenido = ' '.join(linea.split('#')[0] for linea in lineas)

        grupos = []
        ALTO_BARRERA_TILES = 20

        for bloque in re.findall(r'Spikes\s*:\s*\[([^\]]*)\]', contenido):
            nums = [int(t) for t in bloque.split() if t]
            if len(nums) != 3:
                raise ValueError(
                    f"[LevelParser] Spikes en '{ruta}' necesita exactamente 3 "
                    f"números: [x y ancho], se encontraron {len(nums)}: {nums}"
                )
            tx, ty, ancho_tiles = nums

            x     = tx * TILE_SIZE
            ancho = ancho_tiles * TILE_SIZE
            alto  = TILE_SIZE
            y     = Constantes.SUELO_Y - ty * TILE_SIZE - alto

            alto_barrera = ALTO_BARRERA_TILES * TILE_SIZE
            y_barrera    = y - alto_barrera + alto

            # Las barreras NO son adyacentes inmediatas a los pinchos:
            # quedan un tile más hacia cada extremo (con un hueco de 1
            # tile entre el borde de los pinchos y la barrera), para que
            # el jugador las pise claramente antes de poder llegar a los
            # pinchos desde cualquiera de los dos lados.
            barrera_izq = {
                'x': x - 2 * TILE_SIZE, 'y': y_barrera,
                'ancho': TILE_SIZE, 'alto': alto_barrera,
            }
            barrera_der = {
                'x': x + ancho + TILE_SIZE, 'y': y_barrera,
                'ancho': TILE_SIZE, 'alto': alto_barrera,
            }

            grupos.append({
                'x': x, 'y': y, 'ancho': ancho, 'alto': alto,
                'barrera_izq': barrera_izq,
                'barrera_der': barrera_der,
            })

        return grupos

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
