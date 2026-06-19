"""Menú principal del juego.

Se ejecuta antes de construir las capas MVP.
Devuelve una acción ('jugar', 'cargar', 'salir') que main.py interpreta.

Diseño:
- Fondo oscuro con imagen del juego (misma que el fondo del nivel)
- Título grande centrado
- Cuatro botones apilados verticalmente
- Navegación con ratón y también con flechas + Enter
"""

import pygame
import Constantes
import Fuentes
from MenuConfig import MenuConfig

from view.AudioManager import AudioManager

# ── Paleta ──────────────────────────────────────────────────────────────────
COLOR_FONDO_OVERLAY = (10, 10, 30, 200)   # capa semitransparente sobre el fondo
COLOR_TITULO        = (230, 210, 160)      # dorado pálido
COLOR_BTN_NORMAL    = (40,  40,  70)       # botón sin hover
COLOR_BTN_HOVER     = (80,  70, 130)       # botón con hover
COLOR_BTN_BORDE     = (120, 100, 180)      # borde del botón
COLOR_BTN_TEXTO     = (220, 220, 255)      # texto del botón
COLOR_BTN_DISABLED  = (50,  50,  55)       # botón deshabilitado
COLOR_TEXTO_DISABLED= (100, 100, 110)      # texto deshabilitado


class MenuPrincipal:
    """Menú principal con cuatro opciones.

    Parameters
    ----------
    screen : pygame.Surface
        Ventana ya creada (se crea en main antes de llamar al menú).
    tiene_save : bool
        Si es False, el botón «Cargar partida» aparece deshabilitado.
    fondo_path : str
        Ruta de la imagen de fondo (la misma que usa el juego).
    """

    OPCIONES = [
        ('jugar',    'Jugar'),
        ('cargar',   'Cargar partida'),
        ('config',   'Configuracion'),
        ('salir',    'Salir'),
    ]

    BTN_ANCHO  = 320
    BTN_ALTO   = 54
    BTN_GAP    = 18       # separación entre botones
    BTN_RADIO  = 8        # redondeo de esquinas

    def __init__(self, screen: pygame.Surface, tiene_save: bool = False, audio=None,
                 fondo_path: str = "Assets/Enviorments/caverns-files-web/layers/background.png",):
        self.screen     = screen
        self.tiene_save = tiene_save
        self.seleccion  = 0   # índice del botón resaltado con teclado
        self._audio = audio

        # Fuentes
        self._fuente_titulo = Fuentes.obtener_fuente(96)
        self._fuente_btn    = Fuentes.obtener_fuente(38)
        self._fuente_sub    = Fuentes.obtener_fuente(26)

        # Fondo escalado al tamaño de la ventana
        try:
            fondo_raw   = pygame.image.load(fondo_path).convert()
            self._fondo = pygame.transform.scale(
                fondo_raw, (Constantes.WIDTH, Constantes.HEIGHT)
            )
        except Exception:
            # Si no se puede cargar el fondo, usar un color sólido
            self._fondo = pygame.Surface((Constantes.WIDTH, Constantes.HEIGHT))
            self._fondo.fill((20, 20, 40))

        # Overlay semitransparente encima del fondo
        self._overlay = pygame.Surface(
            (Constantes.WIDTH, Constantes.HEIGHT), pygame.SRCALPHA
        )
        self._overlay.fill(COLOR_FONDO_OVERLAY)

        # Pre-calcular rects de los botones centrados verticalmente
        total_alto = len(self.OPCIONES) * self.BTN_ALTO + (len(self.OPCIONES) - 1) * self.BTN_GAP
        inicio_y   = Constantes.HEIGHT // 2 - total_alto // 2 + 60  # +60 deja espacio al título
        cx         = Constantes.WIDTH  // 2

        self._rects = []
        for i in range(len(self.OPCIONES)):
            y    = inicio_y + i * (self.BTN_ALTO + self.BTN_GAP)
            rect = pygame.Rect(0, 0, self.BTN_ANCHO, self.BTN_ALTO)
            rect.center = (cx, y)
            self._rects.append(rect)

    # ── Ayudas ──────────────────────────────────────────────────────────────

    def _esta_deshabilitado(self, accion: str) -> bool:
        if accion == 'cargar' and not self.tiene_save:
            return True
        return False

    def _dibujar(self, hover_idx: int):
        """Dibuja un frame completo del menú."""
        # Fondo + overlay
        self.screen.blit(self._fondo, (0, 0))
        self.screen.blit(self._overlay, (0, 0))

        # Título
        titulo = self._fuente_titulo.render("CAVERN QUEST", True, COLOR_TITULO)
        self.screen.blit(
            titulo,
            (Constantes.WIDTH  // 2 - titulo.get_width()  // 2,
             Constantes.HEIGHT // 2 - titulo.get_height() // 2 - 180)
        )

        # Subtítulo decorativo
        sub = self._fuente_sub.render(" Menu Principal ", True, (150, 140, 100))
        self.screen.blit(
            sub,
            (Constantes.WIDTH // 2 - sub.get_width() // 2,
             Constantes.HEIGHT // 2 - 130)
        )

        # Botones
        for i, ((accion, etiqueta), rect) in enumerate(zip(self.OPCIONES, self._rects)):
            deshabilitado = self._esta_deshabilitado(accion)
            es_hover      = (i == hover_idx) and not deshabilitado
            es_seleccion  = (i == self.seleccion) and not deshabilitado

            # Color de fondo del botón
            if deshabilitado:
                color_fondo = COLOR_BTN_DISABLED
                color_texto = COLOR_TEXTO_DISABLED
                color_borde = (70, 70, 75)
            elif es_hover or es_seleccion:
                color_fondo = COLOR_BTN_HOVER
                color_texto = COLOR_BTN_TEXTO
                color_borde = COLOR_BTN_BORDE
            else:
                color_fondo = COLOR_BTN_NORMAL
                color_texto = COLOR_BTN_TEXTO
                color_borde = COLOR_BTN_BORDE

            pygame.draw.rect(self.screen, color_fondo, rect, border_radius=self.BTN_RADIO)
            pygame.draw.rect(self.screen, color_borde, rect, width=2, border_radius=self.BTN_RADIO)

            # Indicador de selección por teclado (pequeño triángulo izquierdo)
            if es_seleccion and not deshabilitado:
                puntos = [
                    (rect.left - 14, rect.centery),
                    (rect.left - 6,  rect.centery - 6),
                    (rect.left - 6,  rect.centery + 6),
                ]
                pygame.draw.polygon(self.screen, COLOR_BTN_BORDE, puntos)

            texto_surf = self._fuente_btn.render(etiqueta, True, color_texto)
            self.screen.blit(
                texto_surf,
                (rect.centerx - texto_surf.get_width() // 2,
                 rect.centery  - texto_surf.get_height() // 2)
            )

        # Pista de controles
        pista = self._fuente_sub.render(
            "Apreta w s para navegar      Apreta Enter o clica para seleccionar",
            True, (100, 95, 120)
        )
        self.screen.blit(
            pista,
            (Constantes.WIDTH // 2 - pista.get_width() // 2,
             Constantes.HEIGHT - 36)
        )

        pygame.display.flip()

    # ── Loop del menú ────────────────────────────────────────────────────────

    def ejecutar(self) -> str:
        """Muestra el menú y bloquea hasta que el usuario elige una opción.

        Returns
        -------
        str
            Una de: 'jugar', 'cargar', 'config', 'salir'.
        """
        reloj     = pygame.time.Clock()
        hover_idx = -1   # índice del botón bajo el ratón (-1 = ninguno)


        while True:
            reloj.tick(60)

            # ── Eventos ──
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 'salir'

                # Teclado
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return 'salir'

                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.seleccion = (self.seleccion + 1) % len(self.OPCIONES)

                    elif event.key in (pygame.K_UP, pygame.K_w):
                        self.seleccion = (self.seleccion - 1) % len(self.OPCIONES)

                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        accion = self.OPCIONES[self.seleccion][0]
                        if not self._esta_deshabilitado(accion):
                            if accion == 'config':
                                MenuConfig(self.screen, self._audio).ejecutar()  # abre y vuelve

                            else:
                                return accion

                # Ratón: hover
                elif event.type == pygame.MOUSEMOTION:
                    hover_idx = -1
                    for i, rect in enumerate(self._rects):
                        if rect.collidepoint(event.pos):
                            hover_idx = i
                            break

                # Ratón: clic
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for i, (rect, (accion, _)) in enumerate(
                        zip(self._rects, self.OPCIONES)
                    ):
                        if rect.collidepoint(event.pos):
                            if not self._esta_deshabilitado(accion):
                                if accion == 'config':
                                    MenuConfig(self.screen, self._audio).ejecutar()
                                else:
                                    return accion

            # ── Render ──
            self._dibujar(hover_idx)
