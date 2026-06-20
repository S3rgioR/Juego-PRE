"""Efecto visual de impacto de daga sobre un enemigo.

Reproduce una animación de 3 frames una sola vez
(Assets/Efectos/Hit/Sprites/hit[1-3].png) en el punto de contacto
y desaparece al llegar al último frame.
"""

from .OneShotEffect import OneShotEffect


class HitEffect(OneShotEffect):
    """Animación de impacto de un solo uso.

    Parameters
    ----------
    x, y : int
        Punto de impacto en coordenadas de mundo
        (normalmente el centro del proyectil al colisionar).
    frames : list of pygame.Surface
        Los 3 frames cargados desde Assets/Efectos/Hit/Sprites/.
    cooldown_ms : int
        Milisegundos entre frames (default 60 ms → duración total ~180 ms).
    """

    def __init__(self, x: int, y: int, frames: list, cooldown_ms: int = 60):
        super().__init__(x, y, frames, cooldown_ms)
