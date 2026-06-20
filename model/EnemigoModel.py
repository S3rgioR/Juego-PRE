"""Clase base para los enemigos del juego (terrestre y volador).

Unifica el comportamiento que ambos tipos de enemigo comparten:
  - Patrulla horizontal entre patrol_min/patrol_max (heredado de Actor).
  - Detección de pared entre dos puntos (raycast por bounding boxes de
    tiles sólidos, expresados como tuplas (left, top, right, bottom) —
    el Model nunca recibe ni toca objetos de la Vista como Plataforma).
  - "Alerta por golpe": al recibir daño sin estar ya persiguiendo,
    se marca una bandera que el siguiente tick_ia debe consumir para
    girar hacia el atacante y empezar a perseguir.
  - Transición a modo persecución (con notificación opcional on_deteccion
    y exclamación visual nueva).

Las subclases (Enemigo1Model, Enemigo2Model) solo implementan su propio
tick_ia() con la IA específica (ataque cuerpo a cuerpo vs. disparo a
distancia), reutilizando los helpers de aquí para la parte común.
"""

from .Actor import Actor
from .Event import Event


class EnemigoModel(Actor):
    """Estado lógico común a todo enemigo con patrulla y persecución.

    Attributes
    ----------
    velocidad : float
        Velocidad de patrulla (px/frame).
    patrol_min, patrol_max : float
        Límites de la zona de patrulla.
    rango_vision : float
        Distancia máxima a la que el enemigo puede detectar al jugador.
    persiguiendo : bool
        True mientras el enemigo está en modo persecución.
    usa_gravedad : bool
        True si el enemigo es terrestre (la Vista debe aplicarle gravedad
        y colisión vertical con el suelo). False si es volador. Permite
        que la Vista trate a cualquier enemigo de forma polimórfica, sin
        necesidad de importar las subclases concretas para usar isinstance().
    """

    usa_gravedad = True   # valor por defecto; las subclases lo sobreescriben

    def __init__(self, x, hp, iframe_duracion, distancia_patrulla,
                 velocidad, rango_vision):
        super().__init__(hp=hp, iframe_duracion=iframe_duracion)
        self.flip      = True
        self.velocidad = velocidad

        self.patrol_min = x - distancia_patrulla
        self.patrol_max = x + distancia_patrulla

        self.rango_vision = rango_vision

        # --- Persecución / alerta ---
        self.persiguiendo        = False   # True mientras sigue al jugador
        self._exclamacion_nueva  = False   # True solo el frame que detecta
        self._alertado_por_golpe = False   # True el frame en que recibe un golpe

        # Notificación de detección: el Presenter se suscribe vía JuegoModel,
        # sin necesidad de importar Enemigo1Model/Enemigo2Model directamente.
        self.evt_deteccion = Event()

    # --- Combate ---

    def recibir_daño(self, cantidad):
        """Aplica el daño y, si no estaba ya persiguiendo, marca la alerta
        para que el siguiente tick_ia gire hacia el atacante y persiga."""
        ya_persiguiendo = self.persiguiendo
        super().recibir_daño(cantidad)
        if self.vivo and not ya_persiguiendo:
            self._alertado_por_golpe = True

    # --- Helpers de IA compartidos ---

    def _iniciar_tick_ia(self, delta_time_ms):
        """Llamado al principio de tick_ia(): descuenta iframes y resetea
        la bandera de exclamación nueva (se reactivará si procede)."""
        self._tick_iframes(delta_time_ms)
        self._exclamacion_nueva = False

    def _consumir_alerta(self) -> bool:
        """Devuelve True (una sola vez) si el enemigo fue golpeado este
        frame sin estar ya persiguiendo. Consume la bandera al leerla."""
        if self._alertado_por_golpe:
            self._alertado_por_golpe = False
            return True
        return False

    def _iniciar_persecucion(self):
        """Activa el modo persecución y dispara la notificación de
        detección (sonido), si hay algún listener suscrito."""
        self.persiguiendo       = True
        self._exclamacion_nueva = True
        self.evt_deteccion.emit()

    def _hay_pared_entre(self, pos_a, pos_b, tiles_bbox):
        """Raycast simple por una lista de bounding boxes sólidos entre dos puntos.

        Parameters
        ----------
        pos_a, pos_b : tuple of (float, float)
            Puntos origen y destino del rayo, en coordenadas de mundo.
        tiles_bbox : list of tuple, optional
            Geometría pura de los tiles sólidos, cada uno como
            (left, top, right, bottom). El Model nunca recibe objetos
            de la Vista (p. ej. Plataforma) aquí, solo sus límites
            numéricos — así no depende de pygame ni de ninguna clase
            ajena a la capa de Model.
        """
        if not tiles_bbox:
            return False
        ax, ay = pos_a
        bx, by = pos_b
        pasos  = max(abs(bx - ax), abs(by - ay)) // 8 + 1
        for i in range(1, pasos):
            t  = i / pasos
            px = int(ax + (bx - ax) * t)
            py = int(ay + (by - ay) * t)
            for left, top, right, bottom in tiles_bbox:
                if left <= px < right and top <= py < bottom:
                    return True
        return False
