import pygame       # Importa la librería pygame
import Constantes   # Importa nuestro archivo de constantes

class Personaje():                          # Define la clase Personaje
    def __init__(self, x, y):              # Constructor: se ejecuta al crear el personaje
        self.shape = pygame.Rect(          # self → este objeto | shape → su forma/caja
            0, 0,                          # Posición inicial temporal (x=0, y=0)
            Constantes.WIDTH_PERSONAJE,    # Ancho del rectángulo
            Constantes.HEIGHT_PERSONAJE    # Alto del rectángulo
        )
        self.shape.center = (x, y)         # Recoloca el rectángulo para que su centro quede en (x,y)
        self.velocidad_y = 0
        self.en_suelo =False
    def draw(self, interfaz):              # Método para dibujar el personaje
        pygame.draw.rect(                  # pygame → librería | draw → módulo de dibujo | rect → dibuja rectángulo
            interfaz,                      # Superficie donde dibujar (la ventana)
            Constantes.COLOR_PERSONAJE,    # Color del rectángulo
            self.shape                     # El rectángulo a dibujar
        )
    def saltar(self):
        if self.en_suelo:                          # Solo puede saltar si está en el suelo
            self.velocidad_y = Constantes.FUERZA_SALTO  # Aplica la velocidad de salto (hacia arriba)
            self.en_suelo = False
    def movimiento(self, delt_x, delt_y):  # Método para mover el personaje
        self.shape.x += delt_x             # Suma el desplazamiento horizontal a la posición X

        # Colisión con borde izquierdo
        if self.shape.left < 0:
            self.shape.left = 0

        # Colisión con borde derecho
        if self.shape.right > Constantes.WIDTH:
            self.shape.right = Constantes.WIDTH

        # --- Gravedad ---
        self.velocidad_y += Constantes.GRAVEDAD  # Cada fotograma la caída es un poco más rápida

        # Limita la velocidad máxima de caída
        if self.velocidad_y > Constantes.VELOCIDAD_MAX_CAIDA:
            self.velocidad_y = Constantes.VELOCIDAD_MAX_CAIDA

        # --- Movimiento vertical ---
        self.shape.y += self.velocidad_y

        # Colisión con el suelo (borde inferior)
        if self.shape.bottom >= Constantes.HEIGHT:
            self.shape.bottom = Constantes.HEIGHT  # Lo recoloca justo encima del suelo
            self.velocidad_y = 0  # Detiene la caída
            self.en_suelo = True  # Ahora sí está en el suelo

        # Colisión con el techo (borde superior)
        if self.shape.top < 0:
            self.shape.top = 0
            self.velocidad_y = 0
