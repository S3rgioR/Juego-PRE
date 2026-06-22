"""Sub-modelo del proyectil.

Proyectil lanzado por Enemigo2Model, dirigido hacia el jugador.
La Vista mueve el proyectil cada frame usando vel_x y vel_y, y notifica
al Model cuando colisiona con el jugador o con una plataforma.

Hereda de ProyectilBase el shape/flip/vivo/_x/_y y obtener_estado();
aquí solo queda lo propio de este proyectil: calcular vel_x/vel_y
apuntando al objetivo en el momento del disparo. No tiene actualizar()
a propósito — el movimiento lo hace la Vista, no el Model.

Nota: BossModel.ProyectilBoss hereda de esta clase y llama a
super().__init__(x, y, target_x, target_y), así que esta firma debe
mantenerse estable.
"""

import math
import Constantes
from .ProyectilBase import ProyectilBase


class ProyectilModel(ProyectilBase):
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
        dx   = target_x - x
        dy   = target_y - y
        dist = math.hypot(dx, dy) or 1

        super().__init__(
            x, y,
            int(Constantes.WIDTH_PERSONAJE  * 0.8),
            int(Constantes.HEIGHT_PERSONAJE * 0.8),
            flip=dx < 0,
        )

        self.vel_x = (dx / dist) * self.VELOCIDAD
        self.vel_y = (dy / dist) * self.VELOCIDAD
