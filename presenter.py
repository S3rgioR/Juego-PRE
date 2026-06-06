"""Capa Presenter del patrón MVP."""

from SaveManager import SaveManager
from MenuPausa   import MenuPausa


class JuegoPresenter:

    def __init__(self, vista, modelo, num_frames_ataque_jugador=4):
        self.vista      = vista
        self.modelo     = modelo
        self.ejecutando = True
        self._num_frames_ataque_jugador = num_frames_ataque_jugador
        self.save_manager   = SaveManager()
        self._pausado       = False
        self._menu_pausa    = None
        self.salida_forzada = False

        # --- Suscripción a eventos ---
        self.vista.evt_cerrar.add_listener(self._cerrar)
        self.vista.evt_pausa.add_listener(self._togglear_pausa)
        self.vista.evt_mover_derecha_inicio.add_listener(
            self.modelo.jugador_mover_derecha_inicio)
        self.vista.evt_mover_derecha_fin.add_listener(
            self.modelo.jugador_mover_derecha_fin)
        self.vista.evt_mover_izquierda_inicio.add_listener(
            self.modelo.jugador_mover_izquierda_inicio)
        self.vista.evt_mover_izquierda_fin.add_listener(
            self.modelo.jugador_mover_izquierda_fin)
        self.vista.evt_saltar.add_listener(self._saltar)
        self.vista.evt_atacar.add_listener(self._atacar)
        self.vista.evt_guardar.add_listener(self._guardar_partida)
        self.vista.evt_cargar.add_listener(self._cargar_partida)
        self.vista.evt_curar.add_listener(self._curar_jugador)
        self.vista.evt_corazon_recogido.add_listener(self._corazon_recogido)
        self.vista.evt_daga_recogida.add_listener(self._daga_recogida)
        self.vista.evt_lanzar_daga.add_listener(self._lanzar_daga)

    # --- Handlers ---

    def _cerrar(self):
        self.ejecutando     = False
        self.salida_forzada = True

    def _togglear_pausa(self):
        self._pausado = not self._pausado
        if self._pausado:
            self._menu_pausa = MenuPausa(
                screen     = self.vista.screen,
                tiene_save = self.save_manager.existe())

    def _procesar_pausa(self, events):
        import pygame
        hover = self._menu_pausa.hover_idx(pygame.mouse.get_pos())
        for event in events:
            if event.type == pygame.QUIT:
                self.ejecutando = False; self._pausado = False
                self.salida_forzada = True; return
            accion = self._menu_pausa.procesar_evento(event)
            if accion is None: continue
            if accion == 'reanudar':      self._pausado = False
            elif accion == 'cargar':      self._cargar_partida(); self._pausado = False
            elif accion == 'menu_principal': self.ejecutando = False; self._pausado = False
        self._menu_pausa.dibujar(hover)
        pygame.display.flip()

    def _saltar(self):  self.modelo.jugador_saltar()
    def _atacar(self):  self.modelo.jugador_atacar(self._num_frames_ataque_jugador)

    def _curar_jugador(self):
        self.modelo.curar_jugador()
        self.vista.sprite_angel.activar_destello()
        print("[Presenter] ✓ Jugador curado")

    def _corazon_recogido(self, indice):
        self.modelo.jugador_recoger_corazon()
        print(f"[Presenter] ✓ Corazón {indice} recogido — "
              f"hp={self.modelo.jugador.hp}/{self.modelo.jugador.hp_max}")

    def _daga_recogida(self):
        """El jugador recogió el objeto daga: desbloquear habilidad."""
        self.modelo.jugador_desbloquear_daga()
        print("[Presenter] ✓ Habilidad daga desbloqueada")

    def _lanzar_daga(self):
        """El jugador pulsó L: intentar lanzar un proyectil de daga."""
        if not self._frames_daga_disponibles():
            return
        jugador_m = self.modelo.jugador
        pos       = self.vista.sprite_jugador.shape.center
        frame_ref = self.vista._frames_daga_proyectil[0]
        self.modelo.jugador_lanzar_daga(pos[0], pos[1], jugador_m.flip, frame_ref)

    def _frames_daga_disponibles(self) -> bool:
        return bool(self.vista._frames_daga_proyectil)

    def _guardar_partida(self):
        try:
            estado = self.modelo.obtener_estado_guardado()
            estado['pos']                 = list(self.vista.sprite_jugador.shape.center)
            estado['camara']              = self.vista.camara_pos
            estado['corazones_recogidos'] = self.vista.indices_corazones_recogidos()
            # Guardar si la daga pickup ya fue recogida
            estado['daga_recogida'] = (
                self.vista.sprite_daga_pickup is None
                or self.vista.sprite_daga_pickup.recogida
            )
            if self.save_manager.guardar(estado):
                print("[Presenter] ✓ Partida guardada")
                self.vista.sprite_checkpoint.activar()
        except Exception as e:
            print(f"[Presenter] ✗ Error al guardar: {e}")

    def _cargar_partida(self):
        try:
            datos = self.save_manager.cargar()
            if datos is None:
                print("[Presenter] No hay partida guardada"); return

            self.modelo.cargar_estado_guardado(datos)   # restaura hp, hp_max, daga

            if 'pos' in datos:
                x, y = datos['pos']
                self.vista.restaurar_pos_jugador(int(x), int(y))
            if 'camara' in datos:
                self.vista.restaurar_camara(*datos['camara'])
            if 'corazones_recogidos' in datos:
                self.vista.restaurar_corazones_recogidos(
                    set(datos['corazones_recogidos']))
            if datos.get('daga_recogida'):
                # Estaba recogida al guardar → ocultarla y desbloquear habilidad.
                self.vista.restaurar_daga_recogida()
                self.modelo.jugador_desbloquear_daga()
            else:
                # No estaba recogida al guardar → reaparece en el mapa.
                if self.vista.sprite_daga_pickup:
                    self.vista.sprite_daga_pickup.recogida = False

            self.vista.sprite_checkpoint.activado = True
            print("[Presenter] ✓ Partida cargada")
        except Exception as e:
            print(f"[Presenter] ✗ Error al cargar: {e}")

    # --- Game loop ---

    def ejecutar(self):
        import pygame
        reloj = pygame.time.Clock()

        while self.ejecutando:
            events = pygame.event.get()

            if self._pausado:
                reloj.tick(60)
                self._procesar_pausa(events)
                continue

            self.vista.procesar_input(events)

            if self.modelo.jugador.vivo:
                delta_time = self.vista.refrescar()
                self.vista.actualizar_fisica(self.modelo, delta_time)
                muertos = self.modelo.tick(delta_time)
                for i in reversed(muertos):
                    self.vista.eliminar_sprite_enemigo(i)

            estado_jugador   = self.vista.obtener_estado_jugador(self.modelo)
            estados_enemigos = self.vista.obtener_estados_enemigos(self.modelo)
            self.vista.renderizar(estado_jugador, estados_enemigos, self.modelo)
