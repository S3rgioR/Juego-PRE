"""Menú principal del juego.

Se ejecuta antes de construir las capas MVP.
Devuelve una acción ('jugar', 'cargar', 'salir') que main.py interpreta.

Diseño:
- Fondo oscuro con imagen del juego (misma que el fondo del nivel)
- Título grande centrado
- Cuatro botones apilados verticalmente
- Navegación con ratón y también con flechas + Enter

Hereda de MenuBase la lógica de selección/navegación/click; aquí solo
queda lo específico de este menú: el fondo a pantalla completa, el
dibujado de los botones con su paleta propia, y la resolución especial
de la opción 'config' (abre MenuConfig en vez de propagar la acción).
"""

import pygame
import Constantes
import Fuentes
from Menu import MenuBase
from MenuConfig import MenuConfig
from Import import obtener_ruta



# ── Paleta ──────────────────────────────────────────────────────────────────
COLOR_FONDO_OVERLAY = (10, 10, 30, 200)   # capa semitransparente sobre el fondo
COLOR_TITULO        = (230, 210, 160)      # dorado pálido
COLOR_BTN_NORMAL    = (40,  40,  70)       # botón sin hover
COLOR_BTN_HOVER     = (80,  70, 130)       # botón con hover
COLOR_BTN_BORDE     = (120, 100, 180)      # borde del botón
COLOR_BTN_TEXTO     = (220, 220, 255)      # texto del botón
COLOR_BTN_DISABLED  = (50,  50,  55)       # botón deshabilitado
COLOR_TEXTO_DISABLED= (100, 100, 110)      # texto deshabilitado


class MenuPrincipal(MenuBase):
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

    ACCION_ESCAPE = 'salir'

    BTN_ANCHO  = 320
    BTN_ALTO   = 54
    BTN_GAP    = 18       # separación entre botones
    BTN_RADIO  = 8        # redondeo de esquinas

    def __init__(self, screen, tiene_save=False, audio=None,
             abrir_config=None,
                 fondo_path: str = obtener_ruta("Assets/Enviorments/Fondo Pantalla de inicio/background.png"),):
        super().__init__(tiene_save=tiene_save)

        self._abrir_config = abrir_config or (lambda: MenuConfig(screen, audio).ejecutar())

        self.screen = screen
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

        self._calcular_rects(cx, inicio_y, self.BTN_ANCHO, self.BTN_ALTO, self.BTN_GAP)

    # ── Resolución especial de 'config' ─────────────────────────────────────

    def _on_seleccionar(self, accion: str) -> str | None:
        """'config' se resuelve aquí mismo (abre y vuelve) y no se propaga."""
        if accion == 'config':
            self._abrir_config()
            return None
        return accion

    # ── Dibujo ──────────────────────────────────────────────────────────────

    def dibujar(self, hover_idx: int = -1):
        """Dibuja un frame completo del menú sobre self.screen.

        No llama a pygame.display.flip() — eso es responsabilidad de quien
        controla el loop (main.py en ejecutar(), o el Presenter si este
        menú se llegara a integrar como overlay). Misma convención que
        MenuPausa.dibujar().
        """
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
            "Apreta w s para navegar       Apreta Enter o clica para seleccionar",
            True, (100, 95, 120)
        )
        self.screen.blit(
            pista,
            (Constantes.WIDTH // 2 - pista.get_width() // 2,
             Constantes.HEIGHT - 36)
        )

    # ── Loop de convenience (solo para el caso simple: main.py) ────────────

    def ejecutar(self) -> str:
        """Muestra el menú y bloquea hasta que el usuario elige una opción.

        Wrapper delgado sobre procesar_evento()/dibujar()/hover_idx(): no
        duplica lógica de eventos ni de dibujado, solo controla el reloj
        y el flip(). Pensado para el caso simple de main.py, donde no hay
        un Presenter todavía ejecutándose que pueda pilotar el menú.

        Returns
        -------
        str
            Una de: 'jugar', 'cargar', 'salir'.
        """
        reloj = pygame.time.Clock()

        while True:
            reloj.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 'salir'
                accion = self.procesar_evento(event)
                if accion is not None:
                    return accion

            hover = self.hover_idx(pygame.mouse.get_pos())
            self.dibujar(hover)
            pygame.display.flip()
