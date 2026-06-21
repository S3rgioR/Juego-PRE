"""Utilidades de manipulación de píxeles para efectos visuales (tintes)."""

import numpy
import pygame


def aplicar_tinte(imagen: pygame.Surface, r: int, g: int, b: int,
                  intensidad: float = 0.5) -> pygame.Surface:
    """Devuelve una copia de `imagen` con un tinte de color mezclado.

    Mezcla linealmente cada canal RGB hacia (r, g, b) según `intensidad`
    (0.0 = sin cambio, 1.0 = color sólido), respetando los píxeles
    transparentes (alpha == 0).
    """
    resultado = imagen.convert_alpha()
    arr   = pygame.surfarray.pixels3d(resultado)
    alpha = pygame.surfarray.pixels_alpha(resultado)
    mask  = alpha > 0

    arr[:, :, 0][mask] = numpy.clip(
        arr[:, :, 0][mask] * (1 - intensidad) + r * intensidad, 0, 255
    ).astype(numpy.uint8)
    arr[:, :, 1][mask] = numpy.clip(
        arr[:, :, 1][mask] * (1 - intensidad) + g * intensidad, 0, 255
    ).astype(numpy.uint8)
    arr[:, :, 2][mask] = numpy.clip(
        arr[:, :, 2][mask] * (1 - intensidad) + b * intensidad, 0, 255
    ).astype(numpy.uint8)
    del arr, alpha
    return resultado