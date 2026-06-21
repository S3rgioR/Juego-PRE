"""Sprite visual del proyectil de daga lanzado por el jugador."""

import pygame


class DagaProyectilSprite:
    """Sprite animado del proyectil de daga.

    Parameters
    ----------
    frames : list of pygame.Surface
        Frames de animación (puede ser un único frame).
    """

    COOLDOWN_ANIM = 80   # ms entre frames

    def __init__(self, frames: list):
        self.frames      = frames
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()

    def draw(self, interfaz: pygame.Surface, camara, estado: dict) -> None:
        """Dibuja el proyectil en pantalla.

        Parameters
        ----------
        estado : dict
            {'pos': (x, y), 'flip': bool, 'vivo': bool}
        """
        if not estado['vivo']:
            return

        # Avanzar animación
        ahora = pygame.time.get_ticks()
        if ahora - self.update_time > self.COOLDOWN_ANIM:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.update_time = ahora

        frame = self.frames[self.frame_index]
        imagen = pygame.transform.flip(frame, estado['flip'], False)

        rect = imagen.get_rect()
        rect.center = estado['pos']
        interfaz.blit(imagen, camara.aplicar(rect))
