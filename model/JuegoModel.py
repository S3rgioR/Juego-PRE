"""Fachada principal del Model.

Gestiona el estado completo del juego: jugador, enemigos y combate.
La Vista y el Presenter acceden al estado del juego a través de esta clase.
"""

import Constantes
from .JugadorModel  import JugadorModel
from .Enemigo1Model import Enemigo1Model
from .Enemigo2Model import Enemigo2Model
from .BossModel     import BossModel


class JuegoModel:
    """Gestiona el estado completo del juego: jugador, enemigos y combate.

    Actúa como fachada: la Vista y el Presenter acceden al estado
    del juego a través de esta clase.
    """
    def __init__(self, datos_enemigos, datos_boss):
        self.jugador = JugadorModel()

        self.enemigos = []
        self.boss = None
        if datos_boss:
            self.boss = BossModel(datos_boss['x'], datos_boss['y'])
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

        self.boss_delta        = (0.0, 0.0)
        self.jugador_pos_cache = (0, 0)

    # --- Acciones del jugador ---

    def jugador_saltar(self):               self.jugador.saltar()
    def jugador_atacar(self, n):            self.jugador.iniciar_ataque(n)
    def jugador_mover_derecha_inicio(self): self.mover_derecha   = True
    def jugador_mover_derecha_fin(self):    self.mover_derecha   = False
    def jugador_mover_izquierda_inicio(self): self.mover_izquierda = True
    def jugador_mover_izquierda_fin(self):    self.mover_izquierda = False

    def curar_jugador(self):
        self.jugador.curar_completo()

    def jugador_recoger_corazon(self):
        self.jugador.recoger_corazon()

    def jugador_desbloquear_daga(self):
        """El jugador recogió el objeto daga del suelo."""
        self.jugador.desbloquear_daga()

    def jugador_lanzar_daga(self, pos_x, pos_y, flip, frame_ref):
        """Delega el lanzamiento al JugadorModel.

        Returns
        -------
        DagaProyectilModel or None
        """
        return self.jugador.lanzar_daga(pos_x, pos_y, flip, frame_ref)

    # --- Combate ---

    def golpe_jugador_a_enemigo(self, indice):
        """La Vista notifica que la hitbox del jugador ha tocado al enemigo [indice]."""
        if 0 <= indice < len(self.enemigos):
            self.enemigos[indice].recibir_daño(1)

    def golpe_enemigo_a_jugador(self):          self.jugador.recibir_daño(1)
    def golpe_proyectil_a_jugador(self, p):
        self.jugador.recibir_daño(1.5); p.vivo = False
    def golpe_jugador_a_proyectil(self, p):     p.vivo = False
    def golpe_jugador_a_boss(self):
        if self.boss: self.boss.recibir_daño(1)
    def golpe_boss_a_jugador(self):             self.jugador.recibir_daño(1.5)
    def golpe_proyectil_boss_a_jugador(self, p):
        self.jugador.recibir_daño(p.daño); p.vivo = False

    def golpe_daga_jugador_a_enemigo(self, indice, proyectil):
        """La daga del jugador impactó en el enemigo [indice]."""
        if 0 <= indice < len(self.enemigos):
            self.enemigos[indice].recibir_daño(proyectil.daño)
        proyectil.vivo = False

    def golpe_daga_jugador_a_boss(self, proyectil):
        """La daga del jugador impactó en el boss."""
        if self.boss:
            self.boss.recibir_daño(proyectil.daño)
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

        if self.boss and self.boss.vivo:
            self.boss._tick_iframes(delta_time_ms)

        # Recopilar índices Y tipo ANTES de eliminarlos de la lista
        muertos = [
            (i, 'volador' if isinstance(e, Enemigo2Model) else 'terrestre')
            for i, e in enumerate(self.enemigos) if not e.vivo
        ]
        for i, _ in reversed(muertos):
            self.enemigos.pop(i)

        return muertos

    @property
    def delta_x_jugador(self):
        if self.mover_derecha:   return Constantes.VELOCIDAD
        if self.mover_izquierda: return -Constantes.VELOCIDAD
        return 0

    # --- Guardado / Carga de partida ---

    def obtener_estado_guardado(self):
        """Devuelve un dict serializable con el estado a persistir.

        La posición NO se incluye aquí: la Vista la añade antes de guardar,
        ya que en esta arquitectura las posiciones viven en la Vista.

        Returns
        -------
        dict
            Claves: 'hp' (int), 'num_enemigos_vivos' (int).
        """
        return {
            'hp':     self.jugador.hp,
            'hp_max': self.jugador.hp_max,
            # daga_desbloqueada NO se guarda aquí.
            # Al cargar, se deduce de 'daga_recogida' (estado del objeto en el mapa):
            # si el objeto ya fue recogido antes del save → se desbloquea al cargar.
            # Si fue recogido DESPUÉS del save → objeto reaparece, habilidad no activa.
            'num_enemigos_vivos': len(self.enemigos),

        }

    def cargar_estado_guardado(self, datos):
        if 'hp_max' in datos:
            self.jugador.hp_max = max(JugadorModel.HP_MAX_BASE, int(datos['hp_max']))
        if 'hp' in datos:
            self.jugador.hp   = max(1, min(datos['hp'], self.jugador.hp_max))
            self.jugador.vivo = True
        # La daga se restaura desde el Presenter (que conoce el estado del mapa),
        # NO desde aquí. Aseguramos que siempre empieza desactivada al cargar.
        self.jugador.daga_desbloqueada = False

        # Reiniciar velocidades y estado de ataque para evitar artefactos
        self.jugador.velocidad_y  = 0
        self.jugador.atacando     = False
        self.jugador.iframe_timer = 0
        self.jugador.coyote_timer = 0
