"""Definiciones de niveles del juego."""

import pygame
from LevelParser  import LevelParser
from TileCoords   import tp, tp_abs, tiles_to_px


# ===========================================================================
# NIVEL 1
# ===========================================================================

CHECKPOINT_NIVEL_1 = tp_abs(5, 2)

DATOS_NIVEL_1 = {
    'spawn':      tp_abs(1, 0),          # ← posición de aparición del jugador
    'checkpoint': CHECKPOINT_NIVEL_1,
    'musica':     'Assets/Audio/Music/Ambient_Lingering_Action.wav',

    'enemigos': [
        {
            'tipo':               'terrestre',
            **tp(40, 12),
            'distancia_patrulla': tiles_to_px(6),
            'num_frames_ataque':  6,
        },
        {
            'tipo':               'terrestre',
            **tp(2, 15),
            'distancia_patrulla': tiles_to_px(10),
            'num_frames_ataque':  6,
        },
        {
            'tipo': 'terrestre',
            **tp(60, 18),
            'distancia_patrulla': tiles_to_px(166),
            'num_frames_ataque': 6,
        },
        {
            'tipo': 'terrestre',
            **tp(130, 21),
            'distancia_patrulla': tiles_to_px(166),
            'num_frames_ataque': 6,
        },
        {
            'tipo':               'volador',
            **tp(40, 30),
            'distancia_patrulla': tiles_to_px(5),
        },
        {
            'tipo': 'volador',
            **tp(135, 38),
            'distancia_patrulla': tiles_to_px(5),
        },
    ],

    'boss': None,

    'angel':      tp(5, 30),
    'corazones': [tp(145, 38), tp(150, 21)],
    'daga_pickup': tp(10, 28),

    'fin_nivel': {
        **tp(150, 21),
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
    'checkpoint': tp_abs(3, 2),
    'musica':     'Assets/Audio/Music/Ambient_Lingering_Action.wav',

    'enemigos': [
        {
            'tipo':               'terrestre',
            **tp(9, 15),
            'distancia_patrulla': tiles_to_px(5),
            'num_frames_ataque':  6,
        },
        {
            'tipo':               'volador',
            **tp(25, 25),
            'distancia_patrulla': tiles_to_px(6),
        },
    ],

    'boss': {
        'tipo': 'boss',
        **tp(101, 9),
    },

    'angel':       tp(4, 16),
    'corazones':   [tp(15, 27)],
    'daga_pickup': None,

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
