import Constantes

class Camara():
    def __init__(self):
        self.x = 0
        self.y = 0

        # Cuánto se desplaza el jugador del centro hacia la izquierda
        # 0.35 = 35% del ancho → jugador ligeramente a la izquierda
        self.offset_x = Constantes.WIDTH * 0.35
        self.offset_y = Constantes.HEIGHT * 0.75

        # Suavizado: cuanto menor, más suave
        self.suavizado = 0.15

    def update(self, jugador):
        # Posición donde esta la cámara
        target_x = jugador.shape.centerx - self.offset_x
        target_y = jugador.shape.centery - self.offset_y

        # Interpolación suave hacia el target
        self.x += (target_x - self.x) * self.suavizado
        self.y += (target_y - self.y) * self.suavizado

    def aplicar(self, rect):
        """Devuelve el rect desplazado por la cámara para dibujar."""
        return rect.move(-int(self.x), -int(self.y))