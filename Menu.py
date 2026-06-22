"""Clases base para los menús del juego.

Hay dos ejes de cosas en común entre MenuPrincipal, MenuPausa y
MenuConfig, y por eso hay dos clases base separadas en vez de una sola:

  - MenuBase: para menús que son "una lista de botones apilados"
    (MenuPrincipal, MenuPausa). Navegación con flechas/w/s, selección,
    hover, click. MenuConfig NO hereda de esta porque no es una lista
    de botones — tiene sliders, tabs y un toggle, con su propia lógica
    de navegación (izquierda/derecha sobre un slider, no "elegir una
    opción de una lista").

  - PanelFlotante: para menús que se dibujan como un recuadro centrado
    sobre el frame congelado del juego (MenuPausa, MenuConfig). Solo
    cubre la mecánica de tener un panel: su rect centrado en pantalla,
    su superficie con alpha, y la conversión de coordenadas de pantalla
    a coordenadas locales del panel. MenuPrincipal no la usa porque es
    a pantalla completa, no un panel flotante.

Todo lo relacionado con paleta de colores, contenido y el resto del
dibujado se deja deliberadamente en cada subclase concreta.
"""

import pygame
import Constantes


class MenuBase:
    """Lógica común de navegación/selección para menús de botones.

    Subclases esperadas: deben definir `OPCIONES` (lista de tuplas
    `(clave, etiqueta)`) y, si quieren cerrar el menú con Escape,
    `ACCION_ESCAPE` (por defecto None, es decir, Escape no hace nada).
    """

    OPCIONES = []
    ACCION_ESCAPE = None

    def __init__(self, tiene_save: bool = False):
        self.tiene_save = tiene_save
        self.seleccion  = 0
        self._rects     = []   # rects en coordenadas de pantalla (para click/hover)

    # ── Layout ──────────────────────────────────────────────────────────────

    def _calcular_rects(self, cx: int, inicio_y: int,
                         btn_ancho: int, btn_alto: int, btn_gap: int):
        """Calcula self._rects: uno por opción, apilados verticalmente
        y centrados en cx, empezando en inicio_y.
        """
        self._rects = []
        for i in range(len(self.OPCIONES)):
            y    = inicio_y + i * (btn_alto + btn_gap)
            rect = pygame.Rect(0, 0, btn_ancho, btn_alto)
            rect.center = (cx, y)
            self._rects.append(rect)

    # ── Hooks que cada subclase puede sobreescribir ─────────────────────────

    def _esta_deshabilitado(self, accion: str) -> bool:
        """Por defecto solo 'cargar' se deshabilita si no hay save.

        Cubre el caso común a MenuPrincipal y MenuPausa; si una subclase
        necesita otra regla, puede sobreescribir este método.
        """
        return accion == 'cargar' and not self.tiene_save

    def _on_seleccionar(self, accion: str) -> str | None:
        """Se llama cuando el usuario confirma una opción habilitada
        (Enter o click). Por defecto simplemente devuelve la acción para
        que el caller (main.py / Presenter) la resuelva.

        Una subclase puede sobreescribir esto para resolver alguna
        acción ella misma (p. ej. MenuPrincipal abre MenuConfig cuando
        accion == 'config' y devuelve None para no propagarla).
        """
        return accion

    # ── Consultas ───────────────────────────────────────────────────────────

    def hover_idx(self, mouse_pos) -> int:
        """Devuelve el índice del botón bajo el ratón, o -1."""
        for i, rect in enumerate(self._rects):
            if rect.collidepoint(mouse_pos):
                return i
        return -1

    # ── Eventos ─────────────────────────────────────────────────────────────

    def procesar_evento(self, event) -> str | None:
        """Procesa un evento pygame y devuelve la acción elegida o None.

        Maneja navegación (flechas/w/s), confirmación (Enter/click) y,
        si ACCION_ESCAPE está definido, la tecla Escape. La resolución
        final de la acción pasa siempre por _on_seleccionar(), así que
        las subclases pueden interceptar casos especiales sin tener que
        reimplementar todo este método.
        """
        if event.type == pygame.KEYDOWN:
            if self.ACCION_ESCAPE is not None and event.key == pygame.K_ESCAPE:
                return self.ACCION_ESCAPE

            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.seleccion = (self.seleccion + 1) % len(self.OPCIONES)

            elif event.key in (pygame.K_UP, pygame.K_w):
                self.seleccion = (self.seleccion - 1) % len(self.OPCIONES)

            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                accion = self.OPCIONES[self.seleccion][0]
                if not self._esta_deshabilitado(accion):
                    return self._on_seleccionar(accion)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, (accion, _) in zip(self._rects, self.OPCIONES):
                if rect.collidepoint(event.pos):
                    if not self._esta_deshabilitado(accion):
                        return self._on_seleccionar(accion)

        return None


class PanelFlotante:
    """Mecánica común de un panel centrado sobre el frame congelado.

    Cubre solo lo mecánico: el rect del panel (centrado en pantalla),
    la superficie con alpha donde se dibuja el contenido, y la
    conversión de un rect en coordenadas de pantalla a coordenadas
    locales del panel (`_local`). Pensada para componerse junto con
    otra clase (p. ej. MenuPausa hereda de MenuBase y PanelFlotante a
    la vez); no asume nada sobre paleta, contenido ni navegación.
    """

    def __init__(self, screen: pygame.Surface, panel_ancho: int, panel_alto: int):
        self.screen = screen

        self._panel_rect = pygame.Rect(0, 0, panel_ancho, panel_alto)
        self._panel_rect.center = (Constantes.WIDTH // 2, Constantes.HEIGHT // 2)

        self._panel_surf = pygame.Surface((panel_ancho, panel_alto), pygame.SRCALPHA)

    def _local(self, rect: pygame.Rect) -> pygame.Rect:
        """Convierte un Rect en coordenadas de pantalla a coordenadas
        locales del panel (relativas a su esquina superior izquierda).
        """
        return rect.move(-self._panel_rect.x, -self._panel_rect.y)

    def _blit_panel(self):
        """Vuelca la superficie del panel ya dibujada sobre self.screen."""
        self.screen.blit(self._panel_surf, self._panel_rect)
