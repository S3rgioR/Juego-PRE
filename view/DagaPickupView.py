"""Vista visual de la daga recogible (objeto único en el mapa).

Al colisionar el jugador con ella:
  - Desbloquea la habilidad de lanzar proyectiles de daga.
  - Desaparece para siempre.

El save system guarda si ya fue recogida.
"""

import pygame


class DagaPickupView:
    """Sprite del objeto daga en el suelo.

    Parameters
    ----------
    x, y : int
        Posición central en coordenadas de mundo.
    imagen : pygame.Surface
        Imagen cargada en main.py.
    """

    def __init__(self, x: int, y: int, imagen: pygame.Surface):
        self.imagen   = imagen
        self.recogida = False

        self.shape = pygame.Rect(0, 0, imagen.get_width(), imagen.get_height())
        self.shape.center = (x, y)

        self._fuente = None

    # ------------------------------------------------------------------ #

    def colisiona_con(self, jugador_shape: pygame.Rect) -> bool:
        if self.recogida:
            return False
        return self.shape.colliderect(jugador_shape)

    def recoger(self):
        self.recogida = True

    # ------------------------------------------------------------------ #

    def draw(self, interfaz: pygame.Surface, camara) -> None:
        if self.recogida:
            return
        if self._fuente is None:
            self._fuente = pygame.font.SysFont(None, 18)

        interfaz.blit(self.imagen, camara.aplicar(self.shape))

        # Pequeño prompt informativo
        texto = self._fuente.render("Daga", True, (255, 230, 100))
        rect_pantalla = camara.aplicar(self.shape)
        interfaz.blit(texto, (rect_pantalla.centerx - texto.get_width() // 2,
                               rect_pantalla.top - 18))
