"""Efecto visual de explosión al destruirse un proyectil enemigo.

Reproduce una animación de 8 frames una sola vez
(Assets/Efectos/explosion-1-f/Sprites/explosion-f[1-8].png)
en la posición del proyectil y desaparece al llegar al último frame.
"""

import pygame


class ExplosionEffect:
    """Animación de explosión de un solo uso.

    Parameters
    ----------
    x, y : int
        Centro del proyectil en coordenadas de mundo en el momento de morir.
    frames : list of pygame.Surface
        Los 8 frames cargados desde Assets/Efectos/explosion-1-f/Sprites/.
    cooldown_ms : int
        Milisegundos entre frames (default 55 ms ≈ 18 fps).
    """

    def __init__(self, x: int, y: int, frames: list, cooldown_ms: int = 55):
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
