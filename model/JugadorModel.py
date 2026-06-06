"""Sub-modelo del jugador.

Extiende Actor con el control de entrada del jugador: salto con
coyote time, animación de ataque y lanzamiento de dagas.
"""

import pygame
import Constantes
from .Actor import Actor


class JugadorModel(Actor):
    """Estado lógico del jugador.

    Attributes
    ----------
    hp_max : int
        Vida máxima actual. Crece al recoger corazones.
    daga_desbloqueada : bool
        True después de recoger el objeto daga del suelo.
    proyectiles_daga : list of DagaProyectilModel
        Proyectiles de daga activos lanzados por el jugador.
    """

    HP_MAX_BASE      = 5
    COYOTE_TIME      = 300    # ms
    COOLDOWN_ANIM    = 70     # ms entre frames de animación de ataque
    COOLDOWN_DAGA_MS = 1500   # ms mínimos entre lanzamientos

    def __init__(self):
        self.hp_max = self.HP_MAX_BASE
        super().__init__(hp=self.hp_max, iframe_duracion=1000)
        self.flip         = False
        self.moviendose   = False
        self.coyote_timer = 0

        self._frame_index       = 0
        self._update_time       = 0
        self._num_frames_ataque = 4

        # Habilidad daga
        self.daga_desbloqueada  = False
        self.proyectiles_daga   = []
        self._ultimo_lanzamiento = -self.COOLDOWN_DAGA_MS   # listo desde el inicio

    # --- Acciones ---

    def iniciar_ataque(self, num_frames):
        if not self.atacando:
            self.atacando           = True
            self._frame_index       = 0
            self._num_frames_ataque = num_frames
            self._update_time       = pygame.time.get_ticks()

    def saltar(self):
        if self.en_suelo or self.coyote_timer > 0:
            self.velocidad_y  = Constantes.FUERZA_SALTO
            self.en_suelo     = False
            self.coyote_timer = 0

    def curar_completo(self):
        self.hp   = self.hp_max
        self.vivo = True

    def recoger_corazon(self):
        self.hp_max += 1
        self.hp      = min(self.hp + 1, self.hp_max)
        self.vivo    = True

    def desbloquear_daga(self):
        """Llamado al recoger el objeto daga del suelo."""
        self.daga_desbloqueada = True

    def lanzar_daga(self, pos_x: int, pos_y: int, flip: bool, frame_ref):
        """Crea un proyectil de daga si la habilidad está desbloqueada y el
        cooldown ha pasado.

        Parameters
        ----------
        pos_x, pos_y : int
            Centro del jugador en coordenadas de mundo.
        flip : bool
            Dirección que mira el jugador.
        frame_ref : pygame.Surface
            Frame de referencia para calcular el tamaño del proyectil.

        Returns
        -------
        DagaProyectilModel or None
            El proyectil creado, o None si no se puede lanzar.
        """
        if not self.daga_desbloqueada:
            return None

        ahora = pygame.time.get_ticks()
        if ahora - self._ultimo_lanzamiento < self.COOLDOWN_DAGA_MS:
            return None

        # Importación local para evitar ciclo de imports
        from .DagaProyectilModel import DagaProyectilModel

        proyectil = DagaProyectilModel(pos_x, pos_y, flip, frame_ref)
        self.proyectiles_daga.append(proyectil)
        self._ultimo_lanzamiento = ahora
        return proyectil

    # --- Notificaciones de la Vista ---

    def notificar_en_suelo(self):
        super().notificar_en_suelo()
        self.coyote_timer = self.COYOTE_TIME

    def notificar_en_aire(self, delta_time_ms):
        self.en_suelo      = False
        self.coyote_timer -= delta_time_ms
        if self.coyote_timer < 0:
            self.coyote_timer = 0

    # --- Tick interno ---

    def tick(self, delta_time_ms):
        self._tick_iframes(delta_time_ms)

        if self.atacando:
            if pygame.time.get_ticks() - self._update_time > self.COOLDOWN_ANIM:
                self._frame_index += 1
                self._update_time  = pygame.time.get_ticks()
            if self._frame_index >= self._num_frames_ataque:
                self.atacando     = False
                self._frame_index = 0

        # Mover proyectiles de daga y limpiar los muertos
        for p in self.proyectiles_daga:
            p.actualizar()
        self.proyectiles_daga = [p for p in self.proyectiles_daga if p.vivo]

    # --- Exportar estado ---

    def obtener_estado(self, pos, hitbox_ataque):
        return {
            'pos':                pos,
            'flip':               self.flip,
            'atacando':           self.atacando,
            'en_suelo':           self.en_suelo,
            'moviendose':         self.moviendose,
            'hitbox_ataque':      hitbox_ataque,
            'vivo':               self.vivo,
            'hp':                 self.hp,
            'hp_max':             self.hp_max,
            'iframe_activo':      self.iframe_timer > 0,
            'daga_desbloqueada':  self.daga_desbloqueada,
            'proyectiles_daga':   [p.obtener_estado()
                                   for p in self.proyectiles_daga],
            'cooldown_daga_listo': (
                pygame.time.get_ticks() - self._ultimo_lanzamiento
                >= self.COOLDOWN_DAGA_MS
            ),
        }
