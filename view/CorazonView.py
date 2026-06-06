"""Vista visual del corazón recogible.

Objeto estático en el mapa. Al colisionar el jugador con él:
  - +1 hp_max
  - +1 hp (sin superar hp_max)
  - desaparece para siempre (recogido = True)

El save system guarda qué corazones ya han sido recogidos por índice,
así no vuelven a aparecer al cargar partida.
"""

import pygame


class CorazonView:
    """Sprite visual de un corazón de vida recogible.

    Parameters
    ----------
    x, y : int
        Posición central en coordenadas de mundo.
    imagen : pygame.Surface
        Imagen del corazón (cargada en main.py).
    indice : int
        Identificador único del corazón en el nivel (para el save).
    """

    # Radio de colisión con el jugador (px)
    RADIO_COLISION = 30

    def __init__(self, x: int, y: int, imagen: pygame.Surface, indice: int):
        self.imagen   = imagen
        self.indice   = indice
        self.recogido = False

        self.shape = pygame.Rect(0, 0, imagen.get_width(), imagen.get_height())
        self.shape.center = (x, y)

    # ------------------------------------------------------------------ #

    def colisiona_con(self, jugador_shape: pygame.Rect) -> bool:
        """True si el jugador toca el corazón y este no ha sido recogido."""
        if self.recogido:
            return False
        return self.shape.colliderect(jugador_shape)

    def recoger(self):
        """Marca el corazón como recogido (desaparece del mapa)."""
        self.recogido = True

    # ------------------------------------------------------------------ #

    def draw(self, interfaz: pygame.Surface, camara) -> None:
        if self.recogido:
            return
        interfaz.blit(self.imagen, camara.aplicar(self.shape))
