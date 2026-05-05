"""Punto de entrada del juego - Composición explícita del patrón MVP.

Este módulo es responsable de:
1. Cargar todos los assets (imágenes, animaciones)
2. Crear las tres capas del patrón MVP: Model, View, Presenter
3. Conectar las capas entre sí
4. Iniciar el game loop

Arquitectura MVP:
- Model  : estado del juego, física, IA, combate. Sin pygame gráfico.
- View   : pygame, sprites, cámara, input, render. En la carpeta view/.
- Presenter: intermediario. Se suscribe a eventos de la Vista y coordina el loop.

Orden de inicialización importante:
1. pygame.init()
2. Calcular constantes de tamaño del personaje (requiere image.load, NO convert)
3. Cargar frames de animación (image.load + scale, NO convert_alpha aún)
4. Crear Model (no necesita pygame.display)
5. Crear View → aquí se llama pygame.display.set_mode() y DESPUÉS se puede
   usar convert_alpha(). El tileset y los fondos se cargan dentro de View.__init__.
6. Crear Presenter y arrancar el loop.
"""

import pygame
import Constantes
from model import JuegoModel
from view import PygameView
from presenter import JuegoPresenter
from Nivel import cargar_nivel_1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Carga assets, compone las capas MVP e inicia el game loop."""

    pygame.init()

    s = Constantes.SCALA_PERSONAJE

    # Calcular dimensiones del personaje a partir de la primera imagen.
    # Usamos image.load sin convert_alpha() porque aún no hay ventana.
    # Sobreescribimos las constantes ANTES de construir Model o View,
    # ya que ambos las necesitan para sus rects y hitboxes.
    _img_ref = pygame.image.load(
        "Assets/Characters/Terrible Knight/Sprites/Idle/frame1.png"
    )
    Constantes.WIDTH_PERSONAJE  = int(_img_ref.get_width()  * 0.1  * s)
    Constantes.HEIGHT_PERSONAJE = int(_img_ref.get_height() * 0.35 * s)

    # --- Animaciones del jugador ---
    # image.load + scale son seguros antes de crear la ventana.
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

    # --- Datos de enemigos ---
    # El Model usa 'x', 'y', 'distancia_patrulla', 'num_frames_ataque'.
    # La Vista usa 'x', 'y', 'anim_walk', 'anim_attack'.
    datos_enemigos = [
        {
            'x': 600, 'y': 400,
            'distancia_patrulla': 2000,
            'num_frames_ataque':  6,
            'anim_walk':   anim_ogre_walk,
            'anim_attack': anim_ogre_attack,
        },
        {
            'x': 1500, 'y': 400,
            'distancia_patrulla': 10000,
            'num_frames_ataque':  6,
            'anim_walk':   anim_ogre_walk,
            'anim_attack': anim_ogre_attack,
        },
    ]

    # ---------------------------------------------------------------------------
    # Composición MVP
    # ---------------------------------------------------------------------------

    # 1. Model: estado y lógica. Solo necesita datos escalares de cada enemigo.
    modelo = JuegoModel(datos_enemigos)

    # 2. View: pygame, sprites, cámara.
    #    pygame.display.set_mode() se llama DENTRO de PygameView.__init__.
    #    Por eso el tileset (que usa convert_alpha) también se carga dentro,
    #    así como los fondos. NO se pasa tileset desde aquí.
    vista = PygameView(
        frames_jugador=frames_jugador,
        datos_enemigos=datos_enemigos,
        nivel_loader=cargar_nivel_1

    )

    # 3. Presenter: conecta Model y View, gestiona el game loop.
    num_frames_ataque = len(frames_jugador['AtaqueParado'])
    presenter = JuegoPresenter(vista, modelo, num_frames_ataque_jugador=num_frames_ataque)

    # 4. Iniciar el game loop
    presenter.ejecutar()


if __name__ == "__main__":
    main()
