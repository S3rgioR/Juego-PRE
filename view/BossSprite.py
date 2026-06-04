"""Sprite visual del Boss para pygame.

Responsabilidad: gestionar las animaciones del boss y saber dibujarse.
No contiene física ni IA — todo eso vive en BossModel.
Recibe el estado lógico del Model cada frame a través de sincronizar().

Animaciones
-----------
Fase 1  : Assets/Characters/Fire-Skull-Files/Sprites/NoFire/frame[1-4].png
Fase 2  : Assets/Characters/Fire-Skull-Files/Sprites/Fire/frame[1-8].png
Embestida: frame congelado en frame4 de la fase actual + tinte rojo intenso.

Efectos visuales
----------------
- Iframes normales : tinte rojo suave (igual que otros enemigos).
- Embestida        : tinte rojo intenso + más opaco (diferenciado).
- Flotación        : ondulación sinusoidal vertical (solo estética).
- Barra de vida    : dibujada en pantalla encima del boss (coordenadas pantalla).
"""

import math
import pygame
import numpy
import Constantes


class BossSprite:
    """Sprite visual del boss: cráneo de fuego volador.

    Attributes
    ----------
    shape : pygame.Rect
        Rectángulo de colisión (sincronizado con el Model).
    anim_fase1 : list of pygame.Surface
        Frames de la animación en fase 1 (NoFire).
    anim_fase2 : list of pygame.Surface
        Frames de la animación en fase 2 (Fire).
    anim_actual : list of pygame.Surface
        Animación activa en este momento.
    frame_index : int
        Índice del frame actual.
    proyectil_frames : list of pygame.Surface
        Frames del proyectil (asignados desde la Vista tras cargar assets).
    """

    # Cooldown de animación (ms entre frames)
    COOLDOWN_ANIM_F1 = 150
    COOLDOWN_ANIM_F2 = 100   # fase 2 anima más rápido

    # Dimensiones de la barra de vida (en píxeles de pantalla)
    BARRA_ANCHO  = 220
    BARRA_ALTO   = 14
    BARRA_Y      = 20   # px desde el borde superior de la pantalla
    BARRA_X      = Constantes.WIDTH // 2 - 110   # centrada horizontalmente

    def __init__(self, x, y, anim_fase1, anim_fase2):
        """Inicializa el sprite del boss.

        Parameters
        ----------
        x, y        : int   — posición central inicial en coordenadas de mundo.
        anim_fase1  : list  — frames NoFire (4 frames).
        anim_fase2  : list  — frames Fire  (8 frames).
        """
        self.shape = pygame.Rect(
            0, 0,
            int(Constantes.WIDTH_PERSONAJE  * 3),
            int(Constantes.HEIGHT_PERSONAJE * 2),
        )
        self.shape.center = (x, y)

        self.anim_fase1 = anim_fase1
        self.anim_fase2 = anim_fase2
        self.anim_actual = self.anim_fase1

        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.image       = self.anim_actual[0]
        self.flip        = False

        # Estado visual
        self._iframe_activo    = False
        self._embestida_activa = False
        self._frame_congelado  = False
        self._fase             = 1
        self._hp               = 50
        self._hp_max           = 50

        # Flotación
        self._flotacion_offset = 0.0
        self._flotacion_tiempo = 0.0

        # Proyectiles
        self.proyectil_frames     = []   # asignados desde la Vista
        self._sprites_proyectiles = {}   # índice → ProyectilBossSprite

        # Fuente para la barra de vida
        self._fuente = None

    # -----------------------------------------------------------------------
    # Sincronización con el Model
    # -----------------------------------------------------------------------

    def sincronizar(self, estado_modelo):
        """Actualiza el sprite con los datos actuales del BossModel.

        Parameters
        ----------
        estado_modelo : dict
            'pos'              : (cx, cy)
            'flip'             : bool
            'iframe_activo'    : bool
            'embestida_activa' : bool
            'frame_congelado'  : bool  — True = congelar en frame4
            'fase'             : int   — 1 o 2
            'hp'               : int
            'hp_max'           : int
        """
        # Posición
        self.shape.center = (
            int(estado_modelo['pos'][0]),
            int(estado_modelo['pos'][1]),
        )
        self.flip = estado_modelo['flip']

        # Flags visuales
        self._iframe_activo    = estado_modelo.get('iframe_activo',    False)
        self._embestida_activa = estado_modelo.get('embestida_activa', False)
        self._frame_congelado  = estado_modelo.get('frame_congelado',  False)
        self._fase             = estado_modelo.get('fase',             1)
        self._hp               = estado_modelo.get('hp',               self._hp)
        self._hp_max           = estado_modelo.get('hp_max',           self._hp_max)

        # Flotación sinusoidal (visual puro)
        self._flotacion_tiempo += 0.04
        self._flotacion_offset  = math.sin(self._flotacion_tiempo) * 5

        # Seleccionar animación según fase
        nueva_anim = self.anim_fase2 if self._fase == 2 else self.anim_fase1
        if nueva_anim != self.anim_actual:
            self.anim_actual = nueva_anim
            self.frame_index = 0

        # Avanzar frame (a menos que esté congelado)
        if not self._frame_congelado:
            cooldown = (self.COOLDOWN_ANIM_F2
                        if self._fase == 2
                        else self.COOLDOWN_ANIM_F1)
            if pygame.time.get_ticks() - self.update_time > cooldown:
                self.frame_index += 1
                self.update_time  = pygame.time.get_ticks()

            if self.frame_index >= len(self.anim_actual):
                self.frame_index = 0
        else:
            # Congelar en frame4 (índice 3, base 0)
            self.frame_index = min(3, len(self.anim_actual) - 1)

        self.image = self.anim_actual[self.frame_index]

    # -----------------------------------------------------------------------
    # Dibujo
    # -----------------------------------------------------------------------

    def draw(self, interfaz, camara, estado_modelo=None):
        """Dibuja el boss, sus efectos y la barra de vida.

        Parameters
        ----------
        interfaz      : pygame.Surface  — superficie principal.
        camara        : Camara          — transforma coordenadas mundo→pantalla.
        estado_modelo : dict            — mismo dict que sincronizar().
        """
        if self._fuente is None:
            self._fuente = pygame.font.SysFont(None, 18)

        imagen_flip = pygame.transform.flip(self.image, not self.flip, False)
        img_rect = imagen_flip.get_rect(midbottom=self.shape.midbottom)
        img_rect.y += int(self._flotacion_offset)

        # --- Efecto de color ---
        if self._embestida_activa:
            # Rojo intenso + más opaco (diferente al iframe normal)
            img_final = self._aplicar_tinte(imagen_flip, r=220, g=0, b=0, intensidad=0.75)
        elif self._iframe_activo:
            # Rojo suave estándar
            img_final = self._aplicar_tinte(imagen_flip, r=180, g=0, b=0, intensidad=0.40)
        else:
            img_final = imagen_flip

        interfaz.blit(img_final, camara.aplicar(img_rect))

        # Debug: hitbox
        pygame.draw.rect(interfaz, (255, 50, 200), camara.aplicar(self.shape), 1)

        # --- Barra de vida (en coordenadas de pantalla, no de mundo) ---
        self._dibujar_barra_vida(interfaz)

        # --- Proyectiles ---
        if estado_modelo:
            proyectiles_vivos = [
                ep for ep in estado_modelo.get('proyectiles', []) if ep['vivo']
            ]
            # Ajustar pool de sprites de proyectiles
            while len(self._sprites_proyectiles) < len(proyectiles_vivos):
                idx = len(self._sprites_proyectiles)
                self._sprites_proyectiles[idx] = ProyectilBossSprite(
                    self.proyectil_frames
                )
            while len(self._sprites_proyectiles) > len(proyectiles_vivos):
                self._sprites_proyectiles.pop(len(self._sprites_proyectiles) - 1)

            for i, ep in enumerate(proyectiles_vivos):
                self._sprites_proyectiles[i].draw(interfaz, camara, ep)

    def _aplicar_tinte(self, imagen, r, g, b, intensidad=0.5):
        """Devuelve una copia de la imagen con un tinte de color mezclado."""
        resultado = imagen.convert_alpha()
        arr   = pygame.surfarray.pixels3d(resultado)
        alpha = pygame.surfarray.pixels_alpha(resultado)
        mask  = alpha > 0

        arr[:, :, 0][mask] = numpy.clip(
            arr[:, :, 0][mask] * (1 - intensidad) + r * intensidad, 0, 255
        ).astype(numpy.uint8)
        arr[:, :, 1][mask] = numpy.clip(
            arr[:, :, 1][mask] * (1 - intensidad) + g * intensidad, 0, 255
        ).astype(numpy.uint8)
        arr[:, :, 2][mask] = numpy.clip(
            arr[:, :, 2][mask] * (1 - intensidad) + b * intensidad, 0, 255
        ).astype(numpy.uint8)
        del arr, alpha
        return resultado

    def _dibujar_barra_vida(self, interfaz):
        """Dibuja la barra de vida del boss en la parte superior de la pantalla."""
        ratio  = max(0.0, self._hp / self._hp_max)
        llena  = int(self.BARRA_ANCHO * ratio)

        # Fondo oscuro
        pygame.draw.rect(
            interfaz, (40, 0, 0),
            (self.BARRA_X - 2, self.BARRA_Y - 2,
             self.BARRA_ANCHO + 4, self.BARRA_ALTO + 4),
        )
        # Relleno rojo
        if llena > 0:
            color_barra = (200, 0, 0) if self._fase == 1 else (255, 80, 0)
            pygame.draw.rect(
                interfaz, color_barra,
                (self.BARRA_X, self.BARRA_Y, llena, self.BARRA_ALTO),
            )
        # Borde
        pygame.draw.rect(
            interfaz, (180, 180, 180),
            (self.BARRA_X - 2, self.BARRA_Y - 2,
             self.BARRA_ANCHO + 4, self.BARRA_ALTO + 4),
            1,
        )
        # Etiqueta
        label = self._fuente.render("BOSS", True, (220, 220, 220))
        interfaz.blit(label, (self.BARRA_X - label.get_width() - 6,
                               self.BARRA_Y))


# ---------------------------------------------------------------------------
# Sprite visual de los proyectiles del boss
# ---------------------------------------------------------------------------

class ProyectilBossSprite:
    """Sprite visual de un proyectil del boss con escala variable."""

    def __init__(self, frames):
        self.frames      = frames
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.shape       = pygame.Rect(
            0, 0,
            frames[0].get_width(),
            frames[0].get_height(),
        )

    def draw(self, interfaz, camara, estado):
        """Dibuja el proyectil escalado según su 'escala' en el estado."""
        escala = estado.get('escala', 1.0)

        # Avanzar animación
        if pygame.time.get_ticks() - self.update_time > 80:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.update_time = pygame.time.get_ticks()

        frame_base = self.frames[self.frame_index]

        # Escalar si es necesario
        if escala != 1.0:
            w = int(frame_base.get_width()  * escala)
            h = int(frame_base.get_height() * escala)
            frame_base = pygame.transform.scale(frame_base, (w, h))

        imagen = pygame.transform.flip(frame_base, estado['flip'], False)

        self.shape = imagen.get_rect()
        self.shape.center = (int(estado['pos'][0]), int(estado['pos'][1]))

        interfaz.blit(imagen, camara.aplicar(self.shape))

        # Debug: hitbox naranja para proyectiles normales, amarilla para grandes
        color_debug = (255, 200, 0) if escala > 1.5 else (255, 140, 0)
        pygame.draw.rect(interfaz, color_debug, camara.aplicar(self.shape), 1)
