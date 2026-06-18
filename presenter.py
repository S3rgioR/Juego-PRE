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
from model import BossModel
from model.Enemigo1Model import Enemigo1Model
from model.Enemigo2Model import Enemigo2Model

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

    def __init__(self, vista, modelo, num_frames_ataque_jugador=4, audio=None, num_nivel=1):

        self.vista      = vista
        self.audio = audio
        if audio:
            self.vista.evt_saltar.add_listener(audio.sfx_salto)
            self.vista.evt_atacar.add_listener(audio.sfx_ataque_jugador)
        if audio:
            Enemigo1Model.on_ataque = audio.sfx_ataque_ogro
        if audio:
            BossModel.on_disparo = audio.sfx_ataque_boss
        if audio:
            Enemigo1Model.on_deteccion = audio.sfx_deteccion_enemigo
            Enemigo2Model.on_deteccion = audio.sfx_deteccion_enemigo
        self.modelo     = modelo
        self.ejecutando = True
        self._num_frames_ataque_jugador = num_frames_ataque_jugador
        self.save_manager = SaveManager()
        self._pausado     = False
        self._menu_pausa  = None   # se crea al pausar (así tiene el save actualizado)
        self.salida_forzada   = False  # True si el usuario cerró la ventana con la X
        self.nivel_a_cargar   = None   # int si hay que relanzar en otro nivel

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

        self.num_nivel = num_nivel
        self.nivel_completado = False
        self.nivel_anterior = False
        self.estado_jugador_al_retroceder = None

        self.vista.evt_nivel_completado.add_listener(self._nivel_completado)

        self.juego_finalizado = False
        self._seq_activa = False
        self.vista.evt_tecla_e.add_listener(self._usar_portal)

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
        self.estado_jugador_al_retroceder['daga_recogida'] = (
                self.vista.sprite_daga_pickup is None
                or self.vista.sprite_daga_pickup.recogida
        )
        self.estado_jugador_al_retroceder['pos'] = list(self.vista.sprite_jugador.shape.center)  # ← NUEVO
        self.nivel_anterior = True
        self.ejecutando = False

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
        from view.FinDeJuegoSequence import FinDeJuegoSequence
        self.vista._seq_fin_juego = FinDeJuegoSequence(self.vista.screen)
        self._seq_activa = True

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
        """Guarda posición (de la Vista), hp (del Model) y cámara."""
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

            self.vista.sprite_checkpoint.activar()
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
            events = pygame.event.get()

            if self._pausado:
                self.vista.refrescar()   # limita FPS también en pausa
                self._procesar_pausa(events)
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

                # 3. Vista: mover objetos + detectar colisiones + notificar Model
                self.vista.actualizar_fisica(self.modelo, delta_time)

                # 4. Model: avanzar contadores internos
                muertos = self.modelo.tick(delta_time)
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
                # Jugador muerto: limitar FPS igualmente para no saturar la CPU
                self.vista.refrescar()

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
