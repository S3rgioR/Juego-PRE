"""Capa View del patrón MVP - Física, entrada, visualización y eventos.

Responsabilidades:
- Inicializar pygame y la ventana gráfica
- Capturar entrada del usuario (teclado, cierre de ventana)
- Mover todos los objetos del juego (jugador y enemigos)
- Detectar colisiones entre objetos y notificar al Model
- Actualizar la cámara
- Renderizar todos los sprites
- Emitir eventos que el Presenter escucha

Lo que NO hace la Vista:
- Decidir qué ocurre cuando hay una colisión (responsabilidad del Model)
- Gestionar hp, iframes ni cooldowns (responsabilidad del Model)
- Coordinar el flujo del juego (responsabilidad del Presenter)

Filosofía de esta arquitectura:
    La Vista es el motor físico. Mueve los objetos, detecta solapamientos
    y consulta al Model mediante llamadas explícitas:
        - modelo.golpe_jugador_a_enemigo(i)
        - modelo.golpe_enemigo_a_jugador()
        - modelo.golpe_proyectil_a_jugador(p)
        - jugador_model.notificar_en_suelo()
        - enemigo_model.notificar_en_suelo()
    El Model actualiza su estado interno y la Vista sigue dibujando
    a partir del estado exportado por el Model.

Nota sobre convert_alpha():
    pygame.Surface.convert_alpha() requiere que pygame.display.set_mode()
    ya haya sido llamado. Por eso el tileset y los fondos se cargan aquí,
    dentro de __init__, después de crear la ventana.
"""

import pygame
import Constantes
import Fuentes

from .Event              import Event
from .Camara             import Camara
from .Personaje          import PersonajeSprite
from .Ogro          import OgroSprite
from .Fantasma          import FantasmaSprite
from .Plataforma         import Plataforma
from .CheckpointView     import CheckpointView
from .AngelView          import AngelView
from .CorazonView        import CorazonView
from .DagaPickupView     import DagaPickupView
from .DagaProyectilSprite import DagaProyectilSprite
from Nivel               import CHECKPOINT_NIVEL_1
from .BossSprite         import BossSprite
from .BloodEffect        import BloodEffect
from .ExplosionEffect    import ExplosionEffect
from .HitEffect          import HitEffect
from .PortalView         import PortalView
from .ParedBossView      import ParedBossView
from .PortalFinalView    import PortalFinalView
from .FinDeJuegoSequence import FinDeJuegoSequence
from .GameOverSequence   import GameOverSequence

class PygameView:
    """Gestiona física, entrada, cámara, sprites y renderizado del juego.

    Attributes
    ----------
    screen : pygame.Surface
        Superficie principal de la ventana.
    reloj : pygame.time.Clock
        Controla la velocidad del game loop.
    camara : Camara
        Gestiona el desplazamiento de la vista.
    fondo, fondo_walls : pygame.Surface
        Capas de fondo estáticas.
    sprite_jugador : PersonajeSprite
        Sprite visual y shape físico del jugador.
    sprites_enemigos : list
        Sprites visuales y shapes físicos de los enemigos.
    sprites_plataformas : list of Plataforma
        Geometría y visualización del nivel.
    """
    def __init__(self, frames_jugador, datos_enemigos, nivel_loader, datos_boss, audio=None,
                 frames_angel=None, datos_angel=None,
                 imagen_corazon=None, datos_corazones=None,
                 imagen_daga_pickup=None, datos_daga_pickup=None,
                 datos_spawn=None,
                 datos_checkpoint=None,
                 frames_daga_proyectil=None,
                 datos_pared_boss=None,
                 datos_fin_nivel=None,
                 datos_portal_final=None,
                 datos_portal_regreso=None):
        """
        Parámetros nuevos
        -----------------
        imagen_daga_pickup : pygame.Surface
            Imagen del objeto daga en el suelo (Assets/Characters/Daga.png).
        datos_daga_pickup : dict or None
            {'x': int, 'y': int}. Si es None no hay objeto daga en el mapa.
        frames_daga_proyectil : list of pygame.Surface
            Frames del proyectil daga (Assets/Characters/Dagger/dagger.png).
        """
        # pygame.init() y set_mode() ya fueron llamados en main.py
        # No volver a llamarlos aquí: reinicializarían el mixer y matarían la música.
        self.screen = pygame.display.get_surface()

        self.reloj  = pygame.time.Clock()
        self.camara = Camara()

        # Teclas mantenidas: la cámara las usa para desplazarse hacia donde
        # el jugador lleva rato mirando/caminando. A/D ya mueven al jugador;
        # W/S no se usan para nada más en el gameplay, así que quedan libres
        # para "mirar arriba/abajo" con la cámara.
        self._dir_derecha_pulsada  = False
        self._dir_izquierda_pulsada = False
        self._mirar_arriba_pulsada  = False
        self._mirar_abajo_pulsada   = False

        # --- Checkpoint ---
        cx, cy = datos_checkpoint if datos_checkpoint else CHECKPOINT_NIVEL_1
        img_checkpoint = pygame.image.load(
            "Assets/Characters/statue.png"
        ).convert_alpha()
        self.sprite_checkpoint = CheckpointView(cx, cy, img_checkpoint)

        # --- HUD de vida (corazones) ---
        self._frames_vida_hud = self._cargar_frames_vida_hud()
        # --- HUD de inventario (slot + icono de daga) ---
        self._frames_inventario_hud = self._cargar_frames_inventario_hud()
        # --- Fondos ---
        fondo_raw = pygame.image.load(
            "Assets/Enviorments/caverns-files-web/layers/background.png"
        ).convert()
        self.fondo = pygame.transform.scale(fondo_raw, (Constantes.WIDTH, Constantes.HEIGHT))

        fondo_walls_raw = pygame.image.load(
            "Assets/Enviorments/caverns-files-web/layers/back-walls.png"
        ).convert_alpha()
        self.fondo_walls = pygame.transform.scale(
            fondo_walls_raw, (Constantes.WIDTH, Constantes.HEIGHT)
        )

        # --- Tileset + plataformas ---
        tileset = pygame.image.load(
            "Assets/Enviorments/caverns-files-web/layers/tiles_mini.png"
        ).convert_alpha()
        self.sprites_plataformas = nivel_loader(tileset)

        # Subconjunto solido (sin las plataformas flotantes): los enemigos
        # las ignoran por completo, tanto para gravedad como para detectar
        # bordes de patrulla.
        self.sprites_plataformas_solidas = [
            p for p in self.sprites_plataformas if not p.unidireccional
        ]

        # Geometría pura (sin objetos Plataforma) de las plataformas sólidas,
        # para pasar al Model en tick_ia(tiles_solidos=...). Las plataformas
        # son estáticas tras cargar el nivel, así que esta caché se calcula
        # una sola vez aquí: el Model nunca debe recibir ni tocar objetos de
        # la Vista (ver EnemigoModel._hay_pared_entre).
        self._bboxes_plataformas_solidas = [
            (p.shape.left, p.shape.top, p.shape.right, p.shape.bottom)
            for p in self.sprites_plataformas_solidas
        ]

        # --- Proyectiles de enemigos ---
        escala_proj = Constantes.SCALA_PERSONAJE * 0.6
        frames_proyectil = []
        for i in range(1, 3):
            img = pygame.image.load(
                f"Assets/Characters/EnemyProjectile/Sprites/frame{i}.png"
            ).convert_alpha()
            frames_proyectil.append(pygame.transform.scale(
                img, (int(img.get_width() * escala_proj),
                      int(img.get_height() * escala_proj))))
        # Guardar referencia para reutilizarlos en restaurar_enemigos()
        self._frames_proyectil_cache = frames_proyectil

        # Cargar frames del portal
        self._frames_portal = []

        for i in range(1, 65):
            img = pygame.image.load(f"Assets/Efectos/Portal/portal_9/portal{i}.png").convert_alpha()
            w, h = img.get_width(), img.get_height()
            escala = Constantes.SCALA_PERSONAJE * 0.25
            img = pygame.transform.scale(img, (int(w * escala), int(h * escala)))
            self._frames_portal.append(img)

        # --- Portal final de juego (7 frames propios) ---
        self._frames_portal_final = []
        ESCALA_PORTAL_FINAL = Constantes.SCALA_PERSONAJE * 0.5  # ← sube/baja este número para cambiar el tamaño
        for i in range(1, 8):
            img = pygame.image.load(
                f"Assets/Efectos/Portal Final juego/Frames/portal1_frame_{i}.png"
            ).convert_alpha()
            w, h = img.get_width(), img.get_height()
            img = pygame.transform.scale(
                img, (int(w * ESCALA_PORTAL_FINAL), int(h * ESCALA_PORTAL_FINAL)))
            self._frames_portal_final.append(img)

        self.portal_final = None
        self._seq_fin_juego = None
        self._ultimo_delta_ms = 0
        if datos_portal_final:
            self.portal_final = PortalFinalView(
                datos_portal_final['x'], datos_portal_final['y'],
                self._frames_portal_final,
                datos_portal_final.get('ancho', 1),
                datos_portal_final.get('alto', 1),
            )
        # Portal de avance (fin de nivel) — siempre presente si datos_fin_nivel existe
        self.portal_fin = None
        if datos_fin_nivel:
            self.portal_fin = PortalView(
                datos_fin_nivel['x'], datos_fin_nivel['y'],
                self._frames_portal,
                datos_fin_nivel.get('ancho', 1),
                datos_fin_nivel.get('alto', 1),
            )


        # Portal de regreso (solo desde nivel 2 en adelante)
        self.portal_regreso = None
        if datos_portal_regreso:
            self.portal_regreso = PortalView(
                datos_portal_regreso['x'], datos_portal_regreso['y'],
                self._frames_portal,
                datos_portal_regreso.get('ancho', 1),
                datos_portal_regreso.get('alto', 1),
            )

        # --- Sprites jugador y enemigos ---
        # Posición inicial: desde datos_spawn del nivel, o fallback al borde izquierdo.
        if datos_spawn:
            _x_inicio = datos_spawn[0]
            _y_inicio = datos_spawn[1]
        else:
            _x_inicio = 16 + Constantes.WIDTH_PERSONAJE // 2
            _y_inicio = Constantes.SUELO_Y - 16 - Constantes.HEIGHT_PERSONAJE // 2
        self.sprite_jugador = PersonajeSprite(_x_inicio, _y_inicio, frames_jugador)

        self.sprite_boss = None
        if datos_boss:
            self.sprite_boss = BossSprite(
                datos_boss['x'], datos_boss['y'],
                datos_boss['anim_fase1'], datos_boss['anim_fase2'])
            self.sprite_boss.proyectil_frames = frames_proyectil

        # --- Pared del boss ---
        self.pared_boss = None
        if datos_pared_boss:
            img_pared_boss = pygame.image.load(
                "Assets/Enviorments/ParedBoss.png"
            ).convert_alpha()
            self.pared_boss = ParedBossView(
                datos_pared_boss['x'],
                datos_pared_boss['y'],
                datos_pared_boss['ancho'],
                datos_pared_boss['alto'],
                img_pared_boss,
            )
        self.sprites_enemigos = []
        for d in datos_enemigos:
            if d.get('tipo') == 'volador':
                self.sprites_enemigos.append(
                    FantasmaSprite(d['x'], d['y'], d['anim_walk'])
                )
            else:
                self.sprites_enemigos.append(
                    OgroSprite(d['x'], d['y'], d['anim_walk'], d['anim_attack']))

        for sprite in self.sprites_enemigos:
            if isinstance(sprite, FantasmaSprite):
                sprite.proyectil_frames = frames_proyectil
        # El sonido de disparo del enemigo volador se conecta en el Presenter
        # vía modelo.evt_enemigo_disparo (fachada de JuegoModel), no aquí:
        # la Vista no debe conocer ni modificar clases del Model.

        # --- Ángel curador ---
        if datos_angel:
            self.sprite_angel = AngelView(datos_angel['x'], datos_angel['y'], frames_angel or [])
        else:
            self.sprite_angel = None
        # --- Corazones ---
        self.sprites_corazones = []
        if imagen_corazon and datos_corazones:
            for i, d in enumerate(datos_corazones):
                self.sprites_corazones.append(
                    CorazonView(d['x'], d['y'], imagen_corazon, indice=i))

        # --- Daga pickup ---
        self.sprite_daga_pickup = None
        if imagen_daga_pickup and datos_daga_pickup:
            self.sprite_daga_pickup = DagaPickupView(
                datos_daga_pickup['x'], datos_daga_pickup['y'], imagen_daga_pickup)

        # --- Proyectiles de daga del jugador ---
        self._frames_daga_proyectil = frames_daga_proyectil or []
        # Pool de sprites: se crea uno nuevo por cada proyectil vivo
        self._sprites_dagas: list[DagaProyectilSprite] = []

        # --- Eventos MVP ---
        self.evt_cerrar                 = Event()
        self.evt_mover_derecha_inicio   = Event()
        self.evt_mover_derecha_fin      = Event()
        self.evt_mover_izquierda_inicio = Event()
        self.evt_mover_izquierda_fin    = Event()
        self.evt_saltar                 = Event()
        self.evt_atacar                 = Event()
        self.evt_guardar                = Event()
        self.evt_cargar                 = Event()
        self.evt_pausa                  = Event()
        self.evt_curar                  = Event()
        self.evt_corazon_recogido       = Event()   # emite el índice
        self.evt_daga_recogida          = Event()   # sin argumentos
        self.evt_lanzar_daga            = Event()   # sin argumentos
        self.evt_nivel_anterior         = Event()
        self.evt_tecla_e                = Event()

        self.audio = audio

        self.evt_nivel_completado = Event()


        # Rect del trigger (None si el nivel no tiene salida)
        self._trigger_fin_nivel = None
        if datos_fin_nivel:
            self._trigger_fin_nivel = pygame.Rect(
                datos_fin_nivel['x'],
                datos_fin_nivel['y'],
                datos_fin_nivel['ancho'],
                datos_fin_nivel['alto'],
            )



        # --- Efecto de sangre (muerte de enemigos) ---
        self._frames_blood = self._cargar_frames_blood()
        self._efectos_sangre: list = []

        # --- Efecto de explosión (muerte de proyectiles enemigos) ---
        self._frames_explosion = self._cargar_frames_explosion()
        self._efectos_explosion: list = []

        # --- Efecto de impacto de daga ---
        self._frames_hit = self._cargar_frames_hit()
        self._efectos_hit: list = []

        # --- Muerte del boss: flag para disparar una sola vez ---
        self._boss_muerte_disparada = False

        # --- Secuencia de Game Over ---
        self._seq_game_over: GameOverSequence | None = None

    # ------------------------------------------------------------------
    # Acceso a datos compartidos con el Presenter
    # ------------------------------------------------------------------

    @property
    def plataformas(self):
        """Expone la lista de Plataforma al Presenter."""
        return self.sprites_plataformas

    @property
    def camara_pos(self):
        """Devuelve la posición de la cámara como lista serializable."""
        return [self.camara.x, self.camara.y]

    def restaurar_camara(self, cx, cy):
        """Restaura la posición de la cámara al cargar una partida."""
        self.camara.x = cx
        self.camara.y = cy

    def restaurar_pos_jugador(self, x, y):
        """Restaura la posición física del sprite del jugador.

        En esta arquitectura las posiciones viven en la Vista,
        por eso la restauración también debe hacerse aquí.

        Parameters
        ----------
        x, y : int
            Centro del jugador en coordenadas de mundo.
        """
        self.sprite_jugador.shape.center = (x, y)
        self.sprite_jugador._hitbox_ataque_cache = None
        # Sincronizar el float interno _y con la nueva posición.
        # Sin esto, la física parte del _y antiguo el frame siguiente
        # y empuja al jugador de vuelta a donde estaba antes de cargar.
        self.sprite_jugador._y_override = float(self.sprite_jugador.shape.y)

    def restaurar_corazones_recogidos(self, indices: set):
        for c in self.sprites_corazones:
            if c.indice in indices:
                c.recogido = True

    def indices_corazones_recogidos(self):
        return [c.indice for c in self.sprites_corazones if c.recogido]

    def restaurar_daga_recogida(self):
        """Si el save dice que la daga ya fue recogida, ocultarla del mapa."""
        if self.sprite_daga_pickup:
            self.sprite_daga_pickup.recogida = True

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def procesar_input(self, events):
        """Procesa la lista de eventos pygame y emite los eventos MVP correspondientes."""
        for event in events:
            if event.type == pygame.QUIT:
                self.evt_cerrar.emit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.evt_pausa.emit()
                elif event.key == pygame.K_d:
                    self.evt_mover_derecha_inicio.emit()
                    self._dir_derecha_pulsada = True
                elif event.key == pygame.K_a:
                    self.evt_mover_izquierda_inicio.emit()
                    self._dir_izquierda_pulsada = True
                elif event.key == pygame.K_w:
                    self._mirar_arriba_pulsada = True
                elif event.key == pygame.K_s:
                    self._mirar_abajo_pulsada = True
                elif event.key == pygame.K_SPACE:
                    self.evt_saltar.emit()
                elif event.key == pygame.K_j:
                    self.evt_atacar.emit()
                elif event.key == pygame.K_k:
                    if self.sprite_angel and self.sprite_angel.esta_cerca(self.sprite_jugador.shape):
                        self.evt_curar.emit()
                    elif self.sprite_checkpoint.esta_cerca(self.sprite_jugador.shape):
                        self.evt_guardar.emit()
                elif event.key == pygame.K_l:
                    self.evt_lanzar_daga.emit()
                elif event.key == pygame.K_F10:
                    self.evt_cargar.emit()
                elif event.key == pygame.K_SPACE:
                    self.evt_saltar.emit()
                    # El sonido de salto se dispara desde el Presenter
                    # NO llamar aquí para evitar doble disparo si el salto falla.
                elif event.key == pygame.K_e:
                    self.evt_tecla_e.emit()
                    if (self.portal_final and self._seq_fin_juego is None
                            and self.portal_final.esta_cerca(self.sprite_jugador.shape)):
                        self.iniciar_fin_de_juego()

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_d:
                    self.evt_mover_derecha_fin.emit()
                    self._dir_derecha_pulsada = False
                elif event.key == pygame.K_a:
                    self.evt_mover_izquierda_fin.emit()
                    self._dir_izquierda_pulsada = False
                elif event.key == pygame.K_w:
                    self._mirar_arriba_pulsada = False
                elif event.key == pygame.K_s:
                    self._mirar_abajo_pulsada = False

    # ------------------------------------------------------------------
    # Física
    # ------------------------------------------------------------------

    def actualizar_fisica(self, modelo, delta_time_ms):
        """Mueve todos los objetos, detecta colisiones y reporta lo ocurrido.

        IMPORTANTE (MVP): este método ya NO decide ni ejecuta consecuencias
        de combate ni IA. Se limita a:
        1. Mover objetos y resolver colisiones contra el escenario.
        2. Cachear posiciones (jugador/boss) para que el Model pueda usarlas
           internamente (p.ej. para su propia IA en modelo.tick()).
        3. Detectar solapamientos de combate y devolverlos como una lista
           de eventos neutros — quien decide qué hacer con ellos (llamar a
           modelo.golpe_*) es el Presenter, no la Vista.

        Parameters
        ----------
        modelo : JuegoModel
        delta_time_ms : int

        Returns
        -------
        list of tuple
            Eventos de combate detectados este frame, p.ej.:
            ('golpe_jugador_a_enemigo', i)
            ('golpe_enemigo_a_jugador', None)
            ('golpe_proyectil_a_jugador', proyectil)
            ('golpe_jugador_a_proyectil', proyectil)
            ('golpe_daga_jugador_a_enemigo', (i, proyectil))
            ('golpe_daga_jugador_a_boss', proyectil)
            ('golpe_proyectil_boss_a_jugador', proyectil)
            ('golpe_boss_a_jugador', None)
            ('golpe_jugador_a_boss', None)
        """
        eventos = []

        self._mover_jugador(modelo, delta_time_ms)
        self._mover_enemigos(modelo, delta_time_ms)
        self._mover_proyectiles(modelo)
        self._mover_dagas_jugador(modelo, eventos)     # ← proyectiles de daga
        self._detectar_combate(modelo, eventos)
        self._detectar_corazones(modelo)
        self._detectar_daga_pickup(modelo)              # ← recoger objeto daga
        self._ultimo_delta_ms = delta_time_ms  # ← lo usa la secuencia de fin de juego

        hitbox_espada = (self._calcular_hitbox_ataque_jugador(
            self.sprite_jugador.shape, modelo.jugador.flip)
            if modelo.jugador.atacando else None)

        if self.sprite_boss and modelo.boss and modelo.boss.vivo:
            modelo.boss._x = float(self.sprite_boss.shape.centerx)
            modelo.boss._y = float(self.sprite_boss.shape.centery)
            pos_boss    = self.sprite_boss.shape.center
            pos_jugador = self.sprite_jugador.shape.center
            modelo.boss._last_jpos = pos_jugador

            # La Vista solo aporta geometría: cachea las posiciones para que
            # el Model decida y ejecute la IA del boss dentro de modelo.tick().
            # La Vista ya NO llama a modelo.boss.tick_ia() directamente.
            modelo.jugador_pos_cache = pos_jugador
            modelo.boss_pos_cache    = pos_boss

            for p in modelo.boss.proyectiles:
                if not p.vivo:
                    continue
                p._x += p.vel_x
                p._y += p.vel_y
                p.shape.center = (int(p._x), int(p._y))
                # Fuera de mapa: desaparecer sin explosión
                if (p.shape.right < -2000 or p.shape.left > 8000
                        or p.shape.bottom < -1000 or p.shape.top > 1500):
                    p.vivo = False
                    continue
                # Colisión con plataforma
                for plat in self.sprites_plataformas:
                    if p.shape.colliderect(plat.shape):
                        p.vivo = False
                        break
                plats_solidas = self.sprites_plataformas_solidas[:]
                if self.pared_boss and self.pared_boss.activa:
                    plats_solidas.append(self.pared_boss)

                # Bloqueado por espada del jugador
                if p.vivo and hitbox_espada and hitbox_espada.colliderect(p.shape):
                    p.vivo = False
                # Impacta en el jugador
                if p.vivo and p.shape.colliderect(self.sprite_jugador.shape):
                    eventos.append(('golpe_proyectil_boss_a_jugador', p))
                # Explosión solo si acaba de morir en este frame
                if not p.vivo and self._frames_explosion:
                    self._efectos_explosion.append(
                        ExplosionEffect(p.shape.centerx, p.shape.centery,
                                        self._frames_explosion))

            if modelo.boss.embestida_activa:
                if self.sprite_boss.shape.colliderect(self.sprite_jugador.shape):
                    eventos.append(('golpe_boss_a_jugador', None))

            hitbox_espada2 = self.sprite_jugador.hitbox_ataque
            if hitbox_espada2 and hitbox_espada2.colliderect(self.sprite_boss.shape):
                eventos.append(('golpe_jugador_a_boss', None))
            # Detectar muerte del boss en este frame
            if not modelo.boss.vivo and not self._boss_muerte_disparada:
                self._disparar_efectos_muerte_boss()
                if self.pared_boss:  # ← añadir
                    self.pared_boss.activa = False

            modelo.jugador_pos_cache = self.sprite_jugador.shape.center

            if self.audio and modelo.boss and modelo.boss.vivo:
                self.audio.tick_rugido_boss()
        # Portal de avance
        if self.portal_fin:
            cerca = self.portal_fin.esta_cerca(self.sprite_jugador.shape)
            self.portal_fin.set_mostrar_prompt(cerca, "[E] Nivel siguiente")

        # Portal de regreso
        if self.portal_regreso:
            cerca = self.portal_regreso.esta_cerca(self.sprite_jugador.shape)
            self.portal_regreso.set_mostrar_prompt(cerca, "[E] Nivel anterior")

        # Portal final
        if self.portal_final:
            cerca = self.portal_final.esta_cerca(self.sprite_jugador.shape)
            self.portal_final.set_mostrar_prompt(cerca, "[E] Fin del juego")
            self.portal_final.actualizar(delta_time_ms)

        return eventos

    def aplicar_movimiento_boss(self, modelo):
        """Aplica al sprite del boss el desplazamiento decidido por el Model.

        Se llama DESPUÉS de modelo.tick() (que es quien ahora ejecuta
        boss.tick_ia() internamente y calcula modelo.boss_delta). La Vista
        se limita a trasladar ese resultado a coordenadas de sprite —no
        decide ni calcula la IA, solo la dibuja/posiciona.
        """
        if self.sprite_boss and modelo.boss and modelo.boss.vivo:
            dx, dy = modelo.boss_delta
            self.sprite_boss.shape.x += int(dx)
            self.sprite_boss.shape.y += int(dy)


    def _mover_dagas_jugador(self, modelo, eventos):
        """Mueve los proyectiles de daga del jugador y detecta colisiones.

        No llama al Model: añade los impactos detectados a `eventos`
        (lista compartida con actualizar_fisica) para que el Presenter
        decida qué hacer con ellos.
        """
        for p in modelo.jugador.proyectiles_daga:
            if not p.vivo:
                continue

            # Colisión con plataformas → destruir
            for plat in self.sprites_plataformas:
                if p.shape.colliderect(plat.shape):
                    p.vivo = False
                    break

            if not p.vivo:
                continue

            # Colisión con enemigos
            for i, (sprite_e, enemigo_m) in enumerate(
                zip(self.sprites_enemigos, modelo.enemigos)
            ):
                if enemigo_m.vivo and p.shape.colliderect(sprite_e.shape):
                    if self._frames_hit:
                        self._efectos_hit.append(
                            HitEffect(p.shape.centerx, p.shape.centery,
                                      self._frames_hit))
                    eventos.append(('golpe_daga_jugador_a_enemigo', (i, p)))
                    break

            # Colisión con boss
            if (p.vivo and self.sprite_boss
                    and modelo.boss and modelo.boss.vivo
                    and p.shape.colliderect(self.sprite_boss.shape)):
                if self._frames_hit:
                    self._efectos_hit.append(
                        HitEffect(p.shape.centerx, p.shape.centery,
                                  self._frames_hit))
                eventos.append(('golpe_daga_jugador_a_boss', p))

    # --- Recoger objeto daga del suelo ---

    def _detectar_daga_pickup(self, modelo):
        if (self.sprite_daga_pickup
                and self.sprite_daga_pickup.colisiona_con(
                    self.sprite_jugador.shape)):
            self.sprite_daga_pickup.recoger()
            self.evt_daga_recogida.emit()

    # --- Colisión con corazones ---

    def _detectar_corazones(self, modelo):
        shape = self.sprite_jugador.shape
        for corazon in self.sprites_corazones:
            if corazon.colisiona_con(shape):
                corazon.recoger()
                self.evt_corazon_recogido.emit(corazon.indice)

    @property
    def fin_juego_activado(self) -> bool:
        return self._seq_fin_juego is not None

    @property
    def fin_de_juego_terminado(self) -> bool:
        """True cuando la secuencia de fin de juego ya mostró los textos
        y terminó de esperar: el Presenter debe usar esto para volver
        al menú principal."""
        return self._seq_fin_juego is not None and self._seq_fin_juego.terminado

    def iniciar_fin_de_juego(self):
        """Arranca la secuencia de fin de juego (fade a negro + textos).

        La llama internamente esta misma clase cuando el jugador pulsa [E]
        estando cerca del portal_final. A partir de aquí renderizar()
        deja de dibujar el juego y solo muestra la secuencia.
        """
        if self._seq_fin_juego is None:
            self._seq_fin_juego = FinDeJuegoSequence(self.screen)
            if self.portal_final:
                self.portal_final.set_mostrar_prompt(False)

    # --- Movimiento del jugador ---

    def _mover_jugador(self, modelo, delta_time_ms):
        jugador_m = modelo.jugador
        shape     = self.sprite_jugador.shape

        # Aplicar gravedad
        jugador_m.velocidad_y += Constantes.GRAVEDAD
        if jugador_m.velocidad_y > Constantes.VELOCIDAD_MAX_CAIDA:
            jugador_m.velocidad_y = Constantes.VELOCIDAD_MAX_CAIDA

        plats_activas = self.sprites_plataformas[:]
        if self.pared_boss and self.pared_boss.activa:
            plats_activas.append(self.pared_boss)

        # --- Movimiento horizontal ---
        delta_x = modelo.delta_x_jugador
        shape.x += delta_x

        for plat in plats_activas:
            if plat.unidireccional:
                continue  # las plataformas flotantes no bloquean lateralmente
            if shape.colliderect(plat.shape):
                if delta_x > 0:  shape.right = plat.shape.left
                elif delta_x < 0: shape.left  = plat.shape.right

        # --- Movimiento vertical ---
        # Se acumula en float para evitar errores de truncado con velocidades
        # menores a 1 px/frame. El +1 fuerza solapamiento en colliderect
        # incluso cuando la velocidad real es 0 (ver comentario en model original).
        prev_bottom = shape.bottom  # posicion antes de moverse: referencia para
                                     # decidir si una plataforma flotante debe
                                     # actuar como suelo (solo si veniamos de arriba)

        jugador_m._y  = getattr(jugador_m, '_y', float(shape.y))
        # Si restaurar_pos_jugador fijó un override (carga de partida),
        # usarlo y descartarlo para que la física parta de la posición correcta.
        override = getattr(self.sprite_jugador, '_y_override', None)
        if override is not None:
            jugador_m._y = override
            del self.sprite_jugador._y_override
        jugador_m._y += jugador_m.velocidad_y
        shape.y        = int(jugador_m._y) + 1

        tocando_suelo = False
        for plat in  plats_activas:
            if not shape.colliderect(plat.shape):
                continue

            if plat.unidireccional:
                # Plataforma flotante: solo bloquea si caemos sobre ella
                # desde arriba (antes de moverse, los pies estaban a la
                # altura de su superficie o por encima). Si venimos de
                # abajo saltando, o ya estabamos debajo, se atraviesa.
                if jugador_m.velocidad_y >= 0 and prev_bottom <= plat.shape.top:
                    shape.bottom  = plat.shape.top
                    jugador_m._y  = float(shape.y)
                    tocando_suelo = True
                    jugador_m.notificar_en_suelo()
                continue

            if jugador_m.velocidad_y >= 0:
                shape.bottom  = plat.shape.top
                jugador_m._y  = float(shape.y)
                tocando_suelo = True
                jugador_m.notificar_en_suelo()
            else:
                shape.top    = plat.shape.bottom
                jugador_m._y = float(shape.y)
                jugador_m.notificar_golpe_techo()

        if not tocando_suelo:
            jugador_m.notificar_en_aire(delta_time_ms)

        # Límites de pantalla
        if shape.bottom >= Constantes.HEIGHT:
            shape.bottom  = Constantes.HEIGHT
            jugador_m._y  = float(shape.y)
            jugador_m.notificar_en_suelo()
        if shape.top < -5000:  # límite de mundo, no de pantalla
            shape.top    = -5000
            jugador_m._y = float(shape.y)
            jugador_m.notificar_golpe_techo()
        # Pasos (solo si está en suelo y moviéndose)
        if self.audio and tocando_suelo and abs(modelo.delta_x_jugador) > 0:
            self.audio.sfx_paso()

    # --- Movimiento de enemigos ---

    def _mover_enemigos(self, modelo, delta_time_ms):
        pos_jugador = self.sprite_jugador.shape.center

        for sprite, enemigo_m in zip(self.sprites_enemigos, modelo.enemigos):
            if not enemigo_m.vivo:
                continue

            pos_enemigo = sprite.shape.center

            if enemigo_m.usa_gravedad:
                # Enemigo terrestre: gravedad + patrulla
                # (las plataformas flotantes se ignoran: son solo para el jugador)
                delta_x, _ = enemigo_m.tick_ia(pos_enemigo, pos_jugador, delta_time_ms,
                                                tiles_solidos=self._bboxes_plataformas_solidas)

                # Gravedad
                enemigo_m.velocidad_y += Constantes.GRAVEDAD
                if enemigo_m.velocidad_y > Constantes.VELOCIDAD_MAX_CAIDA:
                    enemigo_m.velocidad_y = Constantes.VELOCIDAD_MAX_CAIDA

                # Borde de plataforma: si no hay suelo adelante, invertir dirección
                # Se aplica siempre, tanto en patrulla como en modo alerta.
                if delta_x != 0 and enemigo_m.en_suelo:
                    pie_x = (sprite.shape.right + 2) if delta_x > 0 else (sprite.shape.left - 3)
                    sonda = pygame.Rect(pie_x, sprite.shape.bottom, 2, 6)
                    hay_suelo = any(sonda.colliderect(p.shape) for p in self.sprites_plataformas_solidas)
                    if not hay_suelo:
                        # Invertir: el ogro se da la vuelta y vuelve a patrullar
                        enemigo_m.flip        = not enemigo_m.flip
                        enemigo_m.persiguiendo = False
                        delta_x               = -delta_x

                # Horizontal
                sprite.shape.x += delta_x
                for plat in self.sprites_plataformas_solidas:
                    if sprite.shape.colliderect(plat.shape):
                        if delta_x > 0:
                            sprite.shape.right = plat.shape.left; enemigo_m.flip = True
                        elif delta_x < 0:
                            sprite.shape.left  = plat.shape.right; enemigo_m.flip = False

                # Vertical
                sprite.shape.y += int(enemigo_m.velocidad_y)
                tocando_suelo = False
                for plat in self.sprites_plataformas_solidas:
                    if sprite.shape.colliderect(plat.shape):
                        if enemigo_m.velocidad_y >= 0:
                            sprite.shape.bottom = plat.shape.top
                            tocando_suelo       = True
                            enemigo_m.notificar_en_suelo()
                        else:
                            sprite.shape.top = plat.shape.bottom
                            enemigo_m.notificar_golpe_techo()

                if not tocando_suelo:
                    enemigo_m.en_suelo = False

            else:
                # Enemigo volador: solo patrulla horizontal, sin gravedad
                # (las plataformas flotantes se ignoran: son solo para el jugador)
                delta_x, _ = enemigo_m.tick_ia(pos_enemigo, pos_jugador, delta_time_ms,
                                                tiles_solidos=self._bboxes_plataformas_solidas)
                sprite.shape.x += delta_x

    # --- Movimiento de proyectiles ---

    def _mover_proyectiles(self, modelo):
        """Mueve los proyectiles de todos los enemigos voladores."""
        for enemigo_m in modelo.enemigos:
            if not hasattr(enemigo_m, 'proyectiles'):
                continue
            for p in enemigo_m.proyectiles:
                if not p.vivo:
                    continue
                p._x += p.vel_x
                p._y += p.vel_y
                p.shape.center = (int(p._x), int(p._y))

                # Colisión proyectil con plataforma
                for plat in self.sprites_plataformas:
                    if p.shape.colliderect(plat.shape):
                        p.vivo = False
                        break

                # Explosión al chocar con plataforma (antes de limpiar)
                if not p.vivo and self._frames_explosion:
                    self._efectos_explosion.append(
                        ExplosionEffect(p.shape.centerx, p.shape.centery,
                                        self._frames_explosion))

            # Limpiar proyectiles muertos
            enemigo_m.proyectiles = [p for p in enemigo_m.proyectiles if p.vivo]

    # --- Detección de combate ---

    def _detectar_combate(self, modelo, eventos):
        """Comprueba solapamientos de hitboxes y los añade a `eventos`.

        La Vista solo detecta geometría (qué hitboxes se solapan). Decidir
        las consecuencias (daño, audio) es responsabilidad del Presenter,
        que procesa la lista `eventos` tras llamar a este método.
        """
        jugador_m     = modelo.jugador
        shape_jugador = self.sprite_jugador.shape

        # Hitbox de ataque del jugador (calculada en la Vista a partir del shape)
        hitbox_jugador = None
        if jugador_m.atacando:
            hitbox_jugador = self._calcular_hitbox_ataque_jugador(shape_jugador, jugador_m.flip)

        for i, (sprite, enemigo_m) in enumerate(
            zip(self.sprites_enemigos, modelo.enemigos)
        ):
            if not enemigo_m.vivo:
                continue

            # Jugador golpea al enemigo
            if hitbox_jugador and hitbox_jugador.colliderect(sprite.shape):
                eventos.append(('golpe_jugador_a_enemigo', i))

            # Enemigo golpea al jugador
            if (enemigo_m.hitbox_ataque
                    and enemigo_m.hitbox_ataque.colliderect(shape_jugador)):
                eventos.append(('golpe_enemigo_a_jugador', None))

            # Proyectiles del enemigo
            if hasattr(enemigo_m, 'proyectiles'):
                for p in enemigo_m.proyectiles:
                    if not p.vivo:
                        continue
                    # Proyectil toca al jugador
                    if p.shape.colliderect(shape_jugador):
                        eventos.append(('golpe_proyectil_a_jugador', p))
                    # Jugador destruye el proyectil con la espada
                    elif hitbox_jugador and hitbox_jugador.colliderect(p.shape):
                        if self._frames_explosion:
                            self._efectos_explosion.append(
                                ExplosionEffect(p.shape.centerx, p.shape.centery,
                                                self._frames_explosion))
                        eventos.append(('golpe_jugador_a_proyectil', p))

        # Actualizar hitbox de ataque en el Model para que la Vista la dibuje
        self.sprite_jugador._hitbox_ataque_cache = hitbox_jugador

    def _calcular_hitbox_ataque_jugador(self, shape, flip):
        """Devuelve la hitbox de ataque del jugador según su posición y dirección."""
        ancho_hit = Constantes.WIDTH_PERSONAJE * 3
        x = shape.left - ancho_hit if flip else shape.right
        return pygame.Rect(x, shape.top, ancho_hit, shape.height)

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def renderizar(self, estado_jugador, estados_enemigos, modelo=None):
        """Sincroniza sprites con el estado del Model y dibuja el frame completo.

        Parameters
        ----------
        estado_jugador : dict
            Estado lógico del jugador exportado por el Model.
        estados_enemigos : list of dict
            Estados lógicos de los enemigos vivos.
        modelo : JuegoModel, optional
            Necesario para renderizar el boss si existe.
        """
        # 1. Sincronizar jugador con su estado lógico y actualizar cámara
        self.sprite_jugador.sincronizar(estado_jugador)
        self.camara.update(
            self.sprite_jugador.shape,
            self._ultimo_delta_ms,
            mover_derecha=self._dir_derecha_pulsada,
            mover_izquierda=self._dir_izquierda_pulsada,
            mirar_arriba=self._mirar_arriba_pulsada,
            mirar_abajo=self._mirar_abajo_pulsada,
        )

        # 2. Fondos estáticos
        self.screen.blit(self.fondo, (0, 0))
        self.screen.blit(self.fondo_walls, (0, 0))

        # 3. Plataformas
        for plat in self.sprites_plataformas:
            plat.draw(self.screen, self.camara)

        if self.pared_boss and self.pared_boss.activa:
            self.pared_boss.draw(self.screen, self.camara)
        # Checkpoint
        cerca_cp = self.sprite_checkpoint.esta_cerca(self.sprite_jugador.shape)
        self.sprite_checkpoint.set_mostrar_prompt(cerca_cp)
        self.sprite_checkpoint.draw(self.screen, self.camara)

        # Ángel
        if self.sprite_angel:
            cerca_angel = self.sprite_angel.esta_cerca(self.sprite_jugador.shape)
            self.sprite_angel.set_mostrar_prompt(cerca_angel)
            self.sprite_angel.draw(self.screen, self.camara)

        # Corazones
        for corazon in self.sprites_corazones:
            corazon.draw(self.screen, self.camara)

        # Objeto daga del suelo
        if self.sprite_daga_pickup:
            self.sprite_daga_pickup.draw(self.screen, self.camara)

        # Enemigos
        for sprite, estado in zip(self.sprites_enemigos, estados_enemigos):
            sprite.sincronizar(estado)
            sprite.draw(self.screen, self.camara, estado)
            # El aviso de detección (sonido + "!") respeta un cooldown
            # propio del Sprite (ver EnemigoSpriteBase._sincronizar_base).
            # Es la Vista quien decide aquí si reproducir el SFX, en vez
            # de que el Model lo dispare directo al AudioManager — así el
            # cooldown es puramente gráfico/de presentación y no afecta
            # a la IA de persecución.
            if self.audio and sprite.aviso_deteccion_listo:
                self.audio.sfx_deteccion_enemigo()

        # Boss
        if self.sprite_boss and modelo is not None and modelo.boss and modelo.boss.vivo:
            estado_boss = modelo.boss.obtener_estado(self.sprite_boss.shape.center)
            self.sprite_boss.sincronizar(estado_boss)
            self.sprite_boss.draw(self.screen, self.camara, estado_boss)

        # Proyectiles de daga del jugador
        if modelo is not None:
            estados_dagas = estado_jugador.get('proyectiles_daga', [])
            # Ajustar pool de sprites
            while len(self._sprites_dagas) < len(estados_dagas):
                self._sprites_dagas.append(
                    DagaProyectilSprite(self._frames_daga_proyectil))
            for sprite_d, estado_d in zip(self._sprites_dagas, estados_dagas):
                sprite_d.draw(self.screen, self.camara, estado_d)

        # Efectos de sangre (muerte de enemigos)
        for efecto in self._efectos_sangre:
            efecto.update()
            efecto.draw(self.screen, self.camara)
        self._efectos_sangre = [e for e in self._efectos_sangre if not e.terminado]

        # Efectos de explosión (muerte de proyectiles enemigos)
        for efecto in self._efectos_explosion:
            efecto.update()
            efecto.draw(self.screen, self.camara)
        self._efectos_explosion = [e for e in self._efectos_explosion if not e.terminado]

        # Efectos de impacto de daga
        for efecto in self._efectos_hit:
            efecto.update()
            efecto.draw(self.screen, self.camara)
        self._efectos_hit = [e for e in self._efectos_hit if not e.terminado]

        # Portales (debajo del jugador para que queden en capa media)
        if self.portal_fin:
            self.portal_fin.draw(self.screen, self.camara)
        if self.portal_regreso:
            self.portal_regreso.draw(self.screen, self.camara)

        if self.portal_final:
            self.portal_final.draw(self.screen, self.camara)

        # Secuencia de fin de juego: toma el control total de la pantalla
        # (fade a negro + textos). Mientras esté activa no se dibuja nada
        # más encima (ni jugador, ni HUD), si no se verían flotando sobre
        # el fundido a negro.
        if self._seq_fin_juego:
            self._seq_fin_juego.actualizar(self._ultimo_delta_ms)
            self._seq_fin_juego.draw()
            pygame.display.flip()
            return

        # Jugador (encima de todo)
        self.sprite_jugador.draw(self.screen, self.camara)

        # 6. HUD
        self.dibujar_hud(estado_jugador)

        # Debug: trigger de fin de nivel (solo en desarrollo)
        if self._trigger_fin_nivel:
            pygame.draw.rect(self.screen, (0, 255, 100),
                             self.camara.aplicar(self._trigger_fin_nivel), 3)

        # --- Secuencia de Game Over ---
        # Al detectar que el jugador acaba de morir, capturamos el frame
        # actual (el juego «congelado») y arrancamos el fade a negro.
        if not estado_jugador['vivo']:
            if self._seq_game_over is None:
                captura = self.screen.copy()
                self._seq_game_over = GameOverSequence(self.screen, captura)
            self._seq_game_over.draw()

        # 7. Presentar frame
        pygame.display.flip()

    def obtener_estado_jugador(self, modelo):
        """Construye el dict de estado del jugador combinando Model y Vista.

        El Model conoce flags lógicos; la Vista conoce la posición real.

        Parameters
        ----------
        modelo : JuegoModel

        Returns
        -------
        dict
        """
        hitbox = getattr(self.sprite_jugador, '_hitbox_ataque_cache', None)
        return modelo.jugador.obtener_estado(
            pos=self.sprite_jugador.shape.center,
            hitbox_ataque=hitbox,
        )

    def obtener_estados_enemigos(self, modelo):
        return [em.obtener_estado(pos=s.shape.center)
                for s, em in zip(self.sprites_enemigos, modelo.enemigos)]

    def refrescar(self):
        """Limita el loop a FPS y devuelve delta_time en milisegundos."""
        return self.reloj.tick(Constantes.FPS)

    def eliminar_sprite_enemigo(self, indice):
        """Elimina el sprite de un enemigo muerto de la lista."""
        if 0 <= indice < len(self.sprites_enemigos):
            sprite = self.sprites_enemigos[indice]
            # Disparar efecto de sangre en la posición del enemigo muerto
            if self._frames_blood:
                self._efectos_sangre.append(
                    BloodEffect(sprite.shape.centerx, sprite.shape.centery,
                                self._frames_blood))
            self.sprites_enemigos.pop(indice)

    def restaurar_enemigos(self, datos_enemigos, datos_boss):
        """Recrea los sprites de enemigos y limpia todos los proyectiles.

        Se llama al cargar partida para que los enemigos que hubieran muerto
        reaparezcan en su posición inicial y la pantalla quede limpia de
        proyectiles enemigos (tanto de voladores como del boss).

        Parameters
        ----------
        datos_enemigos : list of dict
            Lista de dicts de enemigos del nivel (misma estructura que en __init__).
        datos_boss : dict or None
            Datos del boss del nivel, o None si no hay boss.
        """
        from .Ogro import OgroSprite
        from .Fantasma import FantasmaSprite

        self.sprites_enemigos = []
        for d in datos_enemigos:
            if d.get('tipo') == 'volador':
                sprite = FantasmaSprite(d['x'], d['y'], d['anim_walk'])
                sprite.proyectil_frames = getattr(self, '_frames_proyectil_cache', [])
                self.sprites_enemigos.append(sprite)
            else:
                self.sprites_enemigos.append(
                    OgroSprite(d['x'], d['y'], d['anim_walk'], d['anim_attack']))

        # Limpiar proyectiles del boss si existe
        if self.sprite_boss and datos_boss:
            self.sprite_boss.shape.center = (datos_boss['x'], datos_boss['y'])

        # Limpiar efectos visuales residuales
        self._efectos_sangre    = []
        self._efectos_explosion = []
        self._efectos_hit       = []
        self._sprites_dagas     = []

    # ------------------------------------------------------------------
    # Efectos visuales: sangre y explosión
    # ------------------------------------------------------------------


    def _cargar_frames_blood(self) -> list:
        """Carga los 21 frames de la animación de sangre.
        Devuelve lista vacía si los assets no están disponibles.
        """
        frames = []
        try:
            s = Constantes.SCALA_PERSONAJE
            for i in range(1, 22):
                img = pygame.image.load(
                    f"Assets/Efectos/Blood/1_{i}.png"
                ).convert_alpha()
                img = pygame.transform.scale(
                    img,
                    (int(img.get_width() * s),
                     int(img.get_height() * s))
                )
                frames.append(img)
        except Exception as e:
            print(f"[BloodEffect] No se pudieron cargar los frames: {e}")
        return frames

    def _cargar_frames_explosion(self) -> list:
        """Carga los 8 frames de la animación de explosión de proyectiles.
        Devuelve lista vacía si los assets no están disponibles.
        """
        frames = []
        try:
            s = Constantes.SCALA_PERSONAJE
            for i in range(1, 9):
                img = pygame.image.load(
                    f"Assets/Efectos/explosion-1-f/Sprites/explosion-f{i}.png"
                ).convert_alpha()
                img = pygame.transform.scale(
                    img,
                    (int(img.get_width() * s),
                     int(img.get_height() * s))
                )
                frames.append(img)
        except Exception as e:
            print(f"[ExplosionEffect] No se pudieron cargar los frames: {e}")
        return frames

    def _disparar_efectos_muerte_boss(self):
        """Dispara sangre en las 3 puntas de un triángulo y explosión en el
        centro, todos centrados sobre el sprite del boss en el momento de morir.

        Triángulo equilátero orientado hacia arriba:
          - Punta superior    : centro + (0,       -radio)
          - Punta inf-derecha : centro + (+radio·sin60, +radio·cos60) ≈ (+r·0.866, +r·0.5)
          - Punta inf-izquierda: centro + (-radio·sin60, +radio·cos60)
        """
        import math
        self._boss_muerte_disparada = True

        if not self.sprite_boss:
            return

        cx, cy = self.sprite_boss.shape.center
        radio  = max(self.sprite_boss.shape.width,
                     self.sprite_boss.shape.height) * 0.35

        # Vértices del triángulo equilátero (punta arriba)
        puntas = [
            (cx,                             cy - radio),             # arriba
            (cx + int(radio * math.sin(math.radians(120))),
             cy - int(radio * math.cos(math.radians(120)))),          # inf-derecha
            (cx - int(radio * math.sin(math.radians(120))),
             cy - int(radio * math.cos(math.radians(120)))),          # inf-izquierda
        ]

        # Sangre en las tres puntas (cooldown alto = animación lenta y larga)
        if self._frames_blood:
            for px, py in puntas:
                self._efectos_sangre.append(
                    BloodEffect(px, py, self._frames_blood, cooldown_ms=100))

        # Explosión en el centro (cooldown alto = animación lenta y larga)
        if self._frames_explosion:
            self._efectos_explosion.append(
                ExplosionEffect(cx, cy, self._frames_explosion, cooldown_ms=120))

    def _cargar_frames_hit(self) -> list:
        """Carga los 3 frames de la animación de impacto de daga.
        Devuelve lista vacía si los assets no están disponibles.
        """
        frames = []
        try:
            s = Constantes.SCALA_PERSONAJE
            for i in range(1, 4):
                img = pygame.image.load(
                    f"Assets/Efectos/Hit/Sprites/hit{i}.png"
                ).convert_alpha()
                img = pygame.transform.scale(
                    img,
                    (int(img.get_width() * s),
                     int(img.get_height() * s))
                )
                frames.append(img)
        except Exception as e:
            print(f"[HitEffect] No se pudieron cargar los frames: {e}")
        return frames

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------

    def _cargar_frames_vida_hud(self) -> dict:
        """Carga los 3 estados visuales del corazón de vida del HUD.

        Prueba la ruta indicada y, si falla, variantes razonables (mayúsculas/
        minúsculas en 'assets', con y sin la 's' final, etc.) para tolerar
        pequeñas discrepancias entre el nombre de carpeta esperado y el real,
        ya que en Linux las rutas son sensibles a mayúsculas.

        Returns
        -------
        dict
            Claves 'lleno', 'medio', 'vacio' -> pygame.Surface escalada,
            o dict vacío si los assets no están disponibles.
        """
        nombres = {
            'lleno': "Hearts_Red_1.png",
            'medio': "Hearts_Red_0.5.png",
            'vacio': "Hearts_Red_0.png",
        }
        carpetas_candidatas = ["Assets/Interfaz/Vida/"]

        frames = {}
        for clave, nombre in nombres.items():
            surface = None
            for carpeta in carpetas_candidatas:
                ruta = carpeta + nombre
                try:
                    surface = pygame.image.load(ruta).convert_alpha()
                    if carpeta != carpetas_candidatas[0]:
                        print(f"[HUD] ⚠ '{carpetas_candidatas[0] + nombre}' no encontrada; "
                              f"usando '{ruta}' en su lugar.")
                    break
                except Exception:
                    continue
            if surface is None:
                print(f"[HUD] ✗ No se pudo cargar ningún corazón '{nombre}' "
                      f"en ninguna de las rutas probadas: "
                      f"{[c + nombre for c in carpetas_candidatas]}")
                return {}
            w, h = surface.get_width(), surface.get_height()
            frames[clave] = pygame.transform.scale(surface, (int(w * 1.0), int(h * 1.0)))

        print(f"[HUD] ✓ Corazones de vida cargados "
              f"({frames['lleno'].get_width()}x{frames['lleno'].get_height()} px)")
        return frames

    def _cargar_frames_inventario_hud(self) -> dict:
        """Carga el slot de inventario y el icono de la daga del HUD.

        El icono de daga se carga una vez en color y se genera además una
        versión en gris (para mostrar mientras la habilidad está en
        cooldown), evitando recalcular el grisado cada frame.

        Returns
        -------
        dict
            Claves 'slot', 'daga', 'daga_gris' -> pygame.Surface,
            o dict vacío si los assets no están disponibles.
        """
        rutas = {
            'slot': "Assets/Interfaz/Objeto/Inventory_Slot_1.png",
            'daga': "Assets/Interfaz/Objeto/Daga.png",
        }
        carpetas_candidatas = ["", "assets/Interfaz/Objeto/", "Assets/interfaz/objeto/"]

        frames = {}
        for clave, ruta in rutas.items():
            surface = None
            # Primero la ruta tal cual; si falla, probar variantes de mayúsculas
            candidatas = [ruta] + [
                c + ruta.split('/')[-1] for c in carpetas_candidatas if c
            ]
            for r in candidatas:
                try:
                    surface = pygame.image.load(r).convert_alpha()
                    break
                except Exception:
                    continue
            if surface is None:
                print(f"[HUD] ✗ No se pudo cargar '{ruta}' para el HUD de inventario.")
                return {}
            frames[clave] = surface

        # Versión en gris del icono de daga (cooldown activo)
        gris = frames['daga'].copy()
        arr   = pygame.surfarray.pixels3d(gris)
        alpha = pygame.surfarray.pixels_alpha(gris)
        mask  = alpha > 0
        promedio = (
            arr[:, :, 0][mask].astype(int)
            + arr[:, :, 1][mask].astype(int)
            + arr[:, :, 2][mask].astype(int)
        ) // 3
        arr[:, :, 0][mask] = promedio
        arr[:, :, 1][mask] = promedio
        arr[:, :, 2][mask] = promedio
        del arr, alpha
        frames['daga_gris'] = gris

        print("[HUD] ✓ Iconos de inventario cargados")
        return frames

    def _dibujar_corazones_vida(self, hp, hp_max):
        """Dibuja la fila de corazones de vida en la esquina superior izquierda.

        El número de corazones mostrados es siempre hp_max (redondeado al
        entero superior, por si hp_max llegase a ser fraccionario). Se
        rellenan de izquierda a derecha según hp: los corazones íntegros
        primero, luego como máximo un corazón a medias, y el resto vacíos.

        Parameters
        ----------
        hp : int or float
            Vida actual del jugador (puede ser fraccionaria, p.ej. 3.5).
        hp_max : int or float
            Vida máxima del jugador.
        """
        num_corazones = int(round(hp_max))
        if num_corazones <= 0:
            return

        img_w = self._frames_vida_hud['lleno'].get_width()
        margen_izq = 20
        margen_sup = 20
        espaciado  = img_w + 6   # misma distancia entre todos los corazones

        hp_restante = max(0.0, hp)

        for i in range(num_corazones):
            if hp_restante >= 1:
                clave = 'lleno'
                hp_restante -= 1
            elif hp_restante >= 0.5:
                clave = 'medio'
                hp_restante -= 0.5
            else:
                clave = 'vacio'

            img = self._frames_vida_hud[clave]
            x = margen_izq + i * espaciado
            self.screen.blit(img, (x, margen_sup))

    def dibujar_hud(self, estado_jugador):
        fuente = Fuentes.obtener_fuente(36)

        hp     = estado_jugador['hp']
        hp_max = estado_jugador.get('hp_max', hp)

        if self._frames_vida_hud:
            self._dibujar_corazones_vida(hp, hp_max)
        else:
            # Fallback a texto si los assets no cargaron
            texto_hp = fuente.render(f"Vidas: {hp} / {hp_max}", True, (255, 255, 255))
            self.screen.blit(texto_hp, (20, 20))

        # Slot de inventario (siempre visible) + icono de daga (si desbloqueada)
        if self._frames_inventario_hud:
            y_slot = (20 + self._frames_vida_hud['lleno'].get_height() + 10
                      if self._frames_vida_hud else 52)
            slot_x, slot_y = 20, y_slot
            slot = self._frames_inventario_hud['slot']
            self.screen.blit(slot, (slot_x, slot_y))

            if estado_jugador.get('daga_desbloqueada'):
                listo = estado_jugador.get('cooldown_daga_listo', True)
                icono = (self._frames_inventario_hud['daga'] if listo
                         else self._frames_inventario_hud['daga_gris'])
                # Icono centrado dentro del slot (objeto colocado en su hueco)
                icono_x = slot_x + (slot.get_width()  - icono.get_width())  // 2
                icono_y = slot_y + (slot.get_height() - icono.get_height()) // 2
                self.screen.blit(icono, (icono_x, icono_y))
        elif estado_jugador.get('daga_desbloqueada'):
            # Fallback a texto si los assets de inventario no cargaron
            listo = estado_jugador.get('cooldown_daga_listo', True)
            color = (100, 220, 255) if listo else (140, 140, 140)
            texto_daga = fuente.render(
                "[L] Daga" + (" ✓" if listo else " …"), True, color)
            y_daga = (20 + self._frames_vida_hud['lleno'].get_height() + 8
                      if self._frames_vida_hud else 52)
            self.screen.blit(texto_daga, (20, y_daga))

    @property
    def game_over_terminado(self) -> bool:
        """True cuando la secuencia de Game Over ha finalizado."""
        return self._seq_game_over is not None and self._seq_game_over.terminado

    def tick_game_over(self, delta_ms: int):
        """Avanza el timer de la secuencia de Game Over si está activa."""
        if self._seq_game_over and not self._seq_game_over.terminado:
            self._seq_game_over.actualizar(delta_ms)

    def dibujar_pantalla_cargando(self):
        """Pinta un overlay negro con 'Cargando...' centrado en pantalla.

        Se llama cada frame durante el estado de carga post-restauración,
        mientras la física resuelve la posición del jugador en silencio.
        No llama a pygame.display.flip() — lo gestiona el presenter.
        """
        self.screen.fill((0, 0, 0))
        fuente =  Fuentes.obtener_fuente(58)
        texto  = fuente.render("Cargando...", True, (255, 255, 255))
        x = (Constantes.WIDTH  - texto.get_width())  // 2
        y = (Constantes.HEIGHT - texto.get_height()) // 2
        self.screen.blit(texto, (x, y))
        pygame.display.flip()