"""Vista visual del Ángel curador.

Sprite animado estático (no se mueve por el mundo).
Muestra un prompt [K] cuando el jugador se acerca y,
cuando se activa la curación, reproduce un destello dorado.

Ruta de assets: Assets/Characters/angel/sprites/angel[1-8].png
"""

import pygame
import numpy


class AngelView:
    """Sprite visual del ángel curador.

    Parameters
    ----------
    x, y : int
        Posición central en coordenadas de mundo.
    frames : list of pygame.Surface
        Los 8 frames de animación del ángel (cargados en main.py).
    """

    RADIO_ACTIVACION  = 100       # px de distancia para mostrar el prompt
    COOLDOWN_ANIM     = 100       # ms entre frames de animación
    DURACION_DESTELLO = 1200      # ms que dura el efecto dorado al curar

    def __init__(self, x: int, y: int, frames: list):
        self.frames      = frames
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()

        # Shape centrado (usa el primer frame como referencia de tamaño)
        self.shape = pygame.Rect(0, 0,
                                 frames[0].get_width(),
                                 frames[0].get_height())
        self.shape.center = (x, y)

        self._mostrar_prompt  = False
        self._fuente          = None
        self._destello_activo = False
        self._inicio_destello = 0

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def esta_cerca(self, jugador_shape: pygame.Rect) -> bool:
        dx = jugador_shape.centerx - self.shape.centerx
        dy = jugador_shape.centery - self.shape.centery
        return dx * dx + dy * dy <= self.RADIO_ACTIVACION ** 2

    def activar_destello(self):
        """Arranca el efecto dorado de curación."""
        self._destello_activo = True
        self._inicio_destello = pygame.time.get_ticks()

    def set_mostrar_prompt(self, valor: bool):
        self._mostrar_prompt = valor

    # ------------------------------------------------------------------ #
    # Animación                                                            #
    # ------------------------------------------------------------------ #

    def _avanzar_frame(self):
        ahora = pygame.time.get_ticks()
        if ahora - self.update_time > self.COOLDOWN_ANIM:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.update_time = ahora

    # ------------------------------------------------------------------ #
    # Dibujo                                                               #
    # ------------------------------------------------------------------ #

    def draw(self, interfaz: pygame.Surface, camara) -> None:
        if self._fuente is None:
            self._fuente = pygame.font.SysFont(None, 20)

        self._avanzar_frame()
        frame_base = self.frames[self.frame_index]
        img_rect   = frame_base.get_rect(midbottom=self.shape.midbottom)

        # --- Efecto dorado durante el destello ---
        if self._destello_activo:
            ms = pygame.time.get_ticks() - self._inicio_destello
            if ms < self.DURACION_DESTELLO:
                # Intensidad decae con el tiempo (1.0 → 0.0)
                intensidad = 0.6 * (1.0 - ms / self.DURACION_DESTELLO)
                imagen = self._aplicar_tinte(frame_base, r=255, g=220, b=50,
                                             intensidad=intensidad)
            else:
                self._destello_activo = False
                imagen = frame_base
        else:
            imagen = frame_base

        interfaz.blit(imagen, camara.aplicar(img_rect))

        # --- Prompt de interacción ---
        if self._mostrar_prompt:
            texto = self._fuente.render("[K] Curar", True, (255, 255, 180))
            rect_pantalla = camara.aplicar(self.shape)
            interfaz.blit(texto,
                          (rect_pantalla.centerx - texto.get_width() // 2,
                           rect_pantalla.top - 24))

    def _aplicar_tinte(self, imagen, r, g, b, intensidad=0.5):
        """Devuelve una copia de la imagen con un tinte de color mezclado."""
        resultado = imagen.convert_alpha()
        arr   = pygame.surfarray.pixels3d(resultado)
        alpha = pygame.surfarray.pixels_alpha(resultado)
        mask  = alpha > 0

        arr[:, :, 0][mask] = numpy.clip(
            arr[:, :, 0][mask] * (1 - intensidad) + r * intensidad, 0, 255
        ).astype(numpy.uint8)
        arr[:, :, 1][mask] = numpy.clip(
            arr[:, :, 1][mask] * (1 - intensidad) + g * intensidad, 0, 255
        ).astype(numpy.uint8)
        arr[:, :, 2][mask] = numpy.clip(
            arr[:, :, 2][mask] * (1 - intensidad) + b * intensidad, 0, 255
        ).astype(numpy.uint8)
        del arr, alpha
        return resultado
