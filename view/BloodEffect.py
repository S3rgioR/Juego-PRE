"""Efecto visual de sangre al morir un enemigo.

Reproduce una animación de 21 frames una sola vez
(Assets/Efectos/Blood/1_[1-21].png) en la posición del enemigo
y desaparece al llegar al último frame.
"""

import pygame


class BloodEffect:
    """Animación de muerte de un solo uso.

    Parameters
    ----------
    x, y : int
        Centro del enemigo en coordenadas de mundo en el momento de morir.
    frames : list of pygame.Surface
        Los 21 frames cargados desde Assets/Efectos/Blood/.
    cooldown_ms : int
        Milisegundos entre frames (default 40 ms ≈ 25 fps).
    """

    def __init__(self, x: int, y: int, frames: list, cooldown_ms: int = 40):
        self.frames      = frames
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.cooldown_ms = cooldown_ms
        self.terminado   = False

        # Shape centrado en la posición del enemigo
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
