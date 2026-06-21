"""Sprite visual del Enemigo_2 para pygame."""

import pygame
import Constantes
import numpy
import math


class Enemigo2Sprite:
    EXCLAMACION_DURACION_MS = 800

    def __init__(self, x, y, anim_walk):
        self.shape = pygame.Rect(
            0, 0,
            Constantes.WIDTH_PERSONAJE * 2,
            Constantes.HEIGHT_PERSONAJE * 1.5
        )
        self.shape.center = (x, y)

        self.anim_walk   = anim_walk
        self.anim_actual = self.anim_walk
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.image       = self.anim_actual[0]
        self.flip        = True

        self.hitbox_ataque  = None
        self._iframe_activo = False

        self._flotacion_offset = 0.0
        self._flotacion_tiempo = 0.0

        self.proyectil_frames     = []
        self._sprites_proyectiles = {}

        # Exclamación
        self._exclamacion_timer  = 0
        self._fuente_exclamacion = None
        self._last_draw_time     = pygame.time.get_ticks()

    def sincronizar(self, estado_modelo):
        self.shape.center = (
            int(estado_modelo['pos'][0]),
            int(estado_modelo['pos'][1])
        )
        self.flip           = estado_modelo['flip']
        self._iframe_activo = estado_modelo.get('iframe_activo', False)

        if estado_modelo.get('exclamacion_nueva'):
            self._exclamacion_timer = self.EXCLAMACION_DURACION_MS

        self._flotacion_tiempo += 0.05
        self._flotacion_offset  = math.sin(self._flotacion_tiempo) * 6

        cooldown = 120
        if pygame.time.get_ticks() - self.update_time > cooldown:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()

        if self.frame_index >= len(self.anim_actual):
            self.frame_index = 0

        self.image = self.anim_actual[self.frame_index]

    def draw(self, interfaz, camara, estado_modelo=None):
        imagen_flip = pygame.transform.flip(self.image, self.flip, False)
        img_rect = imagen_flip.get_rect(midbottom=self.shape.midbottom)
        img_rect.y += int(self._flotacion_offset)

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

        pygame.draw.rect(interfaz, (0, 180, 255), camara.aplicar(self.shape), 1)

        # Exclamación
        ahora = pygame.time.get_ticks()
        if self._exclamacion_timer > 0:
            self._exclamacion_timer -= ahora - self._last_draw_time
            self._dibujar_exclamacion(interfaz, camara)
        self._last_draw_time = ahora

        # Proyectiles
        if estado_modelo:
            proyectiles = [ep for ep in estado_modelo.get('proyectiles', []) if ep['vivo']]
            while len(self._sprites_proyectiles) < len(proyectiles):
                self._sprites_proyectiles[len(self._sprites_proyectiles)] = ProyectilSprite(self.proyectil_frames)
            while len(self._sprites_proyectiles) > len(proyectiles):
                self._sprites_proyectiles.pop(len(self._sprites_proyectiles) - 1)
            for i, ep in enumerate(proyectiles):
                self._sprites_proyectiles[i].draw(interfaz, camara, ep)

    def _dibujar_exclamacion(self, interfaz, camara):
        if self._fuente_exclamacion is None:
            self._fuente_exclamacion = pygame.font.SysFont(None, 36)

        txt   = self._fuente_exclamacion.render("!", True, (255, 220, 0))
        rect  = camara.aplicar(self.shape)
        pos_x = rect.centerx - txt.get_width() // 2
        pos_y = rect.top - txt.get_height() - 4

        bg = pygame.Rect(pos_x - 3, pos_y - 2, txt.get_width() + 6, txt.get_height() + 4)
        pygame.draw.rect(interfaz, (40, 20, 0), bg, border_radius=3)
        pygame.draw.rect(interfaz, (255, 180, 0), bg, width=1, border_radius=3)
        interfaz.blit(txt, (pos_x, pos_y))


class ProyectilSprite:
    def __init__(self, frames):
        self.frames      = frames
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.shape       = pygame.Rect(0, 0, frames[0].get_width(), frames[0].get_height())

    def draw(self, interfaz, camara, estado):
        self.shape.center = (int(estado['pos'][0]), int(estado['pos'][1]))

        if pygame.time.get_ticks() - self.update_time > 80:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.update_time = pygame.time.get_ticks()

        imagen = pygame.transform.flip(self.frames[self.frame_index], estado['flip'], False)
        interfaz.blit(imagen, camara.aplicar(self.shape))
        pygame.draw.rect(interfaz, (255, 165, 0), camara.aplicar(self.shape), 1)
