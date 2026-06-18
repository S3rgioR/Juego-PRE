"""Vista visual de la pared del boss.

Responsabilidad: mostrar una imagen estática en unas coordenadas de mundo
y exponer un shape (Rect) para que la física de view.py la trate como
una plataforma sólida normal.

La pared desaparece (deja de dibujarse y de colisionar) cuando el boss muere.
"""

import pygame


class ParedBossView:
    """Pared sólida que bloquea el paso hasta que el boss es derrotado.

    Attributes
    ----------
    shape : pygame.Rect
        Hitbox en coordenadas de mundo. La física de view.py la usa igual
        que cualquier Plataforma sólida.
    unidireccional : bool
        Siempre False: bloquea en las 4 direcciones.
    activa : bool
        Mientras sea True la pared colisiona y se dibuja.
        Se pone a False cuando el boss muere.
    """

    unidireccional = False

    def __init__(self, x: int, y: int, ancho: int, alto: int):
        self.shape  = pygame.Rect(x, y, ancho, alto)
        self.activa = True

        img_raw = pygame.image.load(
            "Assets/Enviorments/ParedBoss.png"
        ).convert_alpha()
        self.imagen = pygame.transform.scale(img_raw, (ancho, alto))

    def draw(self, interfaz: pygame.Surface, camara) -> None:
        if self.activa:
            interfaz.blit(self.imagen, camara.aplicar(self.shape))
