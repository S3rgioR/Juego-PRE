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
    w = image.get_width()
    h = image.get_height()
    return pygame.transform.scale(image, (int(w * scale), int(h * scale)))


def cargar_frames(patron, n, scale):
    frames = []
    for i in range(1, n + 1):
        img = pygame.image.load(patron.format(i))
        img = escalar_img(img, scale)
        frames.append(img)
    return frames


def iniciar_partida(cargar_save=False):
    """Carga assets, compone MVP e inicia el game loop. Devuelve el presenter."""
    s = Constantes.SCALA_PERSONAJE

    _img_ref = pygame.image.load(
        "Assets/Characters/Terrible Knight/Sprites/Idle/frame1.png"
    )
    Constantes.WIDTH_PERSONAJE  = int(_img_ref.get_width()  * 0.1  * s)
    Constantes.HEIGHT_PERSONAJE = int(_img_ref.get_height() * 0.35 * s)

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

    anim_ogre_walk    = cargar_frames("Assets/Characters/Ogre/Sprites/walk/ogre-walk{}.png", 6, s)
    anim_ogre_attack  = cargar_frames("Assets/Characters/Ogre/Sprites/Attack/ogre-attack{}.png", 6, s)
    anim_volador_walk = cargar_frames("Assets/Characters/Ghost/Sprites/ghost-{}.png", 4, s)

    datos_enemigos = [
        {
            'tipo': 'terrestre', 'x': 600, 'y': 400,
            'distancia_patrulla': 2000, 'num_frames_ataque': 6,
            'anim_walk': anim_ogre_walk, 'anim_attack': anim_ogre_attack,
        },
        {
            'tipo': 'terrestre', 'x': 1500, 'y': 400,
            'distancia_patrulla': 10000, 'num_frames_ataque': 6,
            'anim_walk': anim_ogre_walk, 'anim_attack': anim_ogre_attack,
        },
        {
            'tipo': 'volador', 'x': 1000, 'y': 400,
            'distancia_patrulla': 300,
            'anim_walk': anim_volador_walk,
        },
    ]

    modelo    = JuegoModel(datos_enemigos)
    vista     = PygameView(frames_jugador=frames_jugador,
                           datos_enemigos=datos_enemigos,
                           nivel_loader=cargar_nivel_1)
    presenter = JuegoPresenter(vista, modelo,
                               num_frames_ataque_jugador=len(frames_jugador['AtaqueParado']))

    if cargar_save:
        presenter._cargar_partida()

    presenter.ejecutar()
    return presenter   # main() lee presenter.salida_forzada


def main():
    pygame.init()
    pygame.display.set_mode((Constantes.WIDTH, Constantes.HEIGHT), pygame.DOUBLEBUF)
    pygame.display.set_caption("Cavern Quest")

    save_manager = SaveManager()

    while True:
        menu   = MenuPrincipal(
            screen     = pygame.display.get_surface(),
            tiene_save = save_manager.existe(),
        )
        accion = menu.ejecutar()

        if accion == 'salir':
            break

        elif accion == 'config':
            pass

        elif accion == 'jugar':
            presenter = iniciar_partida(cargar_save=False)
            if presenter.salida_forzada:
                break   # X de la ventana → cerrar todo

        elif accion == 'cargar':
            presenter = iniciar_partida(cargar_save=True)
            if presenter.salida_forzada:
                break   # X de la ventana → cerrar todo

        # Si salida_forzada es False → volver al menú principal

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
