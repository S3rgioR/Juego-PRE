"""Definiciones de niveles del juego."""

import pygame
from LevelParser  import LevelParser
from TileCoords   import tp, tp_abs, tiles_to_px


# ===========================================================================
# NIVEL 1
# ===========================================================================

CHECKPOINT_NIVEL_1 = tp_abs(10, 0)

DATOS_NIVEL_1 = {
    'spawn':      tp_abs(1, 0),          # ← posición de aparición del jugador
    'checkpoint': CHECKPOINT_NIVEL_1,
    'musica':     'Assets/Audio/Music/Ambient_Lingering_Action.wav',

    'enemigos': [
        {
            'tipo':               'terrestre',
            **tp(20, 0),
            'distancia_patrulla': tiles_to_px(33),
            'num_frames_ataque':  6,
        },
        {
            'tipo':               'terrestre',
            **tp(50, 0),
            'distancia_patrulla': tiles_to_px(166),
            'num_frames_ataque':  6,
        },
        {
            'tipo':               'volador',
            **tp(33, 5),
            'distancia_patrulla': tiles_to_px(5),
        },
    ],

    'boss': None,

    'angel':      tp(3, 2),
    'corazones': [tp(30, 1), tp(60, 16)],
    'daga_pickup': None,

    'fin_nivel': {
        **tp(75, 16),
        'ancho': 40,
        'alto':  200,
    },
}


def cargar_nivel_1(tileset: pygame.Surface) -> list:
    return LevelParser(tileset).cargar('levels/nivel1.txt')


# ===========================================================================
# NIVEL 2
# ===========================================================================

DATOS_NIVEL_2 = {
    'spawn':      tp_abs(1, 0),          # ← posición de aparición del jugador
    'checkpoint': tp_abs(3, 1),
    'musica':     'Assets/Audio/Music/Ambient_Lingering_Action.wav',

    'enemigos': [
        {
            'tipo':               'terrestre',
            **tp(9, 33),
            'distancia_patrulla': tiles_to_px(5),
            'num_frames_ataque':  6,
        },
        {
            'tipo':               'volador',
            **tp(63, 54),
            'distancia_patrulla': tiles_to_px(6),
        },
    ],

    'boss': {
        'tipo': 'boss',
        **tp(101, 18),
    },

    'angel':       tp(4, 33),
    'corazones':   [tp(15, 51)],
    'daga_pickup': tp(6, 51),

    'fin_nivel': {
        **tp(660, 0),
        'ancho': 40,
        'alto':  200,
    },
}


def cargar_nivel_2(tileset: pygame.Surface) -> list:
    return LevelParser(tileset).cargar('levels/nivel2.txt')


# ===========================================================================
# Registro de niveles
# ===========================================================================
NIVELES = {
    1: (cargar_nivel_1, DATOS_NIVEL_1),
    2: (cargar_nivel_2, DATOS_NIVEL_2),
}
