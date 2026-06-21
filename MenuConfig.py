"""Menú de configuración: audio, pantalla completa y controles.

Se muestra como un panel centrado encima del frame actual (igual que MenuPausa).
Tiene dos subpantallas: 'audio' (por defecto) y 'controles'.

Controles:
  - W/S · ↑/↓  → navegar entre sliders
  - ←/→        → ajustar slider seleccionado
  - Escape      → cerrar
"""

import pygame
import Constantes
import Fuentes

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
COLOR_TECLA_BG     = (40,  38,  70)
COLOR_TECLA_BORDE  = (110, 95, 170)
COLOR_TOGGLE_ON    = (90, 170,  90)
COLOR_TOGGLE_OFF   = (80,  40,  40)


class MenuConfig:
    """Panel de configuración superpuesto sobre la pantalla.

    Parameters
    ----------
    screen : pygame.Surface
        Superficie principal de la ventana.
    audio : AudioManager
        Instancia del gestor de audio.
    """

    PANEL_ANCHO = 460
    PANEL_ALTO  = 540
    BTN_ANCHO   = 160
    BTN_ALTO    = 40
    BTN_RADIO   = 7

    SLIDER_ANCHO = 260
    SLIDER_ALTO  = 10
    KNOB_RADIO   = 9
    SLIDER_PASO  = 0.05

    SLIDERS = [
        ('general', 'Volumen general'),
        ('musica',  'Musica de fondo'),
        ('sfx',     'Efectos de sonido'),
    ]

    # Controles del juego para mostrar en la subpantalla
    CONTROLES = [
        ('A / D',        'Mover izq. / der.'),
        ('W / S',        'Mover arriba / abajo'),
        ('Espacio',      'Saltar'),
        ('J',            'Atacar'),
        ('L',            'Lanzar daga'),
        ('E',            'Usar portal'),
        ('K',            'Interactuar'),
        ('F5',           'Guardar partida'),
        ('F9',           'Cargar partida'),
        ('Esc',          'Pausa'),
    ]

    def __init__(self, screen: pygame.Surface, audio):
        self.screen      = screen
        self.audio       = audio
        self.subpantalla = 'audio'   # 'audio' | 'controles'
        self.seleccion   = 0
        self._arrastando = False

        self._fuente_titulo  = Fuentes.obtener_fuente(40)
        self._fuente_tab     = Fuentes.obtener_fuente(28)
        self._fuente_label   = Fuentes.obtener_fuente(29)
        self._fuente_valor   = Fuentes.obtener_fuente(27)
        self._fuente_btn     = Fuentes.obtener_fuente(30)
        self._fuente_sub     = Fuentes.obtener_fuente(21)
        self._fuente_tecla   = Fuentes.obtener_fuente(25)
        self._fuente_control = Fuentes.obtener_fuente(26)

        # Panel centrado
        self._panel_rect = pygame.Rect(0, 0, self.PANEL_ANCHO, self.PANEL_ALTO)
        self._panel_rect.center = (Constantes.WIDTH // 2, Constantes.HEIGHT // 2)
        self._panel_surf = pygame.Surface(
            (self.PANEL_ANCHO, self.PANEL_ALTO), pygame.SRCALPHA
        )

        # Volúmenes actuales — se leen de los valores "crudos" del AudioManager
        # (lo que el usuario puso en el slider), NO de volumen_musica/sfx que
        # ya llevan la multiplicación por el volumen general aplicada.
        self._volumen = {
            'general': getattr(audio, 'volumen_general_raw', 1.0),
            'musica':  getattr(audio, 'volumen_musica_raw',  audio.volumen_musica),
            'sfx':     getattr(audio, 'volumen_sfx_raw',     audio.volumen_sfx),
        }

        # Pantalla completa
        self._pantalla_completa = bool(
            pygame.display.get_surface().get_flags() & pygame.FULLSCREEN
        )

        self._calcular_rects()

    # ── Layout ──────────────────────────────────────────────────────────────

    def _calcular_rects(self):
        cx = self._panel_rect.centerx
        pl = self._panel_rect.left
        pt = self._panel_rect.top

        # Tabs (Audio | Controles) — en pantalla
        tab_ancho = 180
        tab_alto  = 34
        tab_gap   = 8
        tab_y     = pt + 58
        self._tab_rects = {
            'audio':     pygame.Rect(cx - tab_ancho - tab_gap // 2, tab_y, tab_ancho, tab_alto),
            'controles': pygame.Rect(cx + tab_gap // 2,             tab_y, tab_ancho, tab_alto),
        }

        # Sliders — en pantalla
        self._slider_rects = {}
        inicio_y = pt + 130
        gap_y    = 82
        for i, (clave, _) in enumerate(self.SLIDERS):
            y    = inicio_y + i * gap_y
            rect = pygame.Rect(0, 0, self.SLIDER_ANCHO, self.SLIDER_ALTO)
            rect.centerx = cx
            rect.centery = y
            self._slider_rects[clave] = rect

        # Toggle pantalla completa — en pantalla
        toggle_y = pt + 130 + len(self.SLIDERS) * gap_y + 10
        self._toggle_rect = pygame.Rect(cx - 25, toggle_y, 50, 26)

        # Botón Volver — en pantalla
        btn = pygame.Rect(0, 0, self.BTN_ANCHO, self.BTN_ALTO)
        btn.centerx = cx
        btn.bottom  = self._panel_rect.bottom - 40
        self._btn_volver_rect = btn

    # ── Helpers locales ──────────────────────────────────────────────────────

    def _local(self, rect: pygame.Rect) -> pygame.Rect:
        """Convierte un Rect de pantalla a coordenadas locales del panel."""
        return rect.move(-self._panel_rect.x, -self._panel_rect.y)

    # ── Dibujo ──────────────────────────────────────────────────────────────

    def dibujar(self, hover_btn: bool = False, hover_tab: str = None):
        s = self._panel_surf
        s.fill(COLOR_PANEL_FONDO)
        pygame.draw.rect(s, COLOR_PANEL_BORDE, s.get_rect(), width=2, border_radius=12)

        # Título
        titulo = self._fuente_titulo.render("CONFIGURACION", True, COLOR_TITULO)
        s.blit(titulo, (self.PANEL_ANCHO // 2 - titulo.get_width() // 2, 16))

        # Tabs
        for clave, rect_p in self._tab_rects.items():
            r     = self._local(rect_p)
            activa = (clave == self.subpantalla)
            hover  = (clave == hover_tab)
            c_fondo = COLOR_BTN_HOVER  if (activa or hover) else COLOR_BTN_NORMAL
            c_borde = COLOR_TITULO     if activa             else COLOR_BTN_BORDE
            pygame.draw.rect(s, c_fondo, r, border_radius=6)
            pygame.draw.rect(s, c_borde, r, width=2 if activa else 1, border_radius=6)
            etiqueta = 'Audio' if clave == 'audio' else 'Controles'
            txt = self._fuente_tab.render(etiqueta, True,
                                          COLOR_TITULO if activa else COLOR_BTN_TEXTO)
            s.blit(txt, (r.centerx - txt.get_width() // 2,
                         r.centery - txt.get_height() // 2))

        if self.subpantalla == 'audio':
            self._dibujar_audio(s)
        else:
            self._dibujar_controles(s)

        # Botón Volver
        r = self._local(self._btn_volver_rect)
        c = COLOR_BTN_HOVER if hover_btn else COLOR_BTN_NORMAL
        pygame.draw.rect(s, c, r, border_radius=self.BTN_RADIO)
        pygame.draw.rect(s, COLOR_BTN_BORDE, r, width=2, border_radius=self.BTN_RADIO)
        txt = self._fuente_btn.render("Volver", True, COLOR_BTN_TEXTO)
        s.blit(txt, (r.centerx - txt.get_width() // 2,
                     r.centery - txt.get_height() // 2))

        # Pista inferior
        if self.subpantalla == 'audio':
            pista_txt = "W S ·   Esc volver"
        else:
            pista_txt = "Esc para volver"
        pista = self._fuente_sub.render(pista_txt, True, (90, 85, 110))
        s.blit(pista, (self.PANEL_ANCHO // 2 - pista.get_width() // 2,
                       self.PANEL_ALTO - 30))

        self.screen.blit(s, self._panel_rect)

    def _dibujar_audio(self, s):
        # Sliders
        for i, (clave, etiqueta) in enumerate(self.SLIDERS):
            r      = self._local(self._slider_rects[clave])
            es_sel = (i == self.seleccion)
            c_lbl  = COLOR_TITULO if es_sel else COLOR_LABEL

            # Etiqueta
            lbl = self._fuente_label.render(etiqueta, True, c_lbl)
            s.blit(lbl, (self.PANEL_ANCHO // 2 - lbl.get_width() // 2, r.y - 24))

            # Barra fondo
            pygame.draw.rect(s, COLOR_SLIDER_BG,
                             (r.x, r.y, self.SLIDER_ANCHO, self.SLIDER_ALTO),
                             border_radius=5)
            # Barra rellena
            vol    = self._volumen[clave]
            fill_w = int(vol * self.SLIDER_ANCHO)
            if fill_w > 0:
                pygame.draw.rect(s, COLOR_SLIDER_FILL,
                                 (r.x, r.y, fill_w, self.SLIDER_ALTO),
                                 border_radius=5)
            # Knob
            kx, ky = r.x + fill_w, r.y + self.SLIDER_ALTO // 2
            pygame.draw.circle(s, COLOR_SLIDER_KNOB, (kx, ky), self.KNOB_RADIO)
            if es_sel:
                pygame.draw.circle(s, COLOR_TITULO, (kx, ky), self.KNOB_RADIO, width=2)

            # Valor
            val_txt = self._fuente_valor.render(f"{int(vol * 100)}%", True, c_lbl)
            s.blit(val_txt, (r.x + self.SLIDER_ANCHO + 10,
                             ky - val_txt.get_height() // 2))

        # Toggle pantalla completa
        r_tog = self._local(self._toggle_rect)
        lbl_pc = self._fuente_label.render("Pantalla completa", True, COLOR_LABEL)
        lbl_x  = self.PANEL_ANCHO // 2 - (lbl_pc.get_width() + 14 + self._toggle_rect.width) // 2
        s.blit(lbl_pc, (lbl_x, r_tog.centery - lbl_pc.get_height() // 2))

        tog_x = lbl_x + lbl_pc.get_width() + 14
        tog_r = pygame.Rect(tog_x, r_tog.y, self._toggle_rect.width, self._toggle_rect.height)
        c_tog = COLOR_TOGGLE_ON if self._pantalla_completa else COLOR_TOGGLE_OFF
        pygame.draw.rect(s, c_tog, tog_r, border_radius=13)
        pygame.draw.rect(s, COLOR_BTN_BORDE, tog_r, width=2, border_radius=13)
        knob_cx = tog_r.right - 13 if self._pantalla_completa else tog_r.left + 13
        pygame.draw.circle(s, (220, 220, 230), (knob_cx, tog_r.centery), 10)
        # Guardar rect del toggle en pantalla para clicks
        self._toggle_rect_pantalla = pygame.Rect(
            self._panel_rect.x + tog_x,
            self._toggle_rect.y,
            self._toggle_rect.width,
            self._toggle_rect.height,
        )

    def _dibujar_controles(self, s):
        inicio_y = 110
        gap_y    = 34
        col_tecla = 80
        col_desc  = 210

        for i, (tecla, desc) in enumerate(self.CONTROLES):
            y = inicio_y + i * gap_y

            # Caja de tecla
            txt_tecla = self._fuente_tecla.render(tecla, True, COLOR_BTN_TEXTO)
            ancho_caja = max(90, txt_tecla.get_width() + 16)
            caja = pygame.Rect(col_tecla, y, ancho_caja, 26)
            pygame.draw.rect(s, COLOR_TECLA_BG,    caja, border_radius=5)
            pygame.draw.rect(s, COLOR_TECLA_BORDE, caja, width=1, border_radius=5)
            s.blit(txt_tecla, (caja.centerx - txt_tecla.get_width() // 2,
                               caja.centery - txt_tecla.get_height() // 2))

            # Descripción
            txt_desc = self._fuente_control.render(desc, True, COLOR_LABEL)
            s.blit(txt_desc, (col_desc, y + 26 // 2 - txt_desc.get_height() // 2))

    # ── Audio ────────────────────────────────────────────────────────────────

    def _aplicar(self):
        self.audio.set_volumenes(
            self._volumen['general'],
            self._volumen['musica'],
            self._volumen['sfx'],
        )

    def _set_volumen(self, clave: str, valor: float):
        self._volumen[clave] = max(0.0, min(1.0, valor))
        self._aplicar()

    # ── Pantalla completa ────────────────────────────────────────────────────

    def _toggle_fullscreen(self):
        self._pantalla_completa = not self._pantalla_completa
        pygame.display.toggle_fullscreen()

    # ── Interacción ──────────────────────────────────────────────────────────

    def hover_btn(self, mouse_pos) -> bool:
        return self._btn_volver_rect.collidepoint(mouse_pos)

    def hover_tab(self, mouse_pos) -> str | None:
        for clave, rect in self._tab_rects.items():
            if rect.collidepoint(mouse_pos):
                return clave
        return None

    def _slider_desde_x(self, clave, mouse_x):
        rect = self._slider_rects[clave]
        return max(0.0, min(1.0, (mouse_x - rect.x) / self.SLIDER_ANCHO))

    def _slider_en_pos(self, mouse_pos):
        for clave, rect in self._slider_rects.items():
            if rect.inflate(0, self.KNOB_RADIO * 4).collidepoint(mouse_pos):
                return clave
        return None

    def procesar_evento(self, event) -> bool:
        """Devuelve True si hay que cerrar el menú."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return True

            if self.subpantalla == 'audio':
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    self.seleccion = (self.seleccion + 1) % len(self.SLIDERS)
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.seleccion = (self.seleccion - 1) % len(self.SLIDERS)
                elif event.key == pygame.K_LEFT:
                    clave = self.SLIDERS[self.seleccion][0]
                    self._set_volumen(clave, self._volumen[clave] - self.SLIDER_PASO)
                elif event.key == pygame.K_RIGHT:
                    clave = self.SLIDERS[self.seleccion][0]
                    self._set_volumen(clave, self._volumen[clave] + self.SLIDER_PASO)
                elif event.key == pygame.K_f:
                    self._toggle_fullscreen()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._btn_volver_rect.collidepoint(event.pos):
                return True

            # Tabs
            tab = self.hover_tab(event.pos)
            if tab:
                self.subpantalla = tab
                return False

            if self.subpantalla == 'audio':
                # Toggle pantalla completa
                if hasattr(self, '_toggle_rect_pantalla') and \
                   self._toggle_rect_pantalla.collidepoint(event.pos):
                    self._toggle_fullscreen()
                    return False
                # Sliders
                clave = self._slider_en_pos(event.pos)
                if clave:
                    self._arrastando = clave
                    self.seleccion   = [s[0] for s in self.SLIDERS].index(clave)
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

    # ── Loop bloqueante (MenuPrincipal) ──────────────────────────────────────

    def ejecutar(self):
        """Loop bloqueante para usar desde el menú principal."""
        reloj = pygame.time.Clock()
        while True:
            reloj.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if self.procesar_evento(event):
                    return
            mouse = pygame.mouse.get_pos()
            self.dibujar(self.hover_btn(mouse), self.hover_tab(mouse))
            pygame.display.flip()
