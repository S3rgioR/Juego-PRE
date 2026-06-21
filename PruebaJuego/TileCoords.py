"""Conversión de coordenadas en tiles a píxeles de mundo.

Sistema de coordenadas en tiles
--------------------------------
Un tile mide TILE_SIZE px en ambos ejes (cuadrado).

    tx  — tiles desde x = 0, hacia la derecha.
    ty  — tiles desde el suelo base hacia ARRIBA.
         ty = 0  →  la entidad se apoya exactamente sobre el suelo.
         ty = 1  →  un tile por encima del suelo.
         ty = -1 →  un tile bajo el suelo (enterrado; raramente útil).

El "suelo base" es Constantes.SUELO_Y, que corresponde al borde
superior de la primera capa de suelo en coordenadas pygame.

Uso en Nivel.py
----------------
    from TileCoords import tp          # "tile position"

    DATOS_NIVEL_1 = {
        'enemigos': [
            {'tipo': 'terrestre', **tp(10, 0), ...},   # apoyado en el suelo
            {'tipo': 'volador',   **tp(18, 4), ...},   # 4 tiles en el aire
        ],
        'boss':      {'tipo': 'boss', **tp(50, 0)},
        'angel':     tp(5, 0),
        'corazones': [tp(15, 1), tp(30, 0)],
        'fin_nivel': {**tp(85, 0), 'ancho': 40, 'alto': 200},
    }

Notas
------
- TILE_SIZE se sincroniza con el ancho del personaje para que las
  distancias de patrulla (distancia_patrulla) sean coherentes con el
  tamaño de las entidades.
- La función tp() devuelve un dict {'x': px, 'y': py} para poder
  expandirlo con ** directamente en las definiciones de nivel.
- tp_abs() devuelve una tupla (px, py) para los casos que esperan tupla
  (p. ej. checkpoint, ángel como tupla, etc.).
"""

import Constantes


# ---------------------------------------------------------------------------
# Tamaño de un tile en píxeles
# ---------------------------------------------------------------------------
# Usar WIDTH_PERSONAJE como unidad da tiles del tamaño del personaje,
# lo que hace que "10 tiles de patrulla" signifique exactamente lo que
# parece al diseñar un nivel.
#
# Si prefieres un tamaño fijo independiente del personaje, cambia este valor
# por un número concreto (p. ej. TILE_SIZE = 32 o 64).

def get_tile_size() -> int:
    """Devuelve el tamaño de tile en píxeles.

    Se llama en tiempo de ejecución para respetar el valor de
    WIDTH_PERSONAJE, que se inyecta desde main.py DESPUÉS de
    cargar la primera imagen. Llamar a esta función antes de ese
    momento devolvería el valor de fallback (30 px).
    """
    return max(1, Constantes.WIDTH_PERSONAJE)


# ---------------------------------------------------------------------------
# Funciones públicas
# ---------------------------------------------------------------------------

def tp(tx: float, ty: float) -> dict:
    """Convierte (tx, ty) en tiles a {'x': px, 'y': py} en píxeles de mundo.

    Parameters
    ----------
    tx : float
        Posición horizontal en tiles desde x = 0.
    ty : float
        Posición vertical en tiles desde el suelo base hacia arriba.
        ty = 0 → centro de la entidad al nivel del suelo.

    Returns
    -------
    dict
        {'x': int, 'y': int} listo para expandir con ** en los dicts
        de definición de nivel.

    Examples
    --------
    >>> tp(10, 0)   # apoyado en el suelo, 10 tiles a la derecha
    {'x': 300, 'y': 656}
    >>> tp(10, 2)   # 2 tiles por encima del suelo
    {'x': 300, 'y': 596}
    """
    tile = 16
    px   = int(tx * tile)
    py   = int(Constantes.SUELO_Y - ty * tile)
    return {'x': px, 'y': py}


def tp_abs(tx: float, ty: float) -> tuple:
    """Igual que tp() pero devuelve una tupla (px, py).

    Útil para los campos que esperan una tupla directamente,
    como el checkpoint: ``'checkpoint': tp_abs(5, 0)``.
    """
    d = tp(tx, ty)
    return (d['x'], d['y'])


def tiles_to_px(tiles: float) -> int:
    """Convierte una distancia en tiles a píxeles.

    Útil para distancia_patrulla, ancho/alto del trigger de fin de nivel, etc.

    Parameters
    ----------
    tiles : float
        Distancia en tiles.

    Returns
    -------
    int
        Distancia equivalente en píxeles.

    Examples
    --------
    >>> tiles_to_px(5)    # 5 tiles de patrulla
    150
    """
    return int(tiles * get_tile_size())
