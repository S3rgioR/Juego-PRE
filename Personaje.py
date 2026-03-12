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

    def draw(self, interfaz):              # Método para dibujar el personaje
        pygame.draw.rect(                  # pygame → librería | draw → módulo de dibujo | rect → dibuja rectángulo
            interfaz,                      # Superficie donde dibujar (la ventana)
            Constantes.COLOR_PERSONAJE,    # Color del rectángulo
            self.shape                     # El rectángulo a dibujar
        )

    def movimiento(self, delt_x, delt_y):  # Método para mover el personaje
        self.shape.x += delt_x             # Suma el desplazamiento horizontal a la posición X
        self.shape.y += delt_y             # Suma el desplazamiento vertical a la posición Y