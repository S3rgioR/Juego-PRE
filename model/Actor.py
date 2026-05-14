"""Clase base Actor - Estado lógico común a toda entidad con vida.

Encapsula los atributos y comportamientos que comparten el jugador
y todos los tipos de enemigo: puntos de vida, invencibilidad temporal
(iframes), orientación y física vertical básica.

Las subclases añaden la lógica específica de cada rol
(control del jugador, IA de patrulla, disparo, etc.).
"""


class Actor:
    """Estado lógico común a toda entidad con vida del juego.

    Attributes
    ----------
    flip : bool
        True = mirando a la izquierda, False = a la derecha.
    hp : int
        Puntos de vida actuales.
    vivo : bool
        False cuando hp llega a 0.
    iframe_duracion : int
        Milisegundos de invencibilidad tras recibir daño.
    iframe_timer : int
        Milisegundos restantes de invencibilidad activa.
    velocidad_y : float
        Velocidad vertical actual. La Vista la aplica y la actualiza.
    en_suelo : bool
        True si la Vista ha notificado contacto con una superficie.
    atacando : bool
        True durante el transcurso de un ataque.
    hitbox_ataque : pygame.Rect or None
        Hitbox activa durante la ventana de golpe, o None.
    """

    def __init__(self, hp, iframe_duracion):
        self.flip            = False
        self.hp              = hp
        self.vivo            = True
        self.iframe_duracion = iframe_duracion
        self.iframe_timer    = 0

        self.velocidad_y = 0.0
        self.en_suelo    = False

        self.atacando      = False
        self.hitbox_ataque = None

    # --- Combate ---

    def recibir_daño(self, cantidad):
        """Aplica daño si el actor no está en iframes.

        Si los puntos de vida llegan a 0, marca al actor como muerto.

        Parameters
        ----------
        cantidad : int or float
            Puntos de daño a restar.
        """
        if not self.vivo or self.iframe_timer > 0:
            return
        self.hp -= cantidad
        self.iframe_timer = self.iframe_duracion
        if self.hp <= 0:
            self.hp   = 0
            self.vivo = False

    def _tick_iframes(self, delta_time_ms):
        """Descuenta el temporizador de iframes. Llamado por las subclases."""
        if self.iframe_timer > 0:
            self.iframe_timer -= delta_time_ms
            if self.iframe_timer < 0:
                self.iframe_timer = 0

    # --- Notificaciones de la Vista (física vertical) ---

    def notificar_en_suelo(self):
        """La Vista informa de que el actor ha aterrizado sobre una superficie."""
        self.en_suelo    = True
        self.velocidad_y = 0

    def notificar_golpe_techo(self):
        """La Vista informa de que el actor ha chocado con una superficie por encima."""
        self.velocidad_y = 0

    # --- Patrulla horizontal (compartida por los dos tipos de enemigo) ---

    def _calcular_patrulla(self, pos_x):
        """Devuelve el desplazamiento horizontal de patrulla para este frame.

        Invierte la dirección al alcanzar los límites de la zona asignada.
        Requiere que la subclase haya definido patrol_min, patrol_max y velocidad.

        Parameters
        ----------
        pos_x : int
            Posición horizontal actual del centro del sprite.

        Returns
        -------
        int
            Desplazamiento a aplicar (+velocidad o -velocidad).
        """
        if pos_x <= self.patrol_min:
            self.flip = False
        elif pos_x >= self.patrol_max:
            self.flip = True
        return -self.velocidad if self.flip else self.velocidad
