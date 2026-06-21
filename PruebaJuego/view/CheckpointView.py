"""Vista visual del checkpoint - estatua con destello azul al activarse."""

import pygame
from .InteractableView import InteractableView
from .VisualEffects import aplicar_tinte


class CheckpointView(InteractableView):
    """Estatua de checkpoint.

    La imagen se recibe inyectada desde quien construye la vista (igual que
    PersonajeSprite recibe `frames` o Plataforma recibe `tileset`), en vez
    de cargarse con una ruta hardcodeada dentro del constructor. Así la
    carga de assets queda centralizada en un único sitio y esta clase no
    necesita conocer rutas de disco.
    """

    RADIO_ACTIVACION = 80
    DURACION_AZUL    = 1500   # ms que dura el efecto azul
    _COLOR_PROMPT    = (50, 50, 255)

    def __init__(self, x: int, y: int, imagen: pygame.Surface):
        self.image = imagen
        super().__init__(
            x, y,
            self.image.get_width(),
            self.image.get_height(),
            texto_prompt="[K] Guardar",
        )

        self._inicio_azul   = 0
        self._efecto_activo = False

    # ------------------------------------------------------------------ #

    def activar(self) -> None:
        """Arranca el destello azul."""
        self._efecto_activo = True
        self._inicio_azul   = pygame.time.get_ticks()

    def draw(self, interfaz: pygame.Surface, camara) -> None:
        img_rect = self.image.get_rect(midbottom=self.shape.midbottom)

        if self._efecto_activo:
            ms = pygame.time.get_ticks() - self._inicio_azul
            if ms < self.DURACION_AZUL:
                imagen_azul = aplicar_tinte(self.image, r=0, g=0, b=255, intensidad=0.5)
                interfaz.blit(imagen_azul, camara.aplicar(img_rect))
            else:
                self._efecto_activo = False
                interfaz.blit(self.image, camara.aplicar(img_rect))
        else:
            interfaz.blit(self.image, camara.aplicar(img_rect))

        self._dibujar_prompt(interfaz, camara)
