"""Sub-modelo del Enemigo_2: patrullador volador con persecución y disparo."""

import math
from .EnemigoModel import EnemigoModel
from .ProyectilModel import ProyectilModel
from .Event import Event


class FantasmaModel(EnemigoModel):
    """Patrullador volador con persecución y disparo a distancia."""

    usa_gravedad = False
    DISTANCIA_COMBATE = 200   # px — distancia que mantiene respecto al jugador

    def __init__(self, x, y, distancia_patrulla=150):
        super().__init__(
            x, hp=3, iframe_duracion=600,
            distancia_patrulla=distancia_patrulla,
            velocidad=2, rango_vision=450,
        )

        self.cooldown_disparo = 1000
        self._timer_disparo   = 0   # ms restantes hasta poder disparar de nuevo
        self.proyectiles      = []

        self.velocidad_persecucion = 2

        # Notificación de disparo: el Presenter se suscribe vía JuegoModel
        # (evt_enemigo_disparo), sin necesidad de importar Enemigo2Model
        # directamente. Único canal de notificación de disparo.
        self.evt_disparo = Event()

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
            return 0, []

        self._iniciar_tick_ia(delta_time_ms)

        if self._timer_disparo > 0:
            self._timer_disparo = max(0, self._timer_disparo - delta_time_ms)

        ex, ey = pos_enemigo
        jx, jy = pos_jugador
        dist   = math.hypot(jx - ex, jy - ey)

        # Detección visual: solo si el jugador está en el lado al que mira
        jugador_en_frente = (jx - ex < 0) if self.flip else (jx - ex > 0)
        ve_al_jugador = (
            dist <= self.rango_vision
            and jugador_en_frente
            and not self._hay_pared_entre(pos_enemigo, pos_jugador, tiles_solidos)
        )

        # Alerta por golpe: girar hacia el jugador y entrar en modo alerta
        if self._consumir_alerta():
            self.flip = (jx - ex) < 0
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

        # Movimiento
        delta_x = 0
        if self.persiguiendo:
            dx = jx - ex
            self.flip = dx < 0
            if dist > self.DISTANCIA_COMBATE:
                # Acercarse al jugador
                angulo  = math.atan2(jy - ey, jx - ex)
                delta_x = int(math.cos(angulo) * self.velocidad_persecucion)
            elif dist < self.DISTANCIA_COMBATE * 0.7:
                # Alejarse un poco si está demasiado cerca
                angulo  = math.atan2(jy - ey, jx - ex)
                delta_x = -int(math.cos(angulo) * self.velocidad_persecucion)
            # En la banda de combate: no moverse horizontalmente
        else:
            delta_x = self._calcular_patrulla(ex)

        # Disparar solo si persigue y tiene visión
        nuevos = []
        if self.persiguiendo and self._timer_disparo <= 0:
            p = ProyectilModel(ex, ey, jx, jy)
            self.proyectiles.append(p)
            nuevos.append(p)
            self._timer_disparo = self.cooldown_disparo

            p = ProyectilModel(ex, ey, jx, jy)
            self.proyectiles.append(p)
            nuevos.append(p)

            self.evt_disparo.emit()

        return delta_x, nuevos

    def obtener_estado(self, pos):
        return {
            'pos':               pos,
            'flip':              self.flip,
            'atacando':          False,
            'hitbox_ataque':     None,
            'vivo':              self.vivo,
            'iframe_activo':     self.iframe_timer > 0,
            'proyectiles':       [p.obtener_estado() for p in self.proyectiles],
            'persiguiendo':      self.persiguiendo,
            'exclamacion_nueva': self._exclamacion_nueva,
        }
