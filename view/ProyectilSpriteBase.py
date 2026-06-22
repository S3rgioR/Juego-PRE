"""Clase base mínima para sprites de proyectil.

Cubre solo el manejo de animación por frames, que es idéntico en
ProyectilSprite (Enemigo_2), ProyectilBossSprite (BossSprite) y
DagaProyectilSprite:
  - Guardar la lista de frames, el índice actual y el reloj de cambio
    de frame.
  - Avanzar el frame cuando toca, con cooldown configurable.

El draw() de cada uno se queda en su propia clase a propósito: difieren
en si dibujan hitbox de debug, si escalan el frame, si comprueban
'vivo' antes de dibujar, etc. Forzar eso a la base complicaría más de
lo que ahorra.
"""

import pygame


class ProyectilSpriteBase:
    """Manejo común de animación por frames para sprites de proyectil."""

    COOLDOWN_ANIM = 80   # ms entre frames, igual en los tres sprites actuales

    def __init__(self, frames: list):
        self.frames      = frames
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()

    def _avanzar_frame(self, cooldown: int = None):
        """Avanza frame_index si ha pasado el cooldown desde el último cambio.

        Parameters
        ----------
        cooldown : int, optional
            ms entre frames. Si no se especifica, usa self.COOLDOWN_ANIM.
        """
        if cooldown is None:
            cooldown = self.COOLDOWN_ANIM

        ahora = pygame.time.get_ticks()
        if ahora - self.update_time > cooldown:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.update_time = ahora

    def _frame_actual(self) -> pygame.Surface:
        """Devuelve el frame actual de la animación."""
        return self.frames[self.frame_index]
