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
        self.cooldown_ataque = 2500
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
        self._alertado_por_golpe   = False   # True el frame en que recibe un golpe

    # --- IA ---

    def tick_ia(self, pos_enemigo, pos_jugador, delta_time_ms, tiles_solidos=None):
        if not self.vivo:
            return 0, None

        self._tick_iframes(delta_time_ms)
        self._exclamacion_nueva = False

        ex, ey = pos_enemigo
        jx, jy = pos_jugador
        dx     = jx - ex
        dy     = jy - ey
        dist   = abs(dx)

        # Detección visual: solo si el jugador está en el lado al que mira
        # y en una Y similar (mismo nivel de plataforma aprox.)
        jugador_en_frente  = (dx < 0) if self.flip else (dx > 0)
        mismo_nivel_y      = abs(dy) <= Constantes.HEIGHT_PERSONAJE * 4
        ve_al_jugador = (
            dist <= self.rango_vision
            and jugador_en_frente
            and mismo_nivel_y
            and not self._hay_pared_entre(pos_enemigo, pos_jugador, tiles_solidos)
        )

        # Alerta por golpe: girar hacia el jugador y entrar en modo alerta
        # NO se fuerza persiguiendo aquí — se gestiona abajo junto al resto
        if self._alertado_por_golpe:
            self._alertado_por_golpe = False
            if not self.atacando:          # no interrumpir un ataque en curso
                self.flip = dx < 0
            if not self.persiguiendo:
                self.persiguiendo       = True
                self._exclamacion_nueva = True
                if hasattr(self, 'on_deteccion'):
                    self.on_deteccion()

        # Transición patrulla → persecución (detección visual frontal)
        if ve_al_jugador and not self.persiguiendo:
            self.persiguiendo       = True
            self._exclamacion_nueva = True
            if hasattr(self, 'on_deteccion'):
                self.on_deteccion()

        # Transición persecución → patrulla:
        # En modo alerta conoce la posición del jugador aunque esté de espaldas,
        # pero deja de perseguir si el jugador se aleja más del rango de visión.
        if self.persiguiendo and dist > self.rango_vision:
            self.persiguiendo = False

        ahora          = pygame.time.get_ticks()
        cooldown_listo = (ahora - self.ultimo_ataque) >= self.cooldown_ataque

        # Atacar si está en rango de ataque, persiguiendo Y cooldown listo
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
                # En modo alerta siempre sabe dónde está el jugador: actualizar flip
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

    def recibir_daño(self, cantidad):
        """Marca el flag para que tick_ia gire y persiga al atacante."""
        ya_persiguiendo = self.persiguiendo
        super().recibir_daño(cantidad)
        if self.vivo and not ya_persiguiendo:
            self._alertado_por_golpe = True

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
