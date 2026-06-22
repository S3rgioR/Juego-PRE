"""Clase base mínima para proyectiles.

Cubre solo lo que de verdad es idéntico entre ProyectilModel y
DagaProyectilModel (y, por herencia, ProyectilBoss en BossModel.py):
  - Crear el shape (Rect) centrado en (x, y) con un ancho/alto dados.
  - flip / vivo / _x / _y como atributos base.
  - obtener_estado(), que las tres devuelven igual.

NO incluye vel_x/vel_y/actualizar() porque eso difiere demasiado entre
subclases (quién mueve el proyectil, si sigue al jugador, si tiene
distancia máxima, etc.) — cada una lo define a su manera.
"""

import pygame


class ProyectilBase:
    """Atributos y comportamiento mínimo común a todos los proyectiles."""

    def __init__(self, x, y, ancho: int, alto: int, flip: bool):
        self.shape = pygame.Rect(0, 0, ancho, alto)
        self.shape.center = (x, y)

        self.flip = flip
        self.vivo = True
        self._x   = float(x)
        self._y   = float(y)

    def obtener_estado(self) -> dict:
        return {
            'pos':  self.shape.center,
            'flip': self.flip,
            'vivo': self.vivo,
        }
