"""Modelo del proyectil de daga lanzado por el jugador.

Viaja en línea recta en la dirección que miraba el jugador al lanzarlo.
Se destruye al:
  - Tocar una plataforma/pared.
  - Superar la distancia máxima (WIDTH / 2).
  - Tocar a un enemigo (la Vista lo notifica).
"""

import pygame
import Constantes


class DagaProyectilModel:
    """Proyectil de daga del jugador.

    Attributes
    ----------
    shape : pygame.Rect
        Rectángulo de colisión.
    vel_x : float
        Velocidad horizontal (negativa = izquierda).
    flip : bool
        True si va hacia la izquierda.
    vivo : bool
        False cuando impacta o supera la distancia máxima.
    daño : int
        Daño que aplica al enemigo al impactar.
    """

    VELOCIDAD    = 10
    DISTANCIA_MAX = Constantes.WIDTH // 2   # píxeles de mundo máximos
    DAÑO         = 1

    def __init__(self, x: int, y: int, flip: bool,
                 frame_ref: pygame.Surface):
        """
        Parameters
        ----------
        x, y : int
            Posición central de lanzamiento (centro del jugador).
        flip : bool
            True = lanzar hacia la izquierda.
        frame_ref : pygame.Surface
            Primer frame del sprite, para calcular el tamaño del shape.
        """
        self.flip  = flip
        self.vivo  = True
        self.daño  = self.DAÑO

        self.shape = pygame.Rect(0, 0,
                                 frame_ref.get_width(),
                                 frame_ref.get_height())
        self.shape.center = (x, y)

        self.vel_x      = -self.VELOCIDAD if flip else self.VELOCIDAD
        self._x         = float(x)
        self._y         = float(y)
        self._origen_x  = float(x)   # para medir distancia recorrida

    # ------------------------------------------------------------------ #

    def actualizar(self):
        """Mueve el proyectil y comprueba si superó la distancia máxima."""
        if not self.vivo:
            return

        self._x += self.vel_x
        self.shape.center = (int(self._x), int(self._y))

        if abs(self._x - self._origen_x) >= self.DISTANCIA_MAX:
            self.vivo = False

    def obtener_estado(self) -> dict:
        return {
            'pos':  self.shape.center,
            'flip': self.flip,
            'vivo': self.vivo,
        }
