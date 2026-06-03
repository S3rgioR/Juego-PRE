"""Vista visual del checkpoint - Cuadrado simple.

Responsabilidad: Mostrar un cuadrado en el mapa que representa
el punto de guardado. Sin lógica compleja.
"""

import pygame
import numpy


class CheckpointView:

    RADIO_ACTIVACION = 80
    DURACION_AZUL    = 1500  # ms que dura el efecto azul

    def __init__(self, x: int, y: int):
        self.image = pygame.image.load("Assets/Characters/statue.png").convert_alpha()
        self.shape = pygame.Rect(0, 0, self.image.get_width(), self.image.get_height())
        self.shape.center = (x, y)
        self._mostrar_prompt = False
        self._fuente         = None
        self._inicio_azul    = 0
        self._efecto_activo  = False

    def esta_cerca(self, jugador_shape: pygame.Rect, radio: int = RADIO_ACTIVACION) -> bool:
        dx = jugador_shape.centerx - self.shape.centerx
        dy = jugador_shape.centery - self.shape.centery
        return dx * dx + dy * dy <= radio * radio

    def activar(self):
        """Arranca el destello azul."""
        self._efecto_activo = True
        self._inicio_azul   = pygame.time.get_ticks()

    def set_mostrar_prompt(self, valor: bool):
        self._mostrar_prompt = valor

    def draw(self, interfaz: pygame.Surface, camara) -> None:
        if self._fuente is None:
            self._fuente = pygame.font.SysFont(None, 20)

        img_rect = self.image.get_rect(midbottom=self.shape.midbottom)

        # Comprobar si el efecto azul sigue activo
        if self._efecto_activo:
            ms = pygame.time.get_ticks() - self._inicio_azul
            if ms < self.DURACION_AZUL:
                imagen_azul = self.image.convert_alpha()
                arr   = pygame.surfarray.pixels3d(imagen_azul)
                alpha = pygame.surfarray.pixels_alpha(imagen_azul)
                mask  = alpha > 0
                arr[:, :, 0][mask] = arr[:, :, 0][mask] // 2
                arr[:, :, 1][mask] = arr[:, :, 1][mask] // 2
                arr[:, :, 2][mask] = numpy.minimum(255, arr[:, :, 2][mask].astype(int) + 150)
                del arr, alpha
                interfaz.blit(imagen_azul, camara.aplicar(img_rect))
            else:
                self._efecto_activo = False
                interfaz.blit(self.image, camara.aplicar(img_rect))
        else:
            interfaz.blit(self.image, camara.aplicar(img_rect))

        # Prompt de interacción
        if self._mostrar_prompt:
            texto = self._fuente.render("[K] Guardar", True, (255, 255, 255))
            rect_pantalla = camara.aplicar(self.shape)
            interfaz.blit(texto, (rect_pantalla.centerx - texto.get_width() // 2,
                                   rect_pantalla.top - 22))