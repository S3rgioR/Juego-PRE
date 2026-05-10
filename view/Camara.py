"""Cámara con seguimiento suave del jugador.

Responsabilidad visual: sabe cómo desplazar el mundo para que el jugador
quede encuadrado. Vive en la capa View porque su única misión es
transformar coordenadas de mundo a coordenadas de pantalla.
"""

import Constantes


class Camara:
    """Gestiona el desplazamiento de la vista según la posición del jugador.

    Attributes
    ----------
    x : float
        Desplazamiento horizontal actual de la cámara (en píxeles de mundo).
    y : float
        Desplazamiento vertical actual de la cámara.
    offset_x : float
        Distancia horizontal desde el borde izquierdo hasta el jugador.
    offset_y : float
        Distancia vertical desde el borde superior hasta el jugador.
    suavizado : float
        Factor de interpolación (0-1). Menor = más suave.
    """

    def __init__(self):
        self.x = 0
        self.y = 0

        # 0.35 = 35% del ancho → jugador ligeramente a la izquierda del centro
        self.offset_x = Constantes.WIDTH * 0.35
        self.offset_y = Constantes.HEIGHT * 0.75

        # Suavizado: cuanto menor, más suave el seguimiento
        self.suavizado = 0.15

    def update(self, jugador_shape):
        """Actualiza la posición de la cámara interpolando hacia el jugador.

        Parameters
        ----------
        jugador_shape : pygame.Rect
            Rectángulo (shape) del jugador en coordenadas de mundo.
        """
        target_x = jugador_shape.centerx - self.offset_x
        target_y = jugador_shape.centery - self.offset_y

        # Interpolación suave hacia el target
        self.x += (target_x - self.x) * self.suavizado
        self.y += (target_y - self.y) * self.suavizado

    def aplicar(self, rect):
        """Devuelve el rect desplazado por la cámara para dibujar.

        Parameters
        ----------
        rect : pygame.Rect
            Rect en coordenadas de mundo.

        Returns
        -------
        pygame.Rect
            Rect en coordenadas de pantalla.
        """
        return rect.move(-int(self.x), -int(self.y))
