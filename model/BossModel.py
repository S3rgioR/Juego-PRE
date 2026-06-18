"""Sub-modelo del Boss: cráneo de fuego volador.

FASE 1  (hp > HP_MAX / 2)
    Ataques : Rayo (ráfaga 10 proyectiles) | Cruz (X) diagonal
FASE 2  (hp <= HP_MAX / 2)
    Ataques : Cruz (X) | Tracking (4 proyectiles que siguen al jugador)
            | Embestida

Embestida:
    1. embestida_bajar  → baja al suelo, frame congelado en 4, rojo, invulnerable
    2. embestida_cargar → fija pos jugador, se lanza hacia allí con overshoot
    3. embestida_pasar  → pausa breve inmóvil
    4. embestida_subir  → vuelve a la altura de vuelo original, pierde rojo
"""

import math
import random
import pygame
import Constantes
from model.Actor         import Actor
from model.ProyectilModel import ProyectilModel


# ---------------------------------------------------------------------------
# Proyectil extendido
# ---------------------------------------------------------------------------

class ProyectilBoss(ProyectilModel):
    """Proyectil del boss con tamaño variable y seguimiento opcional."""

    def __init__(self, x, y, target_x, target_y,
                 escala=1.0, velocidad=4.0, tracking=False, daño=1.5):
        super().__init__(x, y, target_x, target_y)

        dx   = target_x - x
        dy   = target_y - y
        dist = math.hypot(dx, dy) or 1
        self.vel_x = (dx / dist) * velocidad
        self.vel_y = (dy / dist) * velocidad

        w = int(Constantes.WIDTH_PERSONAJE  * 0.8 * escala)
        h = int(Constantes.HEIGHT_PERSONAJE * 0.8 * escala)
        centro = self.shape.center
        self.shape = pygame.Rect(0, 0, w, h)
        self.shape.center = centro
        self._x = float(centro[0])
        self._y = float(centro[1])

        self.tracking  = tracking
        self.daño      = daño
        self.escala    = escala
        self.velocidad = velocidad

    def actualizar_tracking(self, target_x, target_y):
        if not self.vivo or not self.tracking:
            return
        dx   = target_x - self.shape.centerx
        dy   = target_y - self.shape.centery
        dist = math.hypot(dx, dy) or 1
        nx = (dx / dist) * self.velocidad
        ny = (dy / dist) * self.velocidad
        self.vel_x += (nx - self.vel_x) * 0.10
        self.vel_y += (ny - self.vel_y) * 0.10
        self.flip  = self.vel_x < 0

    def obtener_estado(self):
        estado = super().obtener_estado()
        estado['escala']   = self.escala
        estado['tracking'] = self.tracking
        return estado


# ---------------------------------------------------------------------------
# BossModel
# ---------------------------------------------------------------------------

class BossModel(Actor):

    on_disparo = staticmethod(lambda: None)  # sobreescrito por el Presenter si hay audio

    HP_MAX = 16

    # Distancias / velocidades
    DIST_ATAQUE       = 350   # px horizontal para empezar a atacar
    VEL_ACERCAMIENTO  = 3   # px/frame
    Y_SUELO           = 610   # y del suelo donde aterriza durante embestida

    # Cooldowns de ataque (ms)  — más cortos para que ataque con frecuencia
    CD_RAYO      = 3000
    CD_X         = 3000
    CD_MAS       = 3000
    CD_TRACKING  = 4000
    CD_EMBESTIDA = 10000

    # Cooldown de descanso tras cada ataque (ms)
    CD_DESCANSO = 1200

    # Rayo
    RAYO_NUM   = 10
    RAYO_DELAY = 80   # ms entre proyectiles de la ráfaga
    TRACKING_DELAY_MS = 1000

    # Embestida
    VEL_BAJAR      = 5
    VEL_EMBESTIDA  = 11
    OVERSHOOT_PX   = 130
    VEL_SUBIR      = 3
    PAUSA_PASAR_MS = 350   # tiempo inmóvil tras pasarse

    def __init__(self, x, y):
        super().__init__(hp=self.HP_MAX, iframe_duracion=500)

        self._x = float(x)
        self._y = float(y)
        self._y_vuelo = float(y)   # altura de vuelo → se restaura al subir

        self.shape = pygame.Rect(
            0, 0,
            int(Constantes.WIDTH_PERSONAJE  * 3),
            int(Constantes.HEIGHT_PERSONAJE * 1.5),
        )
        self.shape.midbottom = (int(self._x), int(self._y))

        self.fase        = 1
        self.proyectiles = []

        # --- Máquina de estados ---
        # Estados: 'acercarse' | 'descanso' | 'atacar_rayo' | 'atacar_x' |
        #          'atacar_tracking' | 'embestida_bajar' | 'embestida_cargar' |
        #          'embestida_pasar' | 'embestida_subir'
        self.estado_ia = 'acercarse'

        # Temporizador genérico (descanso / pausa embestida)
        self._timer_estado = 0

        # Cooldowns individuales: inicializados en negativo para que el boss
        # pueda atacar en cuanto llegue al rango.
        ahora = pygame.time.get_ticks()
        self._t_rayo      = ahora - self.CD_RAYO
        self._t_x         = ahora - self.CD_X
        self._t_mas = ahora - self.CD_MAS
        self._t_tracking  = ahora - self.CD_TRACKING
        self._t_embestida = ahora - self.CD_EMBESTIDA

        # Ráfaga del rayo
        self._rayo_pendiente = 0
        self._rayo_timer     = 0
        self._rayo_target    = (0, 0)

        # Embestida
        self._embestida_dir       = 1
        self._embestida_objetivo  = 0.0   # x destino con overshoot

        # Flags visuales
        self.embestida_activa  = False
        self._frame_congelado  = False

        # Caché de la última posición conocida del jugador
        self._last_jpos = (float(x) + 300, float(y))

        self._tracking_pendiente = 0
        self._tracking_timer = 0
        self._tracking_target = (0, 0)
        TRACKING_DELAY_MS = 2500  # ms entre el primer y segundo proyectil

    # -----------------------------------------------------------------------
    # Propiedades
    # -----------------------------------------------------------------------

    @property
    def en_fase2(self):
        return self.hp <= self.HP_MAX // 2

    # -----------------------------------------------------------------------
    # Tick principal
    # -----------------------------------------------------------------------

    def tick_ia(self, pos_boss, pos_jugador, delta_time_ms):
        """Avanza la IA del boss un frame.

        Returns (delta_x, delta_y, nuevos_proyectiles).
        """
        if not self.vivo:
            return 0.0, 0.0, []

        self._tick_iframes(delta_time_ms)

        # Actualizar fase
        if self.en_fase2 and self.fase == 1:
            self.fase = 2

        # Sincronizar posición interna
        self._x = float(pos_boss[0])
        self._y = float(pos_boss[1])

        # Guardar última posición del jugador
        self._last_jpos = pos_jugador
        jx, jy = pos_jugador

        # Orientación
        self.flip = jx < self._x

        ahora  = pygame.time.get_ticks()
        nuevos = []

        # --- Avanzar ráfaga de rayo pendiente ---
        if self._rayo_pendiente > 0:
            self._rayo_timer -= delta_time_ms
            if self._rayo_timer <= 0:
                p = ProyectilBoss(
                    self._x, self._y,
                    self._rayo_target[0], self._rayo_target[1],
                    escala=1.0, velocidad=5.0, tracking=False, daño=1.0,
                )
                self.proyectiles.append(p)
                nuevos.append(p)
                self._rayo_pendiente -= 1
                self._rayo_timer      = self.RAYO_DELAY

        if self._tracking_pendiente > 0:
            self._tracking_timer -= delta_time_ms
            if self._tracking_timer <= 0:
                p = ProyectilBoss(
                    self._x, self._y,
                    self._tracking_target[0], self._tracking_target[1],
                    escala=2.0, velocidad=3.5, tracking=True, daño=1.5,
                )
                self.proyectiles.append(p)
                nuevos.append(p)
                self._tracking_pendiente -= 1
                self._tracking_timer = self.TRACKING_DELAY_MS
        # --- Tracking de proyectiles en vuelo ---
        for p in self.proyectiles:
            if isinstance(p, ProyectilBoss) and p.tracking and p.vivo:
                p.actualizar_tracking(jx, jy)

        # --- Máquina de estados ---
        delta_x, delta_y = 0.0, 0.0

        if self.estado_ia == 'acercarse':
            delta_x, delta_y = self._tick_acercarse(jx, jy)
            if abs(jx - self._x) <= self.DIST_ATAQUE:
                # En rango: pasar directamente a elegir ataque
                siguiente = self._elegir_ataque(ahora)
                self._iniciar_estado(siguiente, ahora, jx, jy)


        elif self.estado_ia == 'descanso':
            self._timer_estado -= delta_time_ms
            dx_abs = abs(jx - self._x)
            if dx_abs > 60:  # zona muerta: no seguir si está muy cerca en X
                dir_x = 1.0 if jx > self._x else -1.0
                delta_x = dir_x * self.VEL_ACERCAMIENTO
            if self._timer_estado <= 0:
                if abs(jx - self._x) <= self.DIST_ATAQUE:
                    siguiente = self._elegir_ataque(ahora)
                    self._iniciar_estado(siguiente, ahora, jx, jy)
                else:
                    self.estado_ia = 'acercarse'

        elif self.estado_ia == 'atacar_rayo':
            delta_x = self._acercarse_suave(jx)
            # Esperar a que termine la ráfaga
            if self._rayo_pendiente == 0:
                self._t_rayo = ahora
                self._pasar_a_descanso()

        elif self.estado_ia == 'atacar_x':
            delta_x = self._acercarse_suave(jx)
            # El lanzamiento ya se hizo en _iniciar_estado
            self._t_x = ahora
            self._pasar_a_descanso()

        elif self.estado_ia == 'atacar_mas':
            delta_x = self._acercarse_suave(jx)
            self._pasar_a_descanso()

        elif self.estado_ia == 'atacar_tracking':
            delta_x = self._acercarse_suave(jx)
            # El lanzamiento ya se hizo en _iniciar_estado
            if self._tracking_pendiente == 0:   # los 2 disparados
                self._t_tracking = ahora
                self._pasar_a_descanso()

        # ---- EMBESTIDA ----

        elif self.estado_ia == 'embestida_bajar':
            # Bajar verticalmente hacia el suelo
            delta_y = self.VEL_BAJAR
            delta_x = self._acercarse_suave(jx)
            if self._y >= self.Y_SUELO:
                # Llegó al suelo → fijar posición del jugador y cargar
                self._y = float(self.Y_SUELO)
                target_x = float(jx)
                self._embestida_dir      = 1 if target_x >= self._x else -1
                self._embestida_objetivo = target_x + self._embestida_dir * self.OVERSHOOT_PX
                self.estado_ia = 'embestida_cargar'

        elif self.estado_ia == 'embestida_cargar':
            delta_x = self._embestida_dir * self.VEL_EMBESTIDA
            # ¿Pasamos el objetivo?
            pasado = (
                (self._embestida_dir > 0 and self._x >= self._embestida_objetivo) or
                (self._embestida_dir < 0 and self._x <= self._embestida_objetivo)
            )
            if pasado:
                self._frame_congelado = False
                self._timer_estado    = self.PAUSA_PASAR_MS
                self.estado_ia        = 'embestida_pasar'

        elif self.estado_ia == 'embestida_pasar':
            # Pausa inmóvil breve
            self._timer_estado -= delta_time_ms
            if self._timer_estado <= 0:
                self.embestida_activa = False
                self.estado_ia = 'embestida_subir'

        elif self.estado_ia == 'embestida_subir':
            delta_y = -self.VEL_SUBIR
            if self._y <= self._y_vuelo:
                self._y = self._y_vuelo
                self._t_embestida = ahora
                self._pasar_a_descanso()

        # Limpiar proyectiles muertos
        self.proyectiles = [p for p in self.proyectiles if p.vivo]

        return delta_x, delta_y, nuevos

    # -----------------------------------------------------------------------
    # Helpers de movimiento
    # -----------------------------------------------------------------------

    def _tick_acercarse(self, jx, jy):
        dx_abs = abs(jx - self._x)
        if dx_abs > self.DIST_ATAQUE:
            dir_x = 1.0 if jx > self._x else -1.0
            vel   = min(self.VEL_ACERCAMIENTO, dx_abs)
            return dir_x * vel, 0.0
        return 0.0, 0.0

    def _acercarse_suave(self, jx):
        """Movimiento suave para no alejarse durante ataques/descanso."""
        dx   = jx - self._x
        dist = abs(dx)
        if dist > self.DIST_ATAQUE:
            return math.copysign(2.0, dx)
        return 0.0

    def _pasar_a_descanso(self):
        self._timer_estado = self.CD_DESCANSO
        self.estado_ia     = 'descanso'

    # -----------------------------------------------------------------------
    # Selección aleatoria de ataque
    # -----------------------------------------------------------------------

    def _elegir_ataque(self, ahora):
        """Elige aleatoriamente entre los ataques cuyo cooldown ha expirado."""
        opciones = []
        if self.fase == 1:
            if (ahora - self._t_rayo) >= self.CD_RAYO:
                opciones.append('atacar_rayo')
            if (ahora - self._t_x) >= self.CD_X:
                opciones.append('atacar_x')
            if (ahora - self._t_mas) >= self.CD_MAS:
                    opciones.append('atacar_mas')
        else:
            if (ahora - self._t_x) >= self.CD_X:
                opciones.append('atacar_x')
            if (ahora - self._t_mas) >= self.CD_MAS:
                opciones.append('atacar_mas')
            if (ahora - self._t_tracking) >= self.CD_TRACKING:
                opciones.append('atacar_tracking')
            if (ahora - self._t_embestida) >= self.CD_EMBESTIDA:
                opciones.append('embestida_bajar')

        if not opciones:
            # Ningún ataque disponible → descanso breve y reintentar
            return 'descanso'

        return random.choice(opciones)

    def _iniciar_estado(self, estado, ahora, jx, jy):
        """Prepara el estado elegido y lanza proyectiles si procede."""
        self.estado_ia = estado

        if estado == 'atacar_rayo':
            # Fijar objetivo del rayo en la posición actual del jugador
            self._rayo_pendiente = self.RAYO_NUM
            self._rayo_timer     = 0
            self._rayo_target    = (jx, jy)
            self.on_disparo()

        elif estado == 'atacar_x':
            nuevos = self._lanzar_x(self._x, self._y, jx, jy)
            self.proyectiles.extend(nuevos)
            # Transición inmediata a descanso (los proyectiles ya están creados)
            self._t_x = ahora
            self.on_disparo()

        elif estado == 'atacar_mas':
            nuevos = self._lanzar_mas(self._x, self._y, jx, jy)
            self.proyectiles.extend(nuevos)
            self._t_mas = ahora
            self.on_disparo()

        elif estado == 'atacar_tracking':

            self._tracking_pendiente = 2
            self._tracking_timer = 0
            self._tracking_target = (jx, jy)



        elif estado == 'embestida_bajar':
            self.embestida_activa = True
            self._frame_congelado = True
            # _y_vuelo ya guardado en __init__ y permanece constante

        elif estado == 'descanso':
            # Descanso mínimo antes de reintentar
            self._timer_estado = 600

    # -----------------------------------------------------------------------
    # Ataques
    # -----------------------------------------------------------------------

    def _lanzar_x(self, ex, ey, jx, jy):
        diagonales = [(1,-1),(1,1),(-1,-1),(-1,1)]
        return [
            ProyectilBoss(ex, ey, ex + dx*100, ey + dy*100,
                          escala=2.0, velocidad=4.5, tracking=False, daño=1.5)
            for dx, dy in diagonales
        ]

    def _lanzar_mas(self, ex, ey, jx, jy):
        direcciones = [(1, 0), (-1, 0), (0, -1), (0, 1)]
        return [
            ProyectilBoss(ex, ey, ex + dx * 100, ey + dy * 100,
                          escala=2.0, velocidad=4.5, tracking=False, daño=1.5)
            for dx, dy in direcciones
        ]
    def _lanzar_tracking(self, ex, ey, jx, jy):
        offsets = [(-20, 0), (20, 0)]  # solo 2 proyectiles
        return [
            ProyectilBoss(ex, ey, jx + ox, jy + oy,
                          escala=2.0, velocidad=3.5, tracking=True, daño=1.5)
            for ox, oy in offsets
        ]

    # -----------------------------------------------------------------------
    # recibir_daño: bloqueado durante la embestida
    # -----------------------------------------------------------------------

    def recibir_daño(self, cantidad):
        if self.embestida_activa:
            return
        super().recibir_daño(cantidad)

    # -----------------------------------------------------------------------
    # Exportar estado para la Vista
    # -----------------------------------------------------------------------

    def obtener_estado(self, pos):
        return {
            'pos':              pos,
            'flip':             self.flip,
            'atacando':         False,
            'hitbox_ataque':    None,
            'vivo':             self.vivo,
            'iframe_activo':    self.iframe_timer > 0 and not self.embestida_activa,
            'embestida_activa': self.embestida_activa,
            'frame_congelado':  self._frame_congelado,
            'fase':             self.fase,
            'hp':               self.hp,
            'hp_max':           self.HP_MAX,
            'proyectiles':      [p.obtener_estado() for p in self.proyectiles],
        }

    # -----------------------------------------------------------------------
    # Guardado / Carga
    # -----------------------------------------------------------------------

    def obtener_estado_guardado(self):
        return {'boss_hp': self.hp, 'boss_fase': self.fase}

    def cargar_estado_guardado(self, datos):
        if 'boss_hp' in datos:
            self.hp   = max(1, int(datos['boss_hp']))
            self.vivo = self.hp > 0
            self.fase = 2 if self.en_fase2 else 1
