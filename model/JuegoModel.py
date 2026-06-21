"""Fachada principal del Model.

Gestiona el estado completo del juego: jugador, enemigos y combate.
La Vista y el Presenter acceden al estado del juego a través de esta clase.
"""

import Constantes
from .JugadorModel  import JugadorModel
from .OgroModel import OgroModel
from .FantasmaModel import FantasmaModel
from .BossModel     import BossModel
from .Event         import Event


class JuegoModel:
    """Gestiona el estado completo del juego: jugador, enemigos y combate.

    Actúa como fachada: la Vista y el Presenter acceden al estado
    del juego a través de esta clase. En particular, el Presenter se
    suscribe únicamente a los eventos de esta fachada (evt_enemigo_ataque,
    evt_enemigo_deteccion, evt_boss_disparo) para reproducir sonido,
    sin necesidad de importar OgroModel, FantasmaModel ni BossModel.
    """
    def __init__(self, datos_enemigos, datos_boss):
        self.jugador = JugadorModel()

        # Eventos de fachada: persisten durante toda la vida de JuegoModel,
        # incluso cuando restaurar_enemigos() recrea las instancias de
        # enemigos/boss. Cada enemigo/boss nuevo se reconecta a ellos.
        self.evt_enemigo_ataque    = Event()
        self.evt_enemigo_deteccion = Event()
        self.evt_enemigo_disparo   = Event()
        self.evt_boss_disparo      = Event()

        self.enemigos = []
        self.boss = None
        self._crear_enemigos_y_boss(datos_enemigos, datos_boss)

        self.mover_derecha   = False
        self.mover_izquierda = False

        self.boss_delta        = (0.0, 0.0)
        self.jugador_pos_cache = (0, 0)
        # Posición actual del boss en pantalla, cacheada por la Vista cada
        # frame (igual que jugador_pos_cache). El Model la necesita para
        # poder ejecutar tick_ia() internamente sin que la Vista tenga que
        # invocar al boss directamente: la Vista solo aporta el dato
        # geométrico (posición), pero no decide ni ejecuta la IA.
        self.boss_pos_cache    = (0, 0)

    def _crear_enemigos_y_boss(self, datos_enemigos, datos_boss):
        """Crea (o recrea) enemigos y boss a partir de los datos del nivel,
        conectando sus eventos de instancia a los eventos de fachada.

        Compartido por __init__ y restaurar_enemigos() para no duplicar
        la lógica de construcción ni el cableado de eventos.
        """
        self.enemigos = []
        for d in datos_enemigos:
            if d.get('tipo') == 'volador':
                enemigo = FantasmaModel(
                    d['x'], d['y'],
                    distancia_patrulla=d.get('distancia_patrulla', 150),
                )
                enemigo.evt_disparo.add_listener(self.evt_enemigo_disparo.emit)
            else:
                enemigo = OgroModel(
                    d['x'], d['y'],
                    distancia_patrulla=d.get('distancia_patrulla', 150),
                    num_frames_ataque=d.get('num_frames_ataque', 6),
                )
                enemigo.evt_ataque.add_listener(self.evt_enemigo_ataque.emit)
            enemigo.evt_deteccion.add_listener(self.evt_enemigo_deteccion.emit)
            self.enemigos.append(enemigo)

        if datos_boss:
            self.boss = BossModel(datos_boss['x'], datos_boss['y'])
            self.boss.evt_disparo.add_listener(self.evt_boss_disparo.emit)
        else:
            self.boss = None

    # --- Acciones del jugador ---

    def jugador_saltar(self):               return self.jugador.saltar()
    def jugador_atacar(self, n):            return self.jugador.iniciar_ataque(n)
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
            # La IA del boss vive en el Model. La Vista solo le aporta las
            # posiciones (geometría de pantalla) a través de jugador_pos_cache
            # y boss_pos_cache; quien decide y ejecuta el comportamiento del
            # boss frame a frame es siempre el Model, nunca la Vista.
            dx, dy, _ = self.boss.tick_ia(
                self.boss_pos_cache, self.jugador_pos_cache, delta_time_ms
            )
            self.boss_delta = (dx, dy)

        # Recopilar índices Y tipo ANTES de eliminarlos de la lista
        muertos = [
            (i, 'volador' if isinstance(e, FantasmaModel) else 'terrestre')
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

        Los enemigos tampoco se incluyen: al cargar, restaurar_enemigos()
        siempre los reconstruye desde los datos originales del nivel
        (reaparecen en su posición inicial), así que guardar cuáles
        seguían vivos no aportaría nada.

        Returns
        -------
        dict
            Claves: 'hp' (int), 'hp_max' (int).
        """
        return {
            'hp':     self.jugador.hp,
            'hp_max': self.jugador.hp_max,
            # daga_desbloqueada NO se guarda aquí.
            # Al cargar, se deduce de 'daga_recogida' (estado del objeto en el mapa):
            # si el objeto ya fue recogido antes del save → se desbloquea al cargar.
            # Si fue recogido DESPUÉS del save → objeto reaparece, habilidad no activa.

        }

    def restaurar_enemigos(self, datos_enemigos, datos_boss):
        """Recrea los modelos de enemigos y boss a partir de los datos originales del nivel.

        Se llama al cargar partida para que los enemigos que hubieran muerto
        vuelvan a aparecer en su posición inicial, y se limpien sus proyectiles.
        Reconecta automáticamente los eventos de los nuevos enemigos/boss a
        los eventos de fachada (evt_enemigo_ataque, evt_enemigo_deteccion,
        evt_boss_disparo), así que el Presenter no necesita re-suscribirse.

        Parameters
        ----------
        datos_enemigos : list of dict
            Lista de dicts de enemigos del nivel (misma estructura que en __init__).
        datos_boss : dict or None
            Datos del boss del nivel, o None si no hay boss.
        """
        self._crear_enemigos_y_boss(datos_enemigos, datos_boss)

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
