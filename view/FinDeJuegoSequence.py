"""Secuencia de fin de juego.

Muestra un fade a negro y luego aparecen los textos
"Felicidades." y "Has finalizado el juego." con fade-in,
y tras unos segundos señaliza que hay que volver al menú.
"""

import pygame


class FinDeJuegoSequence:
    """Gestiona la secuencia de fin de juego.

    Estados internos
    ----------------
    'fade_out'  : la pantalla se oscurece desde el juego en curso.
    'texto_in'  : los textos aparecen gradualmente sobre el negro.
    'espera'    : textos visibles, se espera antes de volver al menú.
    'hecho'     : la secuencia terminó → el caller debe volver al menú.
    """

    # Duraciones en milisegundos
    DURACION_FADE_OUT  = 2000   # tiempo en oscurecer la pantalla
    DURACION_TEXTO_IN  = 2000   # tiempo en que aparecen los textos
    DURACION_ESPERA    = 3000   # tiempo con los textos visibles antes de salir

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.w      = screen.get_width()
        self.h      = screen.get_height()

        self._estado   = 'fade_out'
        self._elapsed  = 0.0
        self.terminado = False          # el caller comprueba esto

        # Overlay negro para el fade
        self._overlay = pygame.Surface((self.w, self.h))
        self._overlay.fill((0, 0, 0))

        # Fuentes
        self._fuente_sub    = pygame.font.SysFont(None, 64)
        self._fuente_titulo = pygame.font.SysFont(None, 96)

        # Captura del frame actual del juego (para el fade desde el juego)
        self._captura = screen.copy()

    def actualizar(self, delta_ms: float):
        if self.terminado:
            return
        self._elapsed += delta_ms

        if self._estado == 'fade_out':
            if self._elapsed >= self.DURACION_FADE_OUT:
                self._elapsed -= self.DURACION_FADE_OUT
                self._estado  = 'texto_in'

        elif self._estado == 'texto_in':
            if self._elapsed >= self.DURACION_TEXTO_IN:
                self._elapsed -= self.DURACION_TEXTO_IN
                self._estado  = 'espera'

        elif self._estado == 'espera':
            if self._elapsed >= self.DURACION_ESPERA:
                self.terminado = True

    def draw(self):
        if self._estado == 'fade_out':
            # Dibujar captura del juego + overlay negro con alpha creciente
            t     = min(1.0, self._elapsed / self.DURACION_FADE_OUT)
            alpha = int(t * 255)
            self.screen.blit(self._captura, (0, 0))
            self._overlay.set_alpha(alpha)
            self.screen.blit(self._overlay, (0, 0))

        else:
            # Fondo completamente negro
            self.screen.fill((0, 0, 0))

            if self._estado == 'texto_in':
                t     = min(1.0, self._elapsed / self.DURACION_TEXTO_IN)
                alpha = int(t * 255)
            else:
                alpha = 255

            cx = self.w // 2
            cy = self.h // 2

            # "Felicidades." — un poco por encima del centro
            surf_sub = self._fuente_sub.render("Felicidades.", True, (255, 255, 255))
            surf_sub.set_alpha(alpha)
            rect_sub = surf_sub.get_rect(center=(cx, cy - 70))
            self.screen.blit(surf_sub, rect_sub)

            # "Has finalizado el juego." — justo debajo, más grande
            surf_tit = self._fuente_titulo.render(
                "Has finalizado el juego.", True, (255, 255, 255))
            surf_tit.set_alpha(alpha)
            rect_tit = surf_tit.get_rect(center=(cx, cy + 20))
            self.screen.blit(surf_tit, rect_tit)
