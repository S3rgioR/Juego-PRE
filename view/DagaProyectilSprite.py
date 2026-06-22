"""Sprite visual del proyectil de daga lanzado por el jugador."""

import pygame
from .ProyectilSpriteBase import ProyectilSpriteBase


class DagaProyectilSprite(ProyectilSpriteBase):
    """Sprite animado del proyectil de daga.

    Parameters
    ----------
    frames : list of pygame.Surface
        Frames de animación (puede ser un único frame).
    """

    COOLDOWN_ANIM = 80   # ms entre frames

    def draw(self, interfaz: pygame.Surface, camara, estado: dict) -> None:
        """Dibuja el proyectil en pantalla.

        Parameters
        ----------
        estado : dict
            {'pos': (x, y), 'flip': bool, 'vivo': bool}
        """
        if not estado['vivo']:
            return

        self._avanzar_frame()

        imagen = pygame.transform.flip(self._frame_actual(), estado['flip'], False)

        rect = imagen.get_rect()
        rect.center = estado['pos']
        interfaz.blit(imagen, camara.aplicar(rect))
