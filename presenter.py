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

import pygame  

from SaveManager import SaveManager
from MenuPausa   import MenuPausa
from MenuConfig  import MenuConfig


class JuegoPresenter:

    def __init__(self, vista, modelo, num_frames_ataque_jugador=4, audio=None, num_nivel=1,
                 datos_enemigos=None, datos_boss=None):
        self.vista  = vista
        self.modelo = modelo
        self.audio  = audio
        if audio:
            self.modelo.evt_enemigo_ataque.add_listener(audio.sfx_ataque_ogro)
            self.modelo.evt_enemigo_disparo.add_listener(audio.sfx_ataque_enemigo2)
            self.modelo.evt_boss_disparo.add_listener(audio.sfx_ataque_boss)

        self.ejecutando = True
        self._num_frames_ataque_jugador = num_frames_ataque_jugador
        self.save_manager = SaveManager()
        self._pausado    = False
        self._menu_pausa = None
        self.salida_forzada = False
        self.nivel_a_cargar = None
        self._datos_enemigos_nivel = datos_enemigos or []
        self._datos_boss_nivel     = datos_boss

        self.vista.evt_cerrar.add_listener(self._cerrar)
        self.vista.evt_pausa.add_listener(self._togglear_pausa)
        self.vista.evt_mover_derecha_inicio.add_listener(self.modelo.jugador_mover_derecha_inicio)
        self.vista.evt_mover_derecha_fin.add_listener(self.modelo.jugador_mover_derecha_fin)
        self.vista.evt_mover_izquierda_inicio.add_listener(self.modelo.jugador_mover_izquierda_inicio)
        self.vista.evt_mover_izquierda_fin.add_listener(self.modelo.jugador_mover_izquierda_fin)
        self.vista.evt_saltar.add_listener(self._saltar)
        self.vista.evt_atacar.add_listener(self._atacar)
        self.vista.evt_guardar.add_listener(self._guardar_partida)
        self.vista.evt_cargar.add_listener(self._cargar_partida)
        self.vista.evt_curar.add_listener(self._curar_jugador)
        self.vista.evt_corazon_recogido.add_listener(self._corazon_recogido)
        self.vista.evt_daga_recogida.add_listener(self._daga_recogida)
        self.vista.evt_lanzar_daga.add_listener(self._lanzar_daga)
        self.vista.evt_nivel_anterior.add_listener(self._nivel_anterior)
        self.vista.evt_tecla_e.add_listener(self._usar_portal)
        self.vista.evt_spikes_tocados.add_listener(self._spikes_tocados)
        self.vista.evt_nivel_completado.add_listener(self._nivel_completado)

        self.num_nivel = num_nivel
        self.nivel_completado = False
        self.nivel_anterior = False
        self.estado_jugador_al_retroceder = None
        self._estado_jugador_previo = None
        self.juego_finalizado = False

        # --- Pantalla de carga ---
        self._cargando      = False
        self._frames_carga  = 0
        self._FRAMES_ESPERA = 30

        # --- Secuencia de pinchos ---
        self._spikes_fase         = None
        self._spikes_timer_ms     = 0
        self._spikes_respawn_pos  = None
        self._SPIKES_MS_CONGELADO = 500
        self._SPIKES_MS_NEGRO     = 1000

        # Nota: el flag de "el boss acaba de morir, sonar una vez" ya no
        # vive aquí. Antes el Presenter lo llevaba como _boss_muerto_sonado
        # comparando contra modelo.boss.vivo directamente; ahora la única
        # fuente de verdad es modelo.boss_recien_derrotado() (ver _frame_normal).

    # --- Handlers de eventos ---

    def _nivel_completado(self):
        self.nivel_completado = True
        self.ejecutando = False

    def _cerrar(self):
        self.ejecutando     = False
        self.salida_forzada = True

    def _nivel_anterior(self):
        self.estado_jugador_al_retroceder = self.modelo.obtener_estado_guardado()
        self.estado_jugador_al_retroceder['daga_desbloqueada']   = self.modelo.jugador.daga_desbloqueada
        self.estado_jugador_al_retroceder['corazones_recogidos'] = self.vista.indices_corazones_recogidos()
        self.estado_jugador_al_retroceder['daga_recogida']       = self.vista.daga_pickup_recogida
        self.estado_jugador_al_retroceder['pos_retroceso']       = list(self.vista.posicion_jugador())
        if self._estado_jugador_previo is not None:
            self.estado_jugador_al_retroceder['estado_niveles_anteriores'] = self._estado_jugador_previo
        self.nivel_anterior = True
        self.ejecutando = False

    def _spikes_tocados(self, pos_respawn):
        if self._spikes_fase is not None:
            return
        self.modelo.golpe_enemigo_a_jugador()
        if self.audio:
            self.audio.sfx_hurt_jugador()

        # Antes: 6 líneas duplicadas tocando atributos privados de la Vista.
        self.vista.cancelar_movimiento_horizontal()

        self._spikes_respawn_pos = pos_respawn
        self._spikes_fase        = 'congelado'
        self._spikes_timer_ms    = self._SPIKES_MS_CONGELADO

    def _togglear_pausa(self):
        self._pausado = not self._pausado
        if self._pausado:
            self.vista.cancelar_movimiento_horizontal()
            self._menu_pausa = MenuPausa(
                screen=self.vista.screen,
                tiene_save=self.save_manager.existe())

    def _procesar_pausa(self, events):
        hover = self._menu_pausa.hover_idx(pygame.mouse.get_pos())
        for event in events:
            if event.type == pygame.QUIT:
                self.ejecutando = False; self._pausado = False
                self.salida_forzada = True; return
            accion = self._menu_pausa.procesar_evento(event)
            if accion is None:
                continue
            if accion == 'reanudar':
                self._pausado = False
            elif accion == 'cargar':
                self._cargar_partida(); self._pausado = False
            elif accion == 'config':
                MenuConfig(self.vista.screen, self.audio).ejecutar()
                estado_jugador   = self.vista.obtener_estado_jugador(self.modelo)
                estados_enemigos = self.vista.obtener_estados_enemigos(self.modelo)
                self.vista.renderizar(estado_jugador, estados_enemigos, self.modelo)
                hover = self._menu_pausa.hover_idx(pygame.mouse.get_pos())
                self._menu_pausa.dibujar(hover)
                pygame.display.flip()
            elif accion == 'menu_principal':
                self.ejecutando = False; self._pausado = False
        self._menu_pausa.dibujar(hover)
        pygame.display.flip()

    def _usar_portal(self):
        # directamente. Ahora la Vista decide su propia geometría interna
        # y solo expone la respuesta booleana.
        if self.vista.cerca_de_portal_fin():
            self._nivel_completado()
        elif self.vista.cerca_de_portal_regreso():
            self._nivel_anterior()
        elif self.vista.cerca_de_portal_final():
            # Único punto de decisión: el Presenter es quien decide arrancar
            # la secuencia de fin de juego (flujo de partida); la Vista
            # solo la ejecuta/dibuja cuando se le pide.
            self._iniciar_fin_de_juego()

    def _iniciar_fin_de_juego(self):
        """Arranca la secuencia de fin de juego.

        Decisión de flujo de partida → vive en el Presenter. La Vista
        solo sabe ejecutar/dibujar la secuencia una vez se le pide.
        """
        self.vista.activar_secuencia_fin_de_juego()

    def _saltar(self):
        if self.modelo.jugador_saltar() and self.audio:
            self.audio.sfx_salto()

    def _atacar(self):
        if self.modelo.jugador_atacar(self._num_frames_ataque_jugador) and self.audio:
            self.audio.sfx_ataque_jugador()

    def _curar_jugador(self):
        self.modelo.curar_jugador()
        self.vista.sprite_angel.activar_destello()

    def _corazon_recogido(self, indice):
        self.modelo.jugador_recoger_corazon()

    def _daga_recogida(self):
        self.modelo.jugador_desbloquear_daga()

    def _lanzar_daga(self):
        if not self.vista.tiene_frames_daga():
            return
        jugador_m = self.modelo.jugador
        pos       = self.vista.posicion_jugador()
        frame_ref = self.vista.frame_daga_referencia()
        self.modelo.jugador_lanzar_daga(pos[0], pos[1], jugador_m.flip, frame_ref)

    def _guardar_partida(self):
        try:
            estado = self.modelo.obtener_estado_guardado()
            estado['pos']                 = list(self.vista.posicion_jugador())
            estado['camara']              = self.vista.camara_pos
            estado['corazones_recogidos'] = self.vista.indices_corazones_recogidos()
            estado['num_nivel']           = self.num_nivel
            estado['daga_desbloqueada']   = self.modelo.jugador.daga_desbloqueada
            estado['boss_derrotado']      = self.modelo.boss_derrotado()
            estado['daga_recogida']       = self.vista.daga_pickup_recogida
            if self._estado_jugador_previo is not None:
                estado['estado_niveles_anteriores'] = self._estado_jugador_previo
            if self.save_manager.guardar(estado):
                self.vista.sprite_checkpoint.activar()
        except Exception as e:
            print(f"[Presenter] ✗ Error al guardar: {e}")

    def _cargar_partida(self):
        try:
            datos = self.save_manager.cargar()
            if datos is None:
                return

            nivel_guardado = datos.get('num_nivel', self.num_nivel)
            if nivel_guardado != self.num_nivel:
                self.nivel_a_cargar = nivel_guardado
                self.ejecutando     = False
                self._pausado       = False
                return

            self.modelo.cargar_estado_guardado(datos)

            if 'pos' in datos:
                x, y = datos['pos']
                self.vista.restaurar_pos_jugador(int(x), int(y))
                self.modelo.jugador.velocidad_y = 0
            if 'camara' in datos:
                self.vista.restaurar_camara(*datos['camara'])
            if 'corazones_recogidos' in datos:
                self.vista.restaurar_corazones_recogidos(set(datos['corazones_recogidos']))

            if datos.get('daga_recogida'):
                self.vista.restaurar_daga_recogida()
                self.modelo.jugador_desbloquear_daga()
            else:
                self.vista.resetear_daga_pickup()

            if datos.get('boss_derrotado'):
                self.modelo.marcar_boss_derrotado()

            self._estado_jugador_previo = datos.get('estado_niveles_anteriores', None)

            self.modelo.restaurar_enemigos(self._datos_enemigos_nivel, self._datos_boss_nivel)
            self.vista.restaurar_enemigos(self._datos_enemigos_nivel, self._datos_boss_nivel)
            self.modelo.limpiar_proyectiles_boss()

            self.vista.sprite_checkpoint.activar()
            self.activar_pantalla_carga()
        except Exception as e:
            print(f"[Presenter] ✗ Error al cargar: {e}")

    def activar_pantalla_carga(self):
        self._cargando     = True
        self._frames_carga = self._FRAMES_ESPERA

    def posicion_jugador_actual(self):
        """Posición actual del jugador en coordenadas de mundo.

        Punto único de acceso para quien esté fuera del Presenter (p.ej.
        main.py) y necesite saber dónde está el jugador al cerrar un
        nivel: delega en la Vista en vez de que el caller externo tenga
        que conocer la existencia de `sprite_jugador.shape`.
        """
        return self.vista.posicion_jugador()

    def _procesar_eventos_combate(self, eventos):
        for tipo, dato in eventos:
            if tipo == 'golpe_jugador_a_enemigo':
                self.modelo.golpe_jugador_a_enemigo(dato)
            elif tipo == 'golpe_enemigo_a_jugador':
                self.modelo.golpe_enemigo_a_jugador()
                if self.audio: self.audio.sfx_hurt_jugador()
            elif tipo == 'golpe_proyectil_a_jugador':
                self.modelo.golpe_proyectil_a_jugador(dato)
                if self.audio: self.audio.sfx_hurt_jugador()
            elif tipo == 'golpe_jugador_a_proyectil':
                self.modelo.golpe_jugador_a_proyectil(dato)
            elif tipo == 'golpe_daga_jugador_a_enemigo':
                indice, proyectil = dato
                self.modelo.golpe_daga_jugador_a_enemigo(indice, proyectil)
            elif tipo == 'golpe_daga_jugador_a_boss':
                self.modelo.golpe_daga_jugador_a_boss(dato)
            elif tipo == 'golpe_proyectil_boss_a_jugador':
                self.modelo.golpe_proyectil_boss_a_jugador(dato)
                if self.audio: self.audio.sfx_hurt_jugador()
            elif tipo == 'golpe_boss_a_jugador':
                self.modelo.golpe_boss_a_jugador()
            elif tipo == 'golpe_jugador_a_boss':
                self.modelo.golpe_jugador_a_boss()

    # --- Game loop ---

    def ejecutar(self):
        while self.ejecutando:
            events = pygame.event.get()

            if self._pausado:
                self.vista.refrescar()
                self._procesar_pausa(events)
                continue

            if self._spikes_fase is not None:
                self._frame_spikes(events)
                continue

            if self._cargando:
                self._frame_carga(events)
                continue

            self._frame_boss_audio(events)
            self.vista.procesar_input(events)

            if self.modelo.jugador.vivo:
                self._frame_normal()
            else:
                delta_time = self.vista.refrescar()
                self.vista.tick_game_over(delta_time)
                if self.vista.game_over_terminado:
                    self.ejecutando = False

            estado_jugador   = self.vista.obtener_estado_jugador(self.modelo)
            estados_enemigos = self.vista.obtener_estados_enemigos(self.modelo)
            self.vista.renderizar(estado_jugador, estados_enemigos, self.modelo)

            # renderizar() ya ha avanzado y dibujado la secuencia de fin de
            # juego internamente si estaba activa — aquí solo comprobamos
            # si ha terminado, SIN volver a tocarla (antes se duplicaba
            # la llamada a actualizar()/draw() con un delta_time falso).
            if self.vista.fin_de_juego_terminado:
                self.juego_finalizado = True
                self.ejecutando = False

    def _frame_spikes(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.ejecutando = False
                self.salida_forzada = True
                return

        delta_time = self.vista.refrescar()
        self._spikes_timer_ms -= delta_time

        if self._spikes_fase == 'congelado':
            estado_jugador   = self.vista.obtener_estado_jugador(self.modelo)
            estados_enemigos = self.vista.obtener_estados_enemigos(self.modelo)
            self.vista.renderizar(estado_jugador, estados_enemigos, self.modelo)
            if self._spikes_timer_ms <= 0:
                x, y = self._spikes_respawn_pos
                self.vista.restaurar_pos_jugador(int(x), int(y))
                self._spikes_fase     = 'negro'
                self._spikes_timer_ms = self._SPIKES_MS_NEGRO

        elif self._spikes_fase == 'negro':
            self.vista.actualizar_gravedad_jugador(self.modelo, delta_time)
            self.vista.dibujar_pantalla_negra()
            if self._spikes_timer_ms <= 0:
                self._spikes_fase        = None
                self._spikes_respawn_pos = None

    def _frame_carga(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.ejecutando = False
                self.salida_forzada = True
                return

        delta_time = self.vista.refrescar()
        eventos = self.vista.actualizar_fisica(self.modelo, delta_time)
        self._procesar_eventos_combate(eventos)
        self.modelo.tick(delta_time)
        self.vista.aplicar_movimiento_boss(self.modelo)
        self.vista.dibujar_pantalla_cargando()

        self._frames_carga -= 1
        if self._frames_carga <= 0:
            self._cargando = False

    def _frame_boss_audio(self, events):
        for event in events:
            if event.type == pygame.USEREVENT + 2:
                if self.audio:
                    self.audio.sfx_muerte_boss()
                pygame.time.set_timer(pygame.USEREVENT + 1, 900, loops=1)
            if event.type == pygame.USEREVENT + 1:
                if self.audio:
                    self.audio.reproducir_musica("Assets/Audio/Music/Ambient_Lingering_Action.wav")

    def _frame_normal(self):
        delta_time = self.vista.refrescar()
        eventos = self.vista.actualizar_fisica(self.modelo, delta_time)
        self._procesar_eventos_combate(eventos)

        muertos = self.modelo.tick(delta_time)
        self.vista.aplicar_movimiento_boss(self.modelo)

        for i, tipo in reversed(muertos):
            if self.audio:
                self.audio.sfx_muerte_enemigo(tipo)

        if self.audio and self.modelo.boss_recien_derrotado():
            pygame.time.set_timer(pygame.USEREVENT + 2, 1500, loops=1)

        for i, _ in reversed(muertos):
            self.vista.eliminar_sprite_enemigo(i)
