"""Sprite visual del Enemigo_1 para pygame.

Responsabilidad: gestionar las animaciones del enemigo y saber dibujarse.
No contiene física, patrulla ni combate — todo eso vive en el Model.
Recibe el estado lógico del Model cada frame a través de `sincronizar()`.
"""

import pygame
import Constantes


class Enemigo1Sprite:
    """Sprite visual del primer tipo de enemigo.

    El sprite sincroniza su posición y estado con el Model en cada frame.

    Attributes
    ----------
    shape : pygame.Rect
        Rectángulo de colisión (sincronizado con el Model).
    anim_walk : list of pygame.Surface
        Frames de la animación de caminar.
    anim_attack : list of pygame.Surface
        Frames de la animación de ataque.
    anim_actual : list of pygame.Surface
        Animación actualmente activa.
    frame_index : int
        Índice del frame actual.
    update_time : int
        Timestamp del último cambio de frame.
    image : pygame.Surface
        Frame actual que se dibuja.
    flip : bool
        True = mirando a la izquierda.
    hitbox_ataque : pygame.Rect or None
        Hitbox de ataque activa, o None.
    """

    def __init__(self, x, y, anim_walk, anim_attack):
        """Inicializa el sprite del enemigo.

        Parameters
        ----------
        x, y : int
            Posición central inicial en coordenadas de mundo.
        anim_walk : list of pygame.Surface
            Frames de caminar.
        anim_attack : list of pygame.Surface
            Frames de ataque.
        """
        self.shape = pygame.Rect(
            0, 0,
            Constantes.WIDTH_PERSONAJE * 2,
            Constantes.HEIGHT_PERSONAJE * 1.5
        )
        self.shape.center = (x, y)

        self.anim_walk = anim_walk
        self.anim_attack = anim_attack
        self.anim_actual = self.anim_walk
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.image = self.anim_actual[0]
        self.flip = True
        self.hitbox_ataque = None

    def sincronizar(self, estado_modelo):
        """Actualiza el sprite con los datos actuales del Model.

        Parameters
        ----------
        estado_modelo : dict con claves:
            'pos'       : (cx, cy) — centro del enemigo
            'flip'      : bool     — dirección que mira
            'atacando'  : bool
            'hitbox_ataque' : pygame.Rect or None
            'vivo'      : bool
        """
        # --- 1. Sincronizar posición ---
        self.shape.center = (
            int(estado_modelo['pos'][0]),
            int(estado_modelo['pos'][1])
        )
        self.flip = estado_modelo['flip']
        self.hitbox_ataque = estado_modelo['hitbox_ataque']

        # --- 2. Seleccionar animación ---
        nueva_anim = self.anim_attack if estado_modelo['atacando'] else self.anim_walk
        if nueva_anim != self.anim_actual:
            self.anim_actual = nueva_anim
            self.frame_index = 0

        # --- 3. Avanzar frame ---
        cooldown = 100
        if pygame.time.get_ticks() - self.update_time > cooldown:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()

        if self.frame_index >= len(self.anim_actual):
            self.frame_index = 0

        self.image = self.anim_actual[self.frame_index]

    def draw(self, interfaz, camara):
        """Dibuja el sprite del enemigo con sus hitboxes de depuración.

        Parameters
        ----------
        interfaz : pygame.Surface
            Superficie principal de la ventana.
        camara : Camara
            Instancia de cámara para transformar coordenadas.
        """
        imagen_flip = pygame.transform.flip(self.image, not self.flip, False)
        img_rect = imagen_flip.get_rect(midbottom=self.shape.midbottom)
        interfaz.blit(imagen_flip, camara.aplicar(img_rect))

        # Debug: hitbox del enemigo
        pygame.draw.rect(interfaz, (255, 0, 0), camara.aplicar(self.shape), 1)

        # Debug: hitbox de ataque
        if self.hitbox_ataque:
            pygame.draw.rect(interfaz, (255, 255, 0), camara.aplicar(self.hitbox_ataque), 2)
