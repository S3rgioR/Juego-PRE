"""Cámara con seguimiento suave del jugador.

Responsabilidad visual: sabe cómo desplazar el mundo para que el jugador
quede encuadrado. Vive en la capa View porque su única misión es
transformar coordenadas de mundo a coordenadas de pantalla.

Comportamiento
--------------
- Posición base: el jugador queda centrado horizontalmente y desplazado
  hacia arriba verticalmente (se ve más suelo/aire por encima que por
  debajo, útil en un plataformas).
- Mirada direccional: si el jugador lleva mantenida una tecla de
  movimiento (A/D) o de mirar arriba/abajo (W/S) más tiempo del umbral
  ``UMBRAL_MS``, la cámara empieza a desplazarse poco a poco hacia esa
  dirección (hasta ``DESPLAZAMIENTO_MAX_X``/``_Y`` píxeles de más),
  mostrando más terreno hacia donde se está yendo o mirando. Al soltar
  la tecla, el desplazamiento se deshace solo, con la misma suavidad.
"""

import Constantes


class Camara:
    """Gestiona el desplazamiento de la vista según la posición del jugador.

    Attributes
    ----------
    x : float
        Desplazamiento horizontal actual de la cámara (en píxeles de mundo).
    y : float
        Desplazamiento vertical actual de la cámara.
    offset_x : float
        Distancia horizontal base desde el borde izquierdo hasta el jugador.
    offset_y : float
        Distancia vertical base desde el borde superior hasta el jugador.
    suavizado : float
        Factor de interpolación (0-1) del seguimiento normal. Menor = más suave.
    extra_x, extra_y : float
        Desplazamiento adicional actual (con su propia suavidad, más lenta)
        causado por mantener pulsadas las teclas de dirección/mirada.
    """

    # --- Ajustes del desplazamiento por tecla mantenida ---
    UMBRAL_MS             = 700   # ms que hay que mantener la tecla antes de que la cámara reaccione
    RAMPA_MS              = 900   # ms desde que se supera el umbral hasta llegar al desplazamiento máximo
    DESPLAZAMIENTO_MAX_X  = 160   # píxeles que se desplaza la cámara hacia A/D como máximo
    DESPLAZAMIENTO_MAX_Y  = 120   # píxeles que se desplaza la cámara hacia W/S como máximo
    SUAVIZADO_EXTRA        = 0.4  # suavidad del desplazamiento extra

    def __init__(self):
        self.x = 0
        self.y = 0

        # Jugador centrado horizontalmente, desplazado hacia arriba
        # (se ve más por encima del jugador que por debajo).
        self.offset_x = Constantes.WIDTH * 0.5
        self.offset_y = Constantes.HEIGHT * 0.75

        # Suavizado: cuanto menor, más suave el seguimiento
        self.suavizado = 0.15

        # --- Estado del desplazamiento direccional ---
        self._tiempo_derecha  = 0.0
        self._tiempo_izquierda = 0.0
        self._tiempo_abajo     = 0.0
        self._tiempo_arriba    = 0.0
        self.extra_x = 0.0
        self.extra_y = 0.0

    def _factor(self, tiempo_mantenida: float) -> float:
        """0.0 si aún no se supera el umbral; sube a 1.0 a lo largo de RAMPA_MS."""
        if tiempo_mantenida <= self.UMBRAL_MS:
            return 0.0
        return min(1.0, (tiempo_mantenida - self.UMBRAL_MS) / self.RAMPA_MS)

    def update(self, jugador_shape, delta_ms: float = 16.0,
               mover_derecha: bool = False, mover_izquierda: bool = False,
               mirar_arriba: bool = False, mirar_abajo: bool = False):
        """Actualiza la posición de la cámara interpolando hacia el jugador.

        Parameters
        ----------
        jugador_shape : pygame.Rect
            Rectángulo (shape) del jugador en coordenadas de mundo.
        delta_ms : float
            Milisegundos transcurridos desde el último frame.
        mover_derecha, mover_izquierda : bool
            True mientras se mantienen pulsadas D / A.
        mirar_arriba, mirar_abajo : bool
            True mientras se mantienen pulsadas W / S.
        """
        # --- Temporizadores: suben mientras se mantiene la tecla, bajan
        # (más rápido) en cuanto se suelta, para que el desplazamiento
        # extra se deshaga con la misma sensación de suavidad. ---
        self._tiempo_derecha = (self._tiempo_derecha + delta_ms) if mover_derecha \
            else max(0.0, self._tiempo_derecha - delta_ms * 2)
        self._tiempo_izquierda = (self._tiempo_izquierda + delta_ms) if mover_izquierda \
            else max(0.0, self._tiempo_izquierda - delta_ms * 2)
        self._tiempo_abajo = (self._tiempo_abajo + delta_ms) if mirar_abajo \
            else max(0.0, self._tiempo_abajo - delta_ms * 2)
        self._tiempo_arriba = (self._tiempo_arriba + delta_ms) if mirar_arriba \
            else max(0.0, self._tiempo_arriba - delta_ms * 2)

        objetivo_extra_x = (self._factor(self._tiempo_derecha)
                             - self._factor(self._tiempo_izquierda)) * self.DESPLAZAMIENTO_MAX_X
        objetivo_extra_y = (self._factor(self._tiempo_abajo)
                             - self._factor(self._tiempo_arriba)) * self.DESPLAZAMIENTO_MAX_Y

        self.extra_x += (objetivo_extra_x - self.extra_x) * self.SUAVIZADO_EXTRA
        self.extra_y += (objetivo_extra_y - self.extra_y) * self.SUAVIZADO_EXTRA

        target_x = jugador_shape.centerx - (self.offset_x - self.extra_x)
        target_y = jugador_shape.centery - (self.offset_y - self.extra_y)

        # Interpolación suave hacia el target
        self.x += (target_x - self.x) * self.suavizado
        self.y += (target_y - self.y) * self.suavizado

    def aplicar(self, rect):
        """Devuelve el rect desplazado por la cámara para dibujar.

        Parameters
        ----------
        rect : pygame.Rect
            Rect en coordenadas de mundo.

        Returns
        -------
        pygame.Rect
            Rect en coordenadas de pantalla.
        """
        return rect.move(-int(self.x), -int(self.y))
