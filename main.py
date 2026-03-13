import pygame        # Importa la librería pygame
import Constantes    # Importa nuestro archivo de constantes
from Personaje import Personaje  # De Personaje.py importa la clase Personaje

pygame.init()                    # Inicializa todos los módulos internos de pygame

Ventana = pygame.display.set_mode(          # pygame → librería | display → módulo de pantalla | set_mode → crea la ventana
    (Constantes.WIDTH, Constantes.HEIGHT)   # Tamaño de la ventana como tupla (ancho, alto)
)
pygame.display.set_caption("Juego")         # display → módulo de pantalla | set_caption → pone el título en la barra superior

def escalar_img(image,scale):
    w= image.get_width()
    h= image.get_height()
    layer_image = pygame.transform.scale(image, (w * scale,
                                                        h * scale))
    return layer_image
animaciones =[]
for i in range(12):
    img = pygame.image.load(f"Assets/Characters/Run/frame{i+1}.png")
    img = escalar_img(img,Constantes.SCALA_PERSONAJE)
    animaciones.append(img)

player_image=pygame.image.load("Assets/Characters/Run/frame1.png")
player_image = escalar_img(player_image,Constantes.SCALA_PERSONAJE)
jugador = Personaje(250, 250,animaciones)    # Crea un Personaje con el centro en la posición (250, 250)

def main():                    # Define la función principal del juego

    mover_derecha = False      # Bandera: indica si la tecla D está pulsada
    mover_izquierda = False    # Bandera: indica si la tecla A está pulsada

    reloj = pygame.time.Clock()  # pygame → librería | time → módulo de tiempo | Clock() → crea un reloj para controlar los FPS

    jugando = True             # Condición que mantiene el juego activo
    while jugando == True:     # Bucle principal: se repite cada fotograma mientras jugando sea True
        reloj.tick(Constantes.FPS)   # Limita la velocidad a 60 FPS (espera lo necesario entre fotogramas)

        Ventana.fill(Constantes.COLOR_FONDO)  # Rellena toda la ventana con el color de fondo (borra el fotograma anterior)

        delta_x = 0   # Desplazamiento horizontal de este fotograma, empieza en 0
        delta_y = 0   # Desplazamiento vertical de este fotograma, empieza en 0

        # Cada if comprueba las banderas y asigna el desplazamiento correspondiente
        if mover_derecha == True:
            delta_x = Constantes.VELOCIDAD     # Mover derecha → X positiva
        if mover_izquierda == True:
            delta_x = -Constantes.VELOCIDAD    # Mover izquierda → X negativa


        jugador.movimiento(delta_x,0)   # Aplica el desplazamiento calculado al personaje
        jugador.draw(Ventana)                  # Dibuja el personaje en la ventana

        jugador.update()

        for event in pygame.event.get():       # Obtiene todos los eventos ocurridos y los recorre uno a uno
            if event.type == pygame.QUIT:      # Si el evento es cerrar la ventana (X)
                jugando = False                # Sale del bucle en el próximo ciclo

            if event.type == pygame.KEYDOWN:   # Si el evento es pulsar una tecla
                if event.key == pygame.K_a:    # Si esa tecla es la A
                    mover_izquierda = True     # Activa la bandera de moverse a la izquierda
                if event.key == pygame.K_d:
                    mover_derecha = True
                if event.key == pygame.K_SPACE:    # Espacio → saltar
                    jugador.saltar()

            if event.type == pygame.KEYUP:     # Si el evento es soltar una tecla
                if event.key == pygame.K_a:    # Si esa tecla es la A
                    mover_izquierda = False    # Desactiva la bandera
                if event.key == pygame.K_d:
                    mover_derecha = False


        pygame.display.update()   # display → pantalla | update → actualiza la ventana mostrando todo lo dibujado este fotograma

    pygame.quit()   # Cierra pygame y libera todos sus recursos


if __name__ == "__main__":   # Solo se ejecuta si lanzas main.py directamente (no si lo importas desde otro archivo)
    main()                   # Llama a la función principal