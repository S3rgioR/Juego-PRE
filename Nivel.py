from typing import final

import pygame
import pygame
from Plataforma import Plataforma

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
    ysuelo = 656
    plataformas.append(Plataforma(-1000, ysuelo, 20000, 16, tileset, tile_tierra))
    plataformas.append(Plataforma(-1000, ysuelo+16, 20000, 160, tileset, tile_suelo))
    def crear_plataforma(tileset, x, y, ancho):
        alto=ysuelo-y
        # --- Plataforma 1 --- #

        plataformas.append(Plataforma(x, y, ancho, 16, tileset, tile_tierra))
        plataformas.append(Plataforma(x-16, y+16, ancho, alto+16, tileset, tile_suelo))

        # Bordes plataforma
        plataformas.append(Plataforma(x-16, y, 16, 16, tileset, tile_final_der))
        plataformas.append(Plataforma(x+ancho-16, y, 16, 16, tileset, tile_final_iz))

        plataformas.append(Plataforma(x-16, y+16, 16, ysuelo-y, tileset, tile_pared_der))
        plataformas.append(Plataforma(x+ancho-16, y+16, 16, ysuelo-y, tileset, tile_pared_iz))

        plataformas.append(Plataforma(x-16, y+alto, 16, 16, tileset, tile_union_der))
        plataformas.append(Plataforma(x+ancho-16, y+alto, 16, 16, tileset, tile_union_iz))


    crear_plataforma(tileset,160,608,200)
    crear_plataforma(tileset, 800, 560, 200)

    crear_plataforma(tileset, 1500, 528, 300)
    return plataformas