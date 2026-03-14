import pygame       # Importa la librería pygame
import Constantes   # Importa nuestro archivo de constantes

class Personaje():                          # Define la clase Personaje
    def __init__(self, x, y,animaciones_idle, animaciones_walk,animaciones_jump):              # Constructor: se ejecuta al crear el personaje
        ### Atributos ###

        self.shape = pygame.Rect(          # self → este objeto | shape → su forma/caja
            0, 0,                          # Posición inicial temporal (x=0, y=0)
            Constantes.WIDTH_PERSONAJE,    # Ancho del rectángulo
            Constantes.HEIGHT_PERSONAJE    # Alto del rectángulo
        )

        self.shape.center = (x, y)         # Recoloca el rectángulo para que su centro quede en (x,y)

        # Animaciones
        self.animaciones_idle = animaciones_idle
        self.animaciones_walk = animaciones_walk
        self.animaciones = animaciones_idle  # empieza en idle
        self.moviendose = False  # nueva bandera
        self.animaciones_jump = animaciones_jump

        # Movimiento/Tiempo
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.image = self.animaciones[self.frame_index]
        self.flip = False
        self.velocidad_y = 0
        self.en_suelo =False

    def update(self):
        cooldown_animacion =100
        self.image = self.animaciones[self.frame_index]
        if pygame.time.get_ticks() - self.update_time > cooldown_animacion:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()
        if self.frame_index >= len(self.animaciones):
            self.frame_index = 0

    def draw(self, interfaz):              # Método para dibujar el personaje
        imagen_flip = pygame.transform.flip(self.image, self.flip, False)
        img_rect = imagen_flip.get_rect(midbottom=self.shape.midbottom)

        interfaz.blit(imagen_flip, img_rect)
        pygame.draw.rect(                  # pygame → librería | draw → módulo de dibujo | rect → dibuja rectángulo
            interfaz,                      # Superficie donde dibujar (la ventana)
            Constantes.COLOR_PERSONAJE,    # Color del rectángulo
            self.shape,                     # El rectángulo a dibujar
            1
        )
    def saltar(self):
        if self.en_suelo:                          # Solo puede saltar si está en el suelo
            self.velocidad_y = Constantes.FUERZA_SALTO  # Aplica la velocidad de salto (hacia arriba)
            self.en_suelo = False
    def movimiento(self, delt_x, delt_y):  # Método para mover el personaje
        if delt_x < 0:
            self.flip= True
            self.moviendose = True
        elif delt_x > 0:
            self.flip= False
            self.moviendose = True
        else:
            self.moviendose = False
        self.shape.x += delt_x             # Suma el desplazamiento horizontal a la posición X

        # Cambia el set de animaciones según el estado
        nueva_anim = self.animaciones_walk if self.moviendose else self.animaciones_idle
        if not self.en_suelo:
            nueva_anim = self.animaciones_jump
        elif self.moviendose:
            nueva_anim = self.animaciones_walk
        else:
            nueva_anim = self.animaciones_idle

        if nueva_anim != self.animaciones:  # solo resetea si cambia de estado
            self.animaciones = nueva_anim
            self.frame_index = 0  # reinicia para no saltar a un frame inexistente
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
