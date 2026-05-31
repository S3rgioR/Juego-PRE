"""Punto de entrada del juego - Composición explícita del patrón MVP.

Responsabilidades de este módulo:
1. Inicializar pygame y abrir la ventana
2. Mostrar el menú principal
3. Cargar todos los assets (imágenes, animaciones)
4. Crear las tres capas del patrón MVP: Model, View, Presenter
5. Conectar las capas entre sí
6. Iniciar el game loop

Arquitectura MVP (física en la Vista):
- Model   : reglas de juego, IA, combate, hp. Sin pygame gráfico ni posiciones.
- View    : pygame, física, sprites, cámara, input, render.
            Mueve los objetos, detecta colisiones y consulta al Model.
- Presenter: intermediario. Se suscribe a eventos de la Vista y
             coordina el loop.

Orden de inicialización:
1. pygame.init() + pygame.display.set_mode()   ← necesario para el menú
2. Mostrar menú principal (bloquea hasta elección del usuario)
3. Calcular constantes de tamaño del personaje (requiere image.load)
4. Cargar frames de animación
5. Crear Model
6. Crear View  ← reutiliza la ventana ya abierta
7. Crear Presenter y arrancar el loop
"""

import sys
import pygame
import Constantes
from model     import JuegoModel
from view      import PygameView
from presenter import JuegoPresenter
from Nivel     import cargar_nivel_1
from SaveManager   import SaveManager
from MenuPrincipal import MenuPrincipal


def escalar_img(image, scale):
    w = image.get_width()
    h = image.get_height()
    return pygame.transform.scale(image, (int(w * scale), int(h * scale)))


def cargar_frames(patron, n, scale):
    """Carga n imágenes usando un patrón con {} como marcador de índice (base 1)."""
    frames = []
    for i in range(1, n + 1):
        img = pygame.image.load(patron.format(i))
        img = escalar_img(img, scale)
        frames.append(img)
    return frames


def iniciar_partida(cargar_save: bool = False):
    """Carga assets, compone las capas MVP e inicia el game loop.

    Parameters
    ----------
    cargar_save : bool
        Si True, el Presenter cargará la partida guardada justo al arrancar.
    """
    s = Constantes.SCALA_PERSONAJE

    # Calcular dimensiones del personaje.
    _img_ref = pygame.image.load(
        "Assets/Characters/Terrible Knight/Sprites/Idle/frame1.png"
    )
    Constantes.WIDTH_PERSONAJE  = int(_img_ref.get_width()  * 0.1  * s)
    Constantes.HEIGHT_PERSONAJE = int(_img_ref.get_height() * 0.35 * s)

    # --- Animaciones del jugador ---
    frames_jugador = {
        'Parado': cargar_frames(
            "Assets/Characters/Terrible Knight/Sprites/Idle/frame{}.png", 4, s),
        'Andando': cargar_frames(
            "Assets/Characters/Terrible Knight/Sprites/Run/frame{}.png", 12, s),
        'Saltando': cargar_frames(
            "Assets/Characters/Terrible Knight/Sprites/Jump/Jump{}.png", 4, s),
        'AtaqueParado': cargar_frames(
            "Assets/Characters/Terrible Knight/Sprites/SwordSlash/frame{}.png", 4, s),
        'AtaqueSalto': cargar_frames(
            "Assets/Characters/Terrible Knight/Sprites/AirSwordSlash/AirSwordSlash-export{}.png", 6, s),
    }

    # --- Animaciones de enemigos ---
    anim_ogre_walk   = cargar_frames(
        "Assets/Characters/Ogre/Sprites/walk/ogre-walk{}.png", 6, s)
    anim_ogre_attack = cargar_frames(
        "Assets/Characters/Ogre/Sprites/Attack/ogre-attack{}.png", 6, s)
    anim_volador_walk = cargar_frames(
        "Assets/Characters/Ghost/Sprites/ghost-{}.png", 4, s)

    datos_enemigos = [
        {
            'tipo': 'terrestre',
            'x': 600, 'y': 400,
            'distancia_patrulla': 2000,
            'num_frames_ataque':  6,
            'anim_walk':   anim_ogre_walk,
            'anim_attack': anim_ogre_attack,
        },
        {
            'tipo': 'terrestre',
            'x': 1500, 'y': 400,
            'distancia_patrulla': 10000,
            'num_frames_ataque':  6,
            'anim_walk':   anim_ogre_walk,
            'anim_attack': anim_ogre_attack,
        },
        {
            'tipo': 'volador',
            'x': 1000, 'y': 400,
            'distancia_patrulla': 300,
            'anim_walk': anim_volador_walk,
        },
    ]

    # ---------------------------------------------------------------------------
    # Composición MVP
    # ---------------------------------------------------------------------------

    modelo = JuegoModel(datos_enemigos)

    vista = PygameView(
        frames_jugador=frames_jugador,
        datos_enemigos=datos_enemigos,
        nivel_loader=cargar_nivel_1,
    )

    num_frames_ataque = len(frames_jugador['AtaqueParado'])
    presenter = JuegoPresenter(vista, modelo, num_frames_ataque_jugador=num_frames_ataque)

    # Si venimos de «Cargar partida», disparar la carga antes de arrancar
    if cargar_save:
        presenter._cargar_partida()

    presenter.ejecutar()


def main():
    """Inicializa pygame, muestra el menú y lanza la acción elegida."""

    pygame.init()

    # Abrir la ventana una sola vez; tanto el menú como el juego la reutilizan
    pygame.display.set_mode((Constantes.WIDTH, Constantes.HEIGHT), pygame.DOUBLEBUF)
    pygame.display.set_caption("Cavern Quest")

    save_manager = SaveManager()

    while True:
        # ── Menú principal ──────────────────────────────────────────────────
        menu   = MenuPrincipal(
            screen     = pygame.display.get_surface(),
            tiene_save = save_manager.existe(),
        )
        accion = menu.ejecutar()

        # ── Despachar acción ────────────────────────────────────────────────
        if accion == 'salir':
            break

        elif accion == 'config':
            # Reservado para una futura pantalla de configuración
            pass

        elif accion == 'jugar':
            iniciar_partida(cargar_save=False)

        elif accion == 'cargar':
            iniciar_partida(cargar_save=True)

        # Tras terminar una partida el bucle vuelve al menú automáticamente

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
