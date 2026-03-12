import pygame
import Constantes


class Personaje():
    def __init__(self,x,y):
        self.shape=pygame.Rect(0,0,Constantes.WIDTH_PERSONAJE,Constantes.HEIGHT_PERSONAJE)
        self.shape.center=(x,y)

    def draw(self,interfaz):
        pygame.draw.rect(interfaz,Constantes.COLOR_PERSONAJE,self.shape)

    def movimiento(self,delt_x,delt_y):
        self.shape.x+=delt_x
        self.shape.y+=delt_y