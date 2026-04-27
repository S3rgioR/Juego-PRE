import pygame
import Constantes

class Enemigo_1():
    def __init__(self, x, y, anim_enemigo_walk, anim_enemigo_attack, distancia_patrulla=150):
        self.shape = pygame.Rect(0, 0, Constantes.WIDTH_PERSONAJE*2, Constantes.HEIGHT_PERSONAJE*1.5)
        self.shape.center = (x, y)

        # Animaciones
        self.anim_enemigo_walk = anim_enemigo_walk
        self.anim_enemigo_attack = anim_enemigo_attack  # ← nueva lista de frames
        self.anim_actual = self.anim_enemigo_walk
        self.frame_index = 0
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
        self.hp = 5
        self.vivo = True

        # --- visión y ataque ---
        self.rango_vision = 300  # píxeles de distancia máxima para ver al jugador
        self.atacando = False
        self.hitbox_ataque = None
        self.cooldown_ataque = 1200  # ms entre ataques
        self.ultimo_ataque = -self.cooldown_ataque  # listo desde el inicio

    def update(self, plataformas, jugador):
        if not self.vivo:
            self._tick_animacion()
            return

        ahora = pygame.time.get_ticks()
        cooldown_listo = (ahora - self.ultimo_ataque) >= self.cooldown_ataque

        if self._jugador_en_vision(jugador) and cooldown_listo and not self.atacando:
            # Iniciar ataque
            self.atacando = True
            self.frame_index = 0
            self.anim_actual = self.anim_enemigo_attack
            self.ultimo_ataque = ahora
            self.hitbox_ataque = self._calcular_hitbox_ataque()
        elif not self.atacando:
            self.hitbox_ataque = None
            self.anim_actual = self.anim_enemigo_walk
            self._patrullar()

        self._movimiento(plataformas)
        self._tick_animacion()

    def _patrullar(self):
        if self.shape.x <= self.patrol_min:
            self.flip = False
        elif self.shape.right >= self.patrol_max:
            self.flip = True

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
                    self.flip= False
                else:  # moviéndose a la derecha
                    self.shape.right = plat.shape.left
                    self.flip = True

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
            if self.atacando:
                # Animación de ataque terminó
                self.atacando = False
                self.hitbox_ataque = None
                self.anim_actual = self.anim_enemigo_walk

        self.image = self.anim_actual[self.frame_index]

    def _jugador_en_vision(self, jugador):
        """True si el jugador está en el lado que mira y dentro del rango."""
        dx = jugador.shape.centerx - self.shape.centerx-200

        # self.flip=True → mira izquierda → dx negativo = en frente
        mirando_al_jugador = (self.flip and dx < 0) or (not self.flip and dx > 0)
        cerca = abs(dx) <= self.rango_vision

        return mirando_al_jugador and cerca

    def _calcular_hitbox_ataque(self):
        ancho_hit = Constantes.WIDTH_PERSONAJE * 4
        if self.flip:
            x = self.shape.left - ancho_hit
        else:
            x = self.shape.right
        return pygame.Rect(x, self.shape.top, ancho_hit, self.shape.height)


    def draw(self, interfaz, camara):
        imagen_flip = pygame.transform.flip(self.image, not self.flip, False)
        img_rect = imagen_flip.get_rect(midbottom=self.shape.midbottom)
        interfaz.blit(imagen_flip, camara.aplicar(img_rect))
        pygame.draw.rect(interfaz, (255, 0, 0), camara.aplicar(self.shape), 1)
        if self.hitbox_ataque:
            hitbox_cam = camara.aplicar(self.hitbox_ataque)
            pygame.draw.rect(interfaz, (255, 255, 0), hitbox_cam, 2)