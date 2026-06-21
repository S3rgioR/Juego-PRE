"""Sprite visual de plataforma para pygame.

Responsabilidad: encapsular la imagen de una plataforma (construida
repitiendo un tile) y saber dibujarse aplicando el offset de cámara.
No contiene física ni lógica de juego — eso vive en el Model.
"""

import pygame


class Plataforma:
    """Sprite visual de una plataforma con textura de tile repetido.

    Attributes
    ----------
    shape : pygame.Rect
        Rectángulo que define posición y dimensiones en coordenadas de mundo.
        Es la fuente de verdad geométrica (también la usa el Model para colisiones).
    superficie : pygame.Surface
        Imagen construida repitiendo el tile para cubrir todo el rect.
    unidireccional : bool
        Si True, el motor de física (view.py) la trata como una plataforma
        "de un solo sentido": solo bloquea cuando se cae sobre ella desde
        arriba, y no bloquea movimiento horizontal. Las Plataforma normales
        son siempre solidas en las 4 direcciones (unidireccional = False).
    """

    unidireccional = False

    def __init__(self, x, y, ancho, alto, tileset, tile_rect):
        """Inicializa la plataforma recortando el tile y construyendo la superficie.

        Parameters
        ----------
        x, y : int
            Posición superior-izquierda en coordenadas de mundo.
        ancho, alto : int
            Dimensiones de la plataforma en píxeles.
        tileset : pygame.Surface
            Hoja de tiles cargada en memoria.
        tile_rect : pygame.Rect
            Región dentro del tileset que corresponde a este tipo de tile.
        """
        self.shape = pygame.Rect(x, y, ancho, alto)

        # Recortar el tile del tileset
        self.tile = pygame.Surface((tile_rect.width, tile_rect.height), pygame.SRCALPHA)
        self.tile.blit(tileset, (0, 0), tile_rect)

        # Construir la superficie repitiendo el tile
        self.superficie = self._construir_superficie(ancho, alto)

    def _construir_superficie(self, ancho, alto):
        """Repite el tile para cubrir toda la plataforma.

        Parameters
        ----------
        ancho, alto : int
            Dimensiones de la superficie a construir.

        Returns
        -------
        pygame.Surface
            Superficie con el tile repetido.
        """
        superficie = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        tw = self.tile.get_width()
        th = self.tile.get_height()

        for x in range(0, ancho, tw):
            for y in range(0, alto, th):
                superficie.blit(self.tile, (x, y))

        return superficie

    def draw(self, interfaz, camara):
        """Dibuja la plataforma en pantalla aplicando el desplazamiento de cámara.

        Parameters
        ----------
        interfaz : pygame.Surface
            Superficie principal de la ventana.
        camara : Camara
            Instancia de cámara que sabe cómo transformar coordenadas.
        """
        interfaz.blit(self.superficie, camara.aplicar(self.shape))


class PlataformaFlotante(Plataforma):
    """Plataforma flotante de un tile de alto, compuesta por varios tiles
    distintos colocados uno junto a otro (no repite un único tile como
    la Plataforma normal).

    Es "unidireccional": si caes encima funciona como suelo normal, pero
    si vienes de abajo (saltando) o te mueves por debajo, la atraviesas
    sin colisión. Tampoco bloquea movimiento horizontal. Esta lógica la
    aplica el motor de física en view.py consultando `unidireccional`;
    esta clase solo se encarga de la geometría y la imagen.
    """

    unidireccional = True

    def __init__(self, x, y, tileset, tile_rects):
        """Inicializa la plataforma componiendo los tiles uno junto a otro.

        Parameters
        ----------
        x, y : int
            Posición superior-izquierda en coordenadas de mundo.
        tileset : pygame.Surface
            Hoja de tiles cargada en memoria.
        tile_rects : list of pygame.Rect
            Región dentro del tileset de cada tile, en orden de izquierda
            a derecha. Se dibujan una sola vez cada uno (sin repetir),
            a diferencia de Plataforma._construir_superficie.
        """
        ancho_tile = tile_rects[0].width
        alto_tile  = tile_rects[0].height
        ancho      = ancho_tile * len(tile_rects)

        self.shape = pygame.Rect(x, y, ancho, alto_tile)

        self.superficie = pygame.Surface((ancho, alto_tile), pygame.SRCALPHA)
        for i, tile_rect in enumerate(tile_rects):
            tile = pygame.Surface((tile_rect.width, tile_rect.height), pygame.SRCALPHA)
            tile.blit(tileset, (0, 0), tile_rect)
            self.superficie.blit(tile, (i * ancho_tile, 0))
