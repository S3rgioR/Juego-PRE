"""Vista visual del checkpoint - Cuadrado simple.

Responsabilidad: Mostrar un cuadrado en el mapa que representa
el punto de guardado. Sin lógica compleja.
"""

import pygame
import numpy

class CheckpointView:
    """Vista visual del checkpoint como cuadrado simple.

    Attributes
    ----------
    shape : pygame.Rect
        Rectángulo que define posición y tamaño en coordenadas de mundo.
    activado : bool
        True si ya se ha guardado una partida.
    """

    TAMAÑO = 40  # Lado del cuadrado en píxeles
    COLOR_INACTIVO = (100, 180, 255)  # Azul frío
    COLOR_ACTIVADO = (255, 220, 60)   # Dorado
    COLOR_BORDE = (255, 255, 255)     # Blanco
    GROSOR_BORDE = 2

    def __init__(self, x: int, y: int):
        """Inicializa el checkpoint como un cuadrado centrado en (x, y).

        Parameters
        ----------
        x, y : int
            Centro del checkpoint en coordenadas de mundo.
        """
        self.image = pygame.image.load("Enviorments/statue.png").convert_alpha()
        self.shape = pygame.Rect(0, 0, self.image.get_width(), self.image.get_height())
        self.shape.center = (x, y)
        self.activado = False
        self._timer_azul = 0  # ms que queda el efecto azul activo
        self._DURACION_AZUL = 1500  # duración del destello en ms


    def esta_cerca(self, jugador_shape: pygame.Rect, radio: int = 80) -> bool:
        """Devuelve True si el jugador está dentro del radio de activación.

        Parameters
        ----------
        jugador_shape : pygame.Rect
            Hitbox del jugador en coordenadas de mundo.
        radio : int, optional
            Radio de activación en píxeles (default: 80).

        Returns
        -------
        bool
            True si está cerca, False en caso contrario.
        """
        dx = jugador_shape.centerx - self.shape.centerx
        dy = jugador_shape.centery - self.shape.centery
        distancia_cuadrado = dx * dx + dy * dy
        return distancia_cuadrado <= radio * radio

    def draw(self, interfaz, camara):
        img_rect = self.image.get_rect(midbottom=self.shape.midbottom)

        tiempo_actual = pygame.time.get_ticks()

        if self._timer_azul > 0:
            ms_transcurridos = tiempo_actual - self._inicio_azul
            if ms_transcurridos < self._DURACION_AZUL:
                imagen_azul = self.image.convert_alpha()
                arr = pygame.surfarray.pixels3d(imagen_azul)
                alpha = pygame.surfarray.pixels_alpha(imagen_azul)
                mask = alpha > 0
                arr[:, :, 0][mask] = arr[:, :, 0][mask] // 2
                arr[:, :, 1][mask] = arr[:, :, 1][mask] // 2
                arr[:, :, 2][mask] = numpy.minimum(255, arr[:, :, 2][mask].astype(int) + 150)
                del arr, alpha
                interfaz.blit(imagen_azul, camara.aplicar(img_rect))
            else:
                self._timer_azul = 0
                interfaz.blit(self.image, camara.aplicar(img_rect))
        else:
            interfaz.blit(self.image, camara.aplicar(img_rect))

    def activar(self):
        self._timer_azul = self._DURACION_AZUL
        self._inicio_azul = pygame.time.get_ticks()