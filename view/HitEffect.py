"""Efecto visual de impacto de daga sobre un enemigo.

Reproduce una animación de 3 frames una sola vez
(Assets/Efectos/Hit/Sprites/hit[1-3].png) en el punto de contacto
y desaparece al llegar al último frame.
"""

import pygame


class HitEffect:
    """Animación de impacto de un solo uso.

    Parameters
    ----------
    x, y : int
        Punto de impacto en coordenadas de mundo
        (normalmente el centro del proyectil al colisionar).
    frames : list of pygame.Surface
        Los 3 frames cargados desde Assets/Efectos/Hit/Sprites/.
    cooldown_ms : int
        Milisegundos entre frames (default 60 ms → duración total ~180 ms).
    """

    def __init__(self, x: int, y: int, frames: list, cooldown_ms: int = 60):
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
