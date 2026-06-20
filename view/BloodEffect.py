"""Efecto visual de sangre al morir un enemigo.

Reproduce una animación de 21 frames una sola vez
(Assets/Efectos/Blood/1_[1-21].png) en la posición del enemigo
y desaparece al llegar al último frame.
"""

from .OneShotEffect import OneShotEffect


class BloodEffect(OneShotEffect):
    """Animación de muerte de un solo uso.

    Parameters
    ----------
    x, y : int
        Centro del enemigo en coordenadas de mundo en el momento de morir.
    frames : list of pygame.Surface
        Los 21 frames cargados desde Assets/Efectos/Blood/.
    cooldown_ms : int
        Milisegundos entre frames (default 40 ms ≈ 25 fps).
    """

    def __init__(self, x: int, y: int, frames: list, cooldown_ms: int = 40):
        super().__init__(x, y, frames, cooldown_ms)
