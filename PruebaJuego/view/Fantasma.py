"""Sprite visual del Enemigo_2 para pygame."""

import pygame
import math
from .EnemigoSpriteBase import EnemigoSpriteBase


class FantasmaSprite(EnemigoSpriteBase):

    def __init__(self, x, y, anim_walk):
        super().__init__(x, y, anim_walk)

        self._flotacion_offset = 0.0
        self._flotacion_tiempo = 0.0

        self.proyectil_frames     = []
        self._sprites_proyectiles = {}

    # ------------------------------------------------------------------ #

    def sincronizar(self, estado_modelo):
        self._sincronizar_base(estado_modelo)

        self._flotacion_tiempo += 0.05
        self._flotacion_offset  = math.sin(self._flotacion_tiempo) * 6

        self._avanzar_frame(cooldown_ms=120)

    # ------------------------------------------------------------------ #

    def draw(self, interfaz, camara, estado_modelo=None):
        imagen_flip = pygame.transform.flip(self.image, self.flip, False)
        img_rect    = imagen_flip.get_rect(midbottom=self.shape.midbottom)
        img_rect.y += int(self._flotacion_offset)

        self._blit_con_iframe(interfaz, camara, imagen_flip, img_rect)

        pygame.draw.rect(interfaz, (0, 180, 255), camara.aplicar(self.shape), 1)

        self._tick_exclamacion(interfaz, camara)

        # Proyectiles
        if estado_modelo:
            proyectiles = [ep for ep in estado_modelo.get("proyectiles", []) if ep["vivo"]]

            # Ajustar el pool al número de proyectiles activos
            while len(self._sprites_proyectiles) < len(proyectiles):
                self._sprites_proyectiles[len(self._sprites_proyectiles)] = ProyectilSprite(
                    self.proyectil_frames
                )
            while len(self._sprites_proyectiles) > len(proyectiles):
                self._sprites_proyectiles.pop(len(self._sprites_proyectiles) - 1)

            for i, ep in enumerate(proyectiles):
                self._sprites_proyectiles[i].draw(interfaz, camara, ep)


# --------------------------------------------------------------------------- #
#  Proyectil                                                                   #
# --------------------------------------------------------------------------- #

class ProyectilSprite:
    def __init__(self, frames):
        self.frames      = frames
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.shape       = pygame.Rect(0, 0, frames[0].get_width(), frames[0].get_height())

    def draw(self, interfaz, camara, estado):
        self.shape.center = (int(estado["pos"][0]), int(estado["pos"][1]))

        if pygame.time.get_ticks() - self.update_time > 80:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.update_time = pygame.time.get_ticks()

        imagen = pygame.transform.flip(self.frames[self.frame_index], estado["flip"], False)
        interfaz.blit(imagen, camara.aplicar(self.shape))
        pygame.draw.rect(interfaz, (255, 165, 0), camara.aplicar(self.shape), 1)
