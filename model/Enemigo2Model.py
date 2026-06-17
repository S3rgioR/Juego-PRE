"""Sub-modelo del Enemigo_2: patrullador volador con persecución y disparo."""

import math
import pygame
from .Actor import Actor
from .ProyectilModel import ProyectilModel


class Enemigo2Model(Actor):
    DISTANCIA_COMBATE = 200   # px — distancia que mantiene respecto al jugador

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

        # --- Persecución ---
        self.persiguiendo          = False
        self._exclamacion_nueva    = False
        self.velocidad_persecucion = 2

    # --- IA ---

    def tick_ia(self, pos_enemigo, pos_jugador, delta_time_ms, tiles_solidos=None):
        if not self.vivo:
            return 0, []

        self._tick_iframes(delta_time_ms)
        self._exclamacion_nueva = False

        ex, ey = pos_enemigo
        jx, jy = pos_jugador
        dist   = math.hypot(jx - ex, jy - ey)

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
        ahora  = pygame.time.get_ticks()
        if self.persiguiendo and (ahora - self.ultimo_disparo) >= self.cooldown_disparo:
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
