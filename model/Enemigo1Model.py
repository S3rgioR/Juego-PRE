"""Sub-modelo del Enemigo_1: patrullador terrestre.

Extiende Actor con IA de patrulla, detección visual del jugador
y ataque cuerpo a cuerpo con ventana de golpe por frames.
"""

import pygame
import Constantes
from .Actor import Actor


class Enemigo1Model(Actor):
    """Estado lógico del primer tipo de enemigo: patrullador terrestre.

    Attributes
    ----------
    velocidad : int
        Píxeles por frame de desplazamiento horizontal.
    patrol_min, patrol_max : int
        Límites de la zona de patrulla en coordenadas de mundo.
    rango_vision : int
        Distancia horizontal máxima de detección del jugador (px).
    cooldown_ataque : int
        Milisegundos mínimos entre ataques consecutivos.
    """

    COOLDOWN_ANIM = 200   # ms entre frames de la animación de ataque

    def __init__(self, x, y, distancia_patrulla=150, num_frames_ataque=6):
        super().__init__(hp=5, iframe_duracion=600)
        self.flip      = True
        self.velocidad = 2

        self.patrol_min = x - distancia_patrulla
        self.patrol_max = x + distancia_patrulla

        self.rango_vision    = 100
        self.cooldown_ataque = 1200
        self.ultimo_ataque   = -self.cooldown_ataque

        self._frame_index       = 0
        self._update_time       = pygame.time.get_ticks()
        self._num_frames_ataque = num_frames_ataque

        self.ataque_frame_inicio = 2
        self.ataque_frame_fin    = 5

    # --- IA ---

    def tick_ia(self, pos_enemigo, pos_jugador, delta_time_ms):
        """Avanza la lógica de IA para este frame.

        Devuelve las instrucciones de movimiento que la Vista debe aplicar.

        Parameters
        ----------
        pos_enemigo : tuple(int, int)
            Centro actual del sprite (lo conoce la Vista).
        pos_jugador : tuple(int, int)
            Centro actual del sprite del jugador.
        delta_time_ms : int
            Milisegundos desde el último frame.

        Returns
        -------
        delta_x : int
            Desplazamiento horizontal a aplicar este frame (0 si está atacando).
        hitbox_ataque : pygame.Rect or None
            Hitbox activa durante la ventana de golpe, o None.
        """
        if not self.vivo:
            return 0, None

        self._tick_iframes(delta_time_ms)

        ahora          = pygame.time.get_ticks()
        cooldown_listo = (ahora - self.ultimo_ataque) >= self.cooldown_ataque

        ex, ey = pos_enemigo
        jx, _  = pos_jugador
        dx     = jx - ex

        en_vision = (
            ((self.flip and dx < 0) or (not self.flip and dx > 0))
            and abs(dx) <= self.rango_vision
        )

        if en_vision and cooldown_listo and not self.atacando:
            self.atacando      = True
            self._frame_index  = 0
            self._update_time  = ahora
            self.ultimo_ataque = ahora

        delta_x = 0
        if not self.atacando:
            self.hitbox_ataque = None
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
                self.hitbox_ataque = self._calcular_hitbox_ataque(ex, ey)
            else:
                self.hitbox_ataque = None

        return delta_x, self.hitbox_ataque

    def _calcular_hitbox_ataque(self, ex, ey):
        ancho_hit  = Constantes.WIDTH_PERSONAJE * 4
        alto_hit   = int(Constantes.HEIGHT_PERSONAJE * 1.5)
        mitad_body = int(Constantes.WIDTH_PERSONAJE)
        x = (ex - mitad_body - ancho_hit) if self.flip else (ex + mitad_body)
        return pygame.Rect(x, ey - alto_hit // 2, ancho_hit, alto_hit)

    # --- Exportar estado ---

    def obtener_estado(self, pos):
        return {
            'pos':           pos,
            'flip':          self.flip,
            'atacando':      self.atacando,
            'hitbox_ataque': self.hitbox_ataque,
            'vivo':          self.vivo,
            'iframe_activo': self.iframe_timer > 0,
        }
