"""Punto de entrada del juego - Composición explícita del patrón MVP."""

import sys
import pygame
import Constantes
from model         import JuegoModel
from view          import PygameView
from presenter     import JuegoPresenter
from Nivel         import NIVELES
from SaveManager   import SaveManager
from MenuPrincipal import MenuPrincipal
from view.AudioManager import AudioManager
from LevelParser import LevelParser
def escalar_img(image, scale):
    w, h = image.get_width(), image.get_height()
    return pygame.transform.scale(image, (int(w * scale), int(h * scale)))


def cargar_frames(patron, n, scale):
    frames = []
    for i in range(1, n + 1):
        img = pygame.image.load(patron.format(i))
        img = escalar_img(img, scale)
        frames.append(img)
    return frames


def _inyectar_anims(datos_nivel, anim_ogre_walk, anim_ogre_attack,
                    anim_volador_walk, anim_boss_nofiro, anim_boss_fire):
    """Inyecta los frames de animación en los dicts de entidades del nivel.

    Los .txt y DATOS_NIVEL solo guardan posiciones y parámetros numéricos;
    los assets (listas de Surface) se añaden aquí tras cargarlos.
    Modifica los dicts en-place y devuelve datos_enemigos y datos_boss listos.
    """
    datos_enemigos = []
    for d in datos_nivel['enemigos']:
        e = dict(d)   # copia para no mutar el original
        if e['tipo'] == 'terrestre':
            e.setdefault('anim_walk',   anim_ogre_walk)
            e.setdefault('anim_attack', anim_ogre_attack)
        elif e['tipo'] == 'volador':
            e.setdefault('anim_walk', anim_volador_walk)
        datos_enemigos.append(e)

    datos_boss = None
    if datos_nivel.get('boss'):
        datos_boss = dict(datos_nivel['boss'])
        datos_boss.setdefault('anim_fase1', anim_boss_nofiro)
        datos_boss.setdefault('anim_fase2', anim_boss_fire)

    return datos_enemigos, datos_boss


def iniciar_partida(audio, num_nivel=1, cargar_save=False, estado_jugador_previo=None):
    """Carga assets, compone MVP e inicia el game loop. Devuelve el presenter.

    Parameters
    ----------
    audio : AudioManager
    num_nivel : int
        Número del nivel a cargar (debe existir en NIVELES).
    cargar_save : bool
        Si True, restaura la partida guardada al arrancar.
    """

    if num_nivel not in NIVELES:
        print(f"[main] ⚠ Nivel {num_nivel} no existe. Cargando nivel 1.")
        num_nivel = 1

    nivel_loader, datos_nivel = NIVELES[num_nivel]
    # --- Pared del boss (opcional, solo en niveles con boss) ---
    from LevelParser import LevelParser as _LP
    _lp_tmp = _LP.__new__(_LP)  # instancia sin tileset para solo leer el txt
    datos_pared_boss = None
    if datos_nivel.get('boss'):
        # El tileset no importa aquí, solo leemos metadatos
        tileset_tmp = pygame.image.load(
            "Assets/Enviorments/caverns-files-web/layers/tiles_mini.png"
        ).convert_alpha()
        datos_pared_boss = LevelParser(tileset_tmp).cargar_pared_boss(
            f'levels/nivel{num_nivel}.txt'
        )
    datos_portal_regreso = datos_nivel.get('portal_regreso', None)
    datos_portal_final   = datos_nivel.get('portal_final', None)
    s = Constantes.SCALA_PERSONAJE

    # --- Dimensiones del personaje (antes de set_mode) ---
    _img_ref = pygame.image.load(
        "Assets/Characters/Terrible Knight/Sprites/Idle/frame1.png"
    )
    Constantes.WIDTH_PERSONAJE  = int(_img_ref.get_width()  * 0.1  * s)
    Constantes.HEIGHT_PERSONAJE = int(_img_ref.get_height() * 0.35 * s)

    # --- Assets del jugador ---
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

    # --- Assets de enemigos ---
    anim_ogre_walk    = cargar_frames("Assets/Characters/Ogre/Sprites/walk/ogre-walk{}.png", 6, s)
    anim_ogre_attack  = cargar_frames("Assets/Characters/Ogre/Sprites/Attack/ogre-attack{}.png", 6, s)
    anim_volador_walk = cargar_frames("Assets/Characters/Ghost/Sprites/ghost-{}.png", 4, s)

    # --- Assets del boss ---
    anim_boss_nofiro = cargar_frames("Assets/Characters/Fire-Skull-Files/Sprites/NoFire/frame{}.png", 4, s)
    anim_boss_fire   = cargar_frames("Assets/Characters/Fire-Skull-Files/Sprites/Fire/frame{}.png", 8, s)

    # --- Assets compartidos ---
    frames_angel = cargar_frames("Assets/Characters/angel/sprites/angel{}.png", 8, s)

    img_corazon = escalar_img(
        pygame.image.load("Assets/Characters/Vida.png").convert_alpha(), s * 0.8)

    img_daga_pickup = escalar_img(
        pygame.image.load("Assets/Characters/Daga.png").convert_alpha(), s * 0.8)

    img_daga_proj = escalar_img(
        pygame.image.load("Assets/Characters/Dagger/dagger.png").convert_alpha(), s * 0.6)
    frames_daga_proyectil = [img_daga_proj]

    # --- Inyectar animaciones en los datos del nivel ---
    datos_enemigos, datos_boss = _inyectar_anims(
        datos_nivel,
        anim_ogre_walk, anim_ogre_attack,
        anim_volador_walk,
        anim_boss_nofiro, anim_boss_fire,
    )

    datos_angel      = datos_nivel.get('angel',      {'x': 0, 'y': 540})
    datos_corazones  = datos_nivel.get('corazones',  [])
    datos_daga_pickup = datos_nivel.get('daga_pickup', None)

    # ---------------------------------------------------------------------------
    # Composición MVP
    # ---------------------------------------------------------------------------
    modelo = JuegoModel(datos_enemigos, datos_boss)

    if estado_jugador_previo:
        modelo.cargar_estado_guardado(estado_jugador_previo)
        if estado_jugador_previo.get('daga_desbloqueada'):
            modelo.jugador_desbloquear_daga()

    datos_fin_nivel = datos_nivel.get('fin_nivel', None)
    datos_spawn     = datos_nivel.get('spawn', None)
    datos_checkpoint = datos_nivel.get('checkpoint')

    vista = PygameView(
        frames_jugador        = frames_jugador,
        datos_enemigos        = datos_enemigos,
        nivel_loader          = nivel_loader,
        datos_boss            = datos_boss,
        audio                 = audio,
        frames_angel          = frames_angel,
        datos_angel           = datos_angel,
        imagen_corazon        = img_corazon,
        datos_corazones       = datos_corazones,
        imagen_daga_pickup    = img_daga_pickup,
        datos_daga_pickup     = datos_daga_pickup,
        frames_daga_proyectil = frames_daga_proyectil,
        datos_fin_nivel       = datos_fin_nivel,
        datos_spawn           = datos_spawn,
        datos_checkpoint      = datos_checkpoint,
        datos_pared_boss      = datos_pared_boss,
        datos_portal_regreso  = datos_portal_regreso,
        datos_portal_final    = datos_portal_final,

    )

    presenter = JuegoPresenter(
        vista, modelo,
        num_frames_ataque_jugador=len(frames_jugador['AtaqueParado']),
        audio=audio,
        num_nivel=num_nivel,
        datos_enemigos=datos_enemigos,
        datos_boss=datos_boss,
    )
    # Dar al presenter acceso al estado acumulado de niveles anteriores
    # para que el checkpoint y el portal de regreso lo preserven.
    presenter._estado_jugador_previo = estado_jugador_previo
    # Arrancar música del nivel (si no hay ya música sonando)
    musica = datos_nivel.get('musica', 'Assets/Audio/Music/Ambient_Lingering_Action.wav')
    if audio and not pygame.mixer.music.get_busy():
        audio.reproducir_musica(musica)

    if cargar_save:
        presenter._cargar_partida()

    if estado_jugador_previo:
        if 'corazones_recogidos' in estado_jugador_previo:
            vista.restaurar_corazones_recogidos(
                set(estado_jugador_previo['corazones_recogidos'])
            )
        if estado_jugador_previo.get('daga_recogida'):
            vista.restaurar_daga_recogida()
        if estado_jugador_previo.get('viene_de_retroceso') and 'pos_retroceso' in estado_jugador_previo:
            x, y = estado_jugador_previo['pos_retroceso']
            vista.restaurar_pos_jugador(int(x), int(y))

    presenter.ejecutar()

    return presenter


def main():
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.init()
    pygame.mixer.init()
    pygame.display.set_mode((Constantes.WIDTH, Constantes.HEIGHT), pygame.DOUBLEBUF)
    pygame.display.set_caption("Cavern Quest")

    audio        = AudioManager()
    save_manager = SaveManager()

    audio.reproducir_musica("Assets/Audio/Music/Goblins_Den_(Regular).wav")

    while True:
        if not pygame.mixer.music.get_busy():  # ← AÑADIR
            audio.reproducir_musica("Assets/Audio/Music/Goblins_Den_(Regular).wav")
        menu   = MenuPrincipal(screen=pygame.display.get_surface(),
                               tiene_save=save_manager.existe(), audio=audio)
        accion = menu.ejecutar()

        if accion == 'salir':
            break
        elif accion == 'jugar':
            num_nivel = 1
            estado_jugador_previo = None
            while num_nivel in NIVELES:
                pygame.mixer.music.stop()
                presenter = iniciar_partida(audio, num_nivel=num_nivel,
                                            estado_jugador_previo=estado_jugador_previo)
                if presenter.salida_forzada:
                    break
                if presenter.nivel_a_cargar:
                    # El jugador pidió cargar desde el menú de pausa y el save
                    # corresponde a un nivel diferente: relanzar en ese nivel.
                    num_nivel = presenter.nivel_a_cargar
                    pygame.mixer.music.stop()
                    presenter = iniciar_partida(audio, num_nivel=num_nivel,
                                                cargar_save=True)
                    if presenter.salida_forzada:
                        break
                    # Actualizar num_nivel con el nivel en que terminó el presenter
                    # y sincronizar estado_jugador_previo desde él, para que el
                    # bucle procese correctamente nivel_completado / nivel_anterior
                    # sin relanzar el nivel innecesariamente con continue.
                    num_nivel = presenter.num_nivel
                    estado_jugador_previo = presenter._estado_jugador_previo
                    # Caer al bloque if/elif de abajo para procesar el resultado
                if presenter.nivel_completado:
                    num_nivel += 1
                    estado_jugador_previo = presenter.modelo.obtener_estado_guardado()
                    estado_jugador_previo['daga_desbloqueada'] = presenter.modelo.jugador.daga_desbloqueada
                    estado_jugador_previo['pos_retroceso'] = list(
                        presenter.vista.sprite_jugador.shape.center)
                    estado_jugador_previo['corazones_recogidos'] = presenter.vista.indices_corazones_recogidos()
                    estado_jugador_previo['daga_recogida'] = estado_jugador_previo['daga_desbloqueada']

                    pygame.mixer.music.stop()
                elif presenter.nivel_anterior and num_nivel > 1:
                    num_nivel -= 1
                    estado_jugador_previo = presenter.estado_jugador_al_retroceder

                    # Si el presenter tiene un snapshot de niveles anteriores
                    # (vía checkpoint cargado o retroceso previo), recuperarlo.
                    # Tiene precedencia sobre el estado_jugador_previo del bucle,
                    # que puede ser None o pertenecer a un nivel diferente.
                    estado_desde_presenter = estado_jugador_previo.get(
                        'estado_niveles_anteriores')
                    if estado_desde_presenter is not None:
                        # El portal de regreso ya lleva toda la cadena dentro:
                        # sustituir estado_jugador_previo por el nivel correcto.
                        estado_jugador_previo = estado_desde_presenter
                    else:
                        # Fallback: usar el estado acumulado del bucle (puede ser
                        # None si es la primera vez que se retrocede sin save).
                        pos_retroceso_guardada = (
                            estado_jugador_previo.get('pos_retroceso')
                            if estado_jugador_previo else None
                        )
                        corazones_retroceso_guardados = (
                            estado_jugador_previo.get('corazones_recogidos')
                            if estado_jugador_previo else None
                        )
                        if pos_retroceso_guardada:
                            estado_jugador_previo['pos_retroceso'] = pos_retroceso_guardada
                        if corazones_retroceso_guardados is not None:
                            estado_jugador_previo['corazones_recogidos'] = corazones_retroceso_guardados

                    estado_jugador_previo['viene_de_retroceso'] = True
                    pygame.mixer.music.stop()
                else:
                    break # volvió al menú sin completar
                pygame.mixer.music.stop()

                if presenter.juego_finalizado:
                    break  # sale del while de niveles → vuelve al menú principal
        elif accion == 'cargar':
            pygame.mixer.music.stop()
            datos_save = save_manager.cargar()
            num_nivel = datos_save.get('num_nivel', 1) if datos_save else 1
            estado_jugador_previo = None
            # Arrancar en el nivel del save y dejar que el bucle de niveles
            # procese nivel_completado / nivel_anterior normalmente.
            presenter = iniciar_partida(audio, num_nivel=num_nivel, cargar_save=True)
            if presenter.salida_forzada:
                break
            estado_jugador_previo = presenter._estado_jugador_previo
            # Procesar el resultado igual que en el bucle jugar
            while True:
                if presenter.nivel_completado:
                    num_nivel += 1
                    estado_jugador_previo = presenter.modelo.obtener_estado_guardado()
                    estado_jugador_previo['daga_desbloqueada'] = presenter.modelo.jugador.daga_desbloqueada
                    estado_jugador_previo['pos_retroceso'] = list(
                        presenter.vista.sprite_jugador.shape.center)
                    estado_jugador_previo['corazones_recogidos'] = presenter.vista.indices_corazones_recogidos()
                    estado_jugador_previo['daga_recogida'] = estado_jugador_previo['daga_desbloqueada']
                    pygame.mixer.music.stop()
                elif presenter.nivel_anterior and num_nivel > 1:
                    num_nivel -= 1
                    estado_jugador_previo = presenter.estado_jugador_al_retroceder
                    estado_desde_presenter = estado_jugador_previo.get('estado_niveles_anteriores')
                    if estado_desde_presenter is not None:
                        estado_jugador_previo = estado_desde_presenter
                    estado_jugador_previo['viene_de_retroceso'] = True
                    pygame.mixer.music.stop()
                else:
                    break
                if presenter.juego_finalizado:
                    break
                if num_nivel not in NIVELES:
                    break
                presenter = iniciar_partida(audio, num_nivel=num_nivel,
                                            estado_jugador_previo=estado_jugador_previo)
                if presenter.salida_forzada:
                    break
                if presenter.nivel_a_cargar:
                    num_nivel = presenter.nivel_a_cargar
                    pygame.mixer.music.stop()
                    presenter = iniciar_partida(audio, num_nivel=num_nivel, cargar_save=True)
                    if presenter.salida_forzada:
                        break
                    num_nivel = presenter.num_nivel
                    estado_jugador_previo = presenter._estado_jugador_previo

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
