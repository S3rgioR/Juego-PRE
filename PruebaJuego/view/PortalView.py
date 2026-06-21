"""Sprite visual del portal (fin de nivel y regreso al anterior)."""

import pygame
from .InteractableView import InteractableView


class PortalView(InteractableView):
    COOLDOWN_ANIM    = 30   # ms entre frames (64 frames → ~2 s por ciclo)
    RADIO_ACTIVACION = 60
    _COLOR_PROMPT    = (255, 255, 180)

    def __init__(self, x: int, y: int, frames: list, ancho: int = 40, alto: int = 200):
        super().__init__(x, y, ancho, alto, texto_prompt="[E] Entrar")

        self.frames      = frames
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()

    # ------------------------------------------------------------------ #

    def colisiona_con(self, jugador_shape: pygame.Rect) -> bool:
        return self.shape.colliderect(jugador_shape)

    def draw(self, interfaz: pygame.Surface, camara) -> None:
        # Avanzar animación
        ahora = pygame.time.get_ticks()
        if ahora - self.update_time > self.COOLDOWN_ANIM:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.update_time = ahora

        frame = self.frames[self.frame_index]
        interfaz.blit(frame, camara.aplicar(frame.get_rect(center=self.shape.center)))

        self._dibujar_prompt(interfaz, camara)
