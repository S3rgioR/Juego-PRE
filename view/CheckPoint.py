"""Vista visual del checkpoint - Cuadrado simple.

Responsabilidad: Mostrar un cuadrado en el mapa que representa
el punto de guardado. Sin lógica compleja.
"""

import pygame


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
        self.shape = pygame.Rect(0, 0, self.TAMAÑO, self.TAMAÑO)
        self.shape.center = (x, y)
        self.activado = False

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

    def draw(self, interfaz: pygame.Surface, camara) -> None:
        """Dibuja el checkpoint como un cuadrado en la pantalla.

        Parameters
        ----------
        interfaz : pygame.Surface
            Superficie principal de la ventana.
        camara : Camara
            Instancia de cámara para transformar coordenadas.
        """
        # Obtener posición en pantalla
        rect_pantalla = camara.aplicar(self.shape)

        # Elegir color según estado
        color = self.COLOR_ACTIVADO if self.activado else self.COLOR_INACTIVO

        # Dibujar cuadrado relleno
        pygame.draw.rect(interfaz, color, rect_pantalla)

        # Dibujar borde
        pygame.draw.rect(interfaz, self.COLOR_BORDE, rect_pantalla, self.GROSOR_BORDE)