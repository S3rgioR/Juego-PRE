"""Sub-modelo del Enemigo_2: patrullador volador.

Extiende Actor con IA de patrulla aérea y disparo de proyectiles
dirigidos al jugador. No aplica gravedad ni necesita plataformas.
"""

import math
import pygame
from .Actor import Actor
from .ProyectilModel import ProyectilModel


class Enemigo2Model(Actor):
    """Estado lógico del segundo tipo de enemigo: patrullador volador.

    Attributes
    ----------
    velocidad : int
        Píxeles por frame de patrulla horizontal.
    patrol_min, patrol_max : int
        Límites de la zona de patrulla.
    rango_vision : int
        Distancia máxima de detección del jugador (px).
    cooldown_disparo : int
        Milisegundos mínimos entre disparos consecutivos.
    proyectiles : list of ProyectilModel
        Proyectiles activos disparados por este enemigo.
    """

    def __init__(self, x, y, distancia_patrulla=150):
        super().__init__(hp=3, iframe_duracion=600)
        self.flip      = True
        self.velocidad = 2

        self.patrol_min = x - distancia_patrulla
        self.patrol_max = x + distancia_patrulla

        self.rango_vision     = 450
        self.cooldown_disparo = 1000
        self.ultimo_disparo   = -2000
        self.proyectiles      = []

    # --- IA ---

    def tick_ia(self, pos_enemigo, pos_jugador, delta_time_ms):
        """Avanza la lógica de IA para este frame.

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
            Desplazamiento horizontal de patrulla.
        nuevos_proyectiles : list of ProyectilModel
            Proyectiles recién creados este frame (lista vacía si ninguno).
        """
        if not self.vivo:
            return 0, []

        self._tick_iframes(delta_time_ms)

        ex, ey = pos_enemigo
        jx, jy = pos_jugador


        delta_x   = self._calcular_patrulla(ex)
        en_vision = math.hypot(jx - ex, jy - ey) <= self.rango_vision

        nuevos = []
        ahora  = pygame.time.get_ticks()
        if en_vision and (ahora - self.ultimo_disparo) >= self.cooldown_disparo:
            p = ProyectilModel(ex, ey, jx, jy)
            self.proyectiles.append(p)
            nuevos.append(p)
            self.ultimo_disparo = ahora

            p = ProyectilModel(ex, ey, jx, jy)
            self.proyectiles.append(p)
            nuevos.append(p)

            if hasattr(self, 'on_disparo'):
                self.on_disparo()


        return delta_x, nuevos



    # --- Exportar estado ---

    def obtener_estado(self, pos):
        return {
            'pos':           pos,
            'flip':          self.flip,
            'atacando':      False,
            'hitbox_ataque': None,
            'vivo':          self.vivo,
            'iframe_activo': self.iframe_timer > 0,
            'proyectiles':   [p.obtener_estado() for p in self.proyectiles],
        }
