"""Vista del portal de fin de juego."""

import pygame
from .InteractableView import InteractableView


class PortalFinalView(InteractableView):
    RADIO_ACTIVACION = 60
    MS_POR_FRAME     = 80

    def __init__(self, x: int, y: int, frames: list, ancho: int = 1, alto: int = 1):
        super().__init__(x, y, ancho, alto, texto_prompt="[E] Fin")

        self.frames      = frames
        self.frame_idx   = 0
        self.frame_timer = 0

    # ------------------------------------------------------------------ #

    def actualizar(self, delta_ms: float) -> None:
        """Avanza la animación."""
        if not self.frames:
            return
        self.frame_timer += delta_ms
        if self.frame_timer >= self.MS_POR_FRAME:
            self.frame_timer = 0
            self.frame_idx   = (self.frame_idx + 1) % len(self.frames)

    def draw(self, interfaz: pygame.Surface, camara) -> None:
        if not self.frames:
            return

        frame = self.frames[self.frame_idx]
        interfaz.blit(frame, camara.aplicar(frame.get_rect(center=self.shape.center)))

        self._dibujar_prompt(interfaz, camara)
