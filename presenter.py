"""Capa Presenter del patrón MVP - Coordinación del flujo del juego.

El Presenter es el intermediario entre Model y View:
1. Se suscribe a todos los eventos de la Vista (teclado, cierre)
2. Llama al Model para actualizar el estado en respuesta a esos eventos
3. Coordina el game loop: input → update → render → refrescar

Flujo por frame en ejecutar():
1. Vista procesa input → emite eventos → Presenter actualiza banderas en Model
2. Model actualiza física, IA y combate
3. Presenter elimina sprites de enemigos muertos de la Vista
4. Vista renderiza usando el estado actual del Model
5. Vista controla FPS y devuelve delta_time
"""
from SaveSystem import SaveManager


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
        Número de frames de la animación de ataque del jugador
        (necesario para que el Model sepa cuándo termina el ataque).
    """

    def __init__(self, vista, modelo, num_frames_ataque_jugador=4):
        """Inicializa el Presenter y se suscribe a los eventos de la Vista.

        Parameters
        ----------
        vista : PygameView
            Instancia de la capa View.
        modelo : JuegoModel
            Instancia de la capa Model.
        num_frames_ataque_jugador : int, optional
            Número de frames de la animación de ataque del jugador.
            Permite que el Model sepa cuándo termina el ataque sin conocer pygame.
        """
        self.vista    = vista
        self.modelo   = modelo
        self.ejecutando = True
        self._num_frames_ataque_jugador = num_frames_ataque_jugador

        self.save_manager = SaveManager() # Gestor de guardado

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
        """Detiene el game loop."""
        self.ejecutando = False

    def _saltar(self):
        """Delega el salto al Model."""
        self.modelo.jugador_saltar()

    def _atacar(self):
        """Delega el ataque al Model, informando cuántos frames dura la animación."""
        self.modelo.jugador_atacar(self._num_frames_ataque_jugador)

    def _guardar_partida(self):
        """Guarda el estado actual del juego en un archivo."""
        try:
            # Obtener estado del Model
            estado = self.modelo.obtener_estado_guardado()

            # Añadir posición de la cámara desde la Vista
            estado['camara'] = self.vista.camara_pos

            # Guardar a disco usando SaveManager
            if self.save_manager.guardar(estado):
                print("[Presenter] ✓ Partida guardada exitosamente")
                self.vista.sprite_checkpoint.activar()
            else:
                print("[Presenter] ✗ Error al guardar la partida")
        except Exception as e:
            print(f"[Presenter] ✗ Excepción al guardar: {e}")

    def _cargar_partida(self):
        """Carga el estado guardado del juego (F10)."""
        try:
            # Intentar cargar usando SaveManager
            datos = self.save_manager.cargar()
            if datos is None:
                print("[Presenter] No hay partida guardada aún")
                return

            # Restaurar estado del Model
            self.modelo.cargar_estado_guardado(datos)

            # Restaurar cámara en la Vista
            if 'camara' in datos:
                cx, cy = datos['camara']
                self.vista.restaurar_camara(cx, cy)

            print("[Presenter] ✓ Partida cargada exitosamente")
        except Exception as e:
            print(f"[Presenter] ✗ Excepción al cargar: {e}")

    # --- Game loop ---

    def ejecutar(self):
        """Bucle principal del juego.

        Secuencia por frame:
        1. Vista procesa input y emite eventos → handlers actualizan el Model
        2. Model actualiza física, IA y combate → devuelve lista de muertos
        3. Presenter sincroniza sprites de la Vista (elimina los de enemigos muertos)
        4. Vista renderiza usando el estado exportado por el Model
        5. Vista controla FPS y devuelve delta_time

        Returns
        -------
        None
            Itera hasta que `self.ejecutando` sea False.
        """
        import pygame  # Solo para pygame.quit() al final

        while self.ejecutando:
            # 1. Input → eventos → handlers
            self.vista.procesar_input()
            if self.modelo.jugador.vivo:
                # 2. Actualizar Model (física + IA + combate)
                #    Recibe delta_time del frame anterior para coyote time
                delta_time = self.vista.refrescar()
                muertos = self.modelo.actualizar(self.vista.plataformas, delta_time)

                # 3. Eliminar sprites de enemigos muertos de la Vista
                #    Se procesan en orden inverso para no alterar índices
                for i in reversed(muertos):
                    self.vista.eliminar_sprite_enemigo(i)

            # 4. Renderizar: la Vista sincroniza sus sprites con el estado del Model
            self.vista.renderizar(
                self.modelo.obtener_estado_jugador(),
                self.modelo.obtener_estados_enemigos(),
            )

        pygame.quit()
