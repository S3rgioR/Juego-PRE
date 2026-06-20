"""Vista visual del Ángel curador.

Sprite animado estático (no se mueve por el mundo).
Muestra un prompt [K] cuando el jugador se acerca y,
cuando se activa la curación, reproduce un destello dorado.

Ruta de assets: Assets/Characters/angel/sprites/angel[1-8].png
"""

import pygame
from .InteractableView import InteractableView
from .VisualEffects import aplicar_tinte


class AngelView(InteractableView):
    RADIO_ACTIVACION  = 100   # px de distancia para mostrar el prompt
    COOLDOWN_ANIM     = 100   # ms entre frames de animación
    DURACION_DESTELLO = 1200  # ms que dura el efecto dorado al curar
    _COLOR_PROMPT     = (255, 255, 180)

    def __init__(self, x: int, y: int, frames: list):
        super().__init__(
            x, y,
            frames[0].get_width(),
            frames[0].get_height(),
            texto_prompt="[K] Curar",
        )

        self.frames      = frames
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()

        self._destello_activo = False
        self._inicio_destello = 0

    # ------------------------------------------------------------------ #

    def activar_destello(self) -> None:
        """Arranca el efecto dorado de curación."""
        self._destello_activo = True
        self._inicio_destello = pygame.time.get_ticks()

    # ------------------------------------------------------------------ #

    def _avanzar_frame(self) -> None:
        ahora = pygame.time.get_ticks()
        if ahora - self.update_time > self.COOLDOWN_ANIM:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.update_time = ahora

    def draw(self, interfaz: pygame.Surface, camara) -> None:
        self._avanzar_frame()
        frame_base = self.frames[self.frame_index]
        img_rect   = frame_base.get_rect(midbottom=self.shape.midbottom)

        # Efecto dorado durante el destello (intensidad decae con el tiempo)
        if self._destello_activo:
            ms = pygame.time.get_ticks() - self._inicio_destello
            if ms < self.DURACION_DESTELLO:
                intensidad = 0.6 * (1.0 - ms / self.DURACION_DESTELLO)
                imagen = aplicar_tinte(frame_base, r=255, g=220, b=50, intensidad=intensidad)
            else:
                self._destello_activo = False
                imagen = frame_base
        else:
            imagen = frame_base

        interfaz.blit(imagen, camara.aplicar(img_rect))

        self._dibujar_prompt(interfaz, camara)
