"""Sprite visual del Enemigo_2 para pygame.

Enemigo volador que patrulla horizontalmente en el aire.
No puede atacar, solo recibe daño igual que el Enemigo_1.

Responsabilidad: gestionar las animaciones del enemigo y saber dibujarse.
No contiene física, patrulla ni combate — todo eso vive en el Model.
Recibe el estado lógico del Model cada frame a través de `sincronizar()`.
"""

import pygame
import Constantes
import numpy
import math


class Enemigo2Sprite:
    """Sprite visual del segundo tipo de enemigo (volador).

    El sprite sincroniza su posición y estado con el Model en cada frame.
    Añade un efecto de flotación sinusoidal visual (solo estético, no afecta
    a la hitbox del Model).

    Attributes
    ----------
    shape : pygame.Rect
        Rectángulo de colisión (sincronizado con el Model).
    anim_walk : list of pygame.Surface
        Frames de la animación de vuelo (se reutiliza la de caminar del asset).
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
    _flotacion_offset : float
        Desplazamiento vertical visual por el efecto de flotación (píxeles).
    _flotacion_tiempo : float
        Acumulador de tiempo para la onda sinusoidal.
    """

    def __init__(self, x, y, anim_walk):
        """Inicializa el sprite del enemigo volador.

        Parameters
        ----------
        x, y : int
            Posición central inicial en coordenadas de mundo.
        anim_walk : list of pygame.Surface
            Frames de la animación de vuelo.
        """
        self.shape = pygame.Rect(
            0, 0,
            Constantes.WIDTH_PERSONAJE * 2,
            Constantes.HEIGHT_PERSONAJE * 1.5
        )
        self.shape.center = (x, y)

        self.anim_walk   = anim_walk
        self.anim_actual = self.anim_walk
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.image       = self.anim_actual[0]
        self.flip        = True

        # Sin hitbox de ataque: siempre None
        self.hitbox_ataque = None

        self._iframe_activo    = False
        self._flotacion_offset = 0.0
        self._flotacion_tiempo = 0.0

    def sincronizar(self, estado_modelo):
        """Actualiza el sprite con los datos actuales del Model.

        Parameters
        ----------
        estado_modelo : dict con claves:
            'pos'           : (cx, cy) — centro del enemigo
            'flip'          : bool     — dirección que mira
            'vivo'          : bool
            'iframe_activo' : bool
        """
        # --- 1. Sincronizar posición ---
        self.shape.center = (
            int(estado_modelo['pos'][0]),
            int(estado_modelo['pos'][1])
        )
        self.flip = estado_modelo['flip']
        self._iframe_activo = estado_modelo.get('iframe_activo', False)

        # --- 2. Actualizar efecto flotación (visual, no afecta shape) ---
        self._flotacion_tiempo += 0.05   # velocidad de la onda
        self._flotacion_offset = math.sin(self._flotacion_tiempo) * 6

        # --- 3. Avanzar frame de animación ---
        cooldown = 120  # ms entre frames (ligeramente más lento que el ogre)
        if pygame.time.get_ticks() - self.update_time > cooldown:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()

        if self.frame_index >= len(self.anim_actual):
            self.frame_index = 0

        self.image = self.anim_actual[self.frame_index]

    def draw(self, interfaz, camara):
        """Dibuja el sprite del enemigo volador con efecto de flotación y depuración.

        Parameters
        ----------
        interfaz : pygame.Surface
            Superficie principal de la ventana.
        camara : Camara
            Instancia de cámara para transformar coordenadas.
        """
        imagen_flip = pygame.transform.flip(self.image, not self.flip, False)

        # El rect visual se desplaza por la flotación (estético, sin tocar shape)
        img_rect = imagen_flip.get_rect(midbottom=self.shape.midbottom)
        img_rect.y += int(self._flotacion_offset)

        # Efecto rojo durante los iframes
        if self._iframe_activo:
            imagen_roja = imagen_flip.convert_alpha()
            arr   = pygame.surfarray.pixels3d(imagen_roja)
            alpha = pygame.surfarray.pixels_alpha(imagen_roja)
            mask = alpha > 0
            arr[:, :, 0][mask] = numpy.minimum(255, arr[:, :, 0][mask].astype(int) + 150)
            arr[:, :, 1][mask] = arr[:, :, 1][mask] // 2
            arr[:, :, 2][mask] = arr[:, :, 2][mask] // 2
            del arr, alpha
            interfaz.blit(imagen_roja, camara.aplicar(img_rect))
        else:
            interfaz.blit(imagen_flip, camara.aplicar(img_rect))

        # Debug: hitbox del enemigo
        pygame.draw.rect(interfaz, (0, 180, 255), camara.aplicar(self.shape), 1)
