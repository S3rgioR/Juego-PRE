"""Capa View del patrón MVP - Entrada de usuario, visualización y eventos.

Responsabilidades:
- Inicializar pygame y la ventana gráfica
- Capturar entrada del usuario (teclado, cierre de ventana)
- Gestionar la cámara (desplazamiento visual)
- Renderizar (dibujar) todos los sprites sincronizados con el Model
- Emitir eventos que el Presenter escucha

Lo que NO hace la Vista:
- Física ni colisiones (responsabilidad del Model)
- Lógica de combate (responsabilidad del Model)
- Coordinar el flujo del juego (responsabilidad del Presenter)

Nota sobre convert_alpha():
    pygame.Surface.convert_alpha() requiere que pygame.display.set_mode()
    ya haya sido llamado (necesita conocer el formato de píxel de la ventana).
    Por eso el tileset y los fondos se cargan AQUÍ, dentro de __init__,
    después de crear la ventana, y NO en main.py antes de crear la Vista.
"""

import pygame
import Constantes

from .Event import Event
from .Camara import Camara
from .Personaje import PersonajeSprite
from .Enemigo_1 import Enemigo1Sprite
from .Plataforma import Plataforma
from .CheckPoint import CheckpointView

from Nivel import CHECKPOINT_NIVEL_1

class PygameView:
    """Gestiona entrada, cámara, sprites y renderizado del juego.

    Attributes
    ----------
    screen : pygame.Surface
        Superficie principal de la ventana.
    reloj : pygame.time.Clock
        Controla la velocidad del game loop (FPS).
    camara : Camara
        Gestiona el desplazamiento de la vista.
    fondo : pygame.Surface
        Imagen de fondo (no se desplaza con la cámara).
    fondo_walls : pygame.Surface
        Segunda capa de fondo estática.
    sprite_jugador : PersonajeSprite
        Sprite visual del jugador.
    sprites_enemigos : list of Enemigo1Sprite
        Lista de sprites visuales de los enemigos.
    sprites_plataformas : list of Plataforma
        Lista de sprites visuales de las plataformas.

    Eventos emitidos
    ----------------
    evt_cerrar, evt_mover_derecha_inicio, evt_mover_derecha_fin,
    evt_mover_izquierda_inicio, evt_mover_izquierda_fin,
    evt_saltar, evt_atacar.
    """

    def __init__(self, frames_jugador, datos_enemigos, nivel_loader):
        """Inicializa pygame, la ventana, los fondos, los sprites y los eventos.

        El tileset y los fondos se cargan aquí (después de set_mode) para que
        convert_alpha() funcione correctamente.

        Parameters
        ----------
        frames_jugador : dict
            Diccionario de listas de frames del jugador por estado.
        datos_enemigos : list of dict
            Lista de dicts con {'x', 'y', 'anim_walk', 'anim_attack'}.
        nivel_loader : callable
            Función que recibe el tileset y devuelve la lista de Plataforma.
        """
        pygame.init()

        # --- Ventana (DEBE ir antes de cualquier convert_alpha) ---
        self.screen = pygame.display.set_mode(
            (Constantes.WIDTH, Constantes.HEIGHT),
            pygame.DOUBLEBUF
        )
        pygame.display.set_caption("Juego de Plataformas - MVP")

        self.reloj = pygame.time.Clock()
        self.camara = Camara()

        # --- Fondos (se cargan DESPUÉS de set_mode) ---
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

        # --- Tileset + plataformas (DESPUÉS de set_mode) ---
        tileset = pygame.image.load(
            "Assets/Enviorments/caverns-files-web/layers/tiles_mini.png"
        ).convert_alpha()
        self.sprites_plataformas = nivel_loader(tileset)

        # --- Sprites ---
        self.sprite_jugador = PersonajeSprite(250, 250, frames_jugador)

        self.sprites_enemigos = [
            Enemigo1Sprite(d['x'], d['y'], d['anim_walk'], d['anim_attack'])
            for d in datos_enemigos
        ]
        self.sprite_checkpoint = CheckpointView(*CHECKPOINT_NIVEL_1)

        # --- Eventos MVP ---
        self.evt_cerrar                 = Event()
        self.evt_mover_derecha_inicio   = Event()
        self.evt_mover_derecha_fin      = Event()
        self.evt_mover_izquierda_inicio = Event()
        self.evt_mover_izquierda_fin    = Event()
        self.evt_saltar                 = Event()
        self.evt_atacar                 = Event()
        self.evt_guardar = Event()
        self.evt_cargar = Event()

    # ------------------------------------------------------------------
    # Acceso a datos que el Model/Presenter necesitan
    # ------------------------------------------------------------------

    @property
    def plataformas(self):
        """Expone la lista de Plataforma (con su shape) al Presenter/Model."""
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
                elif event.key == pygame.K_k:
                    if self.sprite_checkpoint.esta_cerca(self.sprite_jugador.shape):
                        self.evt_guardar.emit()
                elif event.key == pygame.K_F10:
                    self.evt_cargar.emit()

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_d:
                    self.evt_mover_derecha_fin.emit()
                elif event.key == pygame.K_a:
                    self.evt_mover_izquierda_fin.emit()

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def renderizar(self, estado_jugador, estados_enemigos):
        """Sincroniza sprites con el Model y dibuja el frame completo.

        Parameters
        ----------
        estado_jugador : dict
            Estado lógico del jugador (ver PersonajeSprite.sincronizar).
        estados_enemigos : list of dict
            Lista de estados lógicos de los enemigos vivos.
        """
        # 1. Sincronizar jugador y actualizar cámara
        self.sprite_jugador.sincronizar(estado_jugador)
        self.camara.update(self.sprite_jugador.shape)

        # 2. Fondos estáticos
        self.screen.blit(self.fondo, (0, 0))
        self.screen.blit(self.fondo_walls, (0, 0))

        self.sprite_checkpoint.draw(self.screen, self.camara)

        # 3. Plataformas
        for plat in self.sprites_plataformas:
            plat.draw(self.screen, self.camara)

        # 4. Enemigos
        for sprite, estado in zip(self.sprites_enemigos, estados_enemigos):
            sprite.sincronizar(estado)
            sprite.draw(self.screen, self.camara)

        # 5. Jugador (encima de todo)
        self.sprite_jugador.draw(self.screen, self.camara)

        # 6. Dibuja vidas
        self.dibujar_hud(estado_jugador)

        # 7. Flip de buffers
        pygame.display.flip()

    # ------------------------------------------------------------------
    # Tiempo
    # ------------------------------------------------------------------

    def refrescar(self):
        """Limita el loop a FPS y devuelve delta_time en milisegundos.

        Returns
        -------
        int
            Milisegundos transcurridos desde el último frame.
        """
        return self.reloj.tick(Constantes.FPS)

    def eliminar_sprite_enemigo(self, indice):
        """Elimina el sprite de un enemigo muerto de la lista.

        Parameters
        ----------
        indice : int
            Índice del sprite a eliminar en sprites_enemigos.
        """
        if 0 <= indice < len(self.sprites_enemigos):
            self.sprites_enemigos.pop(indice)

    def dibujar_hud(self, estado_jugador):
        fuente = pygame.font.SysFont(None, 36)

        # Contador de hp en esquina superior izquierda
        texto_hp = fuente.render(f"Vidas: {estado_jugador['hp']}", True, (255, 255, 255))
        self.screen.blit(texto_hp, (20, 20))

        # Game over si vivo es False
        if not estado_jugador['vivo']:
            fuente_grande = pygame.font.SysFont(None, 120)
            texto_go = fuente_grande.render("GAME OVER", True, (220, 50, 50))
            x = (Constantes.WIDTH - texto_go.get_width()) // 2
            y = (Constantes.HEIGHT - texto_go.get_height()) // 2
            self.screen.blit(texto_go, (x, y))

    @property
    def camara_pos(self):
        return [self.camara.x, self.camara.y]

    def restaurar_camara(self, cx, cy):
        self.camara.x = cx
        self.camara.y = cy