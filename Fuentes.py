"""Gestión centralizada de la fuente del juego.

Carga la fuente .ttf del juego una sola vez por cada tamaño solicitado
(cache interna) y la reutiliza en todos los menús, HUD y secuencias.
Si el archivo no se puede cargar (no existe, ruta incorrecta, etc.),
cae automáticamente a la fuente de sistema por defecto para que el
juego nunca se rompa por un asset de fuente ausente.

Uso
---
    import Fuentes
    fuente = Fuentes.obtener_fuente(36)
    texto  = fuente.render("Hola", True, (255, 255, 255))
"""

import pygame
from Import import obtener_ruta


RUTA_FUENTE = obtener_ruta("Assets/Font/DungeonFont.ttf")

# Cache: tamaño (int) -> pygame.font.Font
_cache_fuentes: dict[int, "pygame.font.Font"] = {}

# Una vez que falla la carga del .ttf, no se vuelve a intentar
# (evita repetir el mismo print de error en cada tamaño nuevo).
_fuente_no_disponible = False


def obtener_fuente(tamaño: int) -> "pygame.font.Font":
    """Devuelve la fuente del juego en el tamaño indicado.

    La instancia se crea una sola vez por tamaño y se reutiliza en
    llamadas posteriores. Si el .ttf no está disponible, devuelve
    pygame.font.SysFont(None, tamaño) como alternativa segura.

    Parameters
    ----------
    tamaño : int
        Tamaño en puntos de la fuente.

    Returns
    -------
    pygame.font.Font
    """
    global _fuente_no_disponible

    if tamaño in _cache_fuentes:
        return _cache_fuentes[tamaño]

    if not _fuente_no_disponible:
        try:
            fuente = pygame.font.Font(RUTA_FUENTE, tamaño)
            _cache_fuentes[tamaño] = fuente
            return fuente
        except Exception as e:
            print(f"[Fuentes] ✗ No se pudo cargar '{RUTA_FUENTE}': {e!r}. "
                  f"Usando fuente de sistema como alternativa.")
            _fuente_no_disponible = True

    fuente = pygame.font.SysFont(None, tamaño)
    _cache_fuentes[tamaño] = fuente
    return fuente
