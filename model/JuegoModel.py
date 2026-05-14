"""Fachada principal del Model.

Gestiona el estado completo del juego: jugador, enemigos y combate.
La Vista y el Presenter acceden al estado del juego a través de esta clase.
"""

import Constantes
from .JugadorModel  import JugadorModel
from .Enemigo1Model import Enemigo1Model
from .Enemigo2Model import Enemigo2Model


class JuegoModel:
    """Gestiona el estado completo del juego: jugador, enemigos y combate.

    Actúa como fachada: la Vista y el Presenter acceden al estado
    del juego a través de esta clase.

    Attributes
    ----------
    jugador : JugadorModel
        Sub-modelo del jugador.
    enemigos : list of Actor
        Lista de sub-modelos de enemigos vivos.
    mover_derecha : bool
        True mientras la tecla D está pulsada.
    mover_izquierda : bool
        True mientras la tecla A está pulsada.
    """

    def __init__(self, datos_enemigos):
        self.jugador = JugadorModel()

        self.enemigos = []
        for d in datos_enemigos:
            if d.get('tipo') == 'volador':
                self.enemigos.append(
                    Enemigo2Model(
                        d['x'], d['y'],
                        distancia_patrulla=d.get('distancia_patrulla', 150),
                    )
                )
            else:
                self.enemigos.append(
                    Enemigo1Model(
                        d['x'], d['y'],
                        distancia_patrulla=d.get('distancia_patrulla', 150),
                        num_frames_ataque=d.get('num_frames_ataque', 6),
                    )
                )

        self.mover_derecha   = False
        self.mover_izquierda = False

    # --- Acciones del jugador (delegadas desde el Presenter) ---

    def jugador_saltar(self):
        self.jugador.saltar()

    def jugador_atacar(self, num_frames_anim):
        self.jugador.iniciar_ataque(num_frames_anim)

    def jugador_mover_derecha_inicio(self):
        self.mover_derecha = True

    def jugador_mover_derecha_fin(self):
        self.mover_derecha = False

    def jugador_mover_izquierda_inicio(self):
        self.mover_izquierda = True

    def jugador_mover_izquierda_fin(self):
        self.mover_izquierda = False

    # --- Consultas de combate (llamadas por la Vista al detectar colisiones) ---

    def golpe_jugador_a_enemigo(self, indice):
        """La Vista notifica que la hitbox del jugador ha tocado al enemigo [indice]."""
        if 0 <= indice < len(self.enemigos):
            self.enemigos[indice].recibir_daño(1)

    def golpe_enemigo_a_jugador(self):
        """La Vista notifica que la hitbox de un enemigo ha tocado al jugador."""
        self.jugador.recibir_daño(1)

    def golpe_proyectil_a_jugador(self, proyectil):
        """La Vista notifica que un proyectil ha tocado al jugador."""
        self.jugador.recibir_daño(1.5)
        proyectil.vivo = False

    def golpe_jugador_a_proyectil(self, proyectil):
        """La Vista notifica que la espada del jugador ha destruido un proyectil."""
        proyectil.vivo = False

    # --- Tick del Model (llamado por el Presenter cada frame) ---

    def tick(self, delta_time_ms):
        """Avanza los contadores internos del Model.

        No mueve nada: la Vista ya ha movido y colisionado antes de llamar aquí.

        Returns
        -------
        list of int
            Índices de enemigos que han muerto este frame.
        """
        if self.mover_derecha:
            self.jugador.moviendose = True
            self.jugador.flip       = False
        elif self.mover_izquierda:
            self.jugador.moviendose = True
            self.jugador.flip       = True
        else:
            self.jugador.moviendose = False

        self.jugador.tick(delta_time_ms)

        muertos = [i for i, e in enumerate(self.enemigos) if not e.vivo]
        for i in reversed(muertos):
            self.enemigos.pop(i)

        return muertos

    @property
    def delta_x_jugador(self):
        """Desplazamiento horizontal del jugador para este frame."""
        if self.mover_derecha:
            return Constantes.VELOCIDAD
        if self.mover_izquierda:
            return -Constantes.VELOCIDAD
        return 0
