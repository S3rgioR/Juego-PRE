"""Sprite visual del jugador para pygame.

Responsabilidad: gestionar las animaciones del jugador y saber dibujarse.
No contiene física, lógica de salto ni colisiones — todo eso vive en el Model.
La Vista solo necesita saber el estado lógico (que le pasa el Presenter)
para elegir la animación correcta.
"""

import pygame
import Constantes
from .VisualEffects import aplicar_tinte


class PersonajeSprite:
    """Sprite visual del jugador con sistema de animación por estados.

    El sprite sincroniza su posición con el shape del Model cada frame
    (el Model es la fuente de verdad geométrica).

    Attributes
    ----------
    shape : pygame.Rect
        Rectángulo de colisión en coordenadas de mundo (sincronizado con Model).
    frames : dict
        Diccionario de listas de frames por estado:
        {'Parado', 'Andando', 'Saltando', 'AtaqueParado', 'AtaqueSalto'}.
    animaciones : list of pygame.Surface
        Lista de frames de la animación actualmente activa.
    frame_index : int
        Índice del frame actual dentro de `animaciones`.
    update_time : int
        Timestamp del último cambio de frame (para controlar el cooldown).
    image : pygame.Surface
        Frame actual que se dibuja.
    flip : bool
        True = mirando a la izquierda, False = a la derecha.
    hitbox_ataque : pygame.Rect or None
        Rect de la hitbox de ataque activa, o None si no hay ataque.
    """

    def __init__(self, x, y, frames):
        """Inicializa el sprite en la posición dada con sus frames de animación.

        Parameters
        ----------
        x, y : int
            Posición central inicial en coordenadas de mundo.
        frames : dict
            Diccionario con las listas de frames por estado.
        """
        self.shape = pygame.Rect(
            0, 0,
            Constantes.WIDTH_PERSONAJE,
            Constantes.HEIGHT_PERSONAJE
        )
        self.shape.center = (x, y)

        self.frames = frames
        self.animaciones = self.frames['Parado']
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.image = self.animaciones[self.frame_index]
        self.flip = False
        self.hitbox_ataque = None
        self.en_suelo = False

        # --- Animacion puntual de lanzar daga (puramente visual) ---
        # No es un "estado" persistente del Model: es una animacion corta
        # que se reproduce una vez y luego cede el control a la seleccion
        # normal de animacion segun el estado logico del jugador.
        self._lanzando_daga = False
        self._frame_index_lanzar = 0

    def iniciar_animacion_lanzar_daga(self):
        """Activa la animacion corta de lanzar daga (2 frames, sin loop).

        Pensada para ser invocada por la Vista cuando el Presenter confirma
        que la daga se ha lanzado de verdad (daga desbloqueada, etc.).
        """
        if 'LanzarDaga' not in self.frames or not self.frames['LanzarDaga']:
            return
        self._lanzando_daga = True
        self._frame_index_lanzar = 0
        self.update_time = pygame.time.get_ticks()

    def sincronizar(self, estado_modelo):
        """Actualiza el sprite con los datos actuales del Model.

        Recibe un diccionario con el estado lógico del jugador y:
        1. Sincroniza el shape (posición).
        2. Elige la animación correcta según el estado.
        3. Avanza el frame de animación.
        4. Actualiza la hitbox de ataque si procede.

        Parameters
        ----------
        estado_modelo : dict con claves:
            'pos'       : (x, y) — posición centro del personaje
            'flip'      : bool   — dirección que mira
            'atacando'  : bool
            'en_suelo'  : bool
            'moviendose': bool
            'vivo'      : bool
        """
        # --- 1. Sincronizar posición ---
        self.shape.center = (int(estado_modelo['pos'][0]), int(estado_modelo['pos'][1]))
        self.flip = estado_modelo['flip']
        self._iframe_activo = estado_modelo.get('iframe_activo', False)

        # --- 2. Seleccionar animación según estado ---
        atacando  = estado_modelo['atacando']
        en_suelo  = estado_modelo['en_suelo']
        moviendose = estado_modelo['moviendose']

        # La animacion de lanzar daga tiene prioridad visual momentanea:
        # se reproduce una vez (sin loop) y luego vuelve al flujo normal.
        if self._lanzando_daga:
            nueva_anim = self.frames['LanzarDaga']
            if nueva_anim != self.animaciones:
                self.animaciones = nueva_anim
                self.frame_index = self._frame_index_lanzar

            cooldown_animacion = 70
            if pygame.time.get_ticks() - self.update_time > cooldown_animacion:
                self.frame_index += 1
                self.update_time = pygame.time.get_ticks()

            if self.frame_index >= len(self.animaciones):
                # Animacion terminada: ceder el control a la seleccion normal.
                self._lanzando_daga = False
                self.frame_index = 0
            else:
                self.image = self.animaciones[self.frame_index]
                self.hitbox_ataque = None
                return

        if atacando:
            nueva_anim = self.frames['AtaqueSalto'] if not en_suelo else self.frames['AtaqueParado']
        elif not en_suelo:
            nueva_anim = self.frames['Saltando']
        elif moviendose:
            nueva_anim = self.frames['Andando']
        else:
            nueva_anim = self.frames['Parado']

        if nueva_anim != self.animaciones:
            self.animaciones = nueva_anim
            if not atacando:
                self.frame_index = 0

        # --- 3. Avanzar frame ---
        cooldown_animacion = 70
        if pygame.time.get_ticks() - self.update_time > cooldown_animacion:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()

        if self.frame_index >= len(self.animaciones):
            self.frame_index = 0

        self.image = self.animaciones[self.frame_index]

        # --- 4. Hitbox de ataque visual ---
        if atacando:
            self.hitbox_ataque = self._calcular_hitbox_ataque()
        else:
            self.hitbox_ataque = None

    def _calcular_hitbox_ataque(self):
        """Devuelve un Rect delante del personaje según la dirección que mira."""
        ancho_hit = Constantes.WIDTH_PERSONAJE * 3
        alto_hit = self.shape.height
        if self.flip:
            x = self.shape.left - ancho_hit
        else:
            x = self.shape.right
        return pygame.Rect(x, self.shape.top, ancho_hit, alto_hit)

    def draw(self, interfaz, camara):
        """Dibuja el sprite (con flip) y las hitboxes de depuración.

        Parameters
        ----------
        interfaz : pygame.Surface
            Superficie principal de la ventana.
        camara : Camara
            Instancia de cámara para transformar coordenadas.
        """

        imagen_flip = pygame.transform.flip(self.image, self.flip, False)
        img_rect = imagen_flip.get_rect(midbottom=self.shape.midbottom)

        if self._iframe_activo:
            imagen_roja = aplicar_tinte(imagen_flip, r=255, g=0, b=0, intensidad=0.65)

            interfaz.blit(imagen_roja, camara.aplicar(img_rect))
        else:
            interfaz.blit(imagen_flip, camara.aplicar(img_rect))


        # Debug: hitbox del personaje
        if Constantes.DEBUG_HITBOXES:
            pygame.draw.rect(interfaz, Constantes.COLOR_PERSONAJE, camara.aplicar(self.shape), 1)
        # Debug: hitbox de ataque
        if Constantes.DEBUG_HITBOXES and self.hitbox_ataque:
            pygame.draw.rect(interfaz, (255, 255, 0), camara.aplicar(self.hitbox_ataque), 2)
