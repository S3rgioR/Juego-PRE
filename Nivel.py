"""Cargador de niveles.

Construye la lista de objetos Plataforma que define la geometría del nivel.
Cada Plataforma contiene tanto el shape (pygame.Rect, usado por el Model
para colisiones) como la superficie visual (usada por la Vista para dibujar).

Vive fuera de view/ porque lo necesitan tanto el Model (para colisiones)
como la Vista (para dibujar), y el Presenter lo pasa a ambos.
"""

# Posición del checkpoint en el nivel 1 (centro, coordenadas de mundo).
CHECKPOINT_NIVEL_1 = (500, 620)

import pygame
from view.Plataforma import Plataforma


def cargar_nivel_1(tileset):
    """Construye y devuelve la lista de plataformas del nivel 1.

    Parameters
    ----------
    tileset : pygame.Surface
        Hoja de tiles cargada en memoria.

    Returns
    -------
    list of Plataforma
        Lista ordenada de plataformas que forman el nivel.
    """
    plataformas = []

    # --- Definición de tiles dentro del tileset ---
    tile_tierra    = pygame.Rect(0,   0,  16, 16)   # Superficie pisable
    tile_suelo     = pygame.Rect(0,   16, 16, 16)   # Relleno oscuro

    tile_pared_iz  = pygame.Rect(128, 16, 16, 16)
    tile_pared_der = pygame.Rect(48,  16, 16, 16)

    tile_union_iz  = pygame.Rect(128, 48, 16, 16)
    tile_union_der = pygame.Rect(48,  48, 16, 16)

    tile_final_iz  = pygame.Rect(128, 0,  16, 16)
    tile_final_der = pygame.Rect(48,  0,  16, 16)

    # --- Suelo principal ---
    ysuelo = 656
    plataformas.append(Plataforma(-1000, ysuelo,      20000, 16,  tileset, tile_tierra))
    plataformas.append(Plataforma(-1000, ysuelo + 16, 20000, 160, tileset, tile_suelo))

    def crear_plataforma(tileset, x, y, ancho):
        """Añade una plataforma elevada con bordes y paredes laterales."""
        alto = ysuelo - y

        # Superficie superior
        plataformas.append(Plataforma(x,        y,       ancho, 16,          tileset, tile_tierra))
        # Relleno vertical
        plataformas.append(Plataforma(x - 16,   y + 16,  ancho, alto + 16,   tileset, tile_suelo))

        # Esquinas superiores
        plataformas.append(Plataforma(x - 16,         y, 16, 16, tileset, tile_final_der))
        plataformas.append(Plataforma(x + ancho - 16, y, 16, 16, tileset, tile_final_iz))

        # Paredes laterales
        plataformas.append(Plataforma(x - 16,         y + 16, 16, ysuelo - y, tileset, tile_pared_der))
        plataformas.append(Plataforma(x + ancho - 16, y + 16, 16, ysuelo - y, tileset, tile_pared_iz))

        # Esquinas inferiores (unión con el suelo)
        plataformas.append(Plataforma(x - 16,         y + alto, 16, 16, tileset, tile_union_der))
        plataformas.append(Plataforma(x + ancho - 16, y + alto, 16, 16, tileset, tile_union_iz))

    crear_plataforma(tileset, 160,  608, 200)
    crear_plataforma(tileset, 800,  560, 200)
    crear_plataforma(tileset, 1500, 528, 300)

    return plataformas
