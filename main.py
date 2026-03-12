import pygame  # Importa el módulo pygame

import Constantes # Cargar Programa de Constantes
from Personaje import Personaje

jugador =Personaje(250,250)
pygame.init()  # Inicializa pygame

Ventana = pygame.display.set_mode((Constantes.WIDTH, Constantes.HEIGHT))  # Crea la ventana
pygame.display.set_caption("Juego")  # Establece el título



def main():  # Función principal
    mover_arriba = False
    mover_abajo = False
    mover_derecha = False
    mover_izquierda = False
    reloj = pygame.time.Clock()

    jugando = True  # Condición del bucle
    while jugando==True:  # Bucle del juego
        reloj.tick(Constantes.FPS)

        Ventana.fill(Constantes.COLOR_FONDO)

        delta_x=0
        delta_y=0

        if mover_derecha==True:
            delta_x=Constantes.VELOCIDAD
        if mover_izquierda==True:
            delta_x=-Constantes.VELOCIDAD
        if mover_abajo==True:
            delta_y=Constantes.VELOCIDAD
        if mover_arriba==True:
            delta_y=-Constantes.VELOCIDAD

        jugador.movimiento(delta_x,delta_y)

        jugador.draw(Ventana)

        for event in pygame.event.get():  # Obtiene los eventos y los recorre
            if event.type == pygame.QUIT:  # Evento QUIT
                jugando = False  # Salimos del bucle

            if  event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    mover_izquierda=True
                if event.key == pygame.K_d:
                    mover_derecha=True
                if event.key == pygame.K_w:
                    mover_arriba=True
                if event.key == pygame.K_s:
                    mover_abajo=True
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    mover_izquierda=False
                if event.key == pygame.K_d:
                    mover_derecha=False
                if event.key == pygame.K_w:
                    mover_arriba=False
                if event.key == pygame.K_s:
                    mover_abajo=False
        pygame.display.update()

    pygame.quit()  # Cerramos pygame


# Si han ejecutado directamente este archivo, lanzamos main()
if __name__ == "__main__":
    main()