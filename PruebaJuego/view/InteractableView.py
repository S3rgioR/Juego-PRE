"""Clase base para objetos interactuables con prompt de proximidad."""

import pygame
import Fuentes


class InteractableView:
    """Comportamiento común a todos los objetos interactuables del mapa.

    Gestiona:
    - shape (hitbox en coordenadas de mundo)
    - detección de proximidad por distancia al cuadrado
    - prompt de texto flotante encima del objeto
    """

    RADIO_ACTIVACION: int = 60   # las subclases pueden sobreescribir
    _COLOR_PROMPT = (255, 255, 255)
    _OFFSET_PROMPT_Y = 22        # px sobre el borde superior del shape

    # ------------------------------------------------------------------ #
    #  Inicialización                                                      #
    # ------------------------------------------------------------------ #

    def __init__(
        self,
        x: int,
        y: int,
        ancho: int,
        alto: int,
        texto_prompt: str = "[E]",
        tam_fuente: int = 20,
    ):
        self.shape = pygame.Rect(0, 0, ancho, alto)
        self.shape.center = (x, y)

        self._mostrar_prompt = False
        self._texto_prompt   = texto_prompt
        self._fuente         = None
        self._tam_fuente     = tam_fuente

    # ------------------------------------------------------------------ #
    #  API pública                                                         #
    # ------------------------------------------------------------------ #

    def esta_cerca(self, jugador_shape: pygame.Rect) -> bool:
        """True si el jugador está dentro del radio de activación."""
        dx = jugador_shape.centerx - self.shape.centerx
        dy = jugador_shape.centery - self.shape.centery
        return dx * dx + dy * dy <= self.RADIO_ACTIVACION ** 2

    def set_mostrar_prompt(self, valor: bool, texto: str | None = None) -> None:
        self._mostrar_prompt = valor
        if texto is not None:
            self._texto_prompt = texto

    # ------------------------------------------------------------------ #
    #  Dibujo del prompt (llámalo desde draw() en la subclase)            #
    # ------------------------------------------------------------------ #

    def _dibujar_prompt(self, interfaz: pygame.Surface, camara) -> None:
        """Dibuja el texto de prompt centrado sobre el shape si corresponde."""
        if not self._mostrar_prompt:
            return

        if self._fuente is None:
            self._fuente = Fuentes.obtener_fuente(self._tam_fuente)

        texto = self._fuente.render(self._texto_prompt, True, self._COLOR_PROMPT)
        rect_pantalla = camara.aplicar(self.shape)
        interfaz.blit(
            texto,
            (
                rect_pantalla.centerx - texto.get_width() // 2,
                rect_pantalla.top - self._OFFSET_PROMPT_Y,
            ),
        )
