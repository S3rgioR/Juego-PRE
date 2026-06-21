"""Efecto visual de explosión al destruirse un proyectil enemigo.

Reproduce una animación de 8 frames una sola vez
(Assets/Efectos/explosion-1-f/Sprites/explosion-f[1-8].png)
en la posición del proyectil y desaparece al llegar al último frame.
"""

from .OneShotEffect import OneShotEffect


class ExplosionEffect(OneShotEffect):
    """Animación de explosión de un solo uso.

    Parameters
    ----------
    x, y : int
        Centro del proyectil en coordenadas de mundo en el momento de morir.
    frames : list of pygame.Surface
        Los 8 frames cargados desde Assets/Efectos/explosion-1-f/Sprites/.
    cooldown_ms : int
        Milisegundos entre frames (default 55 ms ≈ 18 fps).
    """

    def __init__(self, x: int, y: int, frames: list, cooldown_ms: int = 55):
        super().__init__(x, y, frames, cooldown_ms)
