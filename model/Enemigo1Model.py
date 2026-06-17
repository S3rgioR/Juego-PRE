"""Sub-modelo del Enemigo_1: patrullador terrestre con persecución."""

import pygame
import Constantes
from .Actor import Actor


class Enemigo1Model(Actor):
    COOLDOWN_ANIM = 200

    def __init__(self, x, y, distancia_patrulla=150, num_frames_ataque=6):
        super().__init__(hp=5, iframe_duracion=600)
        self.flip      = True
        self.velocidad = 2

        self.patrol_min = x - distancia_patrulla
        self.patrol_max = x + distancia_patrulla

        self.rango_vision    = 250   # px — rango en el que detecta al jugador
        self.rango_ataque    = 100   # px — distancia a la que ataca
        self.cooldown_ataque = 1200
        self.ultimo_ataque   = -self.cooldown_ataque

        self._frame_index       = 0
        self._update_time       = pygame.time.get_ticks()
        self._num_frames_ataque = num_frames_ataque

        self.ataque_frame_inicio = 2
        self.ataque_frame_fin    = 5

        # --- Persecución ---
        self.persiguiendo          = False   # True mientras sigue al jugador
        self._exclamacion_nueva    = False   # True solo el frame que detecta
        self.velocidad_persecucion = 3       # px/frame al perseguir

    # --- IA ---

    def tick_ia(self, pos_enemigo, pos_jugador, delta_time_ms, tiles_solidos=None):
        if not self.vivo:
            return 0, None

        self._tick_iframes(delta_time_ms)
        self._exclamacion_nueva = False

        ex, ey = pos_enemigo
        jx, _  = pos_jugador
        dx     = jx - ex
        dist   = abs(dx)

        ve_al_jugador = (
            dist <= self.rango_vision
            and not self._hay_pared_entre(pos_enemigo, pos_jugador, tiles_solidos)
        )

        # Transición patrulla → persecución
        if ve_al_jugador and not self.persiguiendo:
            self.persiguiendo       = True
            self._exclamacion_nueva = True
            if hasattr(self, 'on_deteccion'):
                self.on_deteccion()

        # Transición persecución → patrulla
        if self.persiguiendo and not ve_al_jugador:
            self.persiguiendo = False

        ahora          = pygame.time.get_ticks()
        cooldown_listo = (ahora - self.ultimo_ataque) >= self.cooldown_ataque

        # Atacar si está en rango de ataque y persiguiendo
        en_rango_ataque = self.persiguiendo and dist <= self.rango_ataque
        if en_rango_ataque and cooldown_listo and not self.atacando:
            self.atacando      = True
            self._frame_index  = 0
            self._update_time  = ahora
            self.ultimo_ataque = ahora

        delta_x = 0
        if not self.atacando:
            self.hitbox_ataque = None
            if self.persiguiendo:
                # Perseguir: moverse hacia el jugador
                self.flip = dx < 0
                delta_x   = -self.velocidad_persecucion if self.flip else self.velocidad_persecucion
            else:
                delta_x = self._calcular_patrulla(ex)
        else:
            if pygame.time.get_ticks() - self._update_time > self.COOLDOWN_ANIM:
                self._frame_index += 1
                self._update_time  = pygame.time.get_ticks()

            if self._frame_index >= self._num_frames_ataque:
                self.atacando      = False
                self.hitbox_ataque = None
                self._frame_index  = 0
            elif self.ataque_frame_inicio <= self._frame_index <= self.ataque_frame_fin:
                if self._frame_index == self.ataque_frame_inicio:
                    if not getattr(self, '_sonido_ataque_emitido', False):
                        self._sonido_ataque_emitido = True
                        if hasattr(self, 'on_ataque'):
                            self.on_ataque()
                self.hitbox_ataque = self._calcular_hitbox_ataque(ex, ey)
            else:
                self._sonido_ataque_emitido = False
                self.hitbox_ataque = None

        return delta_x, self.hitbox_ataque

    def _hay_pared_entre(self, pos_a, pos_b, tiles):
        if not tiles:
            return False
        ax, ay = pos_a
        bx, by = pos_b
        pasos  = max(abs(bx - ax), abs(by - ay)) // 8 + 1
        for i in range(1, pasos):
            t  = i / pasos
            px = int(ax + (bx - ax) * t)
            py = int(ay + (by - ay) * t)
            for tile in tiles:
                if tile.shape.collidepoint(px, py):
                    return True
        return False

    def _calcular_hitbox_ataque(self, ex, ey):
        ancho_hit  = Constantes.WIDTH_PERSONAJE * 4
        alto_hit   = int(Constantes.HEIGHT_PERSONAJE * 1.5)
        mitad_body = int(Constantes.WIDTH_PERSONAJE)
        x = (ex - mitad_body - ancho_hit) if self.flip else (ex + mitad_body)
        return pygame.Rect(x, ey - alto_hit // 2, ancho_hit, alto_hit)

    def obtener_estado(self, pos):
        return {
            'pos':                pos,
            'flip':               self.flip,
            'atacando':           self.atacando,
            'hitbox_ataque':      self.hitbox_ataque,
            'vivo':               self.vivo,
            'iframe_activo':      self.iframe_timer > 0,
            'persiguiendo':       self.persiguiendo,
            'exclamacion_nueva':  self._exclamacion_nueva,
        }
