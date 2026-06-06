"""Sistema de audio del juego - AudioManager.

Gestiona la carga y reproducción de todos los efectos de sonido (SFX)
y música de fondo mediante pygame.mixer.

Formatos soportados:
    - OGG  → recomendado para música y SFX largos (menor tamaño).
    - WAV  → recomendado para SFX cortos de percusión (menor latencia).
    - MP3  → soportado pero con latencia más alta; evitar para SFX.

Responsabilidad única: audio. Ni física, ni lógica, ni render.
El Presenter y la Vista llaman a los métodos públicos cuando ocurre
un evento de juego relevante.

Integración rápida:
    # En main.py, tras pygame.init() y antes de crear la View:
    from AudioManager import AudioManager
    audio = AudioManager()
    audio.reproducir_musica("Assets/Audio/Music/level1.ogg")

    # En view/__init__.py, pasar audio a PygameView:
    vista = PygameView(..., audio=audio)

    # En presenter.py, suscribir los eventos de sonido:
    self.vista.evt_saltar.add_listener(self.audio.sfx_salto)
    self.vista.evt_atacar.add_listener(self.audio.sfx_ataque_jugador)
    # etc.

Estructura de carpetas esperada:
    Assets/
      Audio/
        Music/
          level1.ogg          ← música de fondo del nivel
          boss.ogg            ← música de la pelea del boss
        SFX/
          jugador/
            paso.wav          ← un solo paso (se llama cada N frames)
            salto.wav
            ataque.wav        ← inicio del swing de espada
          enemigo_1/
            ataque.wav        ← golpe del ogro
            muerte.wav        ← muerte genérica de enemigo terrestre
          enemigo_2/
            ataque.wav        ← disparo del fantasma
            muerte.wav        ← muerte genérica de enemigo volador
          boss/
            rugido_1.ogg      ← sonido ambiental aleatorio (al menos 1)
            rugido_2.ogg      ← cuantos más, más variedad
            rugido_3.ogg
            muerte.ogg        ← boss derrotado
"""

import os
import random
import pygame


class AudioManager:
    """Centraliza la carga y reproducción de SFX y música.

    Atributos
    ---------
    volumen_musica : float
        Volumen de la música de fondo (0.0-1.0).
    volumen_sfx : float
        Volumen global de los efectos de sonido (0.0-1.0).
    """

    # Tiempo entre pasos del jugador (ms). Ajustar según velocidad de animación.
    PASO_INTERVALO_MS = 300

    def __init__(self, volumen_musica: float = 0.5, volumen_sfx: float = 0.8):
        """Inicializa el mixer y carga todos los assets de audio.

        pygame.mixer.pre_init() debe llamarse ANTES de pygame.init() para
        ajustar la frecuencia/tamaño de búfer. Si ya se inicializó, no hay
        problema: esta clase simplemente lo usa tal cual.

        Parameters
        ----------
        volumen_musica : float
            Volumen inicial de la música (0.0-1.0).
        volumen_sfx : float
            Volumen inicial de los efectos de sonido (0.0-1.0).
        """
        # Asegurarse de que el mixer esté inicializado (es idempotente).
        if not pygame.mixer.get_init():
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.init()

        self.volumen_musica = volumen_musica
        self.volumen_sfx    = volumen_sfx

        # Tablas de SFX: nombre → pygame.Sound o None si el archivo falta.
        self._sfx: dict[str, pygame.Sound | None] = {}

        # Lista de rutas de rugidos del boss para reproducción aleatoria.
        self._rugidos_boss: list[pygame.Sound] = []

        # Temporizadores
        self._ultimo_paso_ms    = 0   # último paso del jugador
        self._ultimo_rugido_ms  = 0   # último rugido del boss
        self._proximo_rugido_ms = 0   # cuándo debe sonar el próximo rugido

        self._cargar_todos()
        self._programar_rugido()

    # ------------------------------------------------------------------
    # Carga de assets
    # ------------------------------------------------------------------

    def _cargar_todos(self):
        """Carga todos los SFX declarados. Registra advertencia si falta alguno."""
        mapa = {
            # clave            ruta del archivo
            'paso':            'Assets/Audio/Player/thorn.wav',
            'salto':           'Assets/Audio/Player/jump_Player.wav',
            'ataque_jugador':  'Assets/Audio/Player/attac_Player.ogg',
            'muerte_enemigo1': 'Assets/Audio/Ogro/enemy-death.wav',
            'ataque_ogro':     'Assets/Audio/Ogro/hit_Ogro.wav',
            'ataque_enemigo2': 'Assets/Audio/Ghost/shot_Ghost.wav',
            'muerte_enemigo2': 'Assets/Audio/Ogro/enemy-death.wav',
            'muerte_boss':     'Assets/Audio/Boss/evil-laugh.mp3',
            'ataque_boss':     'Assets/Audio/Boss/explosion.wav',
            'hurt_jugador':    'Assets/Audio/Player/hurt.ogg'
        }
        for clave, ruta in mapa.items():
            self._sfx[clave] = self._cargar_sfx(ruta)

        # Cargar rugidos del boss en su propia lista
        rugido = self._cargar_sfx('Assets/Audio/Boss/evil-laugh.mp3')
        if rugido:
            self._rugidos_boss.append(rugido)


    def _cargar_sfx(self, ruta: str) -> 'pygame.Sound | None':
        """Carga un archivo de sonido con manejo de error silencioso.

        Parameters
        ----------
        ruta : str
            Ruta relativa al archivo de audio.

        Returns
        -------
        pygame.Sound or None
        """
        if not os.path.exists(ruta):
            print(f'[AudioManager] ⚠ Archivo no encontrado: {ruta}')
            return None
        try:
            sfx = pygame.mixer.Sound(ruta)
            sfx.set_volume(self.volumen_sfx)
            return sfx
        except pygame.error as e:
            print(f'[AudioManager] ✗ Error al cargar {ruta}: {e}')
            return None

    # ------------------------------------------------------------------
    # Música de fondo
    # ------------------------------------------------------------------

    def reproducir_musica(self, ruta: str, loops: int = -1, fade_ms: int = 1000):
        """Carga y reproduce música de fondo en bucle.

        Parameters
        ----------
        ruta : str
            Ruta al archivo de música (.ogg recomendado).
        loops : int
            Número de repeticiones. -1 = infinito.
        fade_ms : int
            Milisegundos de fade-in.
        """
        if not os.path.exists(ruta):
            print(f'[AudioManager] ⚠ Música no encontrada: {ruta}')
            return
        try:
            pygame.mixer.music.load(ruta)
            pygame.mixer.music.set_volume(self.volumen_musica)
            pygame.mixer.music.play(loops=loops, fade_ms=fade_ms)
        except pygame.error as e:
            print(f'[AudioManager] ✗ Error al reproducir música: {e}')

    def detener_musica(self, fade_ms: int = 500):
        """Para la música con fade-out."""
        pygame.mixer.music.fadeout(fade_ms)

    def pausar_musica(self):
        pygame.mixer.music.pause()

    def reanudar_musica(self):
        pygame.mixer.music.unpause()

    def cambiar_musica(self, ruta: str, fade_ms: int = 800):
        """Realiza crossfade hacia una nueva pista."""
        self.detener_musica(fade_ms)
        pygame.time.wait(fade_ms)       # síncrono; llamar solo en transiciones
        self.reproducir_musica(ruta, fade_ms=fade_ms)

    # ------------------------------------------------------------------
    # SFX del jugador
    # ------------------------------------------------------------------

    def sfx_paso(self):
        """Reproduce el sonido de paso respetando el intervalo mínimo.

        Llamar cada frame mientras el jugador esté moviéndose en suelo.
        El intervalo interno evita que suene demasiado rápido.
        """
        ahora = pygame.time.get_ticks()
        if ahora - self._ultimo_paso_ms >= self.PASO_INTERVALO_MS:
            self._reproducir('paso')
            self._ultimo_paso_ms = ahora

    def sfx_salto(self):
        """Reproduce el sonido de salto. Conectar a evt_saltar."""
        self._reproducir('salto')

    def sfx_ataque_jugador(self):
        """Reproduce el swing de espada. Conectar a evt_atacar."""
        self._reproducir('ataque_jugador')

    # ------------------------------------------------------------------
    # SFX de enemigos
    # ------------------------------------------------------------------

    def sfx_muerte_enemigo(self, tipo: str = 'terrestre'):
        """Reproduce el sonido de muerte según el tipo de enemigo.

        Parameters
        ----------
        tipo : str
            'terrestre' para Enemigo1, 'volador' para Enemigo2.
        """
        clave = 'muerte_enemigo2' if tipo == 'volador' else 'muerte_enemigo1'
        self._reproducir(clave)

    def sfx_ataque_ogro(self):
        """Reproduce el golpe del ogro. Llamar cuando su hitbox se activa."""
        self._reproducir('ataque_ogro')
    def sfx_ataque_boss(self):
        """Reproduce el golpe del ogro. Llamar cuando su hitbox se activa."""
        self._reproducir('ataque_boss')
    def sfx_hurt_jugador(self):
        """Reproduce el golpe del ogro. Llamar cuando su hitbox se activa."""
        self._reproducir('hurt_jugador')


    def sfx_ataque_enemigo2(self):
        """Reproduce el disparo del fantasma. Llamar al crear un proyectil."""
        self._reproducir('ataque_enemigo2')

    # ------------------------------------------------------------------
    # SFX del boss
    # ------------------------------------------------------------------

    def sfx_muerte_boss(self):
        """Reproduce el sonido de muerte del boss."""
        self._reproducir('muerte_boss')

    def tick_rugido_boss(self):
        """Comprueba si es hora de reproducir un rugido aleatorio del boss.

        Llamar cada frame mientras el boss esté vivo (desde el Presenter
        o desde la Vista dentro de actualizar_fisica).

        El intervalo entre rugidos se elige aleatoriamente entre 10 y 40 s
        cada vez que se reproduce uno.
        """
        if not self._rugidos_boss:
            return
        ahora = pygame.time.get_ticks()
        if ahora >= self._proximo_rugido_ms:
            rugido = random.choice(self._rugidos_boss)
            rugido.set_volume(self.volumen_sfx)
            rugido.play()
            self._ultimo_rugido_ms = ahora
            self._programar_rugido()

    def _programar_rugido(self):
        """Fija el timestamp del próximo rugido entre 10 y 40 segundos."""
        intervalo_ms          = random.randint(10_000, 40_000)
        self._proximo_rugido_ms = pygame.time.get_ticks() + intervalo_ms

    # ------------------------------------------------------------------
    # Control de volumen global
    # ------------------------------------------------------------------

    def set_volumen_sfx(self, volumen: float):
        """Ajusta el volumen de todos los SFX cargados.

        Parameters
        ----------
        volumen : float
            Valor entre 0.0 (silencio) y 1.0 (máximo).
        """
        self.volumen_sfx = max(0.0, min(1.0, volumen))
        for sfx in self._sfx.values():
            if sfx is not None:
                sfx.set_volume(self.volumen_sfx)
        for rugido in self._rugidos_boss:
            rugido.set_volume(self.volumen_sfx)

    def set_volumen_musica(self, volumen: float):
        """Ajusta el volumen de la música de fondo.

        Parameters
        ----------
        volumen : float
            Valor entre 0.0 y 1.0.
        """
        self.volumen_musica = max(0.0, min(1.0, volumen))
        pygame.mixer.music.set_volume(self.volumen_musica)

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _reproducir(self, clave: str):
        """Reproduce un SFX por su clave. No hace nada si no está cargado."""
        sfx = self._sfx.get(clave)
        if sfx is not None:
            sfx.play()
