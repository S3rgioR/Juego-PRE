"""Sprite visual del portal (fin de nivel y regreso al anterior)."""

import pygame


class PortalView:
    COOLDOWN_ANIM   = 30   # ms entre frames (64 frames → ~2s por ciclo)
    RADIO_ACTIVACION = 60

    def __init__(self, x: int, y: int, frames: list, ancho: int = 40, alto: int = 200):
        self.frames      = frames
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()

        self.shape = pygame.Rect(0, 0, ancho, alto)
        self.shape.center = (x, y)

        self._fuente        = None
        self._mostrar_prompt = False

    def esta_cerca(self, jugador_shape: pygame.Rect) -> bool:
        dx = jugador_shape.centerx - self.shape.centerx
        dy = jugador_shape.centery - self.shape.centery
        return dx * dx + dy * dy <= self.RADIO_ACTIVACION ** 2

    def set_mostrar_prompt(self, valor: bool, texto: str = "[E] Entrar"):
        self._mostrar_prompt = valor
        self._prompt_texto   = texto

    def colisiona_con(self, jugador_shape: pygame.Rect) -> bool:
        return self.shape.colliderect(jugador_shape)

    def draw(self, interfaz: pygame.Surface, camara) -> None:
        if self._fuente is None:
            self._fuente = pygame.font.SysFont(None, 20)

        # Avanzar animación
        ahora = pygame.time.get_ticks()
        if ahora - self.update_time > self.COOLDOWN_ANIM:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.update_time = ahora

        frame = self.frames[self.frame_index]
        img_rect = frame.get_rect(center=self.shape.center)
        interfaz.blit(frame, camara.aplicar(img_rect))

        if self._mostrar_prompt:
            texto = self._fuente.render(
                getattr(self, '_prompt_texto', '[E] Entrar'), True, (255, 255, 180)
            )
            rect_pantalla = camara.aplicar(self.shape)
            interfaz.blit(texto, (rect_pantalla.centerx - texto.get_width() // 2,
                                   rect_pantalla.top - 22))