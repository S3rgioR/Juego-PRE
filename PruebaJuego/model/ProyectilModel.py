"""Sub-modelo del proyectil.

Proyectil lanzado por Enemigo2Model, dirigido hacia el jugador.
La Vista mueve el proyectil cada frame usando vel_x y vel_y, y notifica
al Model cuando colisiona con el jugador o con una plataforma.
"""

import math
import pygame
import Constantes


class ProyectilModel:
    """Proyectil lanzado por Enemigo2Model, dirigido hacia el jugador.

    Attributes
    ----------
    shape : pygame.Rect
        Rectángulo de colisión del proyectil.
    vel_x, vel_y : float
        Velocidad normalizada hacia el objetivo en el momento del disparo.
    flip : bool
        True si se dirige hacia la izquierda.
    vivo : bool
        False cuando colisiona o sale del mapa.
    """

    VELOCIDAD = 4

    def __init__(self, x, y, target_x, target_y):
        self.shape = pygame.Rect(
            0, 0,
            int(Constantes.WIDTH_PERSONAJE  * 0.8),
            int(Constantes.HEIGHT_PERSONAJE * 0.8),
        )
        self.shape.center = (x, y)

        dx   = target_x - x
        dy   = target_y - y
        dist = math.hypot(dx, dy) or 1
        self.vel_x = (dx / dist) * self.VELOCIDAD
        self.vel_y = (dy / dist) * self.VELOCIDAD

        self.flip = dx < 0
        self.vivo = True
        self._x   = float(x)
        self._y   = float(y)

    def obtener_estado(self):
        return {
            'pos':  self.shape.center,
            'flip': self.flip,
            'vivo': self.vivo,
        }
