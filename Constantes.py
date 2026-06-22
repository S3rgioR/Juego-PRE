"""Constantes globales del juego.

IMPORTANTE: Este módulo NO carga imágenes al importarse.
En la versión original, cargar pygame.image.load() a nivel de módulo
obligaba a que pygame estuviese inicializado antes de cualquier import,
lo que rompía el orden de inicialización en el patrón MVP.

Las dimensiones del personaje se calculan en main.py tras cargar
la primera imagen, y se inyectan aquí antes de construir Model y View.
"""

# -------- PANTALLA -------- #
WIDTH  = 1280
HEIGHT = 720
FPS    = 60

# -------- PERSONAJE -------- #
# Estas dos constantes se sobreescriben desde main.py tras cargar la imagen.
# Se definen aquí con valores de fallback razonables.
SCALA_PERSONAJE  = 1.5
WIDTH_PERSONAJE  = 30    # Sobreescrito en main.py
HEIGHT_PERSONAJE = 60    # Sobreescrito en main.py
COLOR_PERSONAJE  = (255, 0, 255)
VELOCIDAD        = 10

# -------- SUELO -------- #
SUELO_Y = 656   # Y fija del suelo base en coordenadas pygame

# -------- FONDO -------- #
COLOR_FONDO = (0, 100, 100)

# -------- FÍSICA -------- #
GRAVEDAD           = 0.6
FUERZA_SALTO       = -15
VELOCIDAD_MAX_CAIDA = 20

DEBUG_HITBOXES =False