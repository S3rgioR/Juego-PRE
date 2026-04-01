from typing import final

import pygame
import pygame
from Plataforma import Plataforma
def crear_plataforma(x, y, ancho, alto):
    pass
def cargar_nivel_1(tileset):
    plataformas = []

    # tile_rect indica x, y, ancho, alto del tile dentro del tileset
    # Ajusta estas coordenadas a tileset real
    tile_tierra= pygame.Rect(0, 0, 16, 16)  # Tierra. Justo de bajo de los pies
    tile_suelo = pygame.Rect(0, 16, 16, 16)  # "Negro" de relleno

    tile_pared_iz = pygame.Rect(128, 16, 16, 16)
    tile_pared_der = pygame.Rect(48, 16, 16, 16)

    tile_union_iz= pygame.Rect(128, 48, 16, 16)
    tile_union_der= pygame.Rect(48, 48, 16, 16)

    tile_final_iz = pygame.Rect(128, 0, 16, 16)
    tile_final_der = pygame.Rect(48, 0, 16, 16)

    # Suelo
    plataformas.append(Plataforma(0, 650, 1280, 16, tileset, tile_tierra))
    plataformas.append(Plataforma(0, 666, 1280, 160, tileset, tile_suelo))

    # --- Plataforma 1 --- #
    plataformas.append(Plataforma(150, 600, 200, 16, tileset, tile_tierra))
    plataformas.append(Plataforma(150, 616, 200, 800, tileset, tile_suelo))

    # Bordes plataforma
    plataformas.append(Plataforma(134, 600, 16, 16, tileset, tile_final_der))
    plataformas.append(Plataforma(350, 600, 16, 16, tileset, tile_final_iz))

    plataformas.append(Plataforma(134, 616, 16, 32, tileset, tile_pared_der))
    plataformas.append(Plataforma(350, 616, 16, 32, tileset, tile_pared_iz))

    plataformas.append(Plataforma(134, 648, 16, 16, tileset, tile_union_der))
    plataformas.append(Plataforma(350, 648, 16, 16, tileset, tile_union_iz))



    return plataformas