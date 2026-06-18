"""Sprite visual del Enemigo_1 para pygame."""

import pygame
import Constantes
import numpy


class Enemigo1Sprite:
    EXCLAMACION_DURACION_MS = 800   # cuánto tiempo se muestra el "!"

    def __init__(self, x, y, anim_walk, anim_attack):
        self.shape = pygame.Rect(
            0, 0,
            Constantes.WIDTH_PERSONAJE * 2,
            Constantes.HEIGHT_PERSONAJE * 1.5
        )
        self.shape.center = (x, y)

        self.anim_walk   = anim_walk
        self.anim_attack = anim_attack
        self.anim_actual = self.anim_walk
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.image       = self.anim_actual[0]
        self.flip        = True
        self.hitbox_ataque  = None
        self._iframe_activo = False

        # Exclamación
        self._exclamacion_timer = 0       # ms restantes de mostrar "!"
        self._fuente_exclamacion = None   # se crea lazy para evitar problemas de init

    def sincronizar(self, estado_modelo):
        self.shape.center = (
            int(estado_modelo['pos'][0]),
            int(estado_modelo['pos'][1])
        )
        self.flip           = estado_modelo['flip']
        self.hitbox_ataque  = estado_modelo['hitbox_ataque']
        self._iframe_activo = estado_modelo.get('iframe_activo', False)

        # Activar exclamación si el modelo lo señaliza
        if estado_modelo.get('exclamacion_nueva'):
            self._exclamacion_timer = self.EXCLAMACION_DURACION_MS

        nueva_anim = self.anim_attack if estado_modelo['atacando'] else self.anim_walk
        if nueva_anim != self.anim_actual:
            self.anim_actual = nueva_anim
            self.frame_index = 0

        cooldown = 100
        if pygame.time.get_ticks() - self.update_time > cooldown:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()

        if self.frame_index >= len(self.anim_actual):
            self.frame_index = 0

        self.image = self.anim_actual[self.frame_index]

    def draw(self, interfaz, camara, estado_modelo=None):
        imagen_flip = pygame.transform.flip(self.image, not self.flip, False)
        img_rect = imagen_flip.get_rect(midbottom=self.shape.midbottom)

        if self._iframe_activo:
            imagen_roja = imagen_flip.convert_alpha()
            arr   = pygame.surfarray.pixels3d(imagen_roja)
            alpha = pygame.surfarray.pixels_alpha(imagen_roja)
            mask  = alpha > 0
            arr[:, :, 0][mask] = numpy.minimum(255, arr[:, :, 0][mask].astype(int) + 150)
            arr[:, :, 1][mask] = arr[:, :, 1][mask] // 2
            arr[:, :, 2][mask] = arr[:, :, 2][mask] // 2
            del arr, alpha
            interfaz.blit(imagen_roja, camara.aplicar(img_rect))
        else:
            interfaz.blit(imagen_flip, camara.aplicar(img_rect))

        # Debug hitboxes
        pygame.draw.rect(interfaz, (255, 0, 0), camara.aplicar(self.shape), 1)
        if self.hitbox_ataque:
            pygame.draw.rect(interfaz, (255, 255, 0), camara.aplicar(self.hitbox_ataque), 2)

        # Exclamación
        if self._exclamacion_timer > 0:
            self._exclamacion_timer -= pygame.time.get_ticks() - getattr(
                self, '_last_draw_time', pygame.time.get_ticks())
            self._last_draw_time = pygame.time.get_ticks()
            self._dibujar_exclamacion(interfaz, camara)
        else:
            self._last_draw_time = pygame.time.get_ticks()

    def _dibujar_exclamacion(self, interfaz, camara):
        if self._fuente_exclamacion is None:
            self._fuente_exclamacion = pygame.font.SysFont(None, 36)

        txt   = self._fuente_exclamacion.render("!", True, (255, 220, 0))
        rect  = camara.aplicar(self.shape)
        pos_x = rect.centerx - txt.get_width() // 2
        pos_y = rect.top - txt.get_height() - 4

        # Fondo oscuro para legibilidad
        bg = pygame.Rect(pos_x - 3, pos_y - 2, txt.get_width() + 6, txt.get_height() + 4)
        pygame.draw.rect(interfaz, (40, 20, 0), bg, border_radius=3)
        pygame.draw.rect(interfaz, (255, 180, 0), bg, width=1, border_radius=3)
        interfaz.blit(txt, (pos_x, pos_y))
