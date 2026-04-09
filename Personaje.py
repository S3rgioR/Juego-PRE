import pygame       # Importa la librería pygame
import Constantes   # Importa nuestro archivo de constantes
import Plataforma

class Personaje():                          # Define la clase Personaje
    def __init__(self, x, y, frames):              # Constructor: se ejecuta al crear el personaje
        ### Atributos ###

        # Creamos rectangulo. Sera la hitbox
        self.shape = pygame.Rect(0, 0,Constantes.WIDTH_PERSONAJE,Constantes.HEIGHT_PERSONAJE)           # self → este objeto | shape → su forma/caja# Posición inicial temporal (x=0, y=0) # Ancho del rectángulo# Alto del rectángulo

        self.shape.center = (x, y)         # Recoloca el rectángulo para que su centro quede en (x,y)

        self.frames = frames

        self.animaciones = self.frames['Parado']  # empieza en idle
        self.moviendose = False
        self.atacando = False
        self.attack_frame_done = False

        # Movimiento/Tiempo
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.image = self.animaciones[self.frame_index]
        self.flip = False
        self.velocidad_y = 0
        self.en_suelo =False

        # Hitbox de ataque
        self.hitbox_ataque = None

        # Coyote time
        self.coyote_time = 300  # milisegundos de margen
        self.coyote_timer = 0  # cuenta atrás activa
    def atacar(self):
        if not self.atacando:  # Evita interrumpir el ataque en curso
            self.atacando = True
            self.frame_index = 0
            self.attack_frame_done = False

    def _calcular_hitbox_ataque(self):
        """Crea un rect delante del personaje según la dirección que mira."""
        ancho_hit = Constantes.WIDTH_PERSONAJE * 3  # 1.5x más ancha que el personaje
        alto_hit = self.shape.height
        if self.flip:  # mirando izquierda
            x = self.shape.left - ancho_hit
        else:  # mirando derecha
            x = self.shape.right
        return pygame.Rect(x, self.shape.top, ancho_hit, alto_hit)

    def update(self):
        cooldown_animacion = 70

        if pygame.time.get_ticks() - self.update_time > cooldown_animacion:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()

        if self.frame_index >= len(self.animaciones):
            if self.atacando:
                self.atacando = False
                self.hitbox_ataque = None  # Desactiva la hitbox
            self.frame_index = 0
        # Actualiza la hitbox de ataque si está activo
        self.image = self.animaciones[self.frame_index]

        if self.atacando:
            self.hitbox_ataque = self._calcular_hitbox_ataque()

    def draw(self, interfaz, camara):
        imagen_flip = pygame.transform.flip(self.image, self.flip, False)
        img_rect = imagen_flip.get_rect(midbottom=self.shape.midbottom)

        # Aplica el offset de cámara
        img_rect = camara.aplicar(img_rect)
        interfaz.blit(imagen_flip, img_rect)

        # Hitboxes desplazadas también
        shape_cam = camara.aplicar(self.shape)
        pygame.draw.rect(interfaz, Constantes.COLOR_PERSONAJE, shape_cam, 1)

        if self.hitbox_ataque:
            hitbox_cam = camara.aplicar(self.hitbox_ataque)
            pygame.draw.rect(interfaz, (255, 255, 0), hitbox_cam, 2)
    def saltar(self):

        if self.en_suelo or self.coyote_timer > 0:
            self.velocidad_y = Constantes.FUERZA_SALTO
            self.en_suelo = False
            self.coyote_timer = 0  # consume el coyote time para no saltar dos veces

    def movimiento(self, delt_x, delt_y, plataformas, reloj):  # Método para mover el personaje
        if delt_x < 0:
            self.flip= True
            self.moviendose = True
        elif delt_x > 0:
            self.flip= False
            self.moviendose = True
        else:
            self.moviendose = False

        # ---  MOVER EN X y resolver colisiones horizontales ---
        self.shape.x += delt_x             # Suma el desplazamiento horizontal a la posición X

        for plat in plataformas:
            if self.shape.colliderect(plat.shape):
                if delt_x > 0:  # venía moviéndose a la derecha
                    self.shape.right = plat.shape.left
                elif delt_x < 0:  # venía moviéndose a la izquierda
                    self.shape.left = plat.shape.right

        # --- MOVER EN Y y resolver colisiones verticales ---
        self.en_suelo = False  # reset cada frame
        self.shape.y += self.velocidad_y

        for plat in plataformas:
            if self.shape.colliderect(plat.shape):
                if self.velocidad_y > 0:  # cayendo → aterrizar encima
                    self.shape.bottom = plat.shape.top
                    self.velocidad_y = 0
                    self.en_suelo = True
                elif self.velocidad_y < 0:  # subiendo → rebotar en el techo
                    self.shape.top = plat.shape.bottom
                    self.velocidad_y = 0

        # Coyote_time
        if self.en_suelo:
            self.coyote_timer = self.coyote_time  # recarga el timer al tocar suelo
        else:
            # descuenta el tiempo transcurrido desde el último frame
            self.coyote_timer -= reloj.get_time()
            if self.coyote_timer < 0:
                self.coyote_timer = 0
        # --- Selección de animación según estado combinado ---
        if self.atacando:
            nueva_anim = self.frames['AtaqueSalto'] if not self.en_suelo else self.frames['AtaqueParado']
        elif not self.en_suelo:
            nueva_anim = self.frames['Saltando']
        elif self.moviendose:
            nueva_anim = self.frames['Andando']
        else:
            nueva_anim = self.frames['Parado']

        if nueva_anim != self.animaciones:  # solo resetea si cambia de estado
            self.animaciones = nueva_anim
            if not self.atacando:  # No reinicia el frame si ya estamos en medio de un ataque
                self.frame_index = 0



        # --- Gravedad ---
        self.velocidad_y += Constantes.GRAVEDAD  # Cada fotograma la caída es un poco más rápida

        # Limita la velocidad máxima de caída
        if self.velocidad_y > Constantes.VELOCIDAD_MAX_CAIDA:
            self.velocidad_y = Constantes.VELOCIDAD_MAX_CAIDA


        # Colisión con el suelo (borde inferior)
        if self.shape.bottom >= Constantes.HEIGHT:
            self.shape.bottom = Constantes.HEIGHT  # Lo recoloca justo encima del suelo
            self.velocidad_y = 0  # Detiene la caída
            self.en_suelo = True  # Ahora sí está en el suelo

        # Colisión con el techo (borde superior)
        if self.shape.top < 0:
            self.shape.top = 0
            self.velocidad_y = 0
