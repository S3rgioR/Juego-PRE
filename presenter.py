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
from MenuPausa   import MenuPausa
from view import FinDeJuegoSequence

from MenuConfig import MenuConfig

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

    def __init__(self, vista, modelo, num_frames_ataque_jugador=4, audio=None, num_nivel=1,
                 datos_enemigos=None, datos_boss=None):

        self.vista      = vista
        self.modelo     = modelo
        self.audio = audio
        if audio:
            pass  # sfx_salto y sfx_ataque_jugador se reproducen condicionalmente
                  # desde _saltar()/_atacar(), respetando coyote time y cooldown
            # Suscripción a los eventos de la fachada del Model: el Presenter
            # no conoce Enemigo1Model/Enemigo2Model/BossModel directamente,
            # solo JuegoModel (respeta MVP: único punto de acceso al Model).
            self.modelo.evt_enemigo_ataque.add_listener(audio.sfx_ataque_ogro)
            self.modelo.evt_enemigo_disparo.add_listener(audio.sfx_ataque_enemigo2)
            self.modelo.evt_boss_disparo.add_listener(audio.sfx_ataque_boss)
            # evt_enemigo_deteccion NO se conecta aquí: el aviso de
            # detección (sonido + "!") tiene un cooldown de 2s por
            # enemigo que es puramente gráfico/de presentación, así que
            # es la Vista quien decide cuándo reproducirlo (ver
            # PygameView.dibujar / sprite.aviso_deteccion_listo), no el
            # Presenter conectando el evento del Model directo al audio.
        self.ejecutando = True
        self._num_frames_ataque_jugador = num_frames_ataque_jugador
        self.save_manager = SaveManager()
        self._pausado     = False
        self._menu_pausa  = None   # se crea al pausar (así tiene el save actualizado)
        self.salida_forzada   = False  # True si el usuario cerró la ventana con la X
        self.nivel_a_cargar   = None   # int si hay que relanzar en otro nivel
        # Datos originales del nivel: necesarios para restaurar enemigos al cargar
        self._datos_enemigos_nivel = datos_enemigos or []
        self._datos_boss_nivel     = datos_boss

        # --- Suscripción a eventos de la Vista ---
        self.vista.evt_cerrar.add_listener(self._cerrar)
        self.vista.evt_pausa.add_listener(self._togglear_pausa)

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
        self.vista.evt_curar.add_listener(self._curar_jugador)
        self.vista.evt_corazon_recogido.add_listener(self._corazon_recogido)
        self.vista.evt_daga_recogida.add_listener(self._daga_recogida)
        self.vista.evt_lanzar_daga.add_listener(self._lanzar_daga)
        self.vista.evt_nivel_anterior.add_listener(self._nivel_anterior)
        self.vista.evt_tecla_e.add_listener(self._usar_portal)
        self.vista.evt_spikes_tocados.add_listener(self._spikes_tocados)

        self.num_nivel = num_nivel
        self.nivel_completado = False
        self.nivel_anterior = False
        self.estado_jugador_al_retroceder = None
        # Estado acumulado recibido de main.py al entrar al nivel
        # (se usa para guardar en checkpoint y propagar al retroceder).
        self._estado_jugador_previo = None

        self.vista.evt_nivel_completado.add_listener(self._nivel_completado)

        self.juego_finalizado = False
        self._seq_activa = False
        self.vista.evt_tecla_e.add_listener(self._usar_portal)

        # Pantalla de carga: True mientras se muestra el overlay negro
        self._cargando        = False
        # Número de frames físicos que se ejecutan con overlay visible
        # antes de quitar la pantalla. 10 frames ≈ 166 ms a 60 FPS:
        # suficiente para que la física resuelva colisiones post-carga.
        self._frames_carga    = 0
        self._FRAMES_ESPERA   = 30

        # --- Secuencia de pinchos (Spikes) ---
        # fase: None | 'congelado' | 'negro'
        #   'congelado' (500 ms): el juego se congela en el frame del golpe.
        #   'negro'     (1000 ms): pantalla en negro; al terminar se
        #                teletransporta al jugador a la última posición
        #                guardada en una de las barreras de los pinchos.
        self._spikes_fase         = None
        self._spikes_timer_ms     = 0
        self._spikes_respawn_pos  = None
        self._SPIKES_MS_CONGELADO = 500
        self._SPIKES_MS_NEGRO     = 1000

    # --- Handlers de eventos ---
    def _nivel_completado(self):
        self.nivel_completado = True
        self.ejecutando = False

    def _cerrar(self):
        self.ejecutando     = False
        self.salida_forzada = True

    def _nivel_anterior(self):
        self.estado_jugador_al_retroceder = self.modelo.obtener_estado_guardado()
        self.estado_jugador_al_retroceder['daga_desbloqueada'] = self.modelo.jugador.daga_desbloqueada
        self.estado_jugador_al_retroceder['corazones_recogidos'] = self.vista.indices_corazones_recogidos()
        self.estado_jugador_al_retroceder['daga_recogida'] = bool(
                self.vista.sprite_daga_pickup is not None
                and self.vista.sprite_daga_pickup.recogida
        )
        self.estado_jugador_al_retroceder['pos_retroceso'] = list(self.vista.sprite_jugador.shape.center)
        # Propagar el estado de niveles anteriores tal como llegó:
        # main.py lo usará para reconstruir la cadena completa al retroceder.
        if self._estado_jugador_previo is not None:
            self.estado_jugador_al_retroceder['estado_niveles_anteriores'] = self._estado_jugador_previo
        self.nivel_anterior = True
        self.ejecutando = False

    def _spikes_tocados(self, pos_respawn):
        """El jugador ha tocado unos pinchos.

        Aplica 1 corazón de daño (reutilizando la misma regla que un
        golpe de enemigo) y arranca la secuencia: congelar 0.5s →
        pantalla negra 1s → reaparecer en la última posición registrada
        junto a los pinchos (la Vista la guarda al pasar por alguna de
        las dos barreras invisibles adyacentes).

        Si ya hay una secuencia de pinchos en curso, se ignora (evita
        re-disparar mientras el jugador sigue solapando el hitbox).
        """
        if self._spikes_fase is not None:
            return
        self.modelo.golpe_enemigo_a_jugador()
        if self.audio:
            self.audio.sfx_hurt_jugador()

        # Congelar TODO de golpe: si el jugador llevaba A/D pulsado, hay
        # que cortar el movimiento en Vista y Model a la vez (mismo
        # mecanismo que usa _togglear_pausa), o si no la velocidad
        # horizontal queda "pegada" y, al reaparecer, el jugador sigue
        # caminando indefinidamente en esa dirección sin que la tecla
        # siga pulsada.
        if self.vista._dir_derecha_pulsada:
            self.vista.evt_mover_derecha_fin.emit()
            self.vista._dir_derecha_pulsada = False
        if self.vista._dir_izquierda_pulsada:
            self.vista.evt_mover_izquierda_fin.emit()
            self.vista._dir_izquierda_pulsada = False

        self._spikes_respawn_pos = pos_respawn
        self._spikes_fase        = 'congelado'
        self._spikes_timer_ms    = self._SPIKES_MS_CONGELADO

    def _togglear_pausa(self):
        self._pausado = not self._pausado
        if self._pausado:
            # Al pausar, el juego deja de recibir KEYUP de movimiento
            # (la Vista no procesa input mientras _pausado, solo el menú
            # de pausa lo hace). Si el jugador suelta A/D con el menú ya
            # abierto, ese KEYUP se pierde y tanto la Vista
            # (_dir_derecha/izquierda_pulsada) como el Model
            # (mover_derecha/mover_izquierda) quedan "atascados" en
            # movimiento, así que al reanudar el jugador sale disparado
            # en esa dirección. Se fuerza aquí el mismo camino que un
            # KEYUP real (eventos evt_mover_*_fin), que limpia el estado
            # en ambos lados a la vez.
            if self.vista._dir_derecha_pulsada:
                self.vista.evt_mover_derecha_fin.emit()
                self.vista._dir_derecha_pulsada = False
            if self.vista._dir_izquierda_pulsada:
                self.vista.evt_mover_izquierda_fin.emit()
                self.vista._dir_izquierda_pulsada = False

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
            if accion == 'reanudar':
                self._pausado = False
            elif accion == 'cargar':
                self._cargar_partida(); self._pausado = False
            elif accion == 'config':
                MenuConfig(self.vista.screen, self.audio).ejecutar()
                # Redibujar: primero el juego congelado, luego la pausa encima
                estado_jugador = self.vista.obtener_estado_jugador(self.modelo)
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
        shape = self.vista.sprite_jugador.shape
        if self.vista.portal_fin and self.vista.portal_fin.esta_cerca(shape):
            self._nivel_completado()
        elif self.vista.portal_regreso and self.vista.portal_regreso.esta_cerca(shape):
            self._nivel_anterior()
        elif self.vista.portal_final and self.vista.portal_final.esta_cerca(shape):
            self._activar_fin_juego()

    def _activar_fin_juego(self):
        self.vista._seq_fin_juego = FinDeJuegoSequence(self.vista.screen)
        self._seq_activa = True

    def _saltar(self):
        """Pide al Model que intente saltar y solo reproduce el sfx si
        el salto se ha ejecutado realmente (en suelo o dentro del coyote
        time). Si el jugador ya está en el aire fuera de ese margen, la
        pulsación no tiene efecto y no debe sonar nada.
        """
        salto_real = self.modelo.jugador_saltar()
        if salto_real and self.audio:
            self.audio.sfx_salto()
    def _atacar(self):
        """Pide al Model que inicie el ataque y solo reproduce el sfx si
        se ha ejecutado realmente (respeta COOLDOWN_ATAQUE_MS). Si el
        jugador ya está atacando o el cooldown no ha pasado, la
        pulsación no tiene efecto y no debe sonar nada.
        """
        ataque_real = self.modelo.jugador_atacar(self._num_frames_ataque_jugador)
        if ataque_real and self.audio:
            self.audio.sfx_ataque_jugador()

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
        """Guarda posición (de la Vista), hp (del Model), cámara y el estado
        acumulado de los niveles anteriores (para que el portal de regreso
        funcione correctamente tras una carga)."""
        try:
            estado = self.modelo.obtener_estado_guardado()
            estado['pos']                 = list(self.vista.sprite_jugador.shape.center)
            estado['camara']              = self.vista.camara_pos
            estado['corazones_recogidos'] = self.vista.indices_corazones_recogidos()
            estado['num_nivel']           = self.num_nivel
            estado['daga_desbloqueada']   = self.modelo.jugador.daga_desbloqueada
            # Guardar si el boss ya fue derrotado
            estado['boss_derrotado'] = (
                self.modelo.boss is None or not self.modelo.boss.vivo
            )
            # Guardar si la daga pickup ya fue recogida.
            # Si el nivel no tiene daga (sprite_daga_pickup is None) se guarda
            # False: la ausencia del objeto no equivale a haberlo recogido.
            # Solo se guarda True si el sprite existe Y está marcado como recogido.
            estado['daga_recogida'] = bool(
                self.vista.sprite_daga_pickup is not None
                and self.vista.sprite_daga_pickup.recogida
            )
            # Snapshot del estado acumulado de niveles anteriores.
            # Esto permite que al cargar y usar el portal de regreso,
            # los objetos ya recogidos en niveles previos sigan recogidos.
            if self._estado_jugador_previo is not None:
                estado['estado_niveles_anteriores'] = self._estado_jugador_previo
            if self.save_manager.guardar(estado):
                print("[Presenter] ✓ Partida guardada")
                self.vista.sprite_checkpoint.activar()
        except Exception as e:
            print(f"[Presenter] ✗ Error al guardar: {e}")

    def _cargar_partida(self):
        """Carga y restaura posición (en Vista), hp (en Model) y cámara.

        Si el nivel guardado es distinto al actual, cierra este nivel y
        señaliza a main.py para que arranque el nivel correcto vía
        self.nivel_a_cargar (int) con los datos del save ya leídos.
        """
        try:
            datos = self.save_manager.cargar()
            if datos is None:
                print("[Presenter] No hay partida guardada"); return

            nivel_guardado = datos.get('num_nivel', self.num_nivel)

            # Si el nivel guardado es diferente, cerramos este loop y dejamos
            # que main.py relance iniciar_partida con cargar_save=True.
            if nivel_guardado != self.num_nivel:
                self.nivel_a_cargar  = nivel_guardado
                self.ejecutando      = False
                self._pausado        = False
                print(f"[Presenter] → Cambiando al nivel {nivel_guardado} para cargar")
                return

            # Mismo nivel: restaurar en caliente sin reiniciar la escena.
            self.modelo.cargar_estado_guardado(datos)

            if 'pos' in datos:
                x, y = datos['pos']
                self.vista.restaurar_pos_jugador(int(x), int(y))
                # Resetear velocidad vertical para que el jugador no llegue
                # con inercia acumulada del estado anterior al punto de carga.
                self.modelo.jugador.velocidad_y = 0
            if 'camara' in datos:
                self.vista.restaurar_camara(*datos['camara'])
            if 'corazones_recogidos' in datos:
                self.vista.restaurar_corazones_recogidos(
                    set(datos['corazones_recogidos']))
            if datos.get('daga_recogida'):
                self.vista.restaurar_daga_recogida()
                self.modelo.jugador_desbloquear_daga()
            else:
                if self.vista.sprite_daga_pickup:
                    self.vista.sprite_daga_pickup.recogida = False

            # Restaurar boss: si estaba derrotado al guardar, matarlo en el modelo
            if datos.get('boss_derrotado') and self.modelo.boss:
                self.modelo.boss.vivo = False

            # Restaurar el estado acumulado de niveles anteriores.
            # Se guarda en _estado_jugador_previo para que _nivel_anterior()
            # lo propague correctamente si el jugador usa el portal de regreso.
            self._estado_jugador_previo = datos.get('estado_niveles_anteriores', None)

            # Restaurar enemigos: los que habían muerto vuelven a su posición
            # inicial y se limpian todos los proyectiles en pantalla.
            self.modelo.restaurar_enemigos(
                self._datos_enemigos_nivel, self._datos_boss_nivel)
            self.vista.restaurar_enemigos(
                self._datos_enemigos_nivel, self._datos_boss_nivel)
            # Limpiar también los proyectiles de los modelos de enemigos voladores
            # (el modelo los recrea vacíos, pero los del boss se limpian explícitamente)
            if self.modelo.boss:
                self.modelo.boss.proyectiles = []

            self.vista.sprite_checkpoint.activar()
            # Activar pantalla de carga: congela el loop visible hasta que
            # la física haya resuelto la posición guardada correctamente.
            self.activar_pantalla_carga()
            print("[Presenter] ✓ Partida cargada")
        except Exception as e:
            print(f"[Presenter] ✗ Error al cargar: {e}")

    def activar_pantalla_carga(self):
        """Activa el overlay de "Cargando...": congela el loop visible
        (bloquea inputs de juego) durante self._FRAMES_ESPERA frames,
        mientras la física resuelve en silencio la posición del jugador.

        Usado tanto al cargar una partida guardada como al entrar a un
        nivel atravesando un portal (avance o retroceso), para que la
        experiencia sea idéntica en ambos casos.
        """
        self._cargando     = True
        self._frames_carga = self._FRAMES_ESPERA

    # --- Despacho de eventos de combate (MVP: la Vista solo detecta) ---

    def _procesar_eventos_combate(self, eventos):
        """Traduce los eventos de colisión detectados por la Vista en
        llamadas concretas al Model.

        La Vista (en `actualizar_fisica`) solo informa de qué hitboxes se
        solaparon; es el Presenter quien decide invocar al Model y disparar
        los efectos de sonido asociados, manteniendo a la Vista ajena a las
        reglas de negocio.
        """
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
            events = pygame.event.get()

            if self._pausado:
                self.vista.refrescar()   # limita FPS también en pausa
                self._procesar_pausa(events)
                continue

            # --- Secuencia de pinchos (Spikes): congelado → negro → respawn ---
            if self._spikes_fase is not None:
                for event in events:
                    if event.type == pygame.QUIT:
                        self.ejecutando = False
                        self.salida_forzada = True
                        break

                delta_time = self.vista.refrescar()
                self._spikes_timer_ms -= delta_time

                if self._spikes_fase == 'congelado':
                    # Todo congelado: ni física del jugador, ni enemigos,
                    # ni Model.tick(). Se repinta el mismo frame quieto.
                    estado_jugador   = self.vista.obtener_estado_jugador(self.modelo)
                    estados_enemigos = self.vista.obtener_estados_enemigos(self.modelo)
                    self.vista.renderizar(estado_jugador, estados_enemigos, self.modelo)
                    if self._spikes_timer_ms <= 0:
                        # Al empezar la pantalla negra: teletransportar
                        # YA al jugador a la posición guardada, para que
                        # caiga con gravedad real sobre la plataforma
                        # mientras la pantalla está negra (no al final).
                        x, y = self._spikes_respawn_pos
                        self.vista.restaurar_pos_jugador(int(x), int(y))
                        self._spikes_fase     = 'negro'
                        self._spikes_timer_ms = self._SPIKES_MS_NEGRO

                elif self._spikes_fase == 'negro':
                    # Pantalla negra: se retoma la gravedad SOLO del
                    # jugador (cae y se asienta en la plataforma), sin
                    # mover enemigos, sin IA, sin combate y sin leer
                    # inputs de movimiento (siguen desactivados). El
                    # control total (input + resto de entidades) se
                    # retoma recién al salir de esta fase.
                    self.vista.actualizar_gravedad_jugador(self.modelo, delta_time)
                    self.vista.dibujar_pantalla_negra()
                    if self._spikes_timer_ms <= 0:
                        self._spikes_fase        = None
                        self._spikes_respawn_pos = None
                continue

            # --- Pantalla de carga post-restauración ---
            # Mientras _cargando es True: ejecutamos la física en silencio
            # (para que el motor resuelva colisiones con el entorno) y
            # pintamos un overlay negro con "Cargando..." en pantalla.
            # Solo salimos cuando se han procesado _FRAMES_ESPERA frames.
            if self._cargando:
                # Procesar salida de ventana incluso durante la carga
                for event in events:
                    if event.type == pygame.QUIT:
                        self.ejecutando = False
                        self.salida_forzada = True
                        break

                delta_time = self.vista.refrescar()
                # Ejecutar física para que el jugador quede bien colocado
                eventos = self.vista.actualizar_fisica(self.modelo, delta_time)
                self._procesar_eventos_combate(eventos)
                self.modelo.tick(delta_time)
                self.vista.aplicar_movimiento_boss(self.modelo)

                # Dibujar overlay negro con texto
                self.vista.dibujar_pantalla_cargando()

                self._frames_carga -= 1
                if self._frames_carga <= 0:
                    self._cargando = False
                continue

            # Eventos diferidos de muerte del boss
            for event in events:
                if event.type == pygame.USEREVENT + 2:
                    # Rugido de muerte: suena 1.5 s después de morir el boss
                    if self.audio:
                        self.audio.sfx_muerte_boss()
                    # 900 ms después del rugido, cambiar la música
                    pygame.time.set_timer(pygame.USEREVENT + 1, 0, loops=1)
                if event.type == pygame.USEREVENT + 1:
                    if self.audio:
                        self.audio.reproducir_musica("Assets/Audio/Music/Ambient_Lingering_Action.wav")

            self.vista.procesar_input(events)

            if self.modelo.jugador.vivo:
                # 2. Delta time
                delta_time = self.vista.refrescar()

                # 3. Vista: mover objetos + detectar colisiones (solo geometría)
                eventos = self.vista.actualizar_fisica(self.modelo, delta_time)

                # 3b. Presenter: decide qué hacer con cada colisión detectada
                self._procesar_eventos_combate(eventos)

                # 4. Model: avanzar contadores internos (incluye la IA del
                #    boss, que ahora vive enteramente en el Model)
                muertos = self.modelo.tick(delta_time)

                # 4b. Vista: aplica al sprite el desplazamiento que el Model
                #     decidió para el boss (la Vista no decide, solo dibuja)
                self.vista.aplicar_movimiento_boss(self.modelo)
                # muertos es lista de (indice, tipo) — el Model ya los eliminó
                for i, tipo in reversed(muertos):
                    if self.audio:
                        self.audio.sfx_muerte_enemigo(tipo)

                # Muerte del boss (fuera del bucle de enemigos)
                if (self.audio and self.modelo.boss
                        and not self.modelo.boss.vivo
                        and not getattr(self, '_boss_muerto_sonado', False)):
                    self._boss_muerto_sonado = True
                    # Rugido diferido 3 s; la música cambia 900 ms después del rugido
                    pygame.time.set_timer(pygame.USEREVENT + 2, 1500, loops=1)

                # 5. Eliminar sprites de enemigos muertos
                for i, _ in reversed(muertos):
                    self.vista.eliminar_sprite_enemigo(i)

            else:
                # Jugador muerto: avanzar la secuencia de Game Over.
                delta_time = self.vista.refrescar()
                self.vista.tick_game_over(delta_time)
                if self.vista.game_over_terminado:
                    self.ejecutando = False   # sale del loop → main.py vuelve al menú

            # 6. Renderizar
            estado_jugador   = self.vista.obtener_estado_jugador(self.modelo)
            estados_enemigos = self.vista.obtener_estados_enemigos(self.modelo)
            self.vista.renderizar(estado_jugador, estados_enemigos, self.modelo)

            # Secuencia de fin de juego
            if self._seq_activa and self.vista._seq_fin_juego:
                delta_time = getattr(self, '_last_delta', 16)
                self.vista._seq_fin_juego.actualizar(delta_time)
                self.vista._seq_fin_juego.draw()
                pygame.display.flip()
                if self.vista._seq_fin_juego.terminado:
                    self.juego_finalizado = True
                    self.ejecutando = False
