"""Sub-modelo del Enemigo_1: patrullador terrestre con persecución."""

import pygame
import Constantes
from .EnemigoModel import EnemigoModel


class Enemigo1Model(EnemigoModel):
    COOLDOWN_ANIM = 200

    def __init__(self, x, y, distancia_patrulla=150, num_frames_ataque=6):
        super().__init__(
            x, hp=5, iframe_duracion=600,
            distancia_patrulla=distancia_patrulla,
            velocidad=2, rango_vision=250,
        )

        self.rango_ataque    = 100   # px — distancia a la que ataca
        self.cooldown_ataque = 2000
        self.ultimo_ataque   = -self.cooldown_ataque

        self._frame_index       = 0
        self._update_time       = pygame.time.get_ticks()
        self._num_frames_ataque = num_frames_ataque

        self.ataque_frame_inicio = 2
        self.ataque_frame_fin    = 5

        self.velocidad_persecucion = 3       # px/frame al perseguir

    # --- IA ---

    def tick_ia(self, pos_enemigo, pos_jugador, delta_time_ms, tiles_solidos=None):
        if not self.vivo:
            return 0, None

        self._iniciar_tick_ia(delta_time_ms)

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
        if self._consumir_alerta():
            if not self.atacando:          # no interrumpir un ataque en curso
                self.flip = dx < 0
            if not self.persiguiendo:
                self._iniciar_persecucion()

        # Transición patrulla → persecución (detección visual frontal)
        if ve_al_jugador and not self.persiguiendo:
            self._iniciar_persecucion()

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
                # Solo avanzar si aún no ha llegado a la distancia de seguridad
                if dist > self.rango_ataque:
                    delta_x = -self.velocidad_persecucion if self.flip else self.velocidad_persecucion
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

    def _calcular_hitbox_ataque(self, ex, ey):
        ancho_hit  = Constantes.WIDTH_PERSONAJE * 4
        alto_hit   = int(Constantes.HEIGHT_PERSONAJE * 1.5)
        mitad_body = int(Constantes.WIDTH_PERSONAJE)
        # La hitbox cubre el arma (hacia delante) Y el propio cuerpo (hacia atrás),
        # para que el jugador no pueda golpear al enemigo "gratis" desde dentro
        # mientras el ataque está activo.
        ancho_total = ancho_hit + mitad_body * 2   # arma + cuerpo completo
        x = (ex - mitad_body - ancho_hit) if self.flip else (ex - mitad_body)
        return pygame.Rect(x, ey - alto_hit // 2, ancho_total, alto_hit)

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
