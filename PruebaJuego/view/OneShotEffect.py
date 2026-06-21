"""Clase base para efectos visuales de un solo uso.

Reproduce una animación de N frames una sola vez en una posición fija
del mundo y desaparece al llegar al último frame. ExplosionEffect,
HitEffect y BloodEffect heredan de esta clase y solo difieren en el
valor por defecto de cooldown_ms (y en la docstring).
"""

import pygame


class OneShotEffect:
    """Animación de un solo uso, centrada en un punto del mundo.

    Parameters
    ----------
    x, y : int
        Centro del efecto en coordenadas de mundo.
    frames : list of pygame.Surface
        Frames de la animación.
    cooldown_ms : int
        Milisegundos entre frames.
    """

    def __init__(self, x: int, y: int, frames: list, cooldown_ms: int):
        self.frames      = frames
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.cooldown_ms = cooldown_ms
        self.terminado   = False

        w = frames[0].get_width()
        h = frames[0].get_height()
        self.shape = pygame.Rect(0, 0, w, h)
        self.shape.center = (x, y)

    # ------------------------------------------------------------------ #

    def update(self):
        """Avanza el frame. Marca terminado al llegar al último."""
        if self.terminado:
            return
        ahora = pygame.time.get_ticks()
        if ahora - self.update_time >= self.cooldown_ms:
            self.frame_index += 1
            self.update_time  = ahora
            if self.frame_index >= len(self.frames):
                self.terminado = True

    def draw(self, interfaz: pygame.Surface, camara) -> None:
        """Dibuja el frame actual en pantalla."""
        if self.terminado:
            return
        frame = self.frames[self.frame_index]
        interfaz.blit(frame, camara.aplicar(self.shape))
