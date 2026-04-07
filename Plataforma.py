import pygame

class Plataforma():
    def __init__(self, x, y, ancho, alto, tileset, tile_rect):

        self.shape = pygame.Rect(x, y, ancho, alto)

        # Recorta el tile del tileset
        self.tile = pygame.Surface((tile_rect.width, tile_rect.height), pygame.SRCALPHA)
        self.tile.blit(tileset, (0, 0), tile_rect)

        # Escala el tile al tamaño de la plataforma repitiéndolo
        self.superficie = self.construir_superficie(ancho, alto)

    def construir_superficie(self, ancho, alto):
        """Repite el tile para cubrir toda la plataforma."""
        superficie = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        tw = self.tile.get_width()
        th = self.tile.get_height()

        for x in range(0, ancho, tw):
            for y in range(0, alto, th):
                superficie.blit(self.tile, (x, y))

        return superficie

    def draw(self, interfaz, camara):
        interfaz.blit(self.superficie, camara.aplicar(self.shape))