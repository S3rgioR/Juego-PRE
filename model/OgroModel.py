"""Sub-modelo del Enemigo_1: patrullador terrestre con persecución."""

import pygame
import Constantes
from .EnemigoModel import EnemigoModel
from .Event import Event


class OgroModel(EnemigoModel):
    """Patrullador terrestre con persecución y ataque cuerpo a cuerpo."""

    usa_gravedad = True
    COOLDOWN_ANIM = 200

    def __init__(self, x, y, distancia_patrulla=150, num_frames_ataque=6):
        super().__init__(
            x, hp=5, iframe_duracion=600,
            distancia_patrulla=distancia_patrulla,
            velocidad=2, rango_vision=250,
        )

        self.rango_ataque    = 100   # px — distancia a la que ataca
        self.cooldown_ataque = 2000
        self._timer_ataque   = 0   # ms restantes hasta poder atacar de nuevo

        self._frame_index       = 0
        self._anim_timer        = 0   # ms acumulados desde el último frame de ataque
        self._num_frames_ataque = num_frames_ataque

        self.ataque_frame_inicio = 2
        self.ataque_frame_fin    = 5

        self.velocidad_persecucion = 3       # px/frame al perseguir

        # Notificación de ataque: el Presenter se suscribe vía JuegoModel,
        # sin necesidad de importar Enemigo1Model directamente.
        self.evt_ataque = Event()

    # --- IA ---

    def tick_ia(self, pos_enemigo, pos_jugador, delta_time_ms, tiles_solidos=None):
        """Ejecuta un tick de IA.

        Parameters
        ----------
        pos_enemigo, pos_jugador : tuple of (float, float)
            Centros en coordenadas de mundo.
        delta_time_ms : int
        tiles_solidos : list of tuple, optional
            Bounding boxes puros (left, top, right, bottom) de los tiles
            sólidos, usados solo para el raycast de _hay_pared_entre.
            Nunca objetos de la Vista (p. ej. Plataforma).
        """
        if not self.vivo:
            return 0, None

        self._iniciar_tick_ia(delta_time_ms)

        if self._timer_ataque > 0:
            self._timer_ataque = max(0, self._timer_ataque - delta_time_ms)

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

        # Alerta por golpe: girar hacia el jugador y entrar en modo alerta.
        # Si el jugador está en otra plataforma muy por encima/debajo
        # (más de 16 px en Y), el golpe se ignora a efectos de persecución:
        # el enemigo terrestre no "detecta" a alguien fuera de su alcance
        # de altura, aunque lo haya golpeado (p. ej. con un proyectil/daga
        # lanzada desde arriba).
        if self._consumir_alerta() and abs(dy) <= 16:
            if not self.atacando:          # no interrumpir un ataque en curso
                self.flip = dx < 0
            if not self.persiguiendo:
                self._iniciar_persecucion()

        # Transición patrulla → persecución (detección visual frontal)
        if ve_al_jugador and not self.persiguiendo:
            self._iniciar_persecucion()

        # Transición persecución → patrulla:
        # En modo alerta conoce la posición del jugador aunque esté de espaldas,
        # pero deja de perseguir si el jugador se aleja más del rango de visión,
        # o si está en una plataforma a una altura (Y) muy distinta de la suya
        # (más de 16 px): aunque haya exclamación/alerta por golpe, un enemigo
        # terrestre no debería "ignorar la física" y perseguir a alguien que
        # está en otro nivel de plataforma fuera de su alcance.
        if self.persiguiendo and (dist > self.rango_vision or abs(dy) > 16):
            self.persiguiendo = False

        cooldown_listo = self._timer_ataque <= 0

        # Atacar si está en rango de ataque, persiguiendo Y cooldown listo
        en_rango_ataque = self.persiguiendo and dist <= self.rango_ataque
        if en_rango_ataque and cooldown_listo and not self.atacando:
            self.atacando      = True
            self._frame_index  = 0
            self._anim_timer   = 0
            self._timer_ataque = self.cooldown_ataque

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
            self._anim_timer += delta_time_ms
            if self._anim_timer > self.COOLDOWN_ANIM:
                self._frame_index += 1
                self._anim_timer   = 0

            if self._frame_index >= self._num_frames_ataque:
                self.atacando      = False
                self.hitbox_ataque = None
                self._frame_index  = 0
            elif self.ataque_frame_inicio <= self._frame_index <= self.ataque_frame_fin:
                if self._frame_index == self.ataque_frame_inicio:
                    if not getattr(self, '_sonido_ataque_emitido', False):
                        self._sonido_ataque_emitido = True
                        self.evt_ataque.emit()
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
