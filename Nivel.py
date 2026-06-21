"""Definiciones de niveles del juego."""

import pygame
from LevelParser  import LevelParser
from TileCoords   import tp, tp_abs, tiles_to_px


# ===========================================================================
# NIVEL 1
# ===========================================================================

CHECKPOINT_NIVEL_1 = tp_abs(60, 61)

DATOS_NIVEL_1 = {
    'spawn':      tp_abs(4, 37),          # ← posición de aparición del jugador
    'checkpoint': CHECKPOINT_NIVEL_1,
    'musica':     'Assets/Audio/Music/Ambient_Lingering_Action.wav',

    'enemigos': [
        {
            'tipo':               'terrestre',
            **tp(122, 13),
            'distancia_patrulla': tiles_to_px(10),
            'num_frames_ataque':  6,
        },
        {
            'tipo':               'terrestre',
            **tp(38, 53),
            'distancia_patrulla': tiles_to_px(20),
            'num_frames_ataque':  6,
        },
        {
            'tipo': 'terrestre',
            **tp(103, 79),
            'distancia_patrulla': tiles_to_px(166),
            'num_frames_ataque': 6,
        },
        {
            'tipo':               'volador',
            **tp(131, 53),
            'distancia_patrulla': tiles_to_px(10),
        },
        {
            'tipo': 'volador',
            **tp(103, 81),
            'distancia_patrulla': tiles_to_px(5),
        },
    ],

    'boss': None,

    'angel':      tp(69, 68),

    'corazones': [tp(60, 78)],
    'daga_pickup': None,
    'spikes': [],  # se rellena en main.py parseando levels/nivel1.txt

    'fin_nivel': {
        **tp(206, 81),
        'ancho': 5,
        'alto':  5,
    },
}


def cargar_nivel_1(tileset: pygame.Surface) -> list:
    return LevelParser(tileset).cargar('levels/nivel1.txt')


# ===========================================================================
# NIVEL 2
# ===========================================================================
CHECKPOINT_NIVEL_2 = tp_abs(102, 84)  # pon aquí las coordenadas que quieras

DATOS_NIVEL_2 = {
    'spawn':      tp_abs(2, 2),          # posición de aparición del jugador
    'checkpoint': CHECKPOINT_NIVEL_2,
    'musica':     'Assets/Audio/Music/Ambient_Lingering_Action.wav',

    'enemigos': [
        {
            'tipo':               'terrestre',
            **tp(21, 75),
            'distancia_patrulla': tiles_to_px(20),
            'num_frames_ataque':  6,
        },
        {
            'tipo':               'terrestre',
            **tp(135, 85),
            'distancia_patrulla': tiles_to_px(10),
            'num_frames_ataque':  6,
        },
        {
            'tipo': 'terrestre',
            **tp(155, 85),
            'distancia_patrulla': tiles_to_px(166),
            'num_frames_ataque': 6,
        },
        {
            'tipo': 'terrestre',
            **tp(130, 100),
            'distancia_patrulla': tiles_to_px(166),
            'num_frames_ataque': 6,
        },
        {
            'tipo':               'volador',
            **tp(61, 30),
            'distancia_patrulla': tiles_to_px(5),
        },
        {
            'tipo': 'volador',
            **tp(19, 85),
            'distancia_patrulla': tiles_to_px(5),
        },
{
            'tipo': 'volador',
            **tp(135, 65),
            'distancia_patrulla': tiles_to_px(10),
        },
{
            'tipo': 'volador',
            **tp(166, 65),
            'distancia_patrulla': tiles_to_px(6),
        },
    ],

    'boss': None,

    'angel':      tp(81, 62),
    'portal_regreso': {
        **tp(5, 3),
        'ancho': 5,
        'alto':  5,
    },
    'corazones': [tp(200, 84), tp(48, 93)],
    'daga_pickup': tp(45, 84),
    'spikes': [],  # se rellena en main.py parseando levels/nivel2.txt

    'fin_nivel': {
        **tp(203, 107),
        'ancho': 5,
        'alto':  5,
    },
}


def cargar_nivel_2(tileset: pygame.Surface) -> list:
    return LevelParser(tileset).cargar('levels/nivel2.txt')
DATOS_NIVEL_3 = {
    'spawn':      tp_abs(10, 47),          # posición de aparición del jugador
    'checkpoint': None,
    'musica':     'Assets/Audio/Music/Boss_Battle_Sequence.wav',

    'enemigos': [],

    'boss': tp(94, 15),

    'angel':      None,
    'portal_regreso': {
        **tp(10, 38),
        'ancho': 5,
        'alto':  5,
    },
    'corazones': None,
    'daga_pickup': None,
    'spikes': [],  # se rellena en main.py parseando levels/nivel3.txt
    'portal_final': {
        **tp(234, 10),
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
