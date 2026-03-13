import pygame
# Las constantes son variables fijas que usaremos en todo el juego

#-------- PANTALLA--------#
WIDTH = 1280        # Ancho de la ventana en píxeles
HEIGHT = 720       # Alto de la ventana en píxeles
FPS = 60           # Fotogramas por segundo (velocidad del juego)

#-------- PERSONAJE--------#
WIDTH_PERSONAJE = 21          # Ancho del rectángulo del personaje en píxeles
HEIGHT_PERSONAJE = 40         # Alto del rectángulo del personaje en píxeles
COLOR_PERSONAJE = (255, 0, 255)  # Color del personaje en RGB → magenta
VELOCIDAD = 10                # Píxeles que se mueve el personaje por fotograma
SCALA_PERSONAJE = 0.9

#-------- FONDO--------#
COLOR_FONDO = (0, 100, 100)   # Color del fondo en RGB → verde azulado

#-------- FISICA --------#
GRAVEDAD = 0.5        # Cuánto aumenta la velocidad de caída cada fotograma
FUERZA_SALTO = -12    # Velocidad vertical al saltar (negativa = hacia arriba)
VELOCIDAD_MAX_CAIDA = 20  # Límite de velocidad de caída (para que no caiga infinitamente rápido)