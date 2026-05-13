"""Capa Model del patrón MVP - Reglas de juego, IA y combate.

Responsabilidades:
- Estado del jugador (hp, flags de acción, iframes)
- Estado de los enemigos (patrulla, visión, cooldowns de ataque)
- Reglas de combate: quién puede golpear a quién y cuánto daño hace
- Responder a preguntas de la Vista: "¿qué ocurre si X colisiona con Y?"

Lo que NO hace el Model:
- Dibujar nada
- Mover objetos (no modifica posiciones directamente)
- Detectar colisiones (esa responsabilidad es de la Vista)
- Gestionar eventos de teclado
- Gestionar la cámara

Filosofía de esta arquitectura:
    La Vista mueve los objetos, detecta colisiones y consulta al Model
    qué consecuencia tiene cada interacción. El Model responde modificando
    su estado interno (hp, flags) y devolviendo instrucciones de corrección
    geométrica cuando la Vista las necesita.

Jerarquía de clases:
    Actor               ← clase base con hp, iframes, flip, patrulla
    ├── JugadorModel    ← añade salto, coyote time, animación de ataque
    ├── Enemigo1Model   ← añade IA terrestre, ventana de golpe cuerpo a cuerpo
    └── Enemigo2Model   ← añade IA voladora, disparo de proyectiles
"""

import pygame
import Constantes


# ---------------------------------------------------------------------------
# Clase base: Actor
# ---------------------------------------------------------------------------

class Actor:
    """Estado lógico común a toda entidad con vida del juego.

    Encapsula los atributos y comportamientos que comparten el jugador
    y todos los tipos de enemigo: puntos de vida, invencibilidad temporal
    (iframes), orientación y física vertical básica.

    Las subclases añaden la lógica específica de cada rol
    (control del jugador, IA de patrulla, disparo, etc.).

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
        self.flip        = False
        self.hp          = hp
        self.vivo        = True
        self.iframe_duracion = iframe_duracion
        self.iframe_timer    = 0

        self.velocidad_y  = 0.0
        self.en_suelo     = False

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


# ---------------------------------------------------------------------------
# Sub-modelo: Jugador
# ---------------------------------------------------------------------------

class JugadorModel(Actor):
    """Estado lógico del jugador.

    Extiende Actor con el control de entrada del jugador: salto con
    coyote time y animación de ataque con contador de frames.

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


# ---------------------------------------------------------------------------
# Sub-modelo: Enemigo_1 (terrestre)
# ---------------------------------------------------------------------------

class Enemigo1Model(Actor):
    """Estado lógico del primer tipo de enemigo: patrullador terrestre.

    Extiende Actor con IA de patrulla, detección visual del jugador
    y ataque cuerpo a cuerpo con ventana de golpe por frames.

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


# ---------------------------------------------------------------------------
# Sub-modelo: Enemigo_2 (volador)
# ---------------------------------------------------------------------------

class Enemigo2Model(Actor):
    """Estado lógico del segundo tipo de enemigo: patrullador volador.

    Extiende Actor con IA de patrulla aérea y disparo de proyectiles
    dirigidos al jugador. No aplica gravedad ni necesita plataformas.

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
            Desplazamiento horizontal de patrulla.
        nuevos_proyectiles : list of ProyectilModel
            Proyectiles recién creados este frame (lista vacía si ninguno).
        """
        if not self.vivo:
            return 0, []

        self._tick_iframes(delta_time_ms)

        import math
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


# ---------------------------------------------------------------------------
# Proyectil
# ---------------------------------------------------------------------------

class ProyectilModel:
    """Proyectil lanzado por Enemigo2Model, dirigido hacia el jugador.

    La Vista mueve el proyectil cada frame usando vel_x y vel_y, y notifica
    al Model cuando colisiona con el jugador o con una plataforma.
    """

    VELOCIDAD = 4

    def __init__(self, x, y, target_x, target_y):
        import math
        self.shape = pygame.Rect(
            0, 0,
            int(Constantes.WIDTH_PERSONAJE  * 0.8),
            int(Constantes.HEIGHT_PERSONAJE * 0.8),
        )
        self.shape.center = (x, y)

        dx   = target_x - x
        dy   = target_y - y
        dist = math.hypot(dx, dy) or 1
        self.vel_x = (dx / dist) * self.VELOCIDAD
        self.vel_y = (dy / dist) * self.VELOCIDAD

        self.flip = dx < 0
        self.vivo = True
        self._x   = float(x)
        self._y   = float(y)

    def obtener_estado(self):
        return {
            'pos':  self.shape.center,
            'flip': self.flip,
            'vivo': self.vivo,
        }


# ---------------------------------------------------------------------------
# Model principal del juego
# ---------------------------------------------------------------------------

class JuegoModel:
    """Gestiona el estado completo del juego: jugador, enemigos y combate.

    Actúa como fachada: la Vista y el Presenter acceden al estado
    del juego a través de esta clase.

    Attributes
    ----------
    jugador : JugadorModel
        Sub-modelo del jugador.
    enemigos : list of Actor
        Lista de sub-modelos de enemigos vivos.
    mover_derecha : bool
        True mientras la tecla D está pulsada.
    mover_izquierda : bool
        True mientras la tecla A está pulsada.
    """

    def __init__(self, datos_enemigos):
        self.jugador = JugadorModel()

        self.enemigos = []
        for d in datos_enemigos:
            if d.get('tipo') == 'volador':
                self.enemigos.append(
                    Enemigo2Model(
                        d['x'], d['y'],
                        distancia_patrulla=d.get('distancia_patrulla', 150),
                    )
                )
            else:
                self.enemigos.append(
                    Enemigo1Model(
                        d['x'], d['y'],
                        distancia_patrulla=d.get('distancia_patrulla', 150),
                        num_frames_ataque=d.get('num_frames_ataque', 6),
                    )
                )

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

    # --- Consultas de combate (llamadas por la Vista al detectar colisiones) ---

    def golpe_jugador_a_enemigo(self, indice):
        """La Vista notifica que la hitbox del jugador ha tocado al enemigo [indice]."""
        if 0 <= indice < len(self.enemigos):
            self.enemigos[indice].recibir_daño(1)

    def golpe_enemigo_a_jugador(self):
        """La Vista notifica que la hitbox de un enemigo ha tocado al jugador."""
        self.jugador.recibir_daño(1)

    def golpe_proyectil_a_jugador(self, proyectil):
        """La Vista notifica que un proyectil ha tocado al jugador."""
        self.jugador.recibir_daño(1.5)
        proyectil.vivo = False

    def golpe_jugador_a_proyectil(self, proyectil):
        """La Vista notifica que la espada del jugador ha destruido un proyectil."""
        proyectil.vivo = False

    # --- Tick del Model (llamado por el Presenter cada frame) ---

    def tick(self, delta_time_ms):
        """Avanza los contadores internos del Model.

        No mueve nada: la Vista ya ha movido y colisionado antes de llamar aquí.

        Returns
        -------
        list of int
            Índices de enemigos que han muerto este frame.
        """
        if self.mover_derecha:
            self.jugador.moviendose = True
            self.jugador.flip       = False
        elif self.mover_izquierda:
            self.jugador.moviendose = True
            self.jugador.flip       = True
        else:
            self.jugador.moviendose = False

        self.jugador.tick(delta_time_ms)

        muertos = [i for i, e in enumerate(self.enemigos) if not e.vivo]
        for i in reversed(muertos):
            self.enemigos.pop(i)

        return muertos

    @property
    def delta_x_jugador(self):
        """Desplazamiento horizontal del jugador para este frame."""
        if self.mover_derecha:
            return Constantes.VELOCIDAD
        if self.mover_izquierda:
            return -Constantes.VELOCIDAD
        return 0