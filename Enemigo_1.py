import pygame
import Constantes

class Enemigo_1():
    def __init__(self, x, y, animaciones, distancia_patrulla=150):
        self.shape = pygame.Rect(0, 0, Constantes.WIDTH_PERSONAJE, Constantes.HEIGHT_PERSONAJE)
        self.shape.center = (x, y)

        # Animaciones
        self.animaciones = animaciones
        self.frame_index = 0
        self.anim_actual = self.animaciones
        self.update_time = pygame.time.get_ticks()
        self.image = self.anim_actual[0]
        self.flip = True

        # Física
        self.velocidad_y = 0
        self.en_suelo = False

        # Patrulla
        self.velocidad = 3
        self.patrol_min = x - distancia_patrulla
        self.patrol_max = x + distancia_patrulla

        # Combate
        self.hp = 3
        self.vivo = True

    def update(self, plataformas):
        if not self.vivo:
            self._tick_animacion()
            return

        self._patrullar()
        self._movimiento(plataformas)
        self._tick_animacion()

    def _patrullar(self):
        if self.shape.x <= self.patrol_min:
            self.flip = True
        elif self.shape.right >= self.patrol_max:
            self.flip = False

        self.shape.x += -self.velocidad if self.flip else self.velocidad

    def _movimiento(self, plataformas):
        self.velocidad_y += Constantes.GRAVEDAD
        if self.velocidad_y > Constantes.VELOCIDAD_MAX_CAIDA:
            self.velocidad_y = Constantes.VELOCIDAD_MAX_CAIDA

        # --- COLISIONES HORIZONTALES ---
        for plat in plataformas:
            if self.shape.colliderect(plat.shape):
                if self.flip:  # moviéndose a la izquierda
                    self.shape.left = plat.shape.right
                else:  # moviéndose a la derecha
                    self.shape.right = plat.shape.left

        # --- COLISIONES VERTICALES ---
        self.en_suelo = False
        self.shape.y += self.velocidad_y

        for plat in plataformas:
            if self.shape.colliderect(plat.shape):
                if self.velocidad_y > 0:
                    self.shape.bottom = plat.shape.top
                    self.velocidad_y = 0
                    self.en_suelo = True
                elif self.velocidad_y < 0:
                    self.shape.top = plat.shape.bottom
                    self.velocidad_y = 0

    def recibir_daño(self, daño):
        if not self.vivo:
            return
        self.hp -= daño
        if self.hp <= 0:
            self.hp = 0
            self.vivo = False
            self.frame_index = 0

    def _tick_animacion(self):
        cooldown = 100
        if pygame.time.get_ticks() - self.update_time > cooldown:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()

        if self.frame_index >= len(self.anim_actual):
            self.frame_index = 0

        self.image = self.anim_actual[self.frame_index]

    def draw(self, interfaz, camara):
        imagen_flip = pygame.transform.flip(self.image, not self.flip, False)
        img_rect = imagen_flip.get_rect(midbottom=self.shape.midbottom)
        interfaz.blit(imagen_flip, camara.aplicar(img_rect))
        pygame.draw.rect(interfaz, (255, 0, 0), camara.aplicar(self.shape), 1)
