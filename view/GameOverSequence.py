"""Secuencia de Game Over: fade a negro → texto GAME OVER → menú principal.

Fases
-----
1. FADE  (1500 ms): overlay negro que aumenta de opacidad sobre el juego congelado.
2. TEXTO (2000 ms): pantalla totalmente negra con "GAME OVER" en rojo centrado.
3. FIN   : `terminado` pasa a True y el Presenter cierra el loop.
"""

import pygame
import Constantes


class GameOverSequence:
    """Gestiona la transición visual tras la muerte del jugador.

    Uso típico (en el Presenter)
    ----------------------------
    seq = GameOverSequence(screen)
    # cada frame:
    seq.actualizar(delta_ms)
    seq.draw()
    if seq.terminado:
        salir_al_menu()
    """

    _DURACION_FADE_MS  = 1500   # tiempo que tarda el fundido a negro
    _DURACION_TEXTO_MS = 2000   # tiempo que se muestra GAME OVER antes de salir

    def __init__(self, screen: pygame.Surface, captura: pygame.Surface):
        """
        Parameters
        ----------
        screen : pygame.Surface
            Superficie principal de la ventana.
        captura : pygame.Surface
            Foto del frame en el momento de morir (el juego «congelado»).
        """
        self.screen   = screen
        self.captura  = captura
        self._fase    = 'fade'   # 'fade' → 'texto' → 'fin'
        self._elapsed = 0        # ms acumulados en la fase actual
        self.terminado = False

        # Overlay negro reutilizable
        self._overlay = pygame.Surface(
            (Constantes.WIDTH, Constantes.HEIGHT), pygame.SRCALPHA
        )

        # Fuente para el texto
        self._fuente = pygame.font.SysFont(None, 140)

    # ------------------------------------------------------------------

    def actualizar(self, delta_ms: int):
        """Avanza el timer de la fase activa."""
        if self.terminado:
            return

        self._elapsed += delta_ms

        if self._fase == 'fade':
            if self._elapsed >= self._DURACION_FADE_MS:
                self._fase    = 'texto'
                self._elapsed = 0

        elif self._fase == 'texto':
            if self._elapsed >= self._DURACION_TEXTO_MS:
                self._fase    = 'fin'
                self.terminado = True

    def draw(self):
        """Dibuja la fase activa sobre la pantalla. NO llama display.flip()."""
        if self._fase == 'fade':
            # Progreso 0..1 del fundido
            t = min(self._elapsed / self._DURACION_FADE_MS, 1.0)
            alpha = int(t * 255)

            # El juego congelado
            self.screen.blit(self.captura, (0, 0))

            # Overlay negro con la opacidad correspondiente
            self._overlay.fill((0, 0, 0, alpha))
            self.screen.blit(self._overlay, (0, 0))

        elif self._fase == 'texto':
            # Pantalla completamente negra
            self.screen.fill((0, 0, 0))

            # Texto "GAME OVER" centrado en rojo
            texto = self._fuente.render("GAME OVER", True, (220, 50, 50))
            x = (Constantes.WIDTH  - texto.get_width())  // 2
            y = (Constantes.HEIGHT - texto.get_height()) // 2
            self.screen.blit(texto, (x, y))
