"""Capa Model del patrón MVP - Estado y lógica del juego.

Responsabilidades:
- Estado del jugador (posición, velocidad, hp, animación lógica)
- Estado de los enemigos (patrulla, visión, ataque, hp)
- Física (gravedad, colisiones con plataformas)
- Combate (detección de golpes entre hitboxes)

Lo que NO hace el Model:
- Dibujar nada (ni un pixel)
- Conocer pygame salvo para pygame.Rect (estructura geométrica)
- Gestionar eventos de teclado
- Gestionar la cámara

El Model expone su estado mediante `obtener_estado_jugador()` y
`obtener_estados_enemigos()`, que devuelven dicts que la Vista
usa para sincronizar sus sprites.
"""

import pygame
import Constantes


# ---------------------------------------------------------------------------
# Sub-modelo: Jugador
# ---------------------------------------------------------------------------

class JugadorModel:
    """Estado y física del jugador.

    Attributes
    ----------
    shape : pygame.Rect
        Hitbox en coordenadas de mundo (fuente de verdad geométrica).
    velocidad_y : float
        Velocidad vertical actual. Positiva = cayendo.
    en_suelo : bool
        True si el jugador está apoyado sobre algo.
    flip : bool
        True = mirando a la izquierda.
    moviendose : bool
        True si el jugador se está moviendo horizontalmente este frame.
    atacando : bool
        True durante el transcurso de un ataque.
    hitbox_ataque : pygame.Rect or None
        Hitbox de ataque activa, o None.
    coyote_timer : int
        Milisegundos restantes de coyote time (permite saltar tras caer del borde).
    hp : int
        Puntos de vida actuales.
    vivo : bool
        False cuando hp llega a 0.
    _frame_index : int
        Frame actual de la animación (gestionado aquí para saber cuándo termina el ataque).
    _update_time : int
        Timestamp del último cambio de frame.
    """

    COYOTE_TIME = 300      # ms de margen para saltar tras caer del borde
    COOLDOWN_ANIM = 70     # ms entre frames de animación

    def __init__(self, x, y):
        self.shape = pygame.Rect(
            0, 0,
            Constantes.WIDTH_PERSONAJE,
            Constantes.HEIGHT_PERSONAJE
        )
        self.shape.center = (x, y)
        self._y = float(self.shape.y)  # acumulador float para evitar truncado

        self.velocidad_y   = 0
        self.en_suelo      = False
        self.flip          = False
        self.moviendose    = False
        self.atacando      = False
        self.hitbox_ataque = None

        self.coyote_time = 300
        self.coyote_timer = 0
        self.hp   = 5
        self.vivo = True

        # Para saber cuándo termina la animación de ataque
        self._frame_index  = 0
        self._update_time  = pygame.time.get_ticks()
        self._num_frames_ataque = 4   # se actualiza cuando el Presenter informa

        self.iframe_duracion = 1000  # ms de invencibilidad tras recibir golpe
        self.iframe_timer = 0  # ms restantes de invencibilidad
    # --- Acciones (llamadas por el Presenter) ---

    def iniciar_ataque(self, num_frames):
        """Inicia el ataque si no hay uno en curso.

        Parameters
        ----------
        num_frames : int
            Número de frames de la animación de ataque (para saber cuándo termina).
        """
        if not self.atacando:
            self.atacando = True
            self._frame_index = 0
            self._num_frames_ataque = num_frames
            self._update_time = pygame.time.get_ticks()

    def saltar(self):
        """Aplica velocidad de salto si está en suelo o en coyote time."""
        if self.en_suelo or self.coyote_timer > 0:
            self.velocidad_y  = Constantes.FUERZA_SALTO
            self.en_suelo     = False
            self.coyote_timer = 0

    def recibir_daño(self, daño):
        if not self.vivo or self.iframe_timer > 0:  # ← ignorar si hay iframes
            return
        self.hp -= daño
        self.iframe_timer = self.iframe_duracion  # ← activar invencibilidad
        if self.hp <= 0:
            self.hp = 0
            self.vivo = False

    # --- Física (llamada cada frame por el Model principal) ---

    def actualizar(self, delta_x, plataformas, delta_time_ms):
        """Aplica movimiento, física y colisiones para este frame.

        Parameters
        ----------
        delta_x : int
            Desplazamiento horizontal solicitado (-VELOCIDAD, 0 o +VELOCIDAD).
        plataformas : list of Plataforma
            Lista de plataformas con su shape (pygame.Rect).
        delta_time_ms : int
            Milisegundos transcurridos desde el último frame (para coyote time).
        """
        # --- Dirección ---
        if delta_x < 0:
            self.flip = True
            self.moviendose = True
        elif delta_x > 0:
            self.flip = False
            self.moviendose = True
        else:
            self.moviendose = False

        # --- Movimiento horizontal + colisiones ---
        self.shape.x += delta_x
        for plat in plataformas:
            if self.shape.colliderect(plat.shape):
                if delta_x > 0:
                    self.shape.right = plat.shape.left
                elif delta_x < 0:
                    self.shape.left = plat.shape.right
        if self.iframe_timer > 0:
            self.iframe_timer -= delta_time_ms
        # --- Gravedad (ANTES del movimiento vertical) ---
        # Aplicarla aqui garantiza que cuando la colision resetea velocidad_y=0,
        # ese 0 es el valor que exporta obtener_estado() este mismo frame.
        # Si se aplicara despues, el personaje saldria con vel_y=0.6 aunque
        # este en suelo, haciendo parpadear la animacion entre Parado y Saltando.
        self.velocidad_y += Constantes.GRAVEDAD
        if self.velocidad_y > Constantes.VELOCIDAD_MAX_CAIDA:
            self.velocidad_y = Constantes.VELOCIDAD_MAX_CAIDA

        # --- Movimiento vertical + colisiones ---
        # Bug sin este fix: pygame.colliderect solo detecta solapamiento
        # real (bottom > top), nunca contacto (bottom == top).
        # Con int(vel_y=0.6)=0 el personaje no baja → no solapa → en_suelo=False
        # Alternando frames: un frame toca sin solapar, el siguiente solapa.
        # Resultado: parpadeo entre sprite de suelo y sprite de salto.
        # Fix: acumular en float (_y) y forzar +1 pixel en el test,
        # luego recolocar exactamente encima si hay colisión.
        self.en_suelo = False
        self._y += self.velocidad_y
        self.shape.y = int(self._y) + 1  # +1 fuerza solapamiento en colliderect

        for plat in plataformas:
            if self.shape.colliderect(plat.shape):
                if self.velocidad_y >= 0:  # cayendo o en reposo
                    self.shape.bottom = plat.shape.top
                    self._y = float(self.shape.y)  # resync sin el +1
                    self.velocidad_y  = 0
                    self.en_suelo     = True
                elif self.velocidad_y < 0:
                    self.shape.top   = plat.shape.bottom
                    self._y = float(self.shape.y)
                    self.velocidad_y = 0

        # --- Coyote time ---
        if self.en_suelo:
            self.coyote_timer = self.COYOTE_TIME
        else:
            self.coyote_timer -= delta_time_ms
            if self.coyote_timer < 0:
                self.coyote_timer = 0

        # --- Fin del ataque (basado en frames de animación) ---
        if self.atacando:
            if pygame.time.get_ticks() - self._update_time > self.COOLDOWN_ANIM:
                self._frame_index += 1
                self._update_time = pygame.time.get_ticks()
            if self._frame_index >= self._num_frames_ataque:
                self.atacando      = False
                self.hitbox_ataque = None
                self._frame_index  = 0

        # --- Hitbox de ataque ---
        if self.atacando:
            self.hitbox_ataque = self._calcular_hitbox_ataque()

        # --- Límites de pantalla ---
        if self.shape.bottom >= Constantes.HEIGHT:
            self.shape.bottom = Constantes.HEIGHT
            self._y = float(self.shape.y)
            self.velocidad_y  = 0
            self.en_suelo     = True
        if self.shape.top < 0:
            self.shape.top   = 0
            self._y = float(self.shape.y)
            self.velocidad_y = 0

    def _calcular_hitbox_ataque(self):
        ancho_hit = Constantes.WIDTH_PERSONAJE * 3
        if self.flip:
            x = self.shape.left - ancho_hit
        else:
            x = self.shape.right
        return pygame.Rect(x, self.shape.top, ancho_hit, self.shape.height)

    def obtener_estado(self):
        """Devuelve un dict con el estado lógico para que la Vista sincronice su sprite.

        Returns
        -------
        dict
            Claves: 'pos', 'flip', 'atacando', 'en_suelo', 'moviendose',
                    'hitbox_ataque', 'vivo', 'hp'.
        """
        return {
            'pos':          self.shape.center,
            'flip':         self.flip,
            'atacando':     self.atacando,
            'en_suelo':     self.en_suelo,
            'moviendose':   self.moviendose,
            'hitbox_ataque': self.hitbox_ataque,
            'vivo':         self.vivo,
            'hp':           self.hp,
        }


# ---------------------------------------------------------------------------
# Sub-modelo: Enemigo_1
# ---------------------------------------------------------------------------

class Enemigo1Model:
    """Estado y física del primer tipo de enemigo.

    Attributes
    ----------
    shape : pygame.Rect
        Hitbox en coordenadas de mundo.
    velocidad_y : float
        Velocidad vertical actual.
    en_suelo : bool
        True si está apoyado sobre una plataforma.
    flip : bool
        True = mirando a la izquierda.
    velocidad : int
        Velocidad horizontal de patrulla.
    patrol_min, patrol_max : int
        Límites horizontales de la patrulla.
    hp : int
        Puntos de vida.
    vivo : bool
        False cuando hp llega a 0.
    atacando : bool
        True durante el ataque.
    hitbox_ataque : pygame.Rect or None
        Hitbox de ataque activa.
    rango_vision : int
        Distancia máxima de detección del jugador (px).
    cooldown_ataque : int
        Milisegundos entre ataques.
    ultimo_ataque : int
        Timestamp del último ataque iniciado.
    _frame_index : int
        Frame actual (para saber cuándo termina la animación de ataque).
    _update_time : int
        Timestamp del último cambio de frame.
    _num_frames_ataque : int
        Número de frames de la animación de ataque.
    """

    COOLDOWN_ANIM = 200  # ms entre frames

    def __init__(self, x, y, distancia_patrulla=150, num_frames_ataque=6):
        self.shape = pygame.Rect(
            0, 0,
            int(Constantes.WIDTH_PERSONAJE * 2),
            int(Constantes.HEIGHT_PERSONAJE * 1.5)
        )
        self.shape.center = (x, y)

        self.velocidad_y = 0
        self.en_suelo    = False
        self.flip        = True

        self.velocidad    = 2
        self.patrol_min   = x - distancia_patrulla
        self.patrol_max   = x + distancia_patrulla

        self.hp   = 5
        self.vivo = True

        self.rango_vision    = 100
        self.atacando        = False
        self.hitbox_ataque   = None
        self.cooldown_ataque = 1200
        self.ultimo_ataque   = -self.cooldown_ataque  # listo desde el inicio

        self._frame_index        = 0
        self._update_time        = pygame.time.get_ticks()
        self._num_frames_ataque  = num_frames_ataque

        self.ataque_frame_inicio = 2  # frame en que aparece la hitbox
        self.ataque_frame_fin = 5  # frame en que desaparece

        self.iframe_duracion = 600  # ms de invencibilidad tras recibir golpe
        self.iframe_timer = 0  # ms restantes de invencibilidad

    def recibir_daño(self, daño):
        """Reduce hp. Ignora el golpe si hay iframes activos."""
        if not self.vivo or self.iframe_timer > 0:
            return
        self.hp -= daño
        self.iframe_timer = self.iframe_duracion
        if self.hp <= 0:
            self.hp = 0
            self.vivo = False

    def actualizar(self, plataformas, jugador_model, delta_time_ms=16):
        """Actualiza el estado del enemigo para este frame."""
        if not self.vivo:
            return

        # Descontar iframe timer
        if self.iframe_timer > 0:
            self.iframe_timer -= delta_time_ms
            if self.iframe_timer < 0:
                self.iframe_timer = 0

        ahora = pygame.time.get_ticks()
        cooldown_listo = (ahora - self.ultimo_ataque) >= self.cooldown_ataque

        if self._jugador_en_vision(jugador_model) and cooldown_listo and not self.atacando:
            # Iniciar ataque — hitbox empieza None, hit window la activará
            self.atacando = True
            self._frame_index = 0
            self._update_time = ahora
            self.ultimo_ataque = ahora
        elif not self.atacando:
            self.hitbox_ataque = None
            self._patrullar()

        # Avance de animación y hit window
        if self.atacando:
            if pygame.time.get_ticks() - self._update_time > self.COOLDOWN_ANIM:
                self._frame_index += 1
                self._update_time = pygame.time.get_ticks()
            if self._frame_index >= self._num_frames_ataque:
                self.atacando = False
                self.hitbox_ataque = None
                self._frame_index = 0
            elif self.ataque_frame_inicio <= self._frame_index <= self.ataque_frame_fin:
                self.hitbox_ataque = self._calcular_hitbox_ataque()
            else:
                self.hitbox_ataque = None

        self._movimiento(plataformas)

    def _patrullar(self):
        if self.shape.x <= self.patrol_min:
            self.flip = False
        elif self.shape.right >= self.patrol_max:
            self.flip = True
        self.shape.x += -self.velocidad if self.flip else self.velocidad

    def _movimiento(self, plataformas):
        # Gravedad
        self.velocidad_y += Constantes.GRAVEDAD
        if self.velocidad_y > Constantes.VELOCIDAD_MAX_CAIDA:
            self.velocidad_y = Constantes.VELOCIDAD_MAX_CAIDA

        # Colisiones horizontales con plataformas
        for plat in plataformas:
            if self.shape.colliderect(plat.shape):
                if self.flip:
                    self.shape.left = plat.shape.right
                    self.flip = False
                else:
                    self.shape.right = plat.shape.left
                    self.flip = True

        # Colisiones verticales con plataformas
        self.en_suelo = False
        self.shape.y += int(self.velocidad_y)

        for plat in plataformas:
            if self.shape.colliderect(plat.shape):
                if self.velocidad_y > 0:
                    self.shape.bottom = plat.shape.top
                    self.velocidad_y  = 0
                    self.en_suelo     = True
                elif self.velocidad_y < 0:
                    self.shape.top   = plat.shape.bottom
                    self.velocidad_y = 0

    def _jugador_en_vision(self, jugador_model):
        dx = jugador_model.shape.centerx - self.shape.centerx
        mirando_al_jugador = (self.flip and dx < 0) or (not self.flip and dx > 0)
        cerca = abs(dx) <= self.rango_vision
        return mirando_al_jugador and cerca

    def _calcular_hitbox_ataque(self):
        ancho_hit = Constantes.WIDTH_PERSONAJE * 4
        if self.flip:
            x = self.shape.left - ancho_hit
        else:
            x = self.shape.right
        return pygame.Rect(x, self.shape.top, ancho_hit, self.shape.height)

    def obtener_estado(self):
        """Devuelve un dict con el estado lógico para que la Vista sincronice su sprite.

        Returns
        -------
        dict
            Claves: 'pos', 'flip', 'atacando', 'hitbox_ataque', 'vivo'.
        """
        return {
            'pos': self.shape.center,
            'flip': self.flip,
            'atacando': self.atacando,
            'hitbox_ataque': self.hitbox_ataque,
            'vivo': self.vivo,
            'iframe_activo': self.iframe_timer > 0,
        }


# ---------------------------------------------------------------------------
# Model principal del juego
# ---------------------------------------------------------------------------

class JuegoModel:
    """Gestiona el estado completo del juego.

    Contiene el jugador y la lista de enemigos, y delega en ellos
    la física y la lógica de combate cada frame.

    Attributes
    ----------
    jugador : JugadorModel
        Sub-modelo del jugador.
    enemigos : list of Enemigo1Model
        Lista de sub-modelos de enemigos vivos.
    mover_derecha : bool
        True mientras la tecla D está pulsada.
    mover_izquierda : bool
        True mientras la tecla A está pulsada.
    """

    def __init__(self, datos_enemigos):
        """Inicializa el Model con el jugador y los enemigos.

        Parameters
        ----------
        datos_enemigos : list of dict
            Lista de dicts con {'x', 'y', 'distancia_patrulla', 'num_frames_ataque'}.
        """
        self.jugador = JugadorModel(250, 250)

        self.enemigos = [
            Enemigo1Model(
                d['x'],
                d['y'],
                distancia_patrulla=d.get('distancia_patrulla', 150),
                num_frames_ataque=d.get('num_frames_ataque', 6),
            )
            for d in datos_enemigos
        ]

        self.mover_derecha   = False
        self.mover_izquierda = False

    # --- Acciones del jugador (delegadas desde el Presenter) ---

    def jugador_saltar(self):
        self.jugador.saltar()

    def jugador_atacar(self, num_frames_anim):
        self.jugador.iniciar_ataque(num_frames_anim)

    def jugador_mover_derecha_inicio(self):
        self.mover_derecha = True

    def jugador_mover_derecha_fin(self):
        self.mover_derecha = False

    def jugador_mover_izquierda_inicio(self):
        self.mover_izquierda = True

    def jugador_mover_izquierda_fin(self):
        self.mover_izquierda = False

    # --- Actualización del estado (llamada cada frame por el Presenter) ---

    def actualizar(self, plataformas, delta_time_ms):
        """Actualiza física, IA y combate para todos los objetos del juego.

        Parameters
        ----------
        plataformas : list of Plataforma
            Lista de plataformas con su shape (viene de la Vista).
        delta_time_ms : int
            Milisegundos desde el último frame (para coyote time).

        Returns
        -------
        list of int
            Índices de los enemigos que han muerto este frame
            (para que el Presenter elimine sus sprites de la Vista).
        """
        # Calcular delta_x del jugador
        delta_x = 0
        if self.mover_derecha:
            delta_x = Constantes.VELOCIDAD
        if self.mover_izquierda:
            delta_x = -Constantes.VELOCIDAD

        # Actualizar jugador
        self.jugador.actualizar(delta_x, plataformas, delta_time_ms)

        # Actualizar enemigos
        muertos = []
        for i, enemigo in enumerate(self.enemigos):
            enemigo.actualizar(plataformas, self.jugador)

            # Combate: golpe del jugador al enemigo
            if (self.jugador.hitbox_ataque
                    and self.jugador.hitbox_ataque.colliderect(enemigo.shape)
                    and enemigo.vivo):
                enemigo.recibir_daño(1)

            # Combate: golpe del enemigo al jugador
            if (enemigo.hitbox_ataque
                    and enemigo.hitbox_ataque.colliderect(self.jugador.shape)):
                self.jugador.recibir_daño(1)

            if not enemigo.vivo:
                muertos.append(i)

        # Eliminar muertos (en orden inverso para no alterar índices)
        for i in reversed(muertos):
            self.enemigos.pop(i)

        return muertos

    # --- Exportar estado para la Vista ---

    def obtener_estado_jugador(self):
        """Devuelve el estado del jugador para sincronizar la Vista."""
        return self.jugador.obtener_estado()

    def obtener_estados_enemigos(self):
        """Devuelve la lista de estados de todos los enemigos vivos."""
        return [e.obtener_estado() for e in self.enemigos]
