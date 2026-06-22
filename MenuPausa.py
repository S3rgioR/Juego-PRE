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

Hereda de MenuBase la lógica de selección/navegación/click; aquí solo
queda lo específico de este menú: el panel flotante sobre el frame
congelado, su paleta propia, y los rects "locales" (relativos al
panel) que necesita para dibujar, además de los "globales" (en
coordenadas de pantalla) que usa MenuBase para detectar clicks.
"""

import pygame
import Constantes
import Fuentes
from Menu import MenuBase, PanelFlotante


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


class MenuPausa(MenuBase, PanelFlotante):
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
        ('config',          'Configuracion'),
        ('menu_principal',  'Ir al menu principal'),
    ]

    ACCION_ESCAPE = 'reanudar'

    PANEL_ANCHO = 380
    PANEL_ALTO  = 340
    BTN_ANCHO   = 300
    BTN_ALTO    = 48
    BTN_GAP     = 14
    BTN_RADIO   = 7

    def __init__(self, screen: pygame.Surface, tiene_save: bool = False):
        MenuBase.__init__(self, tiene_save=tiene_save)
        PanelFlotante.__init__(self, screen, self.PANEL_ANCHO, self.PANEL_ALTO)

        self._fuente_titulo = Fuentes.obtener_fuente(48)
        self._fuente_btn    = Fuentes.obtener_fuente(34)
        self._fuente_sub    = Fuentes.obtener_fuente(22)

        # Rects de los botones, relativos al panel (para dibujar) y en
        # coordenadas de pantalla (self._rects, heredado de MenuBase,
        # usado para detección de hover/click).
        total_alto = (len(self.OPCIONES) * self.BTN_ALTO
                      + (len(self.OPCIONES) - 1) * self.BTN_GAP)
        inicio_y   = self.PANEL_ALTO // 2 - total_alto // 2 + 20
        cx         = self.PANEL_ANCHO // 2

        self._rects_locales = []
        for i in range(len(self.OPCIONES)):
            y    = inicio_y + i * (self.BTN_ALTO + self.BTN_GAP)
            rect = pygame.Rect(0, 0, self.BTN_ANCHO, self.BTN_ALTO)
            rect.center = (cx, y)
            self._rects_locales.append(rect)

        # self._rects (global, en pantalla) lo espera MenuBase para
        # hover/click; lo derivamos de los locales + posición del panel.
        self._rects = [r.move(self._panel_rect.left, self._panel_rect.top)
                        for r in self._rects_locales]

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
            (self.PANEL_ANCHO // 2 - titulo.get_width() // 2, 22-18)
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
        pista = self._fuente_sub.render("W S mover   Enter   clic", True, (90, 85, 110))
        self._panel_surf.blit(
            pista,
            (self.PANEL_ANCHO // 2 - pista.get_width() // 2,
             self.PANEL_ALTO - 25)
        )

        self._blit_panel()
