"""Clase base compartida para los sprites visuales de enemigos."""

import pygame
import Constantes


class EnemigoSpriteBase:
    """Comportamiento común a todos los sprites de enemigo.

    Gestiona:
    - shape (hitbox de colisión)
    - animación por frames
    - flip horizontal
    - iframe (parpadeo rojo)
    - exclamación "!" flotante
    """

    EXCLAMACION_DURACION_MS = 800
    COOLDOWN_AVISO_DETECCION_MS = 2000   # tiempo mínimo entre avisos (sonido + "!")

    # ------------------------------------------------------------------ #
    #  Inicialización                                                      #
    # ------------------------------------------------------------------ #

    def __init__(self, x: int, y: int, anim_walk: list):
        self.shape = pygame.Rect(
            0, 0,
            Constantes.WIDTH_PERSONAJE * 2,
            Constantes.HEIGHT_PERSONAJE * 1.5,
        )
        self.shape.center = (x, y)

        self.anim_walk   = anim_walk
        self.anim_actual = self.anim_walk
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.image       = self.anim_actual[0]
        self.flip        = True

        self.hitbox_ataque  = None
        self._iframe_activo = False

        # Exclamación
        self._exclamacion_timer  = 0
        self._fuente_exclamacion = None   # lazy: se crea la primera vez que se dibuja
        self._last_draw_time     = pygame.time.get_ticks()

        # Cooldown del aviso de detección (sonido + "!"). Es puramente
        # gráfico/de presentación: el Model puede notificar detección
        # con más frecuencia de la que queremos mostrar/sonar, así que
        # la Vista decide aquí si ese aviso se "deja pasar" o se ignora.
        self._cooldown_aviso_timer  = 0
        self._cooldown_aviso_last   = pygame.time.get_ticks()
        # True solo el frame en que sincronizar() decide que SÍ toca
        # mostrar el aviso (la Vista lo consulta para disparar el SFX).
        self.aviso_deteccion_listo  = False

    # ------------------------------------------------------------------ #
    #  Animación de frames                                                 #
    # ------------------------------------------------------------------ #

    def _avanzar_frame(self, cooldown_ms: int = 100) -> None:
        """Avanza el frame de animación si ha pasado *cooldown_ms* ms."""
        if pygame.time.get_ticks() - self.update_time > cooldown_ms:
            self.frame_index += 1
            self.update_time  = pygame.time.get_ticks()

        if self.frame_index >= len(self.anim_actual):
            self.frame_index = 0

        self.image = self.anim_actual[self.frame_index]

    # ------------------------------------------------------------------ #
    #  Sincronización con el modelo (campos comunes)                       #
    # ------------------------------------------------------------------ #

    def _sincronizar_base(self, estado_modelo: dict) -> None:
        """Aplica los campos compartidos del estado del modelo."""
        self.shape.center = (
            int(estado_modelo["pos"][0]),
            int(estado_modelo["pos"][1]),
        )
        self.flip           = estado_modelo["flip"]
        self._iframe_activo = estado_modelo.get("iframe_activo", False)

        # Cooldown del aviso (sonido + exclamación "!"): descuenta según
        # tiempo real transcurrido, igual que _tick_exclamacion.
        ahora = pygame.time.get_ticks()
        delta = ahora - self._cooldown_aviso_last
        self._cooldown_aviso_last = ahora
        if self._cooldown_aviso_timer > 0:
            self._cooldown_aviso_timer -= delta

        self.aviso_deteccion_listo = False
        if estado_modelo.get("exclamacion_nueva"):
            if self._cooldown_aviso_timer <= 0:
                self._exclamacion_timer    = self.EXCLAMACION_DURACION_MS
                self._cooldown_aviso_timer = self.COOLDOWN_AVISO_DETECCION_MS
                self.aviso_deteccion_listo = True
            # Si el cooldown sigue activo, se ignora este aviso por
            # completo: ni se reinicia la exclamación visual ni se marca
            # aviso_deteccion_listo, así la Vista tampoco reproduce el SFX.

    # ------------------------------------------------------------------ #
    #  Dibujado del sprite con tinte de iframe                             #
    # ------------------------------------------------------------------ #

    def _blit_con_iframe(
        self,
        interfaz: pygame.Surface,
        camara,
        imagen_flip: pygame.Surface,
        dest_rect: pygame.Rect,
    ) -> None:
        """Blitea *imagen_flip* aplicando tinte rojo si el iframe está activo."""
        from .VisualEffects import aplicar_tinte   # import local para evitar ciclos

        if self._iframe_activo:
            imagen_tinte = aplicar_tinte(imagen_flip, r=255, g=0, b=0, intensidad=0.5)
            interfaz.blit(imagen_tinte, camara.aplicar(dest_rect))
        else:
            interfaz.blit(imagen_flip, camara.aplicar(dest_rect))

    # ------------------------------------------------------------------ #
    #  Exclamación "!"                                                     #
    # ------------------------------------------------------------------ #

    def _tick_exclamacion(self, interfaz: pygame.Surface, camara) -> None:
        """Descuenta el timer y dibuja el "!" si sigue activo.

        Debe llamarse una vez por frame desde *draw()*.
        """
        ahora = pygame.time.get_ticks()
        delta = ahora - self._last_draw_time
        self._last_draw_time = ahora

        if self._exclamacion_timer > 0:
            self._exclamacion_timer -= delta
            self._dibujar_exclamacion(interfaz, camara)

    def _dibujar_exclamacion(self, interfaz: pygame.Surface, camara) -> None:
        if self._fuente_exclamacion is None:
            self._fuente_exclamacion = pygame.font.SysFont(None, 36)

        txt   = self._fuente_exclamacion.render("!", True, (255, 220, 0))
        rect  = camara.aplicar(self.shape)
        pos_x = rect.centerx - txt.get_width() // 2
        pos_y = rect.top - txt.get_height() - 4

        bg = pygame.Rect(pos_x - 3, pos_y - 2, txt.get_width() + 6, txt.get_height() + 4)
        pygame.draw.rect(interfaz, (40, 20, 0),    bg, border_radius=3)
        pygame.draw.rect(interfaz, (255, 180, 0),  bg, width=1, border_radius=3)
        interfaz.blit(txt, (pos_x, pos_y))
