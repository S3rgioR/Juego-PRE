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

from .Event     import Event
from .Camara    import Camara
from .Personaje import PersonajeSprite
from .Enemigo_1 import Enemigo1Sprite
from .Enemigo_2 import Enemigo2Sprite
from .Plataforma import Plataforma


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

    Eventos emitidos
    ----------------
    evt_cerrar, evt_mover_derecha_inicio, evt_mover_derecha_fin,
    evt_mover_izquierda_inicio, evt_mover_izquierda_fin,
    evt_saltar, evt_atacar.
    """

    def __init__(self, frames_jugador, datos_enemigos, nivel_loader):
        """Inicializa pygame, la ventana, los fondos, los sprites y los eventos."""
        pygame.init()

        self.screen = pygame.display.set_mode(
            (Constantes.WIDTH, Constantes.HEIGHT),
            pygame.DOUBLEBUF
        )
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
            fondo_walls_raw, (Constantes.WIDTH, Constantes.HEIGHT)
        )

        # --- Tileset + plataformas ---
        tileset = pygame.image.load(
            "Assets/Enviorments/caverns-files-web/layers/tiles_mini.png"
        ).convert_alpha()
        self.sprites_plataformas = nivel_loader(tileset)

        # --- Sprites ---
        self.sprite_jugador = PersonajeSprite(250, 250, frames_jugador)

        self.sprites_enemigos = []
        for d in datos_enemigos:
            if d.get('tipo') == 'volador':
                self.sprites_enemigos.append(
                    Enemigo2Sprite(d['x'], d['y'], d['anim_walk'])
                )
            else:
                self.sprites_enemigos.append(
                    Enemigo1Sprite(d['x'], d['y'], d['anim_walk'], d['anim_attack'])
                )

        # --- Frames del proyectil ---
        escala_proj = Constantes.SCALA_PERSONAJE * 0.6
        frames_proyectil = []
        for i in range(1, 3):
            img = pygame.image.load(
                f"Assets/Characters/EnemyProjectile/Sprites/frame{i}.png"
            ).convert_alpha()
            w = int(img.get_width()  * escala_proj)
            h = int(img.get_height() * escala_proj)
            frames_proyectil.append(pygame.transform.scale(img, (w, h)))

        for sprite in self.sprites_enemigos:
            if isinstance(sprite, Enemigo2Sprite):
                sprite.proyectil_frames = frames_proyectil

        # --- Eventos MVP ---
        self.evt_cerrar                 = Event()
        self.evt_mover_derecha_inicio   = Event()
        self.evt_mover_derecha_fin      = Event()
        self.evt_mover_izquierda_inicio = Event()
        self.evt_mover_izquierda_fin    = Event()
        self.evt_saltar                 = Event()
        self.evt_atacar                 = Event()

    # ------------------------------------------------------------------
    # Acceso a datos compartidos con el Presenter
    # ------------------------------------------------------------------

    @property
    def plataformas(self):
        """Expone la lista de Plataforma al Presenter."""
        return self.sprites_plataformas

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def procesar_input(self):
        """Captura eventos pygame y emite los eventos MVP correspondientes."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.evt_cerrar.emit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.evt_cerrar.emit()
                elif event.key == pygame.K_d:
                    self.evt_mover_derecha_inicio.emit()
                elif event.key == pygame.K_a:
                    self.evt_mover_izquierda_inicio.emit()
                elif event.key == pygame.K_SPACE:
                    self.evt_saltar.emit()
                elif event.key == pygame.K_j:
                    self.evt_atacar.emit()

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_d:
                    self.evt_mover_derecha_fin.emit()
                elif event.key == pygame.K_a:
                    self.evt_mover_izquierda_fin.emit()

    # ------------------------------------------------------------------
    # Física
    # ------------------------------------------------------------------

    def actualizar_fisica(self, modelo, delta_time_ms):
        """Mueve todos los objetos y notifica al Model sobre cada colisión.

        Secuencia por objeto:
        1. Aplicar gravedad (acumular velocidad_y desde el Model)
        2. Mover horizontalmente → detectar colisiones → resolver
        3. Mover verticalmente   → detectar colisiones → resolver
        4. Notificar al Model (en_suelo / en_aire / golpe_techo)
        5. Avanzar IA de enemigos y mover proyectiles

        Parameters
        ----------
        modelo : JuegoModel
            Model principal. Se consulta para leer velocidades y
            se notifica al detectar colisiones.
        delta_time_ms : int
            Milisegundos desde el último frame.
        """
        self._mover_jugador(modelo, delta_time_ms)
        self._mover_enemigos(modelo, delta_time_ms)
        self._mover_proyectiles(modelo)
        self._detectar_combate(modelo)

    # --- Movimiento del jugador ---

    def _mover_jugador(self, modelo, delta_time_ms):
        jugador_m = modelo.jugador
        shape     = self.sprite_jugador.shape

        # Aplicar gravedad
        jugador_m.velocidad_y += Constantes.GRAVEDAD
        if jugador_m.velocidad_y > Constantes.VELOCIDAD_MAX_CAIDA:
            jugador_m.velocidad_y = Constantes.VELOCIDAD_MAX_CAIDA

        # --- Movimiento horizontal ---
        delta_x = modelo.delta_x_jugador
        shape.x += delta_x
        for plat in self.sprites_plataformas:
            if shape.colliderect(plat.shape):
                if delta_x > 0:
                    shape.right = plat.shape.left
                elif delta_x < 0:
                    shape.left  = plat.shape.right

        # --- Movimiento vertical ---
        # Se acumula en float para evitar errores de truncado con velocidades
        # menores a 1 px/frame. El +1 fuerza solapamiento en colliderect
        # incluso cuando la velocidad real es 0 (ver comentario en model original).
        jugador_m._y  = getattr(jugador_m, '_y', float(shape.y))
        jugador_m._y += jugador_m.velocidad_y
        shape.y        = int(jugador_m._y) + 1

        tocando_suelo = False
        for plat in self.sprites_plataformas:
            if shape.colliderect(plat.shape):
                if jugador_m.velocidad_y >= 0:
                    shape.bottom   = plat.shape.top
                    jugador_m._y   = float(shape.y)
                    tocando_suelo  = True
                    jugador_m.notificar_en_suelo()
                else:
                    shape.top    = plat.shape.bottom
                    jugador_m._y = float(shape.y)
                    jugador_m.notificar_golpe_techo()

        if not tocando_suelo:
            jugador_m.notificar_en_aire(delta_time_ms)

        # Límites de pantalla
        if shape.bottom >= Constantes.HEIGHT:
            shape.bottom   = Constantes.HEIGHT
            jugador_m._y   = float(shape.y)
            jugador_m.notificar_en_suelo()
        if shape.top < 0:
            shape.top    = 0
            jugador_m._y = float(shape.y)
            jugador_m.notificar_golpe_techo()

    # --- Movimiento de enemigos ---

    def _mover_enemigos(self, modelo, delta_time_ms):
        from model import Enemigo1Model
        pos_jugador = self.sprite_jugador.shape.center

        for i, (sprite, enemigo_m) in enumerate(
            zip(self.sprites_enemigos, modelo.enemigos)
        ):
            if not enemigo_m.vivo:
                continue

            pos_enemigo = sprite.shape.center

            if isinstance(enemigo_m, Enemigo1Model):
                # Enemigo terrestre: gravedad + patrulla
                delta_x, _ = enemigo_m.tick_ia(pos_enemigo, pos_jugador, delta_time_ms)

                # Gravedad
                enemigo_m.velocidad_y += Constantes.GRAVEDAD
                if enemigo_m.velocidad_y > Constantes.VELOCIDAD_MAX_CAIDA:
                    enemigo_m.velocidad_y = Constantes.VELOCIDAD_MAX_CAIDA

                # Horizontal
                sprite.shape.x += delta_x
                for plat in self.sprites_plataformas:
                    if sprite.shape.colliderect(plat.shape):
                        if delta_x > 0:
                            sprite.shape.right = plat.shape.left
                            enemigo_m.flip     = True
                        elif delta_x < 0:
                            sprite.shape.left  = plat.shape.right
                            enemigo_m.flip     = False

                # Vertical
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
                # Enemigo volador: solo patrulla horizontal, sin gravedad
                delta_x, _ = enemigo_m.tick_ia(pos_enemigo, pos_jugador, delta_time_ms)
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

            # Limpiar proyectiles muertos
            enemigo_m.proyectiles = [p for p in enemigo_m.proyectiles if p.vivo]

    # --- Detección de combate ---

    def _detectar_combate(self, modelo):
        """Comprueba solapamientos de hitboxes y notifica al Model."""
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
                modelo.golpe_jugador_a_enemigo(i)

            # Enemigo golpea al jugador
            if (enemigo_m.hitbox_ataque
                    and enemigo_m.hitbox_ataque.colliderect(shape_jugador)):
                modelo.golpe_enemigo_a_jugador()

            # Proyectiles del enemigo
            if hasattr(enemigo_m, 'proyectiles'):
                for p in enemigo_m.proyectiles:
                    if not p.vivo:
                        continue
                    # Proyectil toca al jugador
                    if p.shape.colliderect(shape_jugador):
                        modelo.golpe_proyectil_a_jugador(p)
                    # Jugador destruye el proyectil con la espada
                    elif hitbox_jugador and hitbox_jugador.colliderect(p.shape):
                        modelo.golpe_jugador_a_proyectil(p)

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

    def renderizar(self, estado_jugador, estados_enemigos):
        """Sincroniza sprites con el estado del Model y dibuja el frame completo.

        Parameters
        ----------
        estado_jugador : dict
            Estado lógico del jugador exportado por el Model.
        estados_enemigos : list of dict
            Estados lógicos de los enemigos vivos.
        """
        # 1. Sincronizar jugador con su estado lógico y actualizar cámara
        self.sprite_jugador.sincronizar(estado_jugador)
        self.camara.update(self.sprite_jugador.shape)

        # 2. Fondos estáticos
        self.screen.blit(self.fondo, (0, 0))
        self.screen.blit(self.fondo_walls, (0, 0))

        # 3. Plataformas
        for plat in self.sprites_plataformas:
            plat.draw(self.screen, self.camara)

        # 4. Enemigos
        for sprite, estado in zip(self.sprites_enemigos, estados_enemigos):
            sprite.sincronizar(estado)
            sprite.draw(self.screen, self.camara, estado)

        # 5. Jugador (encima de todo)
        self.sprite_jugador.draw(self.screen, self.camara)

        # 6. HUD
        self.dibujar_hud(estado_jugador)

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
        """Construye la lista de estados de todos los enemigos vivos.

        Parameters
        ----------
        modelo : JuegoModel

        Returns
        -------
        list of dict
        """
        estados = []
        for sprite, enemigo_m in zip(self.sprites_enemigos, modelo.enemigos):
            estados.append(enemigo_m.obtener_estado(pos=sprite.shape.center))
        return estados

    # ------------------------------------------------------------------
    # Tiempo
    # ------------------------------------------------------------------

    def refrescar(self):
        """Limita el loop a FPS y devuelve delta_time en milisegundos."""
        return self.reloj.tick(Constantes.FPS)

    def eliminar_sprite_enemigo(self, indice):
        """Elimina el sprite de un enemigo muerto de la lista."""
        if 0 <= indice < len(self.sprites_enemigos):
            self.sprites_enemigos.pop(indice)

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------

    def dibujar_hud(self, estado_jugador):
        fuente = pygame.font.SysFont(None, 36)

        texto_hp = fuente.render(f"Vidas: {estado_jugador['hp']}", True, (255, 255, 255))
        self.screen.blit(texto_hp, (20, 20))

        if not estado_jugador['vivo']:
            fuente_grande = pygame.font.SysFont(None, 120)
            texto_go = fuente_grande.render("GAME OVER", True, (220, 50, 50))
            x = (Constantes.WIDTH  - texto_go.get_width())  // 2
            y = (Constantes.HEIGHT - texto_go.get_height()) // 2
            self.screen.blit(texto_go, (x, y))