"""Sprite visual del Enemigo_1 para pygame."""

import pygame
from .EnemigoSpriteBase import EnemigoSpriteBase


class OgroSprite(EnemigoSpriteBase):

    def __init__(self, x, y, anim_walk, anim_attack):
        super().__init__(x, y, anim_walk)
        self.anim_attack = anim_attack

    # ------------------------------------------------------------------ #

    def sincronizar(self, estado_modelo):
        self._sincronizar_base(estado_modelo)

        self.hitbox_ataque = estado_modelo["hitbox_ataque"]

        nueva_anim = self.anim_attack if estado_modelo["atacando"] else self.anim_walk
        if nueva_anim != self.anim_actual:
            self.anim_actual = nueva_anim
            self.frame_index = 0

        self._avanzar_frame(cooldown_ms=100)

    # ------------------------------------------------------------------ #

    def draw(self, interfaz, camara, estado_modelo=None):
        imagen_flip = pygame.transform.flip(self.image, not self.flip, False)
        img_rect    = imagen_flip.get_rect(midbottom=self.shape.midbottom)

        self._blit_con_iframe(interfaz, camara, imagen_flip, img_rect)

        # Debug hitboxes
        pygame.draw.rect(interfaz, (255, 0, 0), camara.aplicar(self.shape), 1)
        if self.hitbox_ataque:
            pygame.draw.rect(interfaz, (255, 255, 0), camara.aplicar(self.hitbox_ataque), 2)

        self._tick_exclamacion(interfaz, camara)
