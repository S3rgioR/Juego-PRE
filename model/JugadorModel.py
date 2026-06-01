"""Sub-modelo del jugador.

Extiende Actor con el control de entrada del jugador: salto con
coyote time y animación de ataque con contador de frames.
"""

import pygame
import Constantes
from .Actor import Actor



class JugadorModel(Actor):
    """Estado lógico del jugador.

    Attributes
    ----------
    moviendose : bool
        True si el jugador se desplaza horizontalmente este frame.
    coyote_timer : int
        Milisegundos restantes de margen para saltar tras caer del borde.
    """

    COYOTE_TIME   = 300   # ms de margen para saltar tras caer del borde
    COOLDOWN_ANIM = 70    # ms entre frames de la animación de ataque

    def __init__(self):
        super().__init__(hp=5, iframe_duracion=1000)
        self.flip         = False
        self.moviendose   = False
        self.coyote_timer = 0

        self._frame_index       = 0
        self._update_time       = 0
        self._num_frames_ataque = 4

    # --- Acciones (iniciadas por el Presenter) ---

    def iniciar_ataque(self, num_frames):
        """Inicia el ataque si no hay uno ya en curso."""
        if not self.atacando:
            self.atacando           = True
            self._frame_index       = 0
            self._num_frames_ataque = num_frames
            self._update_time       = pygame.time.get_ticks()

    def saltar(self):
        """Aplica velocidad de salto si el jugador está en suelo o en coyote time."""
        if self.en_suelo or self.coyote_timer > 0:
            self.velocidad_y  = Constantes.FUERZA_SALTO
            self.en_suelo     = False
            self.coyote_timer = 0

    # --- Notificaciones de la Vista ---

    def notificar_en_suelo(self):
        """Aterriza y recarga el coyote timer."""
        super().notificar_en_suelo()
        self.coyote_timer = self.COYOTE_TIME

    def notificar_en_aire(self, delta_time_ms):
        """La Vista informa de que el jugador no toca ninguna superficie."""
        self.en_suelo      = False
        self.coyote_timer -= delta_time_ms
        if self.coyote_timer < 0:
            self.coyote_timer = 0

    # --- Tick interno ---

    def tick(self, delta_time_ms):
        """Avanza el contador de iframes y la animación de ataque."""
        self._tick_iframes(delta_time_ms)

        if self.atacando:
            if pygame.time.get_ticks() - self._update_time > self.COOLDOWN_ANIM:
                self._frame_index += 1
                self._update_time  = pygame.time.get_ticks()
            if self._frame_index >= self._num_frames_ataque:
                self.atacando     = False
                self._frame_index = 0

    # --- Exportar estado ---

    def obtener_estado(self, pos, hitbox_ataque):
        """Devuelve el estado completo para que la Vista sincronice su sprite.

        Parameters
        ----------
        pos : tuple(int, int)
            Centro del sprite (lo conoce la Vista, no el Model).
        hitbox_ataque : pygame.Rect or None
            Calculada por la Vista a partir de la posición actual.
        """
        return {
            'pos':           pos,
            'flip':          self.flip,
            'atacando':      self.atacando,
            'en_suelo':      self.en_suelo,
            'moviendose':    self.moviendose,
            'hitbox_ataque': hitbox_ataque,
            'vivo':          self.vivo,
            'hp':            self.hp,
            'iframe_activo': self.iframe_timer > 0,
        }
