"""SpikesView — pinchos en el suelo + barreras invisibles de respawn.

Responsabilidades (solo Vista):
- Dibujar el conjunto de pinchos (tile 16x16 repetido `ancho` veces).
- Exponer el hitbox de los pinchos para que la Vista detecte la
  colisión con el jugador.
- Mantener dos zonas sensoras invisibles (barrera_izq / barrera_der)
  adyacentes a los pinchos: cuando el jugador las atraviesa, esta clase
  guarda su posición; esa posición es la que se usará para reaparecer
  al jugador si después cae sobre los pinchos.

Esta clase NO decide qué pasa al tocar los pinchos (daño, congelar,
fundido a negro, teleport): esa coordinación es responsabilidad del
Presenter, que escucha `PygameView.evt_spikes_tocados`. La Vista solo
detecta el solapamiento y reporta la posición de reaparición.
"""

import pygame

TILE_SIZE = 16


class SpikesView:
    """Un grupo de pinchos + sus dos barreras sensoras adyacentes.

    Attributes
    ----------
    shape : pygame.Rect
        Hitbox de los pinchos (en px, coordenadas de mundo).
    pos_respawn : tuple or None
        Última posición (centro del jugador) registrada al pasar por
        alguna de las dos barreras. None hasta el primer paso.
    """

    def __init__(self, x, y, ancho, alto, imagen_tile, barrera_izq, barrera_der):
        """
        Parameters
        ----------
        x, y : int
            Esquina superior izquierda del conjunto de pinchos (px).
        ancho, alto : int
            Tamaño del conjunto de pinchos (px). `alto` es siempre
            TILE_SIZE (16 px), tamaño de Assets/Enviorments/Spikes.png.
        imagen_tile : pygame.Surface
            Imagen 16x16 de los pinchos.
        barrera_izq, barrera_der : dict
            {'x', 'y', 'ancho', 'alto'} (px) de cada zona sensora.
        """
        self.shape = pygame.Rect(x, y, ancho, alto)
        self.imagen_tile = imagen_tile
        self.num_tiles = max(1, ancho // TILE_SIZE)

        self.rect_barrera_izq = pygame.Rect(
            barrera_izq['x'], barrera_izq['y'],
            barrera_izq['ancho'], barrera_izq['alto'])
        self.rect_barrera_der = pygame.Rect(
            barrera_der['x'], barrera_der['y'],
            barrera_der['ancho'], barrera_der['alto'])

        self.pos_respawn = None

        # Cooldown (ms) para no volver a disparar el evento de pinchos
        # mientras el jugador sigue solapando el hitbox — p.ej. mientras
        # está "hundido" tras tocarlos, o justo al reaparecer encima de
        # ellos tras el teletransporte de respawn.
        self._cooldown_ms = 0

    # ------------------------------------------------------------------
    # Lógica (solo detección, sin reglas de negocio)
    # ------------------------------------------------------------------

    def tick(self, delta_ms):
        if self._cooldown_ms > 0:
            self._cooldown_ms = max(0, self._cooldown_ms - delta_ms)

    def actualizar_barreras(self, shape_jugador):
        """Si el jugador solapa alguna barrera, guarda su posición de respawn.

        La posición guardada es SIEMPRE un tile antes del borde de los
        pinchos, por el lado por el que el jugador entró (no encima de
        los pinchos): si toca la barrera izquierda, un tile a la
        izquierda del borde izquierdo de los pinchos; si toca la
        derecha, un tile a la derecha del borde derecho. La X no depende
        de la posición exacta del hitbox del jugador (evita la asimetría
        que había al entrar por la izquierda o por la derecha). Solo se
        conserva la Y del jugador en ese instante, la altura del "suelo"
        desde el que venía antes de pasar sobre los pinchos.
        """
        if self.rect_barrera_izq.colliderect(shape_jugador):
            x = self.shape.left - TILE_SIZE // 2
            self.pos_respawn = (x, shape_jugador.centery)
        elif self.rect_barrera_der.colliderect(shape_jugador):
            x = self.shape.right + TILE_SIZE // 2
            self.pos_respawn = (x, shape_jugador.centery)

    def colisiona_con(self, shape_jugador) -> bool:
        """True si el jugador toca los pinchos y no hay cooldown activo."""
        if self._cooldown_ms > 0:
            return False
        return self.shape.colliderect(shape_jugador)

    def activar_cooldown(self, ms=2000):
        self._cooldown_ms = ms

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------

    def draw(self, screen, camara):
        sx = self.shape.x - camara.x
        sy = self.shape.y - camara.y
        for i in range(self.num_tiles):
            screen.blit(self.imagen_tile, (sx + i * TILE_SIZE, sy))
