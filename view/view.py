"""Capa View del patrón MVP - Física, entrada, visualización y eventos."""

import pygame
import Constantes

from .Event              import Event
from .Camara             import Camara
from .Personaje          import PersonajeSprite
from .Enemigo_1          import Enemigo1Sprite
from .Enemigo_2          import Enemigo2Sprite
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


class PygameView:

    def __init__(self, frames_jugador, datos_enemigos, nivel_loader, datos_boss,
                 frames_angel=None, datos_angel=None,
                 imagen_corazon=None, datos_corazones=None,
                 imagen_daga_pickup=None, datos_daga_pickup=None,
                 frames_daga_proyectil=None):
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
        pygame.init()
        self.screen = pygame.display.get_surface()
        pygame.display.set_caption("Juego de Plataformas - MVP")

        self.reloj  = pygame.time.Clock()
        self.camara = Camara()

        # --- Fondos ---
        fondo_raw = pygame.image.load(
            "Assets/Enviorments/caverns-files-web/layers/background.png"
        ).convert()
        self.fondo = pygame.transform.scale(fondo_raw, (Constantes.WIDTH, Constantes.HEIGHT))

        fondo_walls_raw = pygame.image.load(
            "Assets/Enviorments/caverns-files-web/layers/back-walls.png"
        ).convert_alpha()
        self.fondo_walls = pygame.transform.scale(
            fondo_walls_raw, (Constantes.WIDTH, Constantes.HEIGHT))

        # --- Tileset + plataformas ---
        tileset = pygame.image.load(
            "Assets/Enviorments/caverns-files-web/layers/tiles_mini.png"
        ).convert_alpha()
        self.sprites_plataformas = nivel_loader(tileset)

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

        # --- Sprites jugador y enemigos ---
        self.sprite_jugador = PersonajeSprite(250, 250, frames_jugador)

        self.sprite_boss = None
        if datos_boss:
            self.sprite_boss = BossSprite(
                datos_boss['x'], datos_boss['y'],
                datos_boss['anim_fase1'], datos_boss['anim_fase2'])
            self.sprite_boss.proyectil_frames = frames_proyectil

        self.sprites_enemigos = []
        for d in datos_enemigos:
            if d.get('tipo') == 'volador':
                self.sprites_enemigos.append(
                    Enemigo2Sprite(d['x'], d['y'], d['anim_walk']))
            else:
                self.sprites_enemigos.append(
                    Enemigo1Sprite(d['x'], d['y'], d['anim_walk'], d['anim_attack']))

        for sprite in self.sprites_enemigos:
            if isinstance(sprite, Enemigo2Sprite):
                sprite.proyectil_frames = frames_proyectil

        # --- Ángel curador ---
        pos_angel = (datos_angel['x'], datos_angel['y']) if datos_angel else (2200, 400)
        self.sprite_angel = AngelView(pos_angel[0], pos_angel[1], frames_angel or [])

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

        # --- Checkpoint ---
        self.sprite_checkpoint = CheckpointView(*CHECKPOINT_NIVEL_1)

        # --- Efecto de sangre (muerte de enemigos) ---
        self._frames_blood = self._cargar_frames_blood()
        self._efectos_sangre: list = []

        # --- Efecto de explosión (muerte de proyectiles enemigos) ---
        self._frames_explosion = self._cargar_frames_explosion()
        self._efectos_explosion: list = []

        # --- Efecto de impacto de daga ---
        self._frames_hit = self._cargar_frames_hit()
        self._efectos_hit: list = []

    # ------------------------------------------------------------------
    # Acceso compartido con el Presenter
    # ------------------------------------------------------------------

    @property
    def plataformas(self):
        return self.sprites_plataformas

    @property
    def camara_pos(self):
        return [self.camara.x, self.camara.y]

    def restaurar_camara(self, cx, cy):
        self.camara.x = cx
        self.camara.y = cy

    def restaurar_pos_jugador(self, x, y):
        self.sprite_jugador.shape.center = (x, y)
        self.sprite_jugador._hitbox_ataque_cache = None

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
        for event in events:
            if event.type == pygame.QUIT:
                self.evt_cerrar.emit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.evt_pausa.emit()
                elif event.key == pygame.K_d:
                    self.evt_mover_derecha_inicio.emit()
                elif event.key == pygame.K_a:
                    self.evt_mover_izquierda_inicio.emit()
                elif event.key == pygame.K_SPACE:
                    self.evt_saltar.emit()
                elif event.key == pygame.K_j:
                    self.evt_atacar.emit()
                elif event.key == pygame.K_k:
                    if self.sprite_angel.esta_cerca(self.sprite_jugador.shape):
                        self.evt_curar.emit()
                    elif self.sprite_checkpoint.esta_cerca(self.sprite_jugador.shape):
                        self.evt_guardar.emit()
                elif event.key == pygame.K_l:
                    self.evt_lanzar_daga.emit()
                elif event.key == pygame.K_F10:
                    self.evt_cargar.emit()

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_d:
                    self.evt_mover_derecha_fin.emit()
                elif event.key == pygame.K_a:
                    self.evt_mover_izquierda_fin.emit()

    # ------------------------------------------------------------------
    # Física
    # ------------------------------------------------------------------

    def actualizar_fisica(self, modelo, delta_time_ms):
        self._mover_jugador(modelo, delta_time_ms)
        self._mover_enemigos(modelo, delta_time_ms)
        self._mover_proyectiles(modelo)
        self._mover_dagas_jugador(modelo)      # ← proyectiles de daga
        self._detectar_combate(modelo)
        self._detectar_corazones(modelo)
        self._detectar_daga_pickup(modelo)     # ← recoger objeto daga

        hitbox_espada = (self._calcular_hitbox_ataque_jugador(
            self.sprite_jugador.shape, modelo.jugador.flip)
            if modelo.jugador.atacando else None)

        if self.sprite_boss and modelo.boss and modelo.boss.vivo:
            modelo.boss._x = float(self.sprite_boss.shape.centerx)
            modelo.boss._y = float(self.sprite_boss.shape.centery)
            modelo.jugador_pos_cache = self.sprite_jugador.shape.center
            pos_boss    = self.sprite_boss.shape.center
            pos_jugador = self.sprite_jugador.shape.center
            modelo.boss._last_jpos = pos_jugador
            dx, dy, _ = modelo.boss.tick_ia(pos_boss, pos_jugador, delta_time_ms)
            modelo.boss_delta = (dx, dy)
            self.sprite_boss.shape.x += int(dx)
            self.sprite_boss.shape.y += int(dy)

            for p in modelo.boss.proyectiles:
                if not p.vivo:
                    continue
                p._x += p.vel_x
                p._y += p.vel_y
                p.shape.center = (int(p._x), int(p._y))
                # Fuera de mapa: sin explosión (no se vería)
                if (p.shape.right < -2000 or p.shape.left > 8000
                        or p.shape.bottom < -1000 or p.shape.top > 1500):
                    p.vivo = False
                    continue
                # Colisión con plataforma
                for plat in self.sprites_plataformas:
                    if p.shape.colliderect(plat.shape):
                        p.vivo = False
                        break
                # Bloqueado por espada del jugador
                if p.vivo and hitbox_espada and hitbox_espada.colliderect(p.shape):
                    p.vivo = False
                # Impacta en el jugador
                if p.vivo and p.shape.colliderect(self.sprite_jugador.shape):
                    p.vivo = False
                    modelo.golpe_proyectil_boss_a_jugador(p)
            # Explosión en todos los proyectiles del boss que acaban de morir
            for p in modelo.boss.proyectiles:
                if not p.vivo and self._frames_explosion:
                    self._efectos_explosion.append(
                        ExplosionEffect(p.shape.centerx, p.shape.centery,
                                        self._frames_explosion))

            if modelo.boss.embestida_activa:
                if self.sprite_boss.shape.colliderect(self.sprite_jugador.shape):
                    modelo.golpe_boss_a_jugador()

            hitbox_espada2 = self.sprite_jugador.hitbox_ataque
            if hitbox_espada2 and hitbox_espada2.colliderect(self.sprite_boss.shape):
                modelo.golpe_jugador_a_boss()

            modelo.jugador_pos_cache = self.sprite_jugador.shape.center

    # --- Mover proyectiles de daga del jugador ---

    def _mover_dagas_jugador(self, modelo):
        """Mueve los proyectiles de daga del jugador y detecta colisiones."""
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
                    modelo.golpe_daga_jugador_a_enemigo(i, p)
                    break

            # Colisión con boss
            if (p.vivo and self.sprite_boss
                    and modelo.boss and modelo.boss.vivo
                    and p.shape.colliderect(self.sprite_boss.shape)):
                if self._frames_hit:
                    self._efectos_hit.append(
                        HitEffect(p.shape.centerx, p.shape.centery,
                                  self._frames_hit))
                modelo.golpe_daga_jugador_a_boss(p)

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

    # --- Movimiento del jugador ---

    def _mover_jugador(self, modelo, delta_time_ms):
        jugador_m = modelo.jugador
        shape     = self.sprite_jugador.shape

        jugador_m.velocidad_y += Constantes.GRAVEDAD
        if jugador_m.velocidad_y > Constantes.VELOCIDAD_MAX_CAIDA:
            jugador_m.velocidad_y = Constantes.VELOCIDAD_MAX_CAIDA

        delta_x = modelo.delta_x_jugador
        shape.x += delta_x
        for plat in self.sprites_plataformas:
            if shape.colliderect(plat.shape):
                if delta_x > 0:  shape.right = plat.shape.left
                elif delta_x < 0: shape.left  = plat.shape.right

        jugador_m._y  = getattr(jugador_m, '_y', float(shape.y))
        jugador_m._y += jugador_m.velocidad_y
        shape.y        = int(jugador_m._y) + 1

        tocando_suelo = False
        for plat in self.sprites_plataformas:
            if shape.colliderect(plat.shape):
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

        if shape.bottom >= Constantes.HEIGHT:
            shape.bottom  = Constantes.HEIGHT
            jugador_m._y  = float(shape.y)
            jugador_m.notificar_en_suelo()
        if shape.top < 0:
            shape.top    = 0
            jugador_m._y = float(shape.y)
            jugador_m.notificar_golpe_techo()

    # --- Movimiento de enemigos ---

    def _mover_enemigos(self, modelo, delta_time_ms):
        from model.Enemigo1Model import Enemigo1Model
        pos_jugador = self.sprite_jugador.shape.center

        for sprite, enemigo_m in zip(self.sprites_enemigos, modelo.enemigos):
            if not enemigo_m.vivo:
                continue
            pos_enemigo = sprite.shape.center

            if isinstance(enemigo_m, Enemigo1Model):
                delta_x, _ = enemigo_m.tick_ia(pos_enemigo, pos_jugador, delta_time_ms)

                enemigo_m.velocidad_y += Constantes.GRAVEDAD
                if enemigo_m.velocidad_y > Constantes.VELOCIDAD_MAX_CAIDA:
                    enemigo_m.velocidad_y = Constantes.VELOCIDAD_MAX_CAIDA

                sprite.shape.x += delta_x
                for plat in self.sprites_plataformas:
                    if sprite.shape.colliderect(plat.shape):
                        if delta_x > 0:
                            sprite.shape.right = plat.shape.left; enemigo_m.flip = True
                        elif delta_x < 0:
                            sprite.shape.left  = plat.shape.right; enemigo_m.flip = False

                sprite.shape.y += int(enemigo_m.velocidad_y)
                tocando_suelo = False
                for plat in self.sprites_plataformas:
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
                delta_x, _ = enemigo_m.tick_ia(pos_enemigo, pos_jugador, delta_time_ms)
                sprite.shape.x += delta_x

    # --- Movimiento de proyectiles de enemigos ---

    def _mover_proyectiles(self, modelo):
        for enemigo_m in modelo.enemigos:
            if not hasattr(enemigo_m, 'proyectiles'):
                continue
            for p in enemigo_m.proyectiles:
                if not p.vivo:
                    continue
                p._x += p.vel_x
                p._y += p.vel_y
                p.shape.center = (int(p._x), int(p._y))
                for plat in self.sprites_plataformas:
                    if p.shape.colliderect(plat.shape):
                        p.vivo = False
                        break
            # Explosión en los proyectiles que acaban de morir
            for p in enemigo_m.proyectiles:
                if not p.vivo and self._frames_explosion:
                    self._efectos_explosion.append(
                        ExplosionEffect(p.shape.centerx, p.shape.centery,
                                        self._frames_explosion))
            enemigo_m.proyectiles = [p for p in enemigo_m.proyectiles if p.vivo]

    # --- Detección de combate cuerpo a cuerpo ---

    def _detectar_combate(self, modelo):
        jugador_m     = modelo.jugador
        shape_jugador = self.sprite_jugador.shape

        hitbox_jugador = None
        if jugador_m.atacando:
            hitbox_jugador = self._calcular_hitbox_ataque_jugador(
                shape_jugador, jugador_m.flip)

        for i, (sprite, enemigo_m) in enumerate(
            zip(self.sprites_enemigos, modelo.enemigos)
        ):
            if not enemigo_m.vivo:
                continue
            if hitbox_jugador and hitbox_jugador.colliderect(sprite.shape):
                modelo.golpe_jugador_a_enemigo(i)
            if (enemigo_m.hitbox_ataque
                    and enemigo_m.hitbox_ataque.colliderect(shape_jugador)):
                modelo.golpe_enemigo_a_jugador()
            if hasattr(enemigo_m, 'proyectiles'):
                for p in enemigo_m.proyectiles:
                    if not p.vivo: continue
                    if p.shape.colliderect(shape_jugador):
                        modelo.golpe_proyectil_a_jugador(p)
                    elif hitbox_jugador and hitbox_jugador.colliderect(p.shape):
                        if self._frames_explosion:
                            self._efectos_explosion.append(
                                ExplosionEffect(p.shape.centerx, p.shape.centery,
                                                self._frames_explosion))
                        modelo.golpe_jugador_a_proyectil(p)

        self.sprite_jugador._hitbox_ataque_cache = hitbox_jugador

    def _calcular_hitbox_ataque_jugador(self, shape, flip):
        ancho_hit = Constantes.WIDTH_PERSONAJE * 3
        x = shape.left - ancho_hit if flip else shape.right
        return pygame.Rect(x, shape.top, ancho_hit, shape.height)

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def renderizar(self, estado_jugador, estados_enemigos, modelo=None):
        self.sprite_jugador.sincronizar(estado_jugador)
        self.camara.update(self.sprite_jugador.shape)

        self.screen.blit(self.fondo, (0, 0))
        self.screen.blit(self.fondo_walls, (0, 0))

        for plat in self.sprites_plataformas:
            plat.draw(self.screen, self.camara)

        # Checkpoint
        cerca_cp = self.sprite_checkpoint.esta_cerca(self.sprite_jugador.shape)
        self.sprite_checkpoint.set_mostrar_prompt(cerca_cp)
        self.sprite_checkpoint.draw(self.screen, self.camara)

        # Ángel
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

        # Jugador (encima de todo)
        self.sprite_jugador.draw(self.screen, self.camara)

        # HUD
        self.dibujar_hud(estado_jugador)

        pygame.display.flip()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def obtener_estado_jugador(self, modelo):
        hitbox = getattr(self.sprite_jugador, '_hitbox_ataque_cache', None)
        return modelo.jugador.obtener_estado(
            pos=self.sprite_jugador.shape.center,
            hitbox_ataque=hitbox)

    def obtener_estados_enemigos(self, modelo):
        return [em.obtener_estado(pos=s.shape.center)
                for s, em in zip(self.sprites_enemigos, modelo.enemigos)]

    def refrescar(self):
        return self.reloj.tick(Constantes.FPS)

    def eliminar_sprite_enemigo(self, indice):
        if 0 <= indice < len(self.sprites_enemigos):
            sprite = self.sprites_enemigos[indice]
            # Disparar efecto de sangre en la posición del enemigo muerto
            if self._frames_blood:
                self._efectos_sangre.append(
                    BloodEffect(sprite.shape.centerx, sprite.shape.centery,
                                self._frames_blood))
            self.sprites_enemigos.pop(indice)

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

    def dibujar_hud(self, estado_jugador):
        fuente = pygame.font.SysFont(None, 36)

        hp     = estado_jugador['hp']
        hp_max = estado_jugador.get('hp_max', hp)
        texto_hp = fuente.render(f"Vidas: {hp} / {hp_max}", True, (255, 255, 255))
        self.screen.blit(texto_hp, (20, 20))

        # Indicador de daga desbloqueada + cooldown
        if estado_jugador.get('daga_desbloqueada'):
            listo = estado_jugador.get('cooldown_daga_listo', True)
            color = (100, 220, 255) if listo else (140, 140, 140)
            texto_daga = fuente.render(
                "[L] Daga" + (" ✓" if listo else " …"), True, color)
            self.screen.blit(texto_daga, (20, 52))

        if not estado_jugador['vivo']:
            fuente_grande = pygame.font.SysFont(None, 120)
            texto_go = fuente_grande.render("GAME OVER", True, (220, 50, 50))
            x = (Constantes.WIDTH  - texto_go.get_width())  // 2
            y = (Constantes.HEIGHT - texto_go.get_height()) // 2
            self.screen.blit(texto_go, (x, y))
