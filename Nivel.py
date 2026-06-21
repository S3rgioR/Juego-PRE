"""Definiciones de niveles del juego."""

import pygame
from LevelParser  import LevelParser
from TileCoords   import tp, tp_abs, tiles_to_px


# ===========================================================================
# NIVEL 1
# ===========================================================================

CHECKPOINT_NIVEL_1 = tp_abs(32, 34)

DATOS_NIVEL_1 = {
    'spawn':      tp_abs(2, 20),          # ← posición de aparición del jugador
    'checkpoint': CHECKPOINT_NIVEL_1,
    'musica':     'Assets/Audio/Music/Ambient_Lingering_Action.wav',

    'enemigos': [
        {
            'tipo':               'terrestre',
            **tp(65, 7),
            'distancia_patrulla': tiles_to_px(10),
            'num_frames_ataque':  6,
        },
        {
            'tipo':               'terrestre',
            **tp(20, 28),
            'distancia_patrulla': tiles_to_px(20),
            'num_frames_ataque':  6,
        },
        {
            'tipo': 'terrestre',
            **tp(55, 42),
            'distancia_patrulla': tiles_to_px(166),
            'num_frames_ataque': 6,
        },
        {
            'tipo':               'volador',
            **tp(70, 28),
            'distancia_patrulla': tiles_to_px(10),
        },
        {
            'tipo': 'volador',
            **tp(55, 43),
            'distancia_patrulla': tiles_to_px(5),
        },
    ],

    'boss': None,

    'angel':      tp(37, 36),

    'corazones': [tp(32, 42)],
    'daga_pickup': None,
    'spikes': [],  # se rellena en main.py parseando levels/nivel1.txt

    'fin_nivel': {
        **tp(110, 43),
        'ancho': 5,
        'alto':  5,
    },
}


def cargar_nivel_1(tileset: pygame.Surface) -> list:
    return LevelParser(tileset).cargar('levels/nivel1.txt')


# ===========================================================================
# NIVEL 2
# ===========================================================================
CHECKPOINT_NIVEL_2 = tp_abs(5, 1)   # pon aquí las coordenadas que quieras

DATOS_NIVEL_2 = {
    'spawn':      tp_abs(1, 0),          # posición de aparición del jugador
    'checkpoint': CHECKPOINT_NIVEL_2,
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
            **tp(1, 20),
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
    'portal_regreso': {
        **tp(2, 2),
        'ancho': 5,
        'alto':  5,
    },
    'corazones': [tp(145, 38), tp(140, 21)],
    'daga_pickup': tp(10, 28),
    'spikes': [],  # se rellena en main.py parseando levels/nivel2.txt

    'fin_nivel': {
        **tp(150, 21),
        'ancho': 5,
        'alto':  5,
    },
}


def cargar_nivel_2(tileset: pygame.Surface) -> list:
    return LevelParser(tileset).cargar('levels/nivel2.txt')
DATOS_NIVEL_3 = {
    'spawn':      tp_abs(5, 25),          # posición de aparición del jugador
    'checkpoint': None,
    'musica':     'Assets/Audio/Music/Boss_Battle_Sequence.wav',

    'enemigos': [],

    'boss': tp(50, 8),

    'angel':      None,
    'portal_regreso': {
        **tp(5, 20),
        'ancho': 5,
        'alto':  5,
    },
    'corazones': None,
    'daga_pickup': None,
    'spikes': [],  # se rellena en main.py parseando levels/nivel3.txt
    'portal_final': {
        **tp(125, 5),
        'ancho': 5,
        'alto': 5,
    },
    'fin_nivel': None,
}
def cargar_nivel_3(tileset: pygame.Surface) -> list:
    return LevelParser(tileset).cargar('levels/nivel3.txt')

# ===========================================================================
# Registro de niveles
# ===========================================================================
NIVELES = {
    1: (cargar_nivel_1, DATOS_NIVEL_1),
    2: (cargar_nivel_2, DATOS_NIVEL_2),
    3: (cargar_nivel_3, DATOS_NIVEL_3),
}
