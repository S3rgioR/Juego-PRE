import pygame
# Las constantes son variables fijas que usaremos en todo el juego

#-------- PANTALLA--------#
WIDTH = 1280        # Ancho de la ventana en píxeles
HEIGHT = 720       # Alto de la ventana en píxeles
FPS = 60           # Fotogramas por segundo (velocidad del juego)

#-------- PERSONAJE--------#
image = pygame.image.load("Assets/Characters/Terrible Knight/Sprites/Idle/frame1.png")
SCALA_PERSONAJE = 1.5
WIDTH_PERSONAJE = image.get_width()*0.1*SCALA_PERSONAJE          # Ancho del rectángulo del personaje en píxeles
HEIGHT_PERSONAJE = image.get_height()*0.35*SCALA_PERSONAJE         # Alto del rectángulo del personaje en píxeles
COLOR_PERSONAJE = (255, 0, 255)  # Color del personaje en RGB → magenta
VELOCIDAD = 10                # Píxeles que se mueve el personaje por fotograma


#-------- FONDO--------#
COLOR_FONDO = (0, 100, 100)   # Color del fondo en RGB → verde azulado

#-------- FISICA --------#
GRAVEDAD = 0.6        # Cuánto aumenta la velocidad de caída cada fotograma
FUERZA_SALTO = -15    # Velocidad vertical al saltar (negativa = hacia arriba)
VELOCIDAD_MAX_CAIDA = 20  # Límite de velocidad de caída (para que no caiga infinitamente rápido)