"""Punto de entrada del juego - Composición explícita del patrón MVP."""

import sys
import pygame
import Constantes
from model         import JuegoModel
from view          import PygameView
from presenter     import JuegoPresenter
from Nivel         import cargar_nivel_1
from SaveManager   import SaveManager
from MenuPrincipal import MenuPrincipal


def escalar_img(image, scale):
    w, h = image.get_width(), image.get_height()
    return pygame.transform.scale(image, (int(w * scale), int(h * scale)))


def cargar_frames(patron, n, scale):
    frames = []
    for i in range(1, n + 1):
        img = pygame.image.load(patron.format(i))
        frames.append(escalar_img(img, scale))
    return frames


def iniciar_partida(cargar_save=False):
    s = Constantes.SCALA_PERSONAJE

    _img_ref = pygame.image.load(
        "Assets/Characters/Terrible Knight/Sprites/Idle/frame1.png")
    Constantes.WIDTH_PERSONAJE  = int(_img_ref.get_width()  * 0.1  * s)
    Constantes.HEIGHT_PERSONAJE = int(_img_ref.get_height() * 0.35 * s)

    # --- Animaciones jugador ---
    frames_jugador = {
        'Parado':      cargar_frames("Assets/Characters/Terrible Knight/Sprites/Idle/frame{}.png", 4, s),
        'Andando':     cargar_frames("Assets/Characters/Terrible Knight/Sprites/Run/frame{}.png", 12, s),
        'Saltando':    cargar_frames("Assets/Characters/Terrible Knight/Sprites/Jump/Jump{}.png", 4, s),
        'AtaqueParado':cargar_frames("Assets/Characters/Terrible Knight/Sprites/SwordSlash/frame{}.png", 4, s),
        'AtaqueSalto': cargar_frames("Assets/Characters/Terrible Knight/Sprites/AirSwordSlash/AirSwordSlash-export{}.png", 6, s),
    }

    # --- Animaciones enemigos ---
    anim_ogre_walk    = cargar_frames("Assets/Characters/Ogre/Sprites/walk/ogre-walk{}.png", 6, s)
    anim_ogre_attack  = cargar_frames("Assets/Characters/Ogre/Sprites/Attack/ogre-attack{}.png", 6, s)
    anim_volador_walk = cargar_frames("Assets/Characters/Ghost/Sprites/ghost-{}.png", 4, s)

    # --- Animaciones boss ---
    anim_boss_nofiro = cargar_frames("Assets/Characters/Fire-Skull-Files/Sprites/NoFire/frame{}.png", 4, s)
    anim_boss_fire   = cargar_frames("Assets/Characters/Fire-Skull-Files/Sprites/Fire/frame{}.png", 8, s)

    # --- Ángel ---
    frames_angel = cargar_frames("Assets/Characters/angel/sprites/angel{}.png", 8, s)

    # --- Corazón ---
    img_corazon = escalar_img(
        pygame.image.load("Assets/Characters/Vida.png").convert_alpha(), s * 0.8)

    # --- Objeto daga (pickup en el suelo) ---
    img_daga_pickup = escalar_img(
        pygame.image.load("Assets/Characters/Daga.png").convert_alpha(), s * 0.8)

    # --- Proyectil daga (un único frame; añade más si tienes animación) ---
    img_daga_proj = escalar_img(
        pygame.image.load("Assets/Characters/Dagger/dagger.png").convert_alpha(),
        s * 0.6)
    frames_daga_proyectil = [img_daga_proj]

    # --- Datos de nivel ---
    datos_enemigos = [
        {'tipo': 'terrestre', 'x': 600,  'y': 400, 'distancia_patrulla': 2000,
         'num_frames_ataque': 6, 'anim_walk': anim_ogre_walk, 'anim_attack': anim_ogre_attack},
        {'tipo': 'terrestre', 'x': 1500, 'y': 400, 'distancia_patrulla': 10000,
         'num_frames_ataque': 6, 'anim_walk': anim_ogre_walk, 'anim_attack': anim_ogre_attack},
        {'tipo': 'volador',   'x': 1000, 'y': 400, 'distancia_patrulla': 300,
         'anim_walk': anim_volador_walk},
    ]
    datos_boss  = {'tipo': 'boss', 'x': 3050, 'y': 400,
                   'anim_fase1': anim_boss_nofiro, 'anim_fase2': anim_boss_fire}
    datos_angel = {'x': 2200, 'y': 400}

    datos_corazones = [
        {'x': 900,  'y': 560},
        {'x': 1800, 'y': 528},
        {'x': 2600, 'y': 400},
    ]

    # Posición del objeto daga en el mapa (ajusta a tu nivel)
    datos_daga_pickup = {'x': 1200, 'y': 400}

    # ---------------------------------------------------------------------------
    # Composición MVP
    # ---------------------------------------------------------------------------
    modelo = JuegoModel(datos_enemigos, datos_boss)

    vista = PygameView(
        frames_jugador        = frames_jugador,
        datos_enemigos        = datos_enemigos,
        nivel_loader          = cargar_nivel_1,
        datos_boss            = datos_boss,
        frames_angel          = frames_angel,
        datos_angel           = datos_angel,
        imagen_corazon        = img_corazon,
        datos_corazones       = datos_corazones,
        imagen_daga_pickup    = img_daga_pickup,
        datos_daga_pickup     = datos_daga_pickup,
        frames_daga_proyectil = frames_daga_proyectil,
    )

    presenter = JuegoPresenter(
        vista, modelo,
        num_frames_ataque_jugador=len(frames_jugador['AtaqueParado']))

    if cargar_save:
        presenter._cargar_partida()

    presenter.ejecutar()
    return presenter


def main():
    pygame.init()
    pygame.display.set_mode((Constantes.WIDTH, Constantes.HEIGHT), pygame.DOUBLEBUF)
    pygame.display.set_caption("Cavern Quest")

    save_manager = SaveManager()

    while True:
        menu   = MenuPrincipal(screen=pygame.display.get_surface(),
                               tiene_save=save_manager.existe())
        accion = menu.ejecutar()

        if accion == 'salir':
            break
        elif accion == 'jugar':
            presenter = iniciar_partida(cargar_save=False)
            if presenter.salida_forzada: break
        elif accion == 'cargar':
            presenter = iniciar_partida(cargar_save=True)
            if presenter.salida_forzada: break

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
