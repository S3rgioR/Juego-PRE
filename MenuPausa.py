"""Menú de pausa del juego.

Se muestra como un recuadro centrado encima del frame congelado del juego.
No tiene su propio game loop: el Presenter lo invoca dentro del suyo
cuando el juego está pausado, pasándole los eventos ya capturados.

Devuelve una acción o None si el menú sigue abierto:
  None          → el menú sigue abierto, no ha pasado nada
  'reanudar'    → cerrar el menú y continuar la partida
  'cargar'      → cargar partida guardada
  'config'      → reservado (de momento no hace nada)
  'menu_principal' → salir al menú principal sin guardar
"""

import pygame
import Constantes


# ── Paleta (coordinada con MenuPrincipal pero más compacta) ─────────────────
COLOR_PANEL_FONDO   = (15,  15,  35, 220)   # fondo del recuadro (SRCALPHA)
COLOR_PANEL_BORDE   = (100, 85, 160)
COLOR_TITULO        = (230, 210, 160)
COLOR_BTN_NORMAL    = (35,  35,  65)
COLOR_BTN_HOVER     = (75,  65, 125)
COLOR_BTN_BORDE     = (110, 95, 170)
COLOR_BTN_TEXTO     = (215, 215, 250)
COLOR_BTN_DISABLED  = (45,  45,  52)
COLOR_TEXTO_DISABLED= (95,  95, 105)


class MenuPausa:
    """Recuadro de pausa superpuesto sobre el juego congelado.

    Parameters
    ----------
    screen : pygame.Surface
        Superficie principal de la ventana.
    tiene_save : bool
        Si es False, «Cargar partida» aparece deshabilitado.
    """

    OPCIONES = [
        ('reanudar',        'Volver a la partida'),
        ('cargar',          'Cargar partida'),
        ('config',          'Configuración'),
        ('menu_principal',  'Ir al menú principal'),
    ]

    PANEL_ANCHO = 380
    PANEL_ALTO  = 340
    BTN_ANCHO   = 300
    BTN_ALTO    = 48
    BTN_GAP     = 14
    BTN_RADIO   = 7

    def __init__(self, screen: pygame.Surface, tiene_save: bool = False):
        self.screen     = screen
        self.tiene_save = tiene_save
        self.seleccion  = 0

        self._fuente_titulo = pygame.font.SysFont(None, 48)
        self._fuente_btn    = pygame.font.SysFont(None, 34)
        self._fuente_sub    = pygame.font.SysFont(None, 22)

        # Panel centrado en pantalla
        self._panel_rect = pygame.Rect(
            0, 0, self.PANEL_ANCHO, self.PANEL_ALTO
        )
        self._panel_rect.center = (Constantes.WIDTH // 2, Constantes.HEIGHT // 2)

        # Superficie del panel (con alpha)
        self._panel_surf = pygame.Surface(
            (self.PANEL_ANCHO, self.PANEL_ALTO), pygame.SRCALPHA
        )

        # Rects de los botones, relativos al panel
        total_alto = (len(self.OPCIONES) * self.BTN_ALTO
                      + (len(self.OPCIONES) - 1) * self.BTN_GAP)
        inicio_y   = self.PANEL_ALTO // 2 - total_alto // 2 + 20
        cx         = self.PANEL_ANCHO // 2

        self._rects_locales = []   # coords dentro del panel
        self._rects_globales = []  # coords en la ventana (para detección de clic)
        for i in range(len(self.OPCIONES)):
            y    = inicio_y + i * (self.BTN_ALTO + self.BTN_GAP)
            rect = pygame.Rect(0, 0, self.BTN_ANCHO, self.BTN_ALTO)
            rect.center = (cx, y)
            self._rects_locales.append(rect)

            rect_global = rect.move(self._panel_rect.left, self._panel_rect.top)
            self._rects_globales.append(rect_global)

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _esta_deshabilitado(self, accion: str) -> bool:
        return accion == 'cargar' and not self.tiene_save

    # ── Dibujo ──────────────────────────────────────────────────────────────

    def dibujar(self, hover_idx: int = -1):
        """Dibuja el panel de pausa sobre el frame actual de la ventana.

        Llamado cada frame por el Presenter mientras el juego está pausado.
        No llama a pygame.display.flip() — lo hace el Presenter al final.
        """
        # Fondo del panel
        self._panel_surf.fill(COLOR_PANEL_FONDO)
        pygame.draw.rect(
            self._panel_surf, COLOR_PANEL_BORDE,
            self._panel_surf.get_rect(), width=2, border_radius=12
        )

        # Título «PAUSA»
        titulo = self._fuente_titulo.render("PAUSA", True, COLOR_TITULO)
        self._panel_surf.blit(
            titulo,
            (self.PANEL_ANCHO // 2 - titulo.get_width() // 2, 22)
        )

        # Botones
        for i, ((accion, etiqueta), rect) in enumerate(
            zip(self.OPCIONES, self._rects_locales)
        ):
            deshabilitado = self._esta_deshabilitado(accion)
            es_activo     = (i == hover_idx or i == self.seleccion) and not deshabilitado

            if deshabilitado:
                c_fondo, c_texto, c_borde = COLOR_BTN_DISABLED, COLOR_TEXTO_DISABLED, (65, 65, 72)
            elif es_activo:
                c_fondo, c_texto, c_borde = COLOR_BTN_HOVER, COLOR_BTN_TEXTO, COLOR_BTN_BORDE
            else:
                c_fondo, c_texto, c_borde = COLOR_BTN_NORMAL, COLOR_BTN_TEXTO, COLOR_BTN_BORDE

            pygame.draw.rect(self._panel_surf, c_fondo,  rect, border_radius=self.BTN_RADIO)
            pygame.draw.rect(self._panel_surf, c_borde,  rect, width=2, border_radius=self.BTN_RADIO)

            # Triángulo indicador de selección por teclado
            if i == self.seleccion and not deshabilitado:
                puntos = [
                    (rect.left - 12, rect.centery),
                    (rect.left - 5,  rect.centery - 5),
                    (rect.left - 5,  rect.centery + 5),
                ]
                pygame.draw.polygon(self._panel_surf, COLOR_BTN_BORDE, puntos)

            texto_surf = self._fuente_btn.render(etiqueta, True, c_texto)
            self._panel_surf.blit(
                texto_surf,
                (rect.centerx - texto_surf.get_width() // 2,
                 rect.centery  - texto_surf.get_height() // 2)
            )

        # Pista inferior
        pista = self._fuente_sub.render("W S · Enter · clic", True, (90, 85, 110))
        self._panel_surf.blit(
            pista,
            (self.PANEL_ANCHO // 2 - pista.get_width() // 2,
             self.PANEL_ALTO - 22)
        )

        self.screen.blit(self._panel_surf, self._panel_rect)

    # ── Procesar eventos ────────────────────────────────────────────────────

    def procesar_evento(self, event) -> str | None:
        """Procesa un evento pygame y devuelve la acción elegida o None.

        El Presenter pasa cada evento a este método mientras está pausado.

        Parameters
        ----------
        event : pygame.Event

        Returns
        -------
        str or None
            Acción elegida, o None si el menú sigue abierto.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return 'reanudar'

            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.seleccion = (self.seleccion + 1) % len(self.OPCIONES)

            elif event.key in (pygame.K_UP, pygame.K_w):
                self.seleccion = (self.seleccion - 1) % len(self.OPCIONES)

            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                accion = self.OPCIONES[self.seleccion][0]
                if not self._esta_deshabilitado(accion):
                    return accion

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect_g, (accion, _) in zip(self._rects_globales, self.OPCIONES):
                if rect_g.collidepoint(event.pos):
                    if not self._esta_deshabilitado(accion):
                        return accion

        return None

    def hover_idx(self, mouse_pos) -> int:
        """Devuelve el índice del botón bajo el ratón, o -1."""
        for i, rect_g in enumerate(self._rects_globales):
            if rect_g.collidepoint(mouse_pos):
                return i
        return -1
