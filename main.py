import pygame        # Importa la librería pygame
import Constantes    # Importa nuestro archivo de constantes
from Camara import Camara
from Personaje import Personaje  # De Personaje.py importa la clase Personaje
from Nivel import cargar_nivel_1
from Enemigo_1 import Enemigo_1
pygame.init()                    # Inicializa todos los módulos internos de pygame

Ventana = pygame.display.set_mode(          # pygame → librería | display → módulo de pantalla | set_mode → crea la ventana
    (Constantes.WIDTH, Constantes.HEIGHT)   # Tamaño de la ventana como tupla (ancho, alto)
)
pygame.display.set_caption("Juego")         # display → módulo de pantalla | set_caption → pone el título en la barra superior

camara = Camara()

def escalar_img(image,scale):
    w= image.get_width()
    h= image.get_height()
    layer_image = pygame.transform.scale(image, (w * scale,
                                                        h * scale))
    return layer_image

# Animaciones idle (ya las tienes)
animaciones_idle = []
for i in range(4):
    img = pygame.image.load(f"Assets/Characters/Terrible Knight/Sprites/Idle/frame{i+1}.png")
    img = escalar_img(img, Constantes.SCALA_PERSONAJE)
    animaciones_idle.append(img)

# Animaciones de caminar (ajusta la ruta y el número de frames a tus sprites)
animaciones_walk = []
for i in range(12):  # cambia 6 por el número de frames que tengas
    img = pygame.image.load(f"Assets/Characters/Terrible Knight/Sprites/Run/frame{i+1}.png")
    img = escalar_img(img, Constantes.SCALA_PERSONAJE)
    animaciones_walk.append(img)

animaciones_jump = []
for i in range(4):  # ajusta el número de frames
    img = pygame.image.load(f"Assets/Characters/Terrible Knight/Sprites/Jump/Jump{i+1}.png")
    img = escalar_img(img, Constantes.SCALA_PERSONAJE)
    animaciones_jump.append(img)

animaciones_attack_idle = []
for i in range(4):  # ajusta el número de frames
    img = pygame.image.load(f"Assets/Characters/Terrible Knight/Sprites/SwordSlash/frame{i+1}.png")
    img = escalar_img(img, Constantes.SCALA_PERSONAJE)
    animaciones_attack_idle.append(img)

animaciones_attack_jump = []
for i in range(6):  # ajusta el número de frames
    img = pygame.image.load(f"Assets/Characters/Terrible Knight/Sprites/AirSwordSlash/AirSwordSlash-export{i+1}.png")
    img = escalar_img(img, Constantes.SCALA_PERSONAJE)
    animaciones_attack_jump.append(img)

frames = {'Parado': animaciones_idle,
          'Andando': animaciones_walk,
          'Saltando': animaciones_jump,
          'AtaqueParado': animaciones_attack_idle,
          'AtaqueSalto': animaciones_attack_jump}

# Pasa ambas listas al personaje
jugador = Personaje(250, 250, frames)
anim_enemigo_attack=[]
for i in range(6):  # ajusta el número de frames
    img = pygame.image.load(f"Assets/Characters/Ogre/Sprites/Attack/ogre-attack{1+i}.png")
    img = escalar_img(img, Constantes.SCALA_PERSONAJE)
    anim_enemigo_attack.append(img)
anim_enemigo_walk=[]
for i in range(6):  # ajusta el número de frames
    img = pygame.image.load(f"Assets/Characters/Ogre/Sprites/walk/ogre-walk{1+i}.png")
    img = escalar_img(img, Constantes.SCALA_PERSONAJE)
    anim_enemigo_walk.append(img)
def main():                    # Define la función principal del juego
    enemigos = [
        Enemigo_1(600, 400, anim_enemigo_walk,anim_enemigo_attack, distancia_patrulla=2000),
        Enemigo_1(1500, 400, anim_enemigo_walk,anim_enemigo_attack, distancia_patrulla=10000),
    ]
    mover_derecha = False      # Bandera: indica si la tecla D está pulsada
    mover_izquierda = False    # Bandera: indica si la tecla A está pulsada

    reloj = pygame.time.Clock()  # pygame → librería | time → módulo de tiempo | Clock() → crea un reloj para controlar los FPS

    # Seleccionar fondo
    fondo = pygame.image.load("Assets/Enviorments/caverns-files-web/layers/background.png")
    fondo = pygame.transform.scale(fondo, (Constantes.WIDTH, Constantes.HEIGHT))

    fondo_walls = pygame.image.load("Assets/Enviorments/caverns-files-web/layers/back-walls.png")
    fondo_walls = pygame.transform.scale(fondo_walls, (Constantes.WIDTH, Constantes.HEIGHT))

    # Tilesets
    tileset = pygame.image.load("Assets/Enviorments/caverns-files-web/layers/tiles_mini.png").convert_alpha()
    plataformas = cargar_nivel_1(tileset)

    jugando = True             # Condición que mantiene el juego activo
    while jugando == True:     # Bucle principal: se repite cada fotograma mientras jugando sea True
        reloj.tick(Constantes.FPS)   # Limita la velocidad a 60 FPS (espera lo necesario entre fotogramas)

        # Actualizar cámara (antes de dibujar)
        camara.update(jugador)

        # Fondo — el fondo estático NO se desplaza con la cámara
        Ventana.blit(fondo, (0, 0))
        Ventana.blit(fondo_walls, (0, 0))

        # Plataformas — sí se desplazan
        for plat in plataformas:
            plat.draw(Ventana, camara)
        # Enemigo
        for enemigo in enemigos:
            enemigo.update(plataformas, jugador)
            enemigo.draw(Ventana, camara)
        # Jugador — sí se desplaza
        jugador.draw(Ventana, camara)

        delta_x = 0   # Desplazamiento horizontal de este fotograma, empieza en 0
        delta_y = 0   # Desplazamiento vertical de este fotograma, empieza en 0

        # Ataque
        if jugador.hitbox_ataque:
            for enemigo in enemigos:
                if jugador.hitbox_ataque.colliderect(enemigo.shape) and enemigo.vivo:
                    enemigo.recibir_daño(1)

        enemigos = [enemigo for enemigo in enemigos if enemigo.vivo]

        # Cada if comprueba las banderas y asigna el desplazamiento correspondiente
        if mover_derecha == True:
            delta_x = Constantes.VELOCIDAD     # Mover derecha → X positiva
        if mover_izquierda == True:
            delta_x = -Constantes.VELOCIDAD    # Mover izquierda → X negativa


        jugador.movimiento(delta_x, 0, plataformas,reloj)   # Aplica el desplazamiento calculado al personaje

        jugador.update()

        for enemigo in enemigos:
            if enemigo.hitbox_ataque and enemigo.hitbox_ataque.colliderect(jugador.shape):
                jugador.recibir_daño(1)

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
                if event.key == pygame.K_j:
                    jugador.atacar()

            if event.type == pygame.KEYUP:     # Si el evento es soltar una tecla
                if event.key == pygame.K_a:    # Si esa tecla es la A
                    mover_izquierda = False    # Desactiva la bandera
                if event.key == pygame.K_d:
                    mover_derecha = False


        pygame.display.update()   # display → pantalla | update → actualiza la ventana mostrando todo lo dibujado este fotograma

    pygame.quit()   # Cierra pygame y libera todos sus recursos


if __name__ == "__main__":   # Solo se ejecuta si lanzas main.py directamente (no si lo importas desde otro archivo)
    main()                   # Llama a la función principal