"""Vista del portal de fin de juego.

Responsabilidad: mostrar el portal animado (7 frames) y detectar
si el jugador está cerca para activarlo. Misma interfaz que PortalView.
"""

import pygame
import Fuentes


class PortalFinalView:
    """Portal animado de fin de juego.

    Attributes
    ----------
    shape : pygame.Rect
        Hitbox en coordenadas de mundo.
    RADIO_ACTIVACION : int
        Distancia en píxeles a la que se considera que el jugador "atraviesa" el portal.
    """

    RADIO_ACTIVACION = 60

    def __init__(self, x: int, y: int, frames: list, ancho: int = 1, alto: int = 1):
        self.frames      = frames
        self.frame_idx   = 0
        self.frame_timer = 0
        self.MS_POR_FRAME = 80          # velocidad de animación

        # Hitbox centrada en (x, y) con el tamaño indicado
        self.shape = pygame.Rect(0, 0, ancho, alto)
        self.shape.center = (x, y)

        self._mostrar_prompt = False
        self._fuente         = None

    def esta_cerca(self, jugador_shape: pygame.Rect) -> bool:
        dx = jugador_shape.centerx - self.shape.centerx
        dy = jugador_shape.centery - self.shape.centery
        return dx * dx + dy * dy <= self.RADIO_ACTIVACION ** 2

    def set_mostrar_prompt(self, valor: bool, texto: str = "[E] Fin"):
        self._mostrar_prompt = valor
        self._texto_prompt   = texto

    def actualizar(self, delta_ms: float):
        """Avanza la animación."""
        if not self.frames:
            return
        self.frame_timer += delta_ms
        if self.frame_timer >= self.MS_POR_FRAME:
            self.frame_timer = 0
            self.frame_idx   = (self.frame_idx + 1) % len(self.frames)

    def draw(self, interfaz: pygame.Surface, camara) -> None:
        if not self.frames:
            return
        if self._fuente is None:
            self._fuente = Fuentes.obtener_fuente(20)

        frame      = self.frames[self.frame_idx]
        frame_rect = frame.get_rect(center=self.shape.center)
        interfaz.blit(frame, camara.aplicar(frame_rect))

        if self._mostrar_prompt:
            texto = self._fuente.render(
                getattr(self, '_texto_prompt', '[E] Fin'), True, (255, 255, 255))
            rect_pantalla = camara.aplicar(self.shape)
            interfaz.blit(texto, (rect_pantalla.centerx - texto.get_width() // 2,
                                   rect_pantalla.top - 24))
