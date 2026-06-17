"""Menú de configuración de audio.

Se muestra como un panel centrado encima del frame actual (igual que MenuPausa).
No tiene su propio game loop: el llamador lo invoca en su bucle.

Controles:
  - Clic o flechas izquierda/derecha para ajustar el slider seleccionado.
  - W/S o flechas arriba/abajo para navegar entre sliders.
  - Escape o botón «Volver» para cerrar.
"""

import pygame
import Constantes

# ── Paleta (igual que MenuPausa) ────────────────────────────────────────────
COLOR_PANEL_FONDO  = (15,  15,  35, 220)
COLOR_PANEL_BORDE  = (100, 85, 160)
COLOR_TITULO       = (230, 210, 160)
COLOR_BTN_NORMAL   = (35,  35,  65)
COLOR_BTN_HOVER    = (75,  65, 125)
COLOR_BTN_BORDE    = (110, 95, 170)
COLOR_BTN_TEXTO    = (215, 215, 250)
COLOR_SLIDER_BG    = (50,  45,  80)
COLOR_SLIDER_FILL  = (110, 95, 170)
COLOR_SLIDER_KNOB  = (200, 185, 255)
COLOR_LABEL        = (180, 170, 220)


class MenuConfig:
    """Panel de configuración de volumen superpuesto sobre la pantalla.

    Parameters
    ----------
    screen : pygame.Surface
        Superficie principal de la ventana.
    audio : AudioManager
        Instancia del gestor de audio para leer/escribir volúmenes.
    """

    PANEL_ANCHO = 420
    PANEL_ALTO  = 420
    BTN_ANCHO   = 160
    BTN_ALTO    = 42
    BTN_RADIO   = 7

    SLIDER_ANCHO  = 280
    SLIDER_ALTO   = 10
    KNOB_RADIO    = 9
    SLIDER_PASO   = 0.05   # incremento con teclado

    # Etiquetas de los sliders en orden
    SLIDERS = [
        ('general',  'Volumen general'),
        ('musica',   'Música de fondo'),
        ('sfx',      'Efectos de sonido'),
    ]

    def __init__(self, screen: pygame.Surface, audio):
        self.screen    = screen
        self.audio     = audio
        self.seleccion = 0          # slider activo (navegación teclado)
        self._arrastando = False    # True mientras se arrastra un knob

        self._fuente_titulo = pygame.font.SysFont(None, 44)
        self._fuente_label  = pygame.font.SysFont(None, 30)
        self._fuente_valor  = pygame.font.SysFont(None, 28)
        self._fuente_btn    = pygame.font.SysFont(None, 32)
        self._fuente_sub    = pygame.font.SysFont(None, 22)

        # Panel centrado
        self._panel_rect = pygame.Rect(0, 0, self.PANEL_ANCHO, self.PANEL_ALTO)
        self._panel_rect.center = (Constantes.WIDTH // 2, Constantes.HEIGHT // 2)
        self._panel_surf = pygame.Surface(
            (self.PANEL_ANCHO, self.PANEL_ALTO), pygame.SRCALPHA
        )

        # Leer volúmenes actuales del AudioManager
        self._volumen = {
            'general': (audio.volumen_musica + audio.volumen_sfx) / 2,
            'musica':  audio.volumen_musica,
            'sfx':     audio.volumen_sfx,
        }

        # Pre-calcular rects de sliders (coords en pantalla para interacción)
        self._slider_rects = {}   # clave → Rect de la barra completa (en pantalla)
        self._calcular_slider_rects()

        # Rect del botón Volver (en pantalla)
        btn = pygame.Rect(0, 0, self.BTN_ANCHO, self.BTN_ALTO)
        btn.centerx = self._panel_rect.centerx
        btn.bottom  = self._panel_rect.bottom - 18
        self._btn_volver_rect = btn

    # ── Layout ──────────────────────────────────────────────────────────────

    def _calcular_slider_rects(self):
        """Calcula los rects de los sliders en coordenadas de pantalla."""
        inicio_y = self._panel_rect.top + 100
        gap_y    = 85
        cx       = self._panel_rect.centerx

        for i, (clave, _) in enumerate(self.SLIDERS):
            y    = inicio_y + i * gap_y
            rect = pygame.Rect(0, 0, self.SLIDER_ANCHO, self.SLIDER_ALTO)
            rect.centerx = cx
            rect.centery  = y
            self._slider_rects[clave] = rect

    # ── Dibujo ──────────────────────────────────────────────────────────────

    def dibujar(self, hover_btn: bool = False):
        """Dibuja el panel sobre el frame actual. No llama a display.flip()."""
        self._panel_surf.fill(COLOR_PANEL_FONDO)
        pygame.draw.rect(
            self._panel_surf, COLOR_PANEL_BORDE,
            self._panel_surf.get_rect(), width=2, border_radius=12
        )

        # Título
        titulo = self._fuente_titulo.render("CONFIGURACIÓN", True, COLOR_TITULO)
        self._panel_surf.blit(
            titulo,
            (self.PANEL_ANCHO // 2 - titulo.get_width() // 2, 20)
        )

        # Sliders
        for i, (clave, etiqueta) in enumerate(self.SLIDERS):
            rect_pantalla = self._slider_rects[clave]
            # Convertir a coords locales del panel
            rx = rect_pantalla.x - self._panel_rect.x
            ry = rect_pantalla.y - self._panel_rect.y

            es_sel = (i == self.seleccion)
            color_label = COLOR_TITULO if es_sel else COLOR_LABEL

            # Etiqueta
            label = self._fuente_label.render(etiqueta, True, color_label)
            self._panel_surf.blit(
                label,
                (self.PANEL_ANCHO // 2 - label.get_width() // 2,
                 ry - 26)
            )

            # Barra de fondo
            pygame.draw.rect(
                self._panel_surf, COLOR_SLIDER_BG,
                (rx, ry, self.SLIDER_ANCHO, self.SLIDER_ALTO),
                border_radius=5
            )

            # Barra rellena
            vol   = self._volumen[clave]
            fill_w = int(vol * self.SLIDER_ANCHO)
            if fill_w > 0:
                pygame.draw.rect(
                    self._panel_surf, COLOR_SLIDER_FILL,
                    (rx, ry, fill_w, self.SLIDER_ALTO),
                    border_radius=5
                )

            # Knob
            knob_x = rx + fill_w
            knob_y = ry + self.SLIDER_ALTO // 2
            pygame.draw.circle(
                self._panel_surf, COLOR_SLIDER_KNOB,
                (knob_x, knob_y), self.KNOB_RADIO
            )
            if es_sel:
                pygame.draw.circle(
                    self._panel_surf, COLOR_TITULO,
                    (knob_x, knob_y), self.KNOB_RADIO, width=2
                )

            # Valor numérico
            valor_txt = self._fuente_valor.render(
                f"{int(vol * 100)}%", True, color_label
            )
            self._panel_surf.blit(
                valor_txt,
                (rx + self.SLIDER_ANCHO + 12,
                 ry + self.SLIDER_ALTO // 2 - valor_txt.get_height() // 2)
            )

        # Botón Volver
        btn_local = pygame.Rect(
            self._btn_volver_rect.x - self._panel_rect.x,
            self._btn_volver_rect.y - self._panel_rect.y,
            self.BTN_ANCHO, self.BTN_ALTO
        )
        c_fondo = COLOR_BTN_HOVER if hover_btn else COLOR_BTN_NORMAL
        pygame.draw.rect(self._panel_surf, c_fondo,  btn_local, border_radius=self.BTN_RADIO)
        pygame.draw.rect(self._panel_surf, COLOR_BTN_BORDE, btn_local, width=2, border_radius=self.BTN_RADIO)
        btn_txt = self._fuente_btn.render("Volver", True, COLOR_BTN_TEXTO)
        self._panel_surf.blit(
            btn_txt,
            (btn_local.centerx - btn_txt.get_width() // 2,
             btn_local.centery  - btn_txt.get_height() // 2)
        )

        # Pista
        pista = self._fuente_sub.render(
            "W S · ← → para ajustar   ·   Esc para volver",
            True, (90, 85, 110)
        )
        self._panel_surf.blit(
            pista,
            (self.PANEL_ANCHO // 2 - pista.get_width() // 2,
             self.PANEL_ALTO - 22)
        )

        self.screen.blit(self._panel_surf, self._panel_rect)

    # ── Aplicar volúmenes al AudioManager ───────────────────────────────────

    def _aplicar(self):
        """Envía los volúmenes actuales al AudioManager."""
        # El volumen general escala música y sfx proporcionalmente
        g = self._volumen['general']
        self.audio.set_volumen_musica(self._volumen['musica'] * g)
        self.audio.set_volumen_sfx(self._volumen['sfx'] * g)

    def _set_volumen(self, clave: str, valor: float):
        self._volumen[clave] = max(0.0, min(1.0, valor))
        self._aplicar()

    # ── Interacción ─────────────────────────────────────────────────────────

    def hover_btn(self, mouse_pos) -> bool:
        return self._btn_volver_rect.collidepoint(mouse_pos)

    def _slider_desde_x(self, clave: str, mouse_x: int) -> float:
        """Calcula el volumen según la posición X del ratón sobre el slider."""
        rect = self._slider_rects[clave]
        rel  = mouse_x - rect.x
        return max(0.0, min(1.0, rel / self.SLIDER_ANCHO))

    def _slider_en_pos(self, mouse_pos):
        """Devuelve la clave del slider bajo el ratón, o None."""
        for clave, rect in self._slider_rects.items():
            zona = rect.inflate(0, self.KNOB_RADIO * 4)
            if zona.collidepoint(mouse_pos):
                return clave
        return None

    def procesar_evento(self, event) -> bool:
        """Procesa un evento. Devuelve True si hay que cerrar el menú.

        Parameters
        ----------
        event : pygame.Event

        Returns
        -------
        bool
            True → cerrar; False → seguir abierto.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return True

            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.seleccion = (self.seleccion + 1) % len(self.SLIDERS)

            elif event.key in (pygame.K_UP, pygame.K_w):
                self.seleccion = (self.seleccion - 1) % len(self.SLIDERS)

            elif event.key in (pygame.K_LEFT,):
                clave = self.SLIDERS[self.seleccion][0]
                self._set_volumen(clave, self._volumen[clave] - self.SLIDER_PASO)

            elif event.key in (pygame.K_RIGHT,):
                clave = self.SLIDERS[self.seleccion][0]
                self._set_volumen(clave, self._volumen[clave] + self.SLIDER_PASO)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Botón volver
            if self._btn_volver_rect.collidepoint(event.pos):
                return True
            # Click en slider
            clave = self._slider_en_pos(event.pos)
            if clave:
                self._arrastando = clave
                idx = [s[0] for s in self.SLIDERS].index(clave)
                self.seleccion = idx
                self._set_volumen(clave, self._slider_desde_x(clave, event.pos[0]))

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._arrastando = False

        elif event.type == pygame.MOUSEMOTION:
            if self._arrastando:
                self._set_volumen(
                    self._arrastando,
                    self._slider_desde_x(self._arrastando, event.pos[0])
                )

        return False

    # ── Loop bloqueante (para uso desde el menú principal) ──────────────────

    def ejecutar(self):
        """Loop bloqueante. Usar desde MenuPrincipal (fuera del game loop)."""
        reloj = pygame.time.Clock()
        while True:
            reloj.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if self.procesar_evento(event):
                    return
            self.dibujar(self.hover_btn(pygame.mouse.get_pos()))
            pygame.display.flip()
