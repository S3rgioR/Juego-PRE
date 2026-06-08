"""Definiciones de niveles del juego.

Cada nivel expone:
  - cargar_nivel_N(tileset)  → list[Plataforma]   (terreno leído del .txt)
  - DATOS_NIVEL_N            → dict con entidades, checkpoint, música, etc.

El terreno se construye leyendo un archivo .txt mediante LevelParser.
Las entidades (enemigos, boss, objetos) se definen aquí en Python porque
necesitan referencias a assets (frames de animación) que se cargan en main.py
y se pasan como parámetros al construir la Vista.

Añadir un nivel nuevo:
  1. Crear  levels/nivel2.txt  con los vértices del terreno.
  2. Definir DATOS_NIVEL_2 con sus entidades.
  3. Definir cargar_nivel_2(tileset) que llame a LevelParser.
  4. Registrar el nivel en NIVELES (al final de este archivo).
"""

import pygame
from LevelParser import LevelParser


# ===========================================================================
# NIVEL 1
# ===========================================================================

CHECKPOINT_NIVEL_1 = (500, 620)   # coordenadas de mundo del checkpoint

# Entidades del nivel 1.
# Los frames de animación (listas de pygame.Surface) se inyectan en main.py
# después de cargar los assets; aquí solo se definen posición y parámetros.
DATOS_NIVEL_1 = {
    'checkpoint': CHECKPOINT_NIVEL_1,
    'musica':     'Assets/Audio/Music/Ambient_Lingering_Action.wav',

    'enemigos': [
        {
            'tipo':                 'terrestre',
            'x':                    600,
            'y':                    400,
            'distancia_patrulla':   2000,
            'num_frames_ataque':    6,
            # 'anim_walk' y 'anim_attack' se inyectan desde main.py
        },
        {
            'tipo':                 'terrestre',
            'x':                    1500,
            'y':                    400,
            'distancia_patrulla':   10000,
            'num_frames_ataque':    6,
        },
        {
            'tipo':                 'volador',
            'x':                    1000,
            'y':                    400,
            'distancia_patrulla':   300,
        },
    ],

    'boss': {
        'tipo': 'boss',
        'x':    3050,
        'y':    400,
        # 'anim_fase1' y 'anim_fase2' se inyectan desde main.py
    },

    'angel': {'x': 0, 'y': 540},

    'corazones': [
        {'x': 900,  'y': 560},
        {'x': 1800, 'y': 528},
        {'x': 2600, 'y': 640},
    ],

    'daga_pickup': {'x': 1200, 'y': 620},

    'fin_nivel': {'x': 3400, 'y': 500, 'ancho': 40, 'alto': 200},
}


def cargar_nivel_1(tileset: pygame.Surface) -> list:
    """Construye y devuelve las plataformas del nivel 1 desde su .txt.

    Parameters
    ----------
    tileset : pygame.Surface
        Hoja de tiles cargada en memoria.

    Returns
    -------
    list of Plataforma
    """
    return LevelParser(tileset).cargar('levels/nivel1.txt')


# ===========================================================================
# NIVEL 2  (plantilla — personaliza el .txt y las entidades)
# ===========================================================================

DATOS_NIVEL_2 = {
    'checkpoint': (400, 600),
    'musica':     'Assets/Audio/Music/Ambient_Lingering_Action.wav',

    'enemigos': [
        {
            'tipo':               'terrestre',
            'x':                  500,
            'y':                  400,
            'distancia_patrulla': 300,
            'num_frames_ataque':  6,
        },
        {
            'tipo':               'volador',
            'x':                  900,
            'y':                  350,
            'distancia_patrulla': 400,
        },
    ],

    'boss': None,   # sin boss en el nivel 2

    'angel':       {'x': 0, 'y': 540},
    'corazones':   [{'x': 700, 'y': 560}],
    'daga_pickup': None,   # sin daga en el nivel 2
    'fin_nivel': {'x': 19800, 'y': 500, 'ancho': 40, 'alto': 200},
}


def cargar_nivel_2(tileset: pygame.Surface) -> list:
    """Construye y devuelve las plataformas del nivel 2 desde su .txt."""
    return LevelParser(tileset).cargar('levels/nivel2.txt')


# ===========================================================================
# Registro de niveles
# ===========================================================================
# Añade aquí cada nivel nuevo: (función_loader, dict_datos)
NIVELES = {
    1: (cargar_nivel_1, DATOS_NIVEL_1),
    2: (cargar_nivel_2, DATOS_NIVEL_2),
}
