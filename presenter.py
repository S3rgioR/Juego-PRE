"""Capa Presenter del patrón MVP - Coordinación del flujo del juego.

El Presenter es el intermediario entre Model y View:
1. Se suscribe a todos los eventos de la Vista (teclado, cierre)
2. Llama al Model para registrar las intenciones del jugador
3. Coordina el game loop: input → física → tick Model → render

Flujo por frame en ejecutar():
1. Vista procesa input → emite eventos → Presenter actualiza banderas en Model
2. Vista ejecuta la física: mueve objetos, detecta colisiones, notifica al Model
3. Model avanza sus contadores internos (iframes, fin de ataque, IA)
4. Presenter elimina sprites de enemigos muertos de la Vista
5. Vista renderiza usando el estado combinado Model + posiciones de la Vista
"""

from SaveManager import SaveManager


class JuegoPresenter:
    """Coordinador central que conecta Model y View.

    Attributes
    ----------
    vista : PygameView
        Referencia a la capa View.
    modelo : JuegoModel
        Referencia a la capa Model.
    ejecutando : bool
        Controla si el game loop sigue activo.
    _num_frames_ataque_jugador : int
        Número de frames de la animación de ataque del jugador.
    """

    def __init__(self, vista, modelo, num_frames_ataque_jugador=4):
        self.vista      = vista
        self.modelo     = modelo
        self.ejecutando = True
        self._num_frames_ataque_jugador = num_frames_ataque_jugador
        self.save_manager = SaveManager()

        # --- Suscripción a eventos de la Vista ---
        self.vista.evt_cerrar.add_listener(self._cerrar)

        self.vista.evt_mover_derecha_inicio.add_listener(
            self.modelo.jugador_mover_derecha_inicio
        )
        self.vista.evt_mover_derecha_fin.add_listener(
            self.modelo.jugador_mover_derecha_fin
        )
        self.vista.evt_mover_izquierda_inicio.add_listener(
            self.modelo.jugador_mover_izquierda_inicio
        )
        self.vista.evt_mover_izquierda_fin.add_listener(
            self.modelo.jugador_mover_izquierda_fin
        )
        self.vista.evt_saltar.add_listener(self._saltar)
        self.vista.evt_atacar.add_listener(self._atacar)
        self.vista.evt_guardar.add_listener(self._guardar_partida)
        self.vista.evt_cargar.add_listener(self._cargar_partida)

    # --- Handlers de eventos ---

    def _cerrar(self):
        self.ejecutando = False

    def _saltar(self):
        self.modelo.jugador_saltar()

    def _atacar(self):
        self.modelo.jugador_atacar(self._num_frames_ataque_jugador)

    def _guardar_partida(self):
        """Guarda posición (de la Vista), hp (del Model) y cámara."""
        try:
            estado = self.modelo.obtener_estado_guardado()
            # La posición vive en la Vista en esta arquitectura
            estado['pos']    = list(self.vista.sprite_jugador.shape.center)
            estado['camara'] = self.vista.camara_pos
            if self.save_manager.guardar(estado):
                print("[Presenter] ✓ Partida guardada")
                self.vista.sprite_checkpoint.activar()
        except Exception as e:
            print(f"[Presenter] ✗ Error al guardar: {e}")

    def _cargar_partida(self):
        """Carga y restaura posición (en Vista), hp (en Model) y cámara."""
        try:
            datos = self.save_manager.cargar()
            if datos is None:
                print("[Presenter] No hay partida guardada")
                return
            # Restaurar lógica en el Model
            self.modelo.cargar_estado_guardado(datos)
            # Restaurar posición en la Vista (aquí viven las posiciones)
            if 'pos' in datos:
                x, y = datos['pos']
                self.vista.restaurar_pos_jugador(int(x), int(y))
            if 'camara' in datos:
                self.vista.restaurar_camara(*datos['camara'])
            self.vista.sprite_checkpoint.activado = True
            print("[Presenter] ✓ Partida cargada")
        except Exception as e:
            print(f"[Presenter] ✗ Error al cargar: {e}")

    # --- Game loop ---

    def ejecutar(self):
        """Bucle principal del juego.

        Secuencia por frame:
        1. Vista procesa input → eventos → handlers actualizan el Model
        2. Vista ejecuta la física y notifica al Model sobre colisiones
        3. Model avanza iframes, animación de ataque e IA
        4. Presenter elimina sprites de enemigos muertos
        5. Vista renderiza usando el estado exportado por Model y Vista
        """
        import pygame

        while self.ejecutando:
            # 1. Input
            self.vista.procesar_input()

            if self.modelo.jugador.vivo:
                # 2. Delta time del frame anterior
                delta_time = self.vista.refrescar()

                # 3. Vista: mover objetos + detectar colisiones + notificar Model
                self.vista.actualizar_fisica(self.modelo, delta_time)

                # 4. Model: avanzar contadores internos (iframes, ataques, IA)
                muertos = self.modelo.tick(delta_time)

                # 5. Eliminar sprites de enemigos muertos
                for i in reversed(muertos):
                    self.vista.eliminar_sprite_enemigo(i)

            # 6. Renderizar
            estado_jugador   = self.vista.obtener_estado_jugador(self.modelo)
            estados_enemigos = self.vista.obtener_estados_enemigos(self.modelo)
            self.vista.renderizar(estado_jugador, estados_enemigos)
